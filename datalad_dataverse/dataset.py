from __future__ import annotations

from collections import namedtuple

from pathlib import Path
from pyDataverse.models import Datafile
from requests import delete as delete_request
from requests.auth import HTTPBasicAuth
from shutil import which
import sys

from pyDataverse.api import DataAccessApi

from .utils import mangle_path

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


class OnlineDataverseDataset:
    """Representation of Dataverse dataset in a remote instance.

    Apart from providing an API for basic operations on such a dataset,
    a main purpose of this class is the uniform and consistent mangling
    of local DataLad datasets path to the corresponding counterparts
    on Dataverse. Dataverse imposing strict limits to acceptably names
    for `directoryLabel` and `label`. So strict, that it rules out anything
    not representable by a subset of ASCII, and therefore any non-latin
    alphabet. See the documentation of the ``mangle_path()`` function
    for details.
    """
    def __init__(self, api, dsid: str):
        # dataverse native API handle
        self._api = api
        self._dsid = dsid

        self._data_access_api = None
        self._old_dataset_versions = None
        self._dataset_latest = None
        self._files_old = None
        self._files_latest = None

        # check if instance is readable and authenticated
        resp = api.get_info_version()
        if resp.json()['status'] != 'OK':
            raise RuntimeError(f'Cannot connect to dataverse instance '
                               f'(status: {resp.json()["status"]})')

        # check if project with specified doi exists
        # TODO ask for ':latest' and cache?
        dv_ds = api.get_dataset(identifier=dsid)
        if not dv_ds.ok:
            raise RuntimeError("Cannot find dataset")

    def get_fileid_from_path(
            self, path: Path, *, latest_only: bool) -> int | None:
        """Get the id of a file, that matches a given path

        The path is interpreted as the conjunction of a ``directoryLabel`` and
        a ``label`` (filename) in dataverse terminology.

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
        path = mangle_path(path)
        existing_id = [i for i, f in self.files_latest.items()
                       if f.path == path]
        if not latest_only and not existing_id:
            existing_id = [i for i, f in self.files_old.items()
                           if f.path == path]
        return existing_id[0] if existing_id else None

    def has_fileid(self, fid: int) -> bool:
        # First, check latest version. Second, check older versions.
        # This is to avoid requesting the full file list unless necessary.
        return fid in self.files_latest.keys() \
            or fid in self.files_old.keys()

    def has_fileid_in_latest_version(self, fid: int) -> bool:
        return fid in self.files_latest.keys()

    def has_path(self, path: Path) -> bool:
        path = mangle_path(path)
        return path in [f.path for f in self.files_latest.values()] \
            or path in [f.path for f in self.files_old.values()]

    def has_path_in_latest_version(self, path: Path) -> bool:
        path = mangle_path(path)
        return path in [f.path for f in self.files_latest.values()]

    def is_released_file(self, fid: int) -> bool:
        latest_rec = self.files_latest.get(fid)
        return ((latest_rec and latest_rec.is_released)
                or fid in self.files_old.keys())

    def download_file(self, fid: int, path: Path):
        # pydataverse does not support streaming downloads
        # https://github.com/gdcc/pyDataverse/issues/49
        # the code below is nevertheless readied for such a
        # scenario
        response = self.data_access_api.get_datafile(fid)
        # http error handling
        response.raise_for_status()
        with path.open("wb") as f:
            # `chunk_size=None` means
            # "read data in whatever size the chunks are received"
            for chunk in response.iter_content(chunk_size=None):
                f.write(chunk)

    def remove_file(self, fid: int):
        status = delete_request(
            f'{self._api.base_url}/dvn/api/data-deposit/v1.1/swordv2/'
            f'edit-media/file/{fid}',
            # this relies on having established the NativeApi in prepare()
            auth=HTTPBasicAuth(self._api.api_token, ''))
        # http error handling
        status.raise_for_status()
        # This ID is not part of the latest version anymore.
        self.remove_from_filelist(fid)

    def upload_file(self,
                    local_path: Path,
                    remote_path: Path,
                    replace_id: int | None = None) -> int:
        remote_path = mangle_path(remote_path)
        datafile = Datafile()
        # remote file metadata
        datafile.set({
            # if we do not give `label`, it would use the local filename
            'label': remote_path.name,
            # the model enforces this property, despite `label` being the
            # effective setter, and despite it being ignore and replaced
            # we the local filename
            'filename': remote_path.name,
            'directoryLabel': str(remote_path.parent),
            'pid': self._dsid,
        })
        if replace_id is not None:
            response = self._api.replace_datafile(
                identifier=replace_id,
                filename=local_path,
                json_str=datafile.json(),
                # we are shipping the database fileid (int)
                is_filepid=False,
            )
        else:
            response = self._api.upload_datafile(
                identifier=self._dsid,
                filename=local_path,
                json_str=datafile.json(),
            )
        response.raise_for_status()

        # Success.

        # If we replaced, `replaced_id` is not part of the latest version
        # anymore.
        if replace_id is not None:
            self.remove_from_filelist(replace_id)

        uploaded_file = response.json()['data']['files'][0]
        # update cache:
        self.add_to_filelist(uploaded_file)
        # return the database fileid of the upload
        return uploaded_file['dataFile']['id']

    def rename_file(self,
                    new_path: Path,
                    rename_id: int | None = None,
                    rename_path: Path | None = None):
        """
        Raises
        ------
        RuntimeError
          Whenever the operation cannot or did not succeed. This could be
          because of a missing dependency, or because the file in question
          cannot be renamed (included in an earlier version).
        """
        # Note: In opposition to other API methods, `update_datafile_metadata`
        # is running `curl` in a subprocess. No idea why. As a consequence, this
        # depends on the availability of curl and the return value is not (as in
        # all other cases) a `requests.Response` object, but a
        # `subprocess.CompletedProcess`.
        # This apparently is planned to be changed in pydataverse 0.4.0:
        # https://github.com/gdcc/pyDataverse/issues/88
        if not CURL_EXISTS:
            raise RuntimeError('renaming a file needs CURL')

        if rename_id is None and rename_path is None:
            raise ValueError('rename_id and rename_path cannot both be `None`')

        # mangle_path for rename_path is done inside get_fileid_from_path()
        # in the conditional below
        new_path = mangle_path(new_path)

        if rename_id is None:
            # unclear to MIH why `latest_only=True`, presumably because
            # renaming in an earlier version does not transparently reassign
            # a copy of the file record, but is treated as a disallowed
            # modification attempt
            rename_id = self.get_fileid_from_path(
                rename_path, latest_only=True)

        if rename_id is None:
            raise RuntimeError(f"file {rename_path} cannot be renamed")

        datafile = Datafile()
        datafile.set({
            # same as with upload `filename` and `label` must be redundant
            'label': new_path.name,
            'filename': new_path.name,
            'directoryLabel': str(new_path.parent),
            'pid': self._dsid,
        })

        proc = self._api.update_datafile_metadata(
            rename_id,
            json_str=datafile.json(),
            is_filepid=False,
        )
        if proc.returncode:
            raise RuntimeError(f"Renaming failed: {proc.stderr}")

        # https://github.com/datalad/datalad-dataverse/issues/236
        # we have no record to update the internal file list,
        # we must wipe it out
        self._files_latest = None
        self._dataset_latest = None

    #
    # Helpers
    #
    @property
    def data_access_api(self):
        if self._data_access_api is None:
            self._data_access_api = DataAccessApi(
                base_url=self._api.base_url,
                api_token=self._api.api_token,
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
            versions = self._api.get_dataset_versions(self._dsid)
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
            dataset = self._api.get_dataset(
                identifier=self._dsid,
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
