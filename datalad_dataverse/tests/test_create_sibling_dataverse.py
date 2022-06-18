from unittest.mock import patch
from requests.exceptions import ConnectionError
from datalad.tests.utils_pytest import (
    assert_raises,
    assert_result_count,
    skip_if,
    with_tempfile,
)
from datalad.api import (
    create_sibling_dataverse,
)
from datalad.distribution.dataset import (
    Dataset,
)
from datalad.support.exceptions import IncompleteResultsError

from datalad_dataverse.tests import (
    API_TOKENS,
    DATAVERSE_URL
)
from datalad_dataverse.tests.utils import (
    create_test_dataverse_collection,
)
from datalad_dataverse.utils import get_native_api


@skip_if(cond='testadmin' not in API_TOKENS)
@with_tempfile
def test_basic(path=None):
    ds = Dataset(path).create()
    (ds.pathobj / 'somefile.txt').write_text('content')
    ds.save()
    admin_api = get_native_api(DATAVERSE_URL, API_TOKENS['testadmin'])
    create_test_dataverse_collection(admin_api, 'basetest')
    _check_basic_creation(ds, 'basetest', 'testadmin')


def _check_basic_creation(ds, collection_alias, user):

    with patch.dict('os.environ', {
            'DATALAD_CREDENTIAL_TESTCRED_TOKEN': API_TOKENS[user]}):

        results = ds.create_sibling_dataverse(url=DATAVERSE_URL,
                                              collection=collection_alias,
                                              name='git_remote',
                                              storage_name='special_remote',
                                              mode='annex',
                                              credential='testcred',
                                              existing='error',
                                              recursive=False,
                                              recursion_limit=None,
                                              metadata=None)
        assert_result_count(results, 0, status='error')
