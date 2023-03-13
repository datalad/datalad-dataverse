"""Tests OnlineDataverseDataset

These tests (should) somewhat close mirror the ones fpr pydataverse.
At least as long as we are using that API layer.
"""

from pathlib import (
    Path,
    PurePosixPath,
)

from datalad_next.tests.utils import md5sum

from ..dataset import OnlineDataverseDataset as ODD


def test_file_handling(
        tmp_path,
        dataverse_admin_api,
        dataverse_dataaccess_api,
        dataverse_dataset,
):
    # the starting point of `dataverse_dataset` is a freshly
    # created, non-published dataset in draft mode, with no prior
    # version
    odd = ODD(dataverse_admin_api, dataverse_dataset)

    fcontent = 'some_content'
    fpath = tmp_path / 'dummy.txt'
    fpath.write_text(fcontent)
    src_md5 = md5sum(fpath)

    fileid = check_upload(odd, fcontent, fpath, src_md5)

    check_download(odd, fileid, tmp_path / 'downloaded.txt', src_md5)

    check_remove(odd, fileid, Path(fpath.name))

    check_duplicate_file_deposition(odd, tmp_path)

    # TODO replace_datafile


def check_download(odd, fileid, fpath, src_md5):
    odd.download_file(fileid, fpath)
    assert md5sum(fpath) == src_md5


def check_duplicate_file_deposition(odd, tmp_path):
    content = 'identical'
    fpaths = [tmp_path / 'nonunique1.txt', tmp_path / 'nonunique2.txt']
    for fp in fpaths:
        fp.write_text(content)

    f1 = odd.upload_file(fpaths[0], PurePosixPath(fpaths[0].name))
    # now upload the second file with the same content
    f2 = odd.upload_file(fpaths[1], PurePosixPath(fpaths[1].name))

    # check both files are available under their respective names
    assert f1 != f2
    assert odd.has_fileid(f1)
    assert odd.has_fileid(f2)
    assert odd.has_path(PurePosixPath(fpaths[0].name))
    assert odd.has_path(PurePosixPath(fpaths[1].name))


def check_upload(odd, fcontent, fpath, src_md5):
    # the simplest possible upload, just a source file name
    remote_path = Path(fpath.name)
    file_id = odd.upload_file(fpath, remote_path)
    # internal consistency
    assert odd.has_fileid(file_id)
    assert odd.has_fileid_in_latest_version(file_id)
    assert odd.has_path(remote_path)
    assert odd.has_path_in_latest_version(remote_path)
    assert odd.get_fileid_from_path(remote_path, latest_only=True) == file_id
    assert odd.get_fileid_from_path(remote_path, latest_only=False) == file_id
    assert not odd.is_released_file(file_id)

    return file_id


def check_remove(odd, file_id, remote_path):
    odd.remove_file(file_id)
    assert not odd.has_fileid(file_id)
    assert not odd.has_fileid_in_latest_version(file_id)
    assert not odd.has_path(remote_path)
    assert not odd.has_path_in_latest_version(remote_path)
    assert odd.get_fileid_from_path(remote_path, latest_only=True) == None
    assert odd.get_fileid_from_path(remote_path, latest_only=False) == None
    assert not odd.is_released_file(file_id)
