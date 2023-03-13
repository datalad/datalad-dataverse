from __future__ import annotations

import re

from annexremote import ExportRemote
from pyDataverse.models import Datafile

from datalad_next.annexremotes import (
    RemoteError,
    UnsupportedRequest,
    super_main,
)


from .baseremote import DataverseRemote as BaseDataverseRemote
from .dataset import CURL_EXISTS
from .utils import (
    mangle_directory_names,
)


class DataverseRemote(ExportRemote, BaseDataverseRemote):
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
    #
    # Export API
    #
    def checkpresentexport(self, key, remote_file):
        stored_id = self._get_annex_fileid_record(key)
        if stored_id is not None:
            # Only check latest version in export mode. Doesn't currently
            # work for keys from older versions, since annex fails to even
            # try. See https://github.com/datalad/datalad-dataverse/issues/146#issuecomment-1214409351.
            return self._dvds.has_fileid_in_latest_version(stored_id)
        else:
            # In export mode, we need to fix remote paths:
            remote_file = mangle_directory_names(remote_file)
            return self._dvds.has_path_in_latest_version(remote_file)

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

        # If the remote path already exists, we need to replace rather than
        # upload the file, since otherwise dataverse would rename the file on
        # its end. However, this only concerns the latest version of the
        # dataset (which is what we are pushing into)!
        replace_id = self._get_fileid_from_remotepath(
            remote_file, latest_only=True)

        self._upload_file(remote_file, key, local_file, replace_id)

    def transferexport_retrieve(self, key, local_file, remote_file):
        # In export mode, we need to fix remote paths:
        remote_file = mangle_directory_names(remote_file)

        file_id = self._get_annex_fileid_record(key) \
            or self._get_fileid_from_remotepath(remote_file, latest_only=True)
        if file_id is None:
            raise RemoteError(f"Key {key} unavailable")

        self._download_file(file_id, local_file)

    def removeexport(self, key, remote_file):
        remote_file = mangle_directory_names(remote_file)
        rm_id = self._get_annex_fileid_record(key) \
            or self._get_fileid_from_remotepath(remote_file, latest_only=True)
        self._remove_file(key, rm_id)

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

        file_id = self._get_annex_fileid_record(key) \
            or self._get_fileid_from_remotepath(filename, latest_only=True)
        if file_id is None:
            raise RemoteError(f"{key} not available for renaming")

        # TODO needs to move to OnlineDataverseDataset
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


def main():
    """cmdline entry point"""
    super_main(
        cls=DataverseRemote,
        remote_name='dataverse',
        description="transport file content to and from a Dataverse dataset",
    )
