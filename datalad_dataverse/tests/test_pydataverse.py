"""Tests all essential pydataverse behavior"""

import datetime
import json

from datalad_next.tests.utils import md5sum

#
# functionality tested here is all candidate for a dedicated pydataverse
# abstraction for use in datalad-dataverse. however, first all functionality
# has to be cataloged and the required features confirmed
#


def test_file_handling(
        tmp_path,
        dataverse_admin_api,
        dataverse_dataaccess_api,
        dataverse_dataset,
):
    # the starting point of `dataverse_dataset` is a freshly
    # created, non-published dataset in draft mode, with no prior
    # version
    fcontent = 'some_content'
    fpath = tmp_path / 'dummy.txt'
    fpath.write_text(fcontent)
    src_md5 = md5sum(fpath)

    fileid = check_upload(
        dataverse_admin_api,
        dataverse_dataset, fcontent, fpath, src_md5)

    check_download(
        dataverse_dataaccess_api, fileid,
        dataverse_dataset, tmp_path / 'downloaded.txt', src_md5)

    check_file_metadata_update(
        dataverse_admin_api, dataverse_dataset, fileid, fpath)

    # TODO replace_datafile
    # custom request to remove a file via `data-deposit` API


def check_file_metadata_update(api, dsid, fileid, fpath):
    def _get_md(fid):
        response = api.get_datafile_metadata(
            fileid, is_filepid=False, is_draft=True, auth=True)
        assert response.status_code == 200
        om = response.json()
        return om

    def _update_md(fid, rec, mdid=None):
        proc = api.update_datafile_metadata(
            fid,
            json_str=json.dumps(rec),
            is_filepid=False,
        )
        # curl ran without error
        assert proc.returncode == 0
        if mdid:
            # if give, we check that the metadata record ID is included in
            # the outcome report
            assert f'"id":{mdid}' in str(proc.stdout)

    # the orginal metadata for this file on dataverse
    om = _get_md(fileid)
    # this is a subset of what `upload_datafile()` reported
    assert om['label'] == fpath.name
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
    # stil no "file metadata version id" update
    assert mm['id'] == om['id']

    # 'label' and 'filename' are one and the same thing
    _update_md(fileid, {'label': 'mykey'}, om['id'])
    mm = api.get_datafiles_metadata(dsid).json()['data'][0]
    assert mm['label'] == mm['dataFile']['filename'] == 'mykey'


def check_download(api, fileid, dsid, fpath, src_md5):
    # TODO there is no standalone implementation of the following
    # reimplementing DataverseRemote._download_file
    response = api.get_datafile(fileid)
    # TODO this could also just be a download via HttpUrlOperations
    # avoiding any custom code
    assert response.status_code == 200
    with fpath.open("wb") as f:
        # use a stupdly small chunksize to actual get chunking on
        # our tiny test file
        for chunk in response.iter_content(chunk_size=1):
            f.write(chunk)

    # confirm identity
    assert md5sum(fpath) == src_md5


def check_upload(api, dsid, fcontent, fpath, src_md5):
    # the simplest possible upload, just a source file name
    response = api.upload_datafile(
        identifier=dsid,
        filename=fpath,
    )
    # worked
    assert response.status_code == 200
    # verify structure of response
    rj = response.json()
    assert rj['status'] == 'OK'
    rfiles = rj['data']['files']
    # one file uploaded, one report
    assert len(rfiles) == 1
    rfile = rfiles[0]
    # for a fresh upload a bunch of things should be true
    assert rfile['description'] == ''
    assert rfile['label'] == fpath.name
    assert rfile['restricted'] is False
    assert rfile['version'] == 1
    assert rfile['datasetVersionId']  # we are not testing for identity
    # most info is in a 'dataFile' dict
    df = rfile['dataFile']
    assert df['contentType'] == 'text/plain'
    assert df['creationDate'] == datetime.datetime.today().strftime('%Y-%m-%d')
    # unclear if this is always a copy of the prop above
    assert df['description'] == rfile['description']
    assert df['filename'] == fpath.name
    assert df['filesize'] == len(fcontent)
    assert df['id']
    assert df['checksum']['type'] == 'MD5'
    assert df['md5'] == df['checksum']['value'] == src_md5
    assert df['persistentId'] == ''
    assert df['pidURL'] == ''
    assert df['rootDataFileId'] == -1
    assert df['storageIdentifier'].startswith('s3://demo-dataverse')

    # report the file ID for external use
    return  df['id']
