from unittest.mock import patch
from urllib.parse import quote as urlquote

from datalad.api import (
    Dataset,
    clone,
)
from datalad.tests.utils_pytest import (
    skip_if,
    with_tempfile,
)
from datalad.utils import rmtree

from datalad_dataverse.tests.utils import (
    create_test_dataverse_collection,
    create_test_dataverse_dataset,
)
from datalad_dataverse.utils import get_native_api

from . import (
    API_TOKENS,
    DATAVERSE_URL,
)


@skip_if(cond='testadmin' not in API_TOKENS)
@with_tempfile
def test_remote(path=None):
    ds = Dataset(path).create()
    (ds.pathobj / 'somefile.txt').write_text('content')
    ds.save()
    admin_api = get_native_api(DATAVERSE_URL, API_TOKENS['testadmin'])
    create_test_dataverse_collection(admin_api, 'basetest')
    dspid = create_test_dataverse_dataset(admin_api, 'basetest', 'testds')
    try:
        with patch.dict('os.environ', {
                'DATAVERSE_API_TOKEN': API_TOKENS['testadmin']}):
            _check_remote(ds, dspid)

    finally:
        admin_api.destroy_dataset(dspid)


def _check_remote(ds, dspid):
    repo = ds.repo
    repo.call_annex([
        'initremote', 'mydv', 'encryption=none', 'type=external',
        'externaltype=dataverse', f'url={DATAVERSE_URL}',
        f'doi={dspid}',
    ])
    # some smoke testing of the git-annex interface
    repo.call_annex([
        'copy', '--to', 'mydv', 'somefile.txt',
    ])
    repo.call_annex([
        'fsck', '-f', 'mydv',
    ])
    repo.call_annex([
        'drop', '--force', 'somefile.txt',
    ])
    repo.call_annex([
        'get', '-f', 'mydv', 'somefile.txt',
    ])
    repo.call_annex([
        'drop', '--from', 'mydv', 'somefile.txt',
    ])
    # run git-annex own testsuite
    ds.repo.call_annex([
        'testremote', '--fast', 'mydv',
    ])


@skip_if(cond='testadmin' not in API_TOKENS)
@with_tempfile
@with_tempfile
def test_datalad_annex(dspath=None, clonepath=None):
    ds = Dataset(dspath).create()
    admin_api = get_native_api(DATAVERSE_URL, API_TOKENS['testadmin'])
    create_test_dataverse_collection(admin_api, 'basetest')
    dspid = create_test_dataverse_dataset(admin_api, 'basetest', 'testds')
    try:
        with patch.dict('os.environ', {
                'DATAVERSE_API_TOKEN': API_TOKENS['testadmin']}):
            _check_datalad_annex(ds, dspid, clonepath)

    finally:
        admin_api.destroy_dataset(dspid)


def _check_datalad_annex(ds, dspid, clonepath):
    repo = ds.repo
    # this is the raw datalad-annex URL, convenience could be added on top
    git_remote_url = 'datalad-annex::?type=external&externaltype=dataverse&' \
                     f'url={urlquote(DATAVERSE_URL)}&doi={urlquote(dspid)}&' \
                     'encryption=none'

    repo.call_git(['remote', 'add', 'mydv', git_remote_url])
    repo.call_git(['push', 'mydv', '--all'])

    for url in (
        # generic monster URL
        git_remote_url,
        # actual dataset landing page
        f'{DATAVERSE_URL}/dataset.xhtml?persistentId={dspid}&version=DRAFT',
    ):
        dsclone = clone(git_remote_url, clonepath)

        # we got the same thing
        assert repo.get_hexsha(ds.repo.get_corresponding_branch()) == \
            dsclone.repo.get_hexsha(ds.repo.get_corresponding_branch())

        # cleanup for the next iteration
        rmtree(clonepath)
