"""Tests all essential pydataverse behavior"""

import datetime

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

    # TODO replace_datafile
    # TODO get_datafile
    # TODO update_datafile_metadata
    # custom request to remove a file via `data-deposit` API


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
