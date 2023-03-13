from __future__ import annotations

from pathlib import Path

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
    get_api,
    format_doi,
)


class DataverseRemote(SpecialRemote):
    """Special remote to interface dataverse datasets.

    Dataverse
    ---------

    Dataverse datasets come with their own versioning. A version is created upon
    publishing a draft version. When a change is pushed, it is altering an
    already existing draft version or - if none existed - the push (implicitly)
    creates a new draft version. Publishing is not part of this special remotes
    operations as it has no means to "discover" that this should happen (it only
    communicates with git-annex on a per-file basis and does not even know what
    annex command ran).

    Files put on dataverse have a database ID associated with them, while there
    "path" in the dataverse dataset is treated as metadata to that file. The ID
    is persistent, but not technically a content identifier as it is not created
    from the content like hash. However, once files are published (by being part
    of a published dataset version) those IDs can serve as a content identifier
    for practical purposes, since they are not going to change anymore. There's
    no "real" guarantee for that, but in reality changing it would require some
    strange DB migration to be performed on the side of the respective dataverse
    instance. Note, however, that a file can be pushed into a draft version and
    replaced/removed before it was ever published. In that case the ID of an
    annex key could be changed. Hence, to some extent the special remote needs
    to be aware of whether an annex key and its ID was part of a released
    version of the dataverse dataset in order to make use of those IDs.

    Recording the IDs allows accessing older versions of a file even in export
    mode, as well as faster accessing keys for download. The latter is because
    the API requires the ID, and a path based approach would therefore require
    looking up the ID first (adding a request). Therefore, the special remote
    records the IDs of annex keys and tries to rely on them if possible.

    There is one more trap to mention with dataverse and that is its limitations
    to directory and file names.
    See https://github.com/IQSS/dataverse/issues/8807#issuecomment-1164434278

    Regular special remote
    ----------------------

    In principle the regular special remote simply maintains a flat list of
    annex keys in the dataverse dataset, where the presented file names are the
    anney keys. Therefore, it is feasible to simply rely on the remote path of a
    key when checking for its presence. However, as laid out above, it is faster
    to utilize knowledge about the database ID, so the idea is to use path
    matching only as a fallback.

    Implementation note
    -------------------

    The special remote at first only retrieves a record of what is in the latest
    version (draft or not) of the dataverse dataset including an annotation of
    content on whether it is released. This annotation is crucial, since it has
    implications on what to record should changes be pushed to it.
    For example:
    It is not possible to actually remove content from a released version. That
    means, if annex asks the special remote to remove content, it can only make
    sure that the respective key is not part of the current draft anymore. Its
    ID, however, remains on record. If the content was not released yet, it is
    actually gone and the ID is taken off the record.

    This record is retrieved lazily when first required, but only once (avoiding
    an additional per-key request) and then updated locally when changes are
    pushed. (Note, that we know that we only ever push into a draft version)
    In case of checking the presence of a key that does not appear to be part of
    the latest version, a request for such a record on all known dataverse
    dataset versions is made. Again, this is lazy and only one request. This may
    potentially be a relatively expensive request, but the introduced latency by
    having smaller but possibly much more requests is likely a lot more
    expensive.
    """

    def __init__(self, *args):
        super().__init__(*args)
        self.configs['url'] = 'The Dataverse URL for the remote'
        self.configs['doi'] = 'DOI to the dataset'
        self.configs['dlacredential'] = \
            'Identifier used to retrieve an API token from a local ' \
            'credential store'
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
        # standardize formating to minimize complexity downstream
        doi = format_doi(doi)
        # we need an acces token, use the repo's configmanager to
        # query for one
        repo = AnnexRepo(self.annex.getgitdir())
        # TODO the below is almost literally taken from
        # the datalad-annex:: implementation in datalad-next
        # this could become a comming helper
        # TODO https://github.com/datalad/datalad-dataverse/issues/171
        credman = CredentialManager(repo.config)
        credential_name = self.annex.getconfig('dlacredential')
        # we keep this here to not have OnlineDataverseDataset
        # have to deal with datalad-specific
        api = get_api(
            url,
            credman,
            credential_name=credential_name,
        )
        # TODO this can raise, capture and raise proper error
        self._dvds = OnlineDataverseDataset(api, doi)

    def initremote(self):
        """
            Use this command to initialize a remote
            git annex initremote dv1 type=external externaltype=dataverse encryption=none
        """
        # we also need an active API connection for initremote,
        # simply run prepare()
        self.prepare()

    def checkpresent(self, key):
        stored_id = self._get_annex_fileid_record(key)
        if stored_id is not None:
            return self._dvds.has_fileid(stored_id)
        else:
            # We do not have an ID on record for this key.
            # Fall back to filename matching for two reasons:
            # 1. We have to deal with the special keys of the datalad-annex
            #    git-remote-helper. They must be matched by name, since the
            #    throwaway repo using them doesn't have a relevant git-annex
            #    branch with an ID record (especially when cloning via the
            #    git-remote-helper)
            # 2. We are in "regular annex mode" here - keys are stored under
            #    their name. Falling back to name matching allows to recover
            #    data, despite a lost or not generated id record for it. For
            #    example on could have uploaded lots of data via git-annex-copy,
            #    but failed to push the git-annex branch somewhere.
            return self._dvds.has_path(Path(key))

    def transfer_store(self, key, local_file):
        # If the remote path already exists, we need to replace rather than
        # upload the file, since otherwise dataverse would rename the file on
        # its end. However, this only concerns the latest version of the
        # dataset (which is what we are pushing into)!
        replace_id = self._get_fileid_from_key(key, latest_only=True)

        self._upload_file(
            # TODO must be PurePosixPath
            remote_path=Path(key),
            key=key,
            local_file=local_file,
            replace_id=replace_id,
        )

    def transfer_retrieve(self, key, file):
        stored_id = self._get_annex_fileid_record(key)
        if stored_id is not None:
            file_id = stored_id
        else:
            # Like in `self.checkpresent`, we fall back to path matching.
            # Delayed checking for availability from old versions is included.
            file_id = self._get_fileid_from_key(key, latest_only=False)
            if file_id is None:
                raise RemoteError(f"Key {key} unavailable")

        self._download_file(file_id, file)

    def remove(self, key):
        rm_id = self._get_annex_fileid_record(key) \
            or self._get_fileid_from_key(key, latest_only=True)
        self._remove_file(key, rm_id)

    #
    # Helpers
    #
    def _get_annex_fileid_record(self, key: str) -> int | None:
        """Get the dataverse database id from the git-annex branch

        This is using the getstate/setstate special remote feature. Hence, a
        stored id only exists, if the key was put to the dataverse instance by
        this special remote.

        Parameters
        ----------
        key: str
            annex key to retrieve the id for

        Returns
        -------
        int or None
        """
        stored_id = self.annex.getstate(key)
        if stored_id == "":
            return None
        else:
            return int(stored_id)

    def _set_annex_fileid_record(self, key, id):
        """Store a dataverse database id for a given key

        Parameters
        ----------
        key: str
            annex key to store the id for
        id: int or str
            dataverse database id for `key`. Empty string to unset.
        """
        self.annex.setstate(key, str(id))

    def _get_fileid_from_key(self,
                             key: str,
                             *,
                             latest_only: bool) -> int | None:
        """Get the id of a dataverse file, that matches a given annex key
        dataverse dataset.

        This method assumes that keys are deposited under paths that are
        identical to the key name.

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
            Path(key),
            latest_only=latest_only,
        )

    def _get_fileid_from_remotepath(
            self,
            path: Path,
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
                # not hash based (for example the special keys fo datalad-annex
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
                self._set_annex_fileid_record(key, "")

        # remember dataverse's database id for this key
        self._set_annex_fileid_record(key, upload_id)

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

        self._dvds.remove_file(rm_id)

        # We need to figure whether the removed ID was part of a released
        # version. In that case it's still retrievable from an old, published
        # version.
        # Note, that this would potentially trigger the request of the full
        # file list (`self.files_old`).
        if not self._dvds.is_released_file(rm_id):
            self.message(f"Unset stored id for {key}", type='debug')
            self._set_annex_fileid_record(key, "")
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
            # useful or desireable to always do that.
            # Otherwise not seeing a solution ATM. See https://github.com/datalad/datalad-dataverse/issues/146#issuecomment-1214409351
            pass


def main():
    """cmdline entry point"""
    super_main(
        cls=DataverseRemote,
        remote_name='dataverse',
        description="transport file content to and from a Dataverse dataset",
    )
