"""Dataverse IO abstraction"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import (
    Path,
    PurePosixPath,
)
import re

from pyDataverse.api import ApiAuthorizationError
from pyDataverse.models import Datafile
from requests import (
    delete as delete_request,
    post as post_request,
)
from requests.auth import HTTPBasicAuth
import sys

from pyDataverse.api import DataAccessApi

from .utils import mangle_path


# Object to hold what's on dataverse's end for a given database file id.
# We need the paths in the latest version (if the id is part of that) in order
# to know whether we need to replace rather than just upload a file, and we need
# to know whether an id is released, since that implies we can't replace it
# (but we could change the metadata, right?) and we can't actually delete it.
# The latter meaning: It can be removed from the new DRAFT version, but it's
# still available via its id from an older version of the dataverse dataset.
# This namedtuple is meant to be the value type of a dict with ids as its keys:
@dataclass
class FileIdRecord:
    path: PurePosixPath
    is_released: bool
    is_latest_version: bool


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

    If ``root_path`` is set, then all paths in the scope of the Dataverse
    dataset will be prefixed with this path. This establishes an alternative
    root path for all dataset operations. It will not be possible to upload,
    download, rename (etc) files from outside this prefix scope, or across
    scopes.

    On initialization only a record of what is in the latest version (draft or
    not) of the dataverse dataset is retrieved, including an annotation of
    content on whether it is released. This annotation is crucial, since it has
    implications on what to record should changes be uploaded.  For
    example: It is not possible to actually remove content from a released
    version.

    This record is later maintained locally when changes are made without ever
    requesting a full update again. In case of checking the presence of a file
    that does not appear to be part of the latest version, a request for such a
    record on all known dataverse dataset versions is made.
    """
    def __init__(self, api, dsid: str, root_path: str | None = None):
        # dataverse native API handle
        self._api = api
        self._dsid = dsid
        # unconditional prefix of `directoryLabel` for any remote deposit
        # in POSIX notation
        # (filter out '')
        self._root_path = PurePosixPath(root_path) if root_path else None

        self._data_access_api = None
        # mapping of dataverse database fileids to FileIdRecord
        self._file_records = None
        # flag whether a listing across all dataset versions
        # was already retrieved and incorporated into the file_records
        self._knows_all_versions = False

        # check if instance is readable and authenticated
        resp = api.get_info_version()
        if resp.json()['status'] != 'OK':
            raise RuntimeError(f'Cannot connect to dataverse instance '
                               f'(status: {resp.json()["status"]})')

        # check if project with specified doi exists
        # TODO ask for ':latest' and cache?
        dv_ds = api.get_dataset(identifier=dsid)
        if not dv_ds.status_code < 400:
            raise RuntimeError("Cannot find dataset")

    def get_fileid_from_path(
            self, path: PurePosixPath, *, latest_only: bool) -> int | None:
        """Get the id of a file, that matches a given path

        The path is interpreted as the conjunction of a ``directoryLabel`` and
        a ``label`` (filename) in dataverse terminology.

        Parameters
        ----------
        path: PurePosixPath
        latest_only: bool
            Whether to only consider the latest version on dataverse. If
            `False`, matching against older versions will only be performed
            when there was no match in the latest version (implies that an
            additional request may be performed)

        Returns
        -------
        int or None
        """
        if not latest_only:
            self._ensure_file_records_for_all_versions()
        path = self._mangle_path(path)
        # get all file id records that match the path, and are latest version,
        # if desired
        match_path = dict(
            (i, f) for i, f in self._file_records_by_fileid.items()
            if f.path == path
            if latest_only is False or f.is_latest_version is True
        )
        if not match_path:
            # no match
            return None
        else:
            # any number of matches, report first one
            return match_path.popitem()[0]

    def has_fileid(self, fid: int) -> bool:
        self._ensure_file_records_for_all_versions()
        return fid in self._file_records_by_fileid

    def has_fileid_in_latest_version(self, fid: int) -> bool:
        rec = self._file_records_by_fileid.get(fid)
        if rec is None:
            return False
        else:
            return rec.is_latest_version

    def has_path(self, path: PurePosixPath) -> bool:
        path = self._mangle_path(path)
        self._ensure_file_records_for_all_versions()
        return path in set(
            f.path for f in self._file_records_by_fileid.values()
        )

    def has_path_in_latest_version(self, path: PurePosixPath) -> bool:
        path = self._mangle_path(path)
        return path in set(
            f.path for f in self._file_records_by_fileid.values()
            if f.is_latest_version
        )

    def is_released_file(self, fid: int) -> bool:
        rec = self._file_records_by_fileid.get(fid)
        if rec is None:
            return False
        else:
            return rec.is_released

    def download_file(self, fid: int, path: Path):
        # pydataverse does not support streaming downloads
        # https://github.com/gdcc/pyDataverse/issues/49
        # the code below is nevertheless readied for such a
        # scenario
        response = self.data_access_api.get_datafile(fid, is_pid=False, data_format="original")
        # http error handling
        response.raise_for_status()
        with path.open("wb") as f:
            # accommodate old and newer pydataverse version
            try:
                it = response.iter_content
            except AttributeError:
                it = response.iter_bytes
            # `chunk_size=None` means
            # "read data in whatever size the chunks are received"
            for chunk in it(chunk_size=None):
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
        self._file_records_by_fileid.pop(fid, None)

    def upload_file(self,
                    local_path: Path,
                    remote_path: PurePosixPath,
                    replace_id: int | None = None) -> int:
        remote_path = self._mangle_path(remote_path)
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
            self._file_records_by_fileid.pop(replace_id, None)

        upload_rec = response.json()['data']['files'][0]
        uploaded_df = upload_rec['dataFile']
        # update cache:
        # make sure this property actually exists before assigning:
        # (This may happen on `git-annex-copy --fast`)
        self._file_records_by_fileid[uploaded_df['id']] = FileIdRecord(
            PurePosixPath(upload_rec.get('directoryLabel', '')) / \
            uploaded_df['filename'],
            is_released=False,   # We just added - it can't be released
            is_latest_version=True,
        )
        # return the database fileid of the upload
        return uploaded_df['id']

    def rename_file(self,
                    new_path: PurePosixPath,
                    rename_id: int | None = None,
                    rename_path: PurePosixPath | None = None):
        """
        Raises
        ------
        RuntimeError
          Whenever the operation cannot or did not succeed. This could be
          because of a missing dependency, or because the file in question
          cannot be renamed (included in an earlier version).
        """
        if rename_id is None and rename_path is None:
            raise ValueError('rename_id and rename_path cannot both be `None`')

        # mangle_path for rename_path is done inside get_fileid_from_path()
        # in the conditional below
        new_path = self._mangle_path(new_path)

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

        response = self.update_file_metadata(
            rename_id,
            json_str=datafile.json(),
            is_filepid=False,
        )
        # TODO depending on the release status, we may have to remove
        # the previous record from the internal listing
        response.raise_for_status()

        # the response-content on-success has something like this:
        # b'File Metadata update has been completed:
        #   {"label":"place.txt","directoryLabel":"fresh",...,"id":1845936}
        # pull it out
        d = json.loads(
            re.match(b'.*(?P<rec>{.*})$',
                     response.content).groupdict()['rec']
        )
        self._file_records_by_fileid[d['id']] = FileIdRecord(
            PurePosixPath(d.get('directoryLabel', '')) / d['label'],
            is_released=False,  # We just renamed - it can't be released
            is_latest_version=True,
        )

    def update_file_metadata(self,
                             identifier,
                             json_str=None,
                             is_filepid=False):

        base_str = self._api.base_url_api_native
        if is_filepid:
            query_str = "{0}/files/:persistentId/metadata?persistentId={1}".format(
                base_str, identifier
            )
        else:
            query_str = "{0}/files/{1}/metadata".format(base_str, identifier)

        assert self._api.api_token
        headers = {"X-Dataverse-key": self._api.api_token}

        resp = post_request(
            query_str,
            files={'jsonData': (None, json_str.encode())},
            headers=headers
        )
        if resp.status_code == 401:
            error_msg = resp.json()["message"]
            raise ApiAuthorizationError(
                "ERROR: POST HTTP 401 - Authorization error {0}. MSG: {1}".format(
                    query_str, error_msg
                )
            )
        return resp

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

    def _mangle_path(self, path: str | PurePosixPath) -> PurePosixPath:
        if self._root_path:
            # we cannot use mangle_path() directly for type conversion,
            # because we have to add a root_path first in order to ensure
            # that it gets mangled properly too, in case it needs to
            path = self._root_path / PurePosixPath(path)
        return mangle_path(path)

    def _ensure_file_records_for_all_versions(self) -> None:
        if self._knows_all_versions:
            return

        # This delivers a full record of all known versions of this dataset.
        # Hence, the file lists in the version entries may contain
        # duplicates (unchanged files across versions).
        versions = self._api.get_dataset_versions(self._dsid)
        versions.raise_for_status()

        dataset_versions = versions.json()['data']
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
        dataset_versions.sort(
            key=lambda v: (v.get('versionNumber') or sys.maxsize,
                           v.get('versionMinorNumber') or sys.maxsize),
            reverse=False)
        self._file_records = {}
        # iterate over all versions but the latest, and label the records
        # as such
        for version in dataset_versions[:-1]:
            self._file_records.update(
                self._get_file_records_from_version_listing(
                    version,
                    latest=False,
                )
            )
        # and the latest version
        self._file_records.update(self._get_file_records_from_version_listing(
            dataset_versions[-1],
            latest=True,
        ))
        # set flag to never run this code again
        self._knows_all_versions = True

    def _get_file_records_from_version_listing(
            self, version: dict, latest: bool) -> dict:
        return {
            f['dataFile']['id']: FileIdRecord(
                PurePosixPath(f.get('directoryLabel', '')) / \
                f['dataFile']['filename'],
                version['versionState'] == "RELEASED",
                is_latest_version=latest,
            )
            for f in version['files']
        }

    @property
    def _file_records_by_fileid(self):
        """Cache of files in the latest version of the dataverse dataset.

        This refers to the DRAFT version (if there is any) or the latest
        published version otherwise. That's the version pushes go into. Hence,
        this is needed to determine whether we need and can replace/remove a
        file, while the complete list in `self.files_old` is relevant for key
        retrieval of keys that are not present in the latest version anymore.

        Note, that whie initially we may not be in a draft, we are as soon as we
        change things (upload/replace/remove/rename). We keep track of those
        changes herein w/o rerequesting the new state.
        """

        if self._file_records is None:
            # we have a clean slate, populate with latest.
            # if that is not sufficient, callers will need
            # to call _ensure_file_records_for_all_versions()
            # first
            dataset = self._api.get_dataset(
                identifier=self._dsid,
                version=":latest",
            )
            dataset.raise_for_status()
            # Latest version in self.dataset is first entry.
            self._file_records = self._get_file_records_from_version_listing(
                dataset.json()['data']['latestVersion'],
                latest=True,
            )
        return self._file_records
