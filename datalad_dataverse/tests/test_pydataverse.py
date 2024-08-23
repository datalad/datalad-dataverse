"""Tests all essential pydataverse behavior"""

import datetime
import json
from requests import delete
from requests.auth import HTTPBasicAuth

from datalad_next.tests.utils import md5sum

from .utils import (
    list_dataset_files,
    get_dvfile_with_md5,
)


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
        dataverse_instance_url,
):
    # the starting point of `dataverse_dataset` is a freshly
    # created, non-published dataset in draft mode, with no prior
    # version
    fcontent = 'some_content'
    fpath = tmp_path / 'dummy.txt'
    fpath.write_text(fcontent)
    src_md5 = md5sum(fpath)

    check_duplicate_file_deposition(
        dataverse_admin_api,
        dataverse_dataset,
        tmp_path)

    fileid = check_upload(
        dataverse_admin_api,
        dataverse_dataset, fcontent, fpath, src_md5, dataverse_instance_url)

    check_download(
        dataverse_dataaccess_api, fileid,
        dataverse_dataset, tmp_path / 'downloaded.txt', src_md5)

    # TODO replace_datafile
    # custom request to remove a file via `data-deposit` API


def check_download(api, fileid, dsid, fpath, src_md5):
    # TODO there is no standalone implementation of the following
    # reimplementing DataverseRemote._download_file

    # recent pydataverse requires saying `is_pid=False` for a file-id
    response = api.get_datafile(fileid, is_pid=False)
    # TODO this could also just be a download via HttpUrlOperations
    # avoiding any custom code
    assert response.status_code == 200
    with fpath.open("wb") as f:
        # accommodate old and newer pydataverse version
        try:
            it = response.iter_content
        except AttributeError:
            it = response.iter_bytes
        # use a stupdily small chunksize to actual get chunking on
        # our tiny test file
        for chunk in it(chunk_size=1):
            f.write(chunk)

    # confirm identity
    assert md5sum(fpath) == src_md5


def check_duplicate_file_deposition(api, dsid, tmp_path):
    content = 'identical'
    content_md5 = 'ee0cbdbacdada19376449799774976e8'
    for fname in ('nonunique1.txt', 'nonunique2.txt'):
        (tmp_path / fname).write_text(content)

    response = api.upload_datafile(
        identifier=dsid,
        filename=tmp_path / 'nonunique1.txt'
    )
    # we do not expect issues here
    response.raise_for_status()
    # now upload the second file with the same content
    response = api.upload_datafile(
        identifier=dsid,
        filename=tmp_path / 'nonunique2.txt'
    )
    response.raise_for_status()

    # check both files are available under their respective names
    flist = list_dataset_files(api, dsid)
    identicals = get_dvfile_with_md5(flist, content_md5, all_matching=True)
    assert len(identicals) == 2
    assert any(f['label'] == 'nonunique1.txt' and f['dataFile']['md5'] == content_md5
               for f in identicals)
    assert any(f['label'] == 'nonunique2.txt' and f['dataFile']['md5'] == content_md5
               for f in identicals)


def check_upload(api, dsid, fcontent, fpath, src_md5, dv_url):
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
    # TODO: seemingly discontinued between Dataverse 5.13 and 6.0?
    #assert df['pidURL'] == ''
    assert df['rootDataFileId'] == -1

    if 'localhost' in dv_url or '127.0.0.1' in dv_url:
        assert df['storageIdentifier'].startswith('local://')
    else:
        assert df['storageIdentifier'].startswith('s3://demo-dataverse')

    # report the file ID for external use
    return df['id']


def test_file_removal(
        tmp_path,
        dataverse_admin_api,
        dataverse_dataset,
):

    # the starting point of `dataverse_dataset` is a freshly
    # created, non-published dataset in draft mode, with no prior
    # version
    fcontent = 'some_content'
    fpath = tmp_path / 'dummy.txt'
    fpath.write_text(fcontent)
    response = dataverse_admin_api.upload_datafile(
        identifier=dataverse_dataset,
        filename=fpath,
    )
    # worked
    assert response.status_code == 200, \
        f"failed to upload file {response.status_code}: {response.json()}"
    # No further assertion on upload response - this is tested in
    # test_file_handling.

    fid = response.json()['data']['files'][0]['dataFile']['id']

    # This should be removable:
    status = delete(
        f'{dataverse_admin_api.base_url}/dvn/api/data-deposit/v1.1/swordv2/'
        f'edit-media/file/{fid}',
        auth=HTTPBasicAuth(dataverse_admin_api.api_token, ''))
    # TODO: Not sure, whether that is always a 204. Or why it would be at all
    # for that matter.
    assert status.status_code == 204, \
        f"failed to delete file {status.status_code}: {status.json()}"

    # Re-upload
    response = dataverse_admin_api.upload_datafile(
        identifier=dataverse_dataset,
        filename=fpath,
    )
    assert response.status_code == 200, \
        f"failed to upload file {response.status_code}: {response.json()}"
