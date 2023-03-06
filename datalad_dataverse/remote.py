from __future__ import annotations

from pathlib import Path
import re
import sys

from annexremote import ExportRemote
from collections import namedtuple
from pyDataverse.api import DataAccessApi
from pyDataverse.models import Datafile
from requests import delete
from requests.auth import HTTPBasicAuth
from shutil import which

from datalad_next.annexremotes import (
    RemoteError,
    SpecialRemote,
    UnsupportedRequest,
    super_main,
)
from datalad_next.credman import CredentialManager
# this important is a vast overstatement, we only need
# `AnnexRepo.config`, nothing else
from datalad_next.datasets import LegacyAnnexRepo as AnnexRepo

from datalad_dataverse.utils import (
    get_api,
    format_doi,
    mangle_directory_names,
)

# Object to hold what's on dataverse's end for a given database id.
# We need the paths in the latest version (if the id is part of that) in order
# to know whether we need to replace rather than just upload a file, and we need
# to know whether an id is released, since that implies we can't replace it
# (but we could change the metadata, right?) and we can't actually delete it.
# The latter meaning: It can be removed from the new DRAFT version, but it's
# still available via its id from an older version of the dataverse dataset.
# This namedtuple is meant to be the value type of a dict with ids as its keys:
FileIdRecord = namedtuple("FileIdRecord", ["path", "is_released"])

# Needed to determine whether RENAMEEXPORT can be considered implemented.
CURL_EXISTS = which('curl') is not None


