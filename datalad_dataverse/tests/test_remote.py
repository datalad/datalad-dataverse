from unittest.mock import patch

from datalad.api import Dataset
from datalad.tests.utils_pytest import (
    skip_if,
    with_tempfile,
)

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
