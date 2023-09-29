"""git-annex special remote"""

from __future__ import annotations

from pathlib import (
    Path,
    PurePath,
    PurePosixPath,
)

from requests.exceptions import HTTPError

from datalad_next.annexremotes import (
    RemoteError,
    SpecialRemote,
    super_main,
)
from datalad_next.credman import CredentialManager
# this important is a vast overstatement, we only need
# `AnnexRepo.config`, nothing else
from datalad_next.datasets import LegacyAnnexRepo as AnnexRepo

from .dataset import OnlineDataverseDataset
from .utils import (
    get_native_api,
    format_doi,
)


class DataverseRemote(SpecialRemote):
    """Special remote for IO with Dataverse datasets.

    This remote provides the standard set of operations: CHECKPRESENT,
    STORE, RETRIEVE, and REMOVE.

    It uses the pyDataverse package internally, which presently imposes some
    limitations, such as poor handling of large-file downloads.

    The following sections contain notes on dataverse and this particular
    implementation.

    Dataverse
    ---------

    Dataverse datasets come with their own versioning. A version is created
    upon publishing a draft version. When a change is pushed, it is altering an
    already existing draft version or, if none existed, the push (implicitly)
    creates a new draft version. Publishing is not part of this special
    remote's operations.

    Files uploaded to Dataverse have an associated database file ID. Their
    "path" inside a dataset is a combination of a ``label`` and a
    ``directoryLabel`` that jointly must be unique in a Dataverse dataset.
    However, the are only metadata associated with the file ID.

    A file ID is persistent, but not technically a content identifier as it is
    not created from the content like hash.

    Recording the IDs with git-annex enables faster accessing for download,
    because a dataset content listing request can be avoided.  Therefore, the
    special remote records the IDs of annex keys and tries to rely on them if
    possible.

    Dataverse imposes strict naming limitations for directories and files.
    See https://github.com/IQSS/dataverse/issues/8807#issuecomment-1164434278
    Therefore, remote paths are mangles to match these limitations.
    """

    def __init__(self, *args):
        super().__init__(*args)
        self.configs['url'] = 'URL of the Dataverse site'
        self.configs['doi'] = \
            'DOI-style persistent identifier of the Dataverse dataset'
        self.configs['rootpath'] = \
            'optional alternative root path to use in the Dataverse dataset'
        self.configs['credential'] = \
            'name of a DataLad credential with a Dataverse API token to use'
        # dataverse dataset interface
        self._dvds = None

    #
    # Essential API
    #
    def prepare(self):
        # remove any trailing slash from URL
        url = self.annex.getconfig('url').rstrip('/')
        if not url:
            raise ValueError('url must be specified')
        doi = self.annex.getconfig('doi')
        if not doi:
            raise ValueError('doi must be specified')
        dv_root_path = self.annex.getconfig('rootpath')
        # standardize formatting to minimize complexity downstream
        doi = format_doi(doi)
        # we need an access token, use the repo's configmanager to query for one
        repo = AnnexRepo(self.annex.getgitdir())
        credman = CredentialManager(repo.config)
        credential_name = self.annex.getconfig('credential')
        credential_realm = url.rstrip('/') + '/dataverse'
        credential_name, cred = credman.obtain(
            name=credential_name if credential_name else None,
            prompt=f'A dataverse API token is required for access. '
                   f'Find it at {url} by clicking on your name at the top '
                   f'right corner and then clicking on API Token',
            # give to make legacy credentials accessible
            type_hint='token',
            expected_props=['secret'],
            query_props={'realm': credential_realm},
        )
        # the cred must have a secret at this point as it was in expected_props
        apitoken = cred['secret']
        # we keep this here to not have OnlineDataverseDataset
        # have to deal with datalad-specific
        api = get_native_api(
            url,
            apitoken,
        )
        # TODO this can raise, capture and raise proper error
        self._dvds = OnlineDataverseDataset(api, doi, root_path=dv_root_path)
        # save the credential, now that it has successfully been used
        credman.set(credential_name, _lastused=True, **cred)

    def initremote(self):
        """
            Use this command to initialize a remote
            git annex initremote dv1 type=external externaltype=dataverse encryption=none
        """
        # we also need an active API connection for initremote,
        # simply run prepare()
        self.prepare()

    def checkpresent(self, key):
        stored_ids = self._get_annex_fileid_record(key)
        if stored_ids:
            # In non-export mode, it shouldn't matter which of the recorded IDs
            # the key is available from. In fact, can't think of scenario that
            # would lead to several to begin with.
            return any(self._dvds.has_fileid(stored_id)
                       for stored_id in stored_ids)

        # We do not have an ID on record for this key, check at dataverse
        # for this key (generates a path from the key itself)
        file_id = self._get_fileid_from_key(key, latest_only=False)

        if file_id:
            # store this ID locally to speed up future retrieval
            # (avoids getting a dataset listing first)
            self._add_annex_fileid_record(key, file_id)

        return file_id is not None

    def transfer_store(self, key, local_file):
        # If the remote path already exists, we need to replace rather than
        # upload the file, since otherwise dataverse would rename the file on
        # its end. However, this only concerns the latest version of the
        # dataset (which is what we are pushing into)!
        replace_id = self._get_fileid_from_key(key, latest_only=True)

        self._upload_file(
            remote_path=self._get_remotepath_for_key(key),
            key=key,
            local_file=local_file,
            replace_id=replace_id,
        )

    def transfer_retrieve(self, key, file):
        stored_ids = self._get_annex_fileid_record(key)
        if stored_ids:
            # For content retrieval it doesn't matter which ID we are
            # downloading. Only content matters. Hence, first entry
            # and be done.
            file_id = stored_ids.pop()
        else:
            # Like in `self.checkpresent`, we fall back to path matching.
            # Delayed checking for availability from old versions is included.
            file_id = self._get_fileid_from_key(key, latest_only=False)
            if file_id is None:
                raise RemoteError(f"Key {key} unavailable")

        self._download_file(file_id, file)

    def remove(self, key):
        rm_ids = self._get_annex_fileid_record(key) \
            or [self._get_fileid_from_key(key, latest_only=True)]
        # the loop is only here because the tooling could handle
        # multiple IDs, but the feature is only used for export-mode.
        # Not here.
        for rm_id in rm_ids:
            self._remove_file(key, rm_id)

    #
    # Helpers
    #
    def _get_annex_fileid_record(self, key: str) -> set:
        """Get a Dataverse database file ID for a key from git-annex

        This is using the getstate/setstate special remote feature. Hence, a
        stored ID only exists, if the key was put to the dataverse instance by
        this special remote.

        Parameters
        ----------
        key: str
          Annex key to retrieve the ID for

        Returns
        -------
        set(int)
          A set is returned, because multiple file IDs can be stored
          for each key (Dataverse assigns different IDs for each unique
          combination of file content and associated metadata).
        """
        stored_id = self.annex.getstate(key)
        return set(int(n.strip())
                   for n in stored_id.split(',')
                   if n.strip())

    def _set_annex_fileid_record(self, key: str, fileids: list | set) -> None:
        """Store a dataverse database id for a given key

        Parameters
        ----------
        key: str
          Annex key to store the id for
        fileids: list|set of int
          Dataverse database ID(s) for ``key``. Empty sequence to unset.
        """
        self.annex.setstate(key, ", ".join(str(i) for i in fileids))

    def _add_annex_fileid_record(self, key: str, fileid: int) -> None:
        """Add a dataverse database ID to annex' record for `key`

        Parameters
        ----------
        key: str
          Annex key to store the id for
        fileid: int
          Dataverse database ID for ``key``
        """
        r = self._get_annex_fileid_record(key)
        r.add(fileid)
        self._set_annex_fileid_record(key, r)

    def _remove_annex_fileid_record(self, key: str, fileid: int) -> None:
        """Remove a dataverse database ID from annex' record for `key`

        Parameters
        ----------
        key: str
          Annex key to store the id for
        fileid: int
          Dataverse database ID for ``key``
        """

        r = self._get_annex_fileid_record(key)
        r.discard(fileid)
        self._set_annex_fileid_record(key, r)

    def _get_remotepath_for_key(self, key: str) -> PurePosixPath:
        """Return the canonical remote path for a given key

        Parameters
        ----------
        key: str
          git-annex key

        Returns
        -------
        PurePosixPath
          annex/<dirhash-lower>/<key>
        """
        # dirhash is reported in platform conventions by git-annex
        dirhash = PurePath(self.annex.dirhash_lower(key))
        return PurePosixPath(
            'annex',
            dirhash,
            key,
        )

    def _get_fileid_from_key(self,
                             key: str,
                             *,
                             latest_only: bool) -> int | None:
        """Get the id of a dataverse file, that matches a given annex key
        dataverse dataset.

        Parameters
        ----------
        key:
            Annex key to perform the lookup for
        latest_only: bool
            Whether to only consider the latest version on dataverse. If
            `False`, matching against older versions will only be performed
            when there was no match in the latest version (implies that an
            additional request may be performed)

        Returns
        -------
        int or None
        """
        # for now this also just performs a look-up by path
        # but if other metadata-based lookups become possible
        # this implementation could change
        # https://github.com/datalad/datalad-dataverse/issues/188
        return self._get_fileid_from_remotepath(
            self._get_remotepath_for_key(key),
            latest_only=latest_only,
        )

    def _get_fileid_from_remotepath(
            self,
            path: PurePosixPath,
            *,
            latest_only: bool) -> int | None:
        return self._dvds.get_fileid_from_path(path, latest_only=latest_only)

    def _upload_file(self, remote_path, key, local_file, replace_id):
        """helper for both transfer-store methods"""
        if replace_id is not None:
            self.message(f"Replacing fileId {replace_id} ...", type='debug')
        else:
            self.message(f"Uploading key {key} ...", type='debug')

        try:
            upload_id = self._dvds.upload_file(Path(local_file), remote_path, replace_id)
        except HTTPError as e:
            if e.response.status_code == 400 and \
                    e.response.json()['status'] == "ERROR" and \
                    "duplicate content" in e.response.json()['message']:
                # Ignore this one for now.
                # TODO: This needs better handling. Currently, this happens in
                # git-annex-testremote ("store when already present").
                # Generally it's kinda fine, but we'd better figure this out more
                # reliably. Note, that we have to deal with annex keys, which are
                # not hash based (for example the special keys of datalad-annex
                # git-remote-helper).
                # Hence, having the key on the remote end, doesn't mean it's
                # identical. So, we can't catch it beforehand this way.
                self.message(
                    f"Failed to upload {key}, since dataverse says we are "
                    f"replacing with duplicate content.", type='debug'
                )
                return  # nothing changed and nothing needs to be done
            else:
                raise

        if replace_id is not None:
            # In case of replace we need to figure whether the replaced
            # ID was part of a DRAFT version only. In that case it's gone and
            # we'd need to remove the ID record. Otherwise, it's still
            # retrieval from an old, published version.
            # Note, that this would potentially trigger the request of the full
            # file list (`self.files_old`).
            if not self.is_released_file(replace_id):
                self._remove_annex_fileid_record(key, replace_id)

        # remember dataverse's database id for this key
        self._add_annex_fileid_record(key, upload_id)

    def _download_file(self, file_id, local_file):
        """helper for both transfer-retrieve methods"""
        self._dvds.download_file(file_id, Path(local_file))

    def _remove_file(self, key: str, rm_id: int | None):
        """Remove a file by dataverse fileId

        It is OK to call this method even when there is ``None``. It anticipates
        this case in order to provide uniform handling.
        """
        if rm_id is None:
            # We don't have anything to remove. That should be fine and
            # considered a successful removal by git-annex.
            return
        if not self._dvds.has_fileid_in_latest_version(rm_id):
            # We can't remove from older (hence published) versions.
            return

        try:
            self._dvds.remove_file(rm_id)
        except Exception as e:
            raise RemoteError from e

        # We need to figure whether the removed ID was part of a released
        # version. In that case it's still retrievable from an old, published
        # version.
        # Note, that this would potentially trigger the request of the full
        # file list (`self.files_old`).
        if not self._dvds.is_released_file(rm_id):
            self.message(f"Unset stored id for {key}", type='debug')
            self._remove_annex_fileid_record(key, rm_id)
        else:
            # Despite not actually deleting from the dataverse database, we
            # currently loose access to the old key (in export mode, that is),
            # because annex registers a successful REMOVEEXPORT and there seems
            # to be no way to make annex even try to run a CHECKPRESENT(-EXPORT)
            # on an export remote in such case. get, fsck, checkpresentkey -
            # none of them would do.
            # TODO: We could try to setpresenturl for the not-really-removed
            # file, if it has a persistent URL (should be findable in
            # self.old_dataset_versions) or even via api/access/datafile/811.
            # However, that depends on permissions, etc., so not clear it's
            # useful or desirable to always do that.
            # Otherwise not seeing a solution ATM. See https://github.com/datalad/datalad-dataverse/issues/146#issuecomment-1214409351
            pass


def main():
    """cmdline entry point"""
    super_main(
        cls=DataverseRemote,
        remote_name='dataverse',
        description="transport file content to and from a Dataverse dataset",
    )