class DataverseRemote(ExportRemote, SpecialRemote):
    """Special remote to interface dataverse datasets.

    There are two modes of operation:
    - "Regular" special remote (configured with exporttree=false; default),
      where a flat ist of annex keys is put into that dataverse dataset and
    - export remote (configured with exporttree=yes), where the actual worktree
      is put into the dataverse dataset

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

    Export remote
    -------------

    In export mode the special remote can not conclude the annex key from a
    remote path in general. In order to be able to access versions of a file
    that are not part of the latest version (draft or not) of the dataverse
    dataset, reliance on recorded database IDs is crucial.

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
        # dataverse dataset identifier
        self._doi = None
        # dataverse instance URL
        self._url = None
        # dataverse native API handle
        self._api = None
        self._data_access_api = None
        self._token = None
        self._old_dataset_versions = None
        self._dataset_latest = None
        self._files_old = None
        self._files_latest = None
        self.is_draft = None

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
        self._doi = format_doi(doi)
        self._url = url
        # we need an acces token, use the repo's configmanager to
        # query for one
        repo = AnnexRepo(self.annex.getgitdir())
        # TODO the below is almost literally taken from
        # the datalad-annex:: implementation in datalad-next
        # this could become a comming helper
        # TODO https://github.com/datalad/datalad-dataverse/issues/171
        credman = CredentialManager(repo.config)
        credential_name = self.annex.getconfig('dlacredential')
        api = get_api(
            self._url,
            credman,
            credential_name=credential_name,
        )
        # store for reuse with data access API.
        # we do not initialize that one here, because it is only used
        # for file downloads
        self._token = api.api_token
        self._api = api

    def initremote(self):
        """
            Use this command to initialize a remote
            git annex initremote dv1 type=external externaltype=dataverse encryption=none
        """
        # we also need an active API connection for initremote,
        # simply run prepare()
        self.prepare()
        # check if instance is readable and authenticated
        resp = self._api.get_info_version()
        if resp.json()['status'] != 'OK':
            raise RuntimeError(f'Cannot connect to dataverse instance '
                               f'(status: {resp.json()["status"]})')

        # check if project with specified doi exists
        dv_ds = self._api.get_dataset(identifier=self._doi)
        if not dv_ds.ok:
            raise RuntimeError("Cannot find dataset")

    def checkpresent(self, key):
        stored_id = self._get_annex_fileid_record(key)
        if stored_id is not None:
            # First, check latest version. Second, check older versions.
            # This is to avoid requesting the full file list unless necessary.
            return stored_id in self.files_latest.keys() or \
                   stored_id in self.files_old.keys()
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
            return Path(key) in [f.path for f in self.files_latest.values()] or \
                   Path(key) in [f.path for f in self.files_old.values()]

    def transfer_store(self, key, local_file):
        datafile = Datafile()
        datafile.set({'filename': key, 'label': key})
        datafile.set({'pid': self._doi})

        self._upload_file(datafile=datafile,
                          key=key,
                          local_file=local_file,
                          remote_file=Path(key))

    def transfer_retrieve(self, key, file):
        stored_id = self._get_annex_fileid_record(key)
        if stored_id is not None:
            file_id = stored_id
        else:
            # Like in `self.checkpresent`, we fall back to path matching.
            # Delayed checking for availability from old versions is included.
            file_id = self._get_fileid_from_exportpath(Path(key), latest_only=False)
            if file_id is None:
                raise RemoteError(f"Key {key} unavailable")

        self._download_file(file_id, file)

    def remove(self, key):
        remote_file = Path(key)
        self._remove_file(key, remote_file)

    #
    # Export API
    #
    def checkpresentexport(self, key, remote_file):
        stored_id = self._get_annex_fileid_record(key)
        if stored_id is not None:
            # Only check latest version in export mode. Doesn't currently
            # work for keys from older versions, since annex fails to even
            # try. See https://github.com/datalad/datalad-dataverse/issues/146#issuecomment-1214409351.
            return stored_id in self.files_latest.keys()
        else:
            # In export mode, we need to fix remote paths:
            remote_file = mangle_directory_names(remote_file)
            return remote_file in [f.path for f in self.files_latest.values()]

    def transferexport_store(self, key, local_file, remote_file):
        remote_file = mangle_directory_names(remote_file)
        # TODO: See
        # https://github.com/datalad/datalad-dataverse/issues/83#issuecomment-1214406034
        if re.search(pattern=r'[^a-z0-9_\-.\\/\ ]',
                     string=str(remote_file.parent),
                     flags=re.ASCII | re.IGNORECASE):
            self.annex.error(f"Invalid character in directory name of "
                             f"{str(remote_file)}. Valid characters are a-Z, "
                             f"0-9, '_', '-', '.', '\\', '/' and ' ' "
                             f"(white space).")

        datafile = Datafile()
        datafile.set({'filename': remote_file.name,
                      'directoryLabel': str(remote_file.parent),
                      'label': remote_file.name,
                      'pid': self._doi})

        self._upload_file(datafile, key, local_file, remote_file)

    def transferexport_retrieve(self, key, local_file, remote_file):
        # In export mode, we need to fix remote paths:
        remote_file = mangle_directory_names(remote_file)

        file_id = self._get_annex_fileid_record(key) or self._get_fileid_from_exportpath(remote_file)
        if file_id is None:
            raise RemoteError(f"Key {key} unavailable")

        self._download_file(file_id, local_file)

    def removeexport(self, key, remote_file):
        remote_file = mangle_directory_names(remote_file)
        self._remove_file(key, remote_file)

    def renameexport(self, key, filename, new_filename):
        """Moves an exported file.

        If implemented, this is called by annex-export when a file was moved.
        Otherwise annex calls removeexport + transferexport_store, which doesn't
        scale well performance-wise.
        """
        # Note: In opposition to other API methods, `update_datafile_metadata`
        # is running `curl` in a subprocess. No idea why. As a consequence, this
        # depends on the availability of curl and the return value is not (as in
        # all other cases) a `requests.Response` object, but a
        # `subprocess.CompletedProcess`.
        # This apparently is planned to be changed in pydataverse 0.4.0:
        # https://github.com/gdcc/pyDataverse/issues/88
        if not CURL_EXISTS:
            raise UnsupportedRequest()

        filename = mangle_directory_names(filename)
        new_filename = mangle_directory_names(new_filename)

        file_id = self._get_annex_fileid_record(key) or self._get_fileid_from_exportpath(filename)
        if file_id is None:
            raise RemoteError(f"{key} not available for renaming")

        datafile = Datafile()
        datafile.set({'filename': new_filename.name,
                      'directoryLabel': str(new_filename.parent),
                      'label': new_filename.name,
                      'pid': self._doi})

        proc = self._api.update_datafile_metadata(
            file_id,
            json_str=datafile.json(),
            is_filepid=False,
        )
        if proc.returncode:
            raise RemoteError(f"Renaming failed: {proc.stderr}")

    #
    # Helpers
    #
    @property
    def data_access_api(self):
        if self._data_access_api is None:
            self._data_access_api = DataAccessApi(
                base_url=self._url,
                # this relies on having established the NativeApi in prepare()
                api_token=self._token,
            )
        return self._data_access_api

    @property
    def old_dataset_versions(self):
        """Full JSON record of the dataverse dataset.

        This is requested once when relevant to look for a key that is not
        present in the latest version of the dataverse dataset. In such case,
        `files_old` is build from it.
        """

        if self._old_dataset_versions is None:
            # This delivers a full record of all known versions of this dataset.
            # Hence, the file lists in the version entries may contain
            # duplicates (unchanged files across versions).
            self.message("Request all dataset versions", type='debug')
            versions = self._api.get_dataset_versions(self._doi)
            versions.raise_for_status()

            self._old_dataset_versions = versions.json()['data']
            # Expected structure in self._dataset is a list of (version-)
            # dictionaries, which should have a field 'files'. This again is a
            # list of dicts like this:
            #  {'description': '',
            #   'label': 'third_file.md',
            #   'restricted': False,
            #   'directoryLabel': 'subdir2',
            #   'version': 1,
            #   'datasetVersionId': 72,
            #   'dataFile': {'id': 682,
            #   'persistentId': '',
            #   'pidURL': '',
            #   'filename': 'third_file.md',
            #   'contentType': 'text/plain',
            #   'filesize': 9,
            #   'description': '',
            #   'storageIdentifier': 'local://1821bc70e68-c3c9dedcfce6',
            #   'rootDataFileId': -1,
            #   'md5': 'd8d77109f4a24efc3bd53d7cabb7ee35',
            #   'checksum': {'type': 'MD5',
            #                'value': 'd8d77109f4a24efc3bd53d7cabb7ee35'},
            #   'creationDate': '2022-07-20'}

            # Sort by version, so we can rely on the last entry to refer to the
            # latest version.
            # Note, that ('versionNumber', 'versionMinorNumber', 'versionState')
            # would look like this:
            # (None, None, 'DRAFT'), (2, 0, 'RELEASED'), (1, 0, 'RELEASED')
            # and we need a possible DRAFT to have the greatest key WRT sorting.
            self._old_dataset_versions.sort(
                key=lambda v: (v.get('versionNumber') or sys.maxsize,
                               v.get('versionMinorNumber') or sys.maxsize),
                reverse=False)
            # Remove "latest" - we already have that
            self._old_dataset_versions = self._old_dataset_versions[:-1]

        return self._old_dataset_versions

    @property
    def dataset_latest(self):
        """JSON representation on the latest version of the dataverse dataset.

        This is used to initialize `files_latest` and only requested once.
        """

        if self._dataset_latest is None:
            self.message("Request latest dataset version", type='debug')
            dataset = self._api.get_dataset(
                identifier=self._doi,
                version=":latest",
            )
            dataset.raise_for_status()
            self._dataset_latest = dataset.json()['data']['latestVersion']
        return self._dataset_latest

    @property
    def files_old(self):
        """Files available from older dataverse dataset versions.

        For quick lookup and deduplication, this is a dict {id: FileIdRecord}
        """

        if self._files_old is None:
            self._files_old = {
                f['dataFile']['id']: FileIdRecord(
                    Path(f.get('directoryLabel', '')) / f['dataFile']['filename'],
                    True  # older versions are always released
                )
                for file_lists in [
                    (version['files'], version['versionState'])
                    for version in self.old_dataset_versions
                ]
                for f in file_lists[0]
            }

        return self._files_old

    @property
    def files_latest(self):
        """Cache of files in the latest version of the dataverse dataset.

        This refers to the DRAFT version (if there is any) or the latest
        published version otherwise. That's the version pushes go into. Hence,
        this is needed to determine whether we need and can replace/remove a
        file, while the complete list in `self.files_old` is relevant for key
        retrieval of keys that are not present in the latest version anymore.

        Note, that whie initially we may not be in a draft, we are as soon as we
        change things (upload/repace/remove/rename). We keep track of those
        changes herein w/o rerequesting the new state.
        """

        if self._files_latest is None:
            # Latest version in self.dataset is first entry.
            self._files_latest = {
                f['dataFile']['id']: FileIdRecord(
                    Path(f.get('directoryLabel', '')) / f['dataFile']['filename'],
                    self.dataset_latest['versionState'] == "RELEASED",
                )
                for f in self.dataset_latest['files']
            }

        return self._files_latest

    def remove_from_filelist(self, id):
        """Update self.files_latest after removal"""
        # make sure this property actually exists before assigning:
        # (This may happen when git-annex-export decides to remove a key w/o
        # even considering checkpresent)
        self.files_latest
        self._files_latest.pop(id, None)

    def add_to_filelist(self, d):
        """Update self.files_latest after upload

        d: dict
          dataverse description dict of the file; this dict is in the list
          'data.files' of the response to a successful upload
        """
        # make sure this property actually exists before assigning:
        # (This may happen on `git-annex-copy --fast`)
        self.files_latest

        self._files_latest[d['dataFile']['id']] = FileIdRecord(
            Path(d.get('directoryLabel', '')) / d['dataFile']['filename'],
            False  # We just added - it can't be released
        )

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

    def set_stored_id(self, key, id):
        """Store a dataverse database id for a given key

        Parameters
        ----------
        key: str
            annex key to store the id for
        id: int or str
            dataverse database id for `key`. Empty string to unset.
        """
        self.annex.setstate(key, str(id))

    def _get_fileid_from_exportpath(self,
                                    path: Path,
                                    latest_only: bool = True) -> int | None:
        """Get the id of a dataverse file, that matches a given `Path` in the
        dataverse dataset.

        Parameters
        ----------
        path: Path
        latest_only: bool
            Whether to only consider the latest version on dataverse. If
            `False`, matching against older versions will only be performed
            when there was no match in the latest version (implies that an
            additional request may be performed)

        Returns
        -------
        int or None
        """
        existing_id = [i for i, f in self.files_latest.items()
                       if f.path == path]
        if not latest_only and not existing_id:
            existing_id = [i for i, f in self.files_old.items()
                           if f.path == path]
        return existing_id[0] if existing_id else None

    def _upload_file(self, datafile, key, local_file, remote_file):
        """helper for both transfer-store methods"""
        # If the remote path already exists, we need to replace rather than
        # upload the file, since otherwise dataverse would rename the file on
        # its end. However, this only concerns the latest version of the dataset
        # (which is what we are pushing into)!
        replace_id = self._get_fileid_from_exportpath(remote_file)
        if replace_id is not None:
            self.message(f"Replacing {remote_file} ...", type='debug')
            response = self._api.replace_datafile(
                identifier=replace_id,
                filename=local_file,
                json_str=datafile.json(),
                is_filepid=False,
            )
        else:
            self.message(f"Uploading {remote_file} ...", type='debug')
            response = self._api.upload_datafile(
                identifier=self._doi,
                filename=local_file,
                json_str=datafile.json(),
            )

        if response.status_code == 400 and \
                response.json()['status'] == "ERROR" and \
                "duplicate content" in response.json()['message']:
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
            response.raise_for_status()

        # Success.

        # If we replaced, `replaced_id` is not part of the latest version
        # anymore.
        if replace_id is not None:
            self.remove_from_filelist(re)
            # In case of replace we need to figure whether the replaced
            # ID was part of a DRAFT version only. In that case it's gone and
            # we'd need to remove the ID record. Otherwise, it's still retrieval
            # from an old, published version.
            # Note, that this would potentially trigger the request of the full
            # file list (`self.files_old`).
            if not (self.files_latest[replace_id].is_released or
                    replace_id in self.files_old.keys()):
                self.set_stored_id(key, "")

        uploaded_file = response.json()['data']['files'][0]
        # update cache:
        self.add_to_filelist(uploaded_file)
        # remember dataverse's database id for this key
        self.set_stored_id(key, uploaded_file['dataFile']['id'])

    def _download_file(self, file_id, local_file):
        """helper for both transfer-retrieve methods"""
        response = self.data_access_api.get_datafile(file_id)
        # http error handling
        response.raise_for_status()
        with open(local_file, "wb") as f:
            f.write(response.content)

    def _remove_file(self, key, remote_file):
        """helper for both remove methods"""
        rm_id = self._get_annex_fileid_record(key) or self._get_fileid_from_exportpath(remote_file)

        if rm_id is None:
            # We didn't find anything to remove. That should be fine and
            # considered a successful removal by git-annex.
            return
        if rm_id not in self.files_latest.keys():
            # We can't remove from older (hence published) versions.
            return

        status = delete(
            f'{self._url}/dvn/api/data-deposit/v1.1/swordv2/'
            f'edit-media/file/{rm_id}',
            # this relies on having established the NativeApi in prepare()
            auth=HTTPBasicAuth(self._token, ''))
        # http error handling
        status.raise_for_status()
        # We need to figure whether the removed ID was part of a released
        # version. In that case it's still retrievable from an old, published
        # version.
        # Note, that this would potentially trigger the request of the full
        # file list (`self.files_old`).
        if not (self.files_latest[rm_id].is_released or
                rm_id in self.files_old.keys()):
            self.message(f"Unset stored id for {key}", type='debug')
            self.set_stored_id(key, "")
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
        # This ID is not part of the latest version anymore.
        self.remove_from_filelist(rm_id)


def main():
    """cmdline entry point"""
    super_main(
        cls=DataverseRemote,
        remote_name='dataverse',
        description="transport file content to and from a Dataverse dataset",
    )
