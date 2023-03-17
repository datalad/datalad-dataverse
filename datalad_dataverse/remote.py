"""git-annex special remote with export capabilities"""

from __future__ import annotations

from annexremote import ExportRemote

from datalad_next.annexremotes import (
    RemoteError,
    UnsupportedRequest,
    super_main,
)

from .baseremote import DataverseRemote as BaseDataverseRemote


class DataverseRemote(ExportRemote, BaseDataverseRemote):
    """Special remote to interface dataverse datasets with export-cabilities

    The class extends the base implementation with a git-annex EXPORT protocol
    extension for special remotes.

    It does not implement IMPORTTREE.
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
