"""Tests OnlineDataverseDataset

These tests (should) somewhat close mirror the ones for pydataverse.
At least as long as we are using that API layer.
"""

from pathlib import PurePosixPath
import json

from datalad_next.tests.utils import md5sum

from ..dataset import OnlineDataverseDataset as ODD
from ..utils import mangle_path


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

    check_file_metadata_update(dataverse_admin_api, dataverse_dataset, odd,
                               fileid, fpath)

    fileid = check_replace_file(odd, fileid, tmp_path)

    check_rename_file(odd, fileid)

    check_remove(odd, fileid, PurePosixPath(fpath.name))

    check_duplicate_file_deposition(odd, tmp_path)


def check_rename_file(odd, fileid, name='place.txt'):
    new_path = PurePosixPath('fresh') / name
    assert not odd.has_path(new_path)
    assert odd.has_fileid(fileid)
    odd.rename_file(new_path, fileid)
    assert odd.has_fileid(fileid)
    assert odd.has_path_in_latest_version(new_path)


def check_replace_file(odd, fileid, tmp_path):
    fpath = tmp_path / 'replace_source.txt'
    fpath.write_text('some_new_content')
    remote_path = PurePosixPath('downstairs') / fpath.name

    odd.has_fileid(fileid)
    # we replace the file AND give it a new name at the same time
    new_fileid = odd.upload_file(fpath, remote_path, fileid)
    assert fileid != new_fileid
    assert not odd.has_fileid(fileid)
    assert odd.has_fileid(new_fileid)
    assert odd.has_path_in_latest_version(remote_path)
    return new_fileid


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
    remote_path = PurePosixPath(fpath.name)
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


def check_file_metadata_update(api, dsid, odd, fileid, fpath):

    def _get_md(fid):
        # TODO: Metadata retrieval is still using pydataverse.
        response = api.get_datafile_metadata(
            fid, is_filepid=False, is_draft=True, auth=True)
        assert response.status_code == 200
        om = response.json()
        return om

    def _update_md(fid, rec, mdid=None):
        response = odd.update_file_metadata(
            fid,
            json_str=json.dumps(rec),
            is_filepid=False,
        )

        assert response.status_code == 200
        # Note, what we actually get in response.text is something like this:
        # 'File Metadata update has been completed: {"label":"dummy.txt", \
        # "description":"test description","restricted":false,"id":608}'
        # Meaning: In opposition to other NativeApi responses where we get
        # valid JSON, we can't use response.json() right away. Would need a
        # regex to extract the JSON part.
        if mdid:
            # if given, we check that the metadata record ID is included in
            # the outcome report
            assert f'"id":{mdid}' in response.text

    # the original metadata for this file on dataverse
    om = _get_md(fileid)
    # this is a subset of what `upload_datafile()` reported
    assert om['label'] == str(mangle_path(fpath.name))
    assert om['description'] == ''
    assert om['restricted'] is False
    # this is "the id of the file metadata version" according to the docs
    assert om['id']

    # update the description and verify it was applied
    _update_md(fileid, {'description': 'test description'}, om['id'])
    mm = _get_md(fileid)
    assert mm['description'] == 'test description'
    # this "file metadata version id" does not update
    assert mm['id'] == om['id']

    # amend metadata with other info that it should support according to the
    # docs
    _update_md(
        fileid,
        {
            # capitalization is key here!
            # https://guides.dataverse.org/en/latest/api/native-api.html#list-files-in-a-dataset
            # says `provFreeform`, but this lets the key be discarded silently
            'provFreeForm': 'myprov',
            'categories': ['Data'],
        },
        om['id'],
    )
    mm = _get_md(fileid)
    # description was not included in the 2nd update, but persists
    # update != replacement
    assert mm['description'] == 'test description'
    assert mm['categories'] == ['Data']
    # this field would be ideal to record an annex-key as an external
    # 'sameAs' reference. however, it is not reported in the
    # `get_dataset()` not in the `get_datafiles_metadata()` listings.
    # One a per-file `get_datafile_metadata()` (like done in this test)
    # reveals it -- at least for draft-mode datasets.
    assert mm['provFreeForm'] == 'myprov'
    # still no "file metadata version id" update
    assert mm['id'] == om['id']

    # 'label' and 'filename' are one and the same thing
    _update_md(fileid, {'label': 'mykey'}, om['id'])
    mm = api.get_datafiles_metadata(dsid).json()['data']
    info = [m for m in mm if m['label'] == 'mykey'][0]
    assert info['label'] == info['dataFile']['filename'] == 'mykey'
    old = [m for m in mm if m['label'] == mangle_path(fpath.name)]
    assert old == []


def test_name_mangling(
        tmp_path,
        dataverse_admin_api,
        dataverse_dataaccess_api,
        dataverse_dataset,
):
    odd = ODD(dataverse_admin_api, dataverse_dataset)

    paths = (
        tmp_path / ".dot-in-front" 'c1.txt',
        tmp_path / " space-in-front" 'c2.txt',
        tmp_path / "-minus-in-front" 'c3.txt',
        tmp_path / "Ö-in-front" 'c4.txt',
        tmp_path / ".Ö-dot-Ö-in-front" 'c5.txt',
        tmp_path / " Ö-space-Ö-in-front" 'c6.txt',
    )

    path_info = dict()
    for path in paths:
        if path.parent != tmp_path:
            path.parent.mkdir()
        fcontent = path.name
        path.write_text(path.name)
        src_md5 = md5sum(path)
        fileid = check_upload(odd, fcontent, path, src_md5)
        path_info[path] = (src_md5, fileid)

    for path, (src_md5, fileid) in path_info.items():
        check_download(odd, fileid, tmp_path / 'downloaded.txt', src_md5)

        check_file_metadata_update(
            dataverse_admin_api,
            dataverse_dataset,
            odd,
            fileid,
            path)

        fileid = check_replace_file(odd, fileid, tmp_path)
        check_rename_file(odd, fileid, name="ren" + path.name)
        check_remove(odd, fileid, PurePosixPath(path.name))
        check_duplicate_file_deposition(odd, tmp_path)
