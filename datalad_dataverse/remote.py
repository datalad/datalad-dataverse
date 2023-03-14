from __future__ import annotations

from annexremote import ExportRemote

from datalad_next.annexremotes import (
    RemoteError,
    UnsupportedRequest,
    super_main,
)

from .baseremote import DataverseRemote as BaseDataverseRemote


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
        # Only check latest version of dataverse dataset here.
        # Doesn't currently work for keys from older versions,
        # because annex does not even call CHECKPRESENT
        # https://github.com/datalad/datalad-dataverse/issues/146#issuecomment-1214409351
        stored_ids = self._get_annex_fileid_record(key)
        if stored_ids:
            return self._get_fileid_from_remotepath(
                remote_file, latest_only=True) in stored_ids
        else:
            # Without a stored ID, we fall back to path matching. See
            # https://github.com/datalad/datalad-dataverse/issues/246 for the
            # rationale.
            return self._dvds.has_path_in_latest_version(remote_file)

    def transferexport_store(self, key, local_file, remote_file):
        # If the remote path already exists, we need to replace rather than
        # upload the file, since otherwise dataverse would rename the file on
        # its end. However, this only concerns the latest version of the
        # dataset (which is what we are pushing into)!
        replace_id = self._get_fileid_from_remotepath(
            remote_file, latest_only=True)

        self._upload_file(remote_file, key, local_file, replace_id)

    def transferexport_retrieve(self, key, local_file, remote_file):
        cand_ids = self._get_annex_fileid_record(key)
        if not cand_ids:
            # there are no IDs on record, but there may well be a file
            # at the remote, otherwise git-annex would not call this
            # here. Try lookup by path
            file_id = self._get_fileid_from_remotepath(
                remote_file, latest_only=True)
            if file_id:
                cand_ids.add(file_id)

        if not cand_ids:
            raise RemoteError(f"Key {key} unavailable")

        # Content retrieval doesn't care where the content is coming
        # from. Hence, taking the first ID on record should suffice.
        # TODO it may be that any one of the record fileid is not longer
        # available. An alternative would be to simply loop over the
        # records and have get_fileid_from_remotepath() generate the
        # last candidate.
        file_id = cand_ids.pop()
        self._download_file(file_id, local_file)

    def removeexport(self, key, remote_file):
        # For removal, path matching needs to be done, because we could have
        # several copies (dataverse IDs) of the content. Need to remove the one
        # that also matches the path.
        rm_id = self._get_fileid_from_remotepath(remote_file, latest_only=True)
        # _remove_file() takes care of removing the fileid record
        self._remove_file(key, rm_id)

    def renameexport(self, key, filename, new_filename):
        """Moves an exported file.

        If implemented, this is called by annex-export when a file was moved.
        Otherwise annex calls removeexport + transferexport_store, which
        does not scale well performance-wise.
        """
        # We cannot rely on ID lookup, since there could be several. We need to
        # match the path.
        rename_id = self._get_fileid_from_remotepath(
            filename, latest_only=True)
        try:
            self._dvds.rename_file(
                new_path=new_filename,
                rename_id=rename_id,
                rename_path=filename,
            )
        except RuntimeError as e:
            raise UnsupportedRequest() from e


def main():
    """cmdline entry point"""
    super_main(
        cls=DataverseRemote,
        remote_name='dataverse',
        description="transport file content to and from a Dataverse dataset",
    )
