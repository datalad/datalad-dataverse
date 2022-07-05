from unittest.mock import patch
from requests.exceptions import ConnectionError
from datalad.tests.utils_pytest import (
    assert_in,
    assert_raises,
    assert_result_count,
    skip_if,
    with_tempfile,
)
from datalad.api import (
    clone,
    create_sibling_dataverse,
)
from datalad.distribution.dataset import (
    Dataset,
)
from datalad_next.tests.utils import with_credential

from datalad_dataverse.tests import (
    DATAVERSE_TEST_APITOKENS,
    DATAVERSE_TEST_URL,
)
from datalad_dataverse.tests.utils import (
    create_test_dataverse_collection,
)
from datalad_dataverse.utils import get_native_api


@skip_if(cond='testadmin' not in DATAVERSE_TEST_APITOKENS)
@with_tempfile
@with_tempfile
def test_basic(path=None, clone_path=None):
    ds = Dataset(path).create()
    (ds.pathobj / 'somefile.txt').write_text('content')
    ds.save()
    admin_api = get_native_api(DATAVERSE_TEST_URL, DATAVERSE_TEST_APITOKENS['testadmin'])
    create_test_dataverse_collection(admin_api, 'basetest')
    _check_basic_creation(ds, 'basetest', 'testadmin', clone_path)


@with_credential(
    'dataverse',
    secret=DATAVERSE_TEST_APITOKENS.get('testadmin'),
    realm=f'{DATAVERSE_TEST_URL.rstrip("/")}/dataverse',
)
def _check_basic_creation(ds, collection_alias, user, clone_path):

    with patch.dict('os.environ', {
            'DATALAD_CREDENTIAL_TESTCRED_TOKEN': DATAVERSE_TEST_APITOKENS[user],
            'DATALAD_CREDENTIAL_TESTCRED_REALM': DATAVERSE_TEST_URL}):

        results = ds.create_sibling_dataverse(url=DATAVERSE_TEST_URL,
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
        assert_result_count(results, 1,
                            status='ok',
                            action='create_sibling_dataverse')
        assert_result_count(results, 1,
                            status='ok',
                            action='create_sibling_dataverse.storage')
        assert_result_count(results, 2)

        assert_in('doi', results[0])
        assert_in('doi', results[1])

        clone_url = [r['url'] for r in results
                     if r['action'] == "create_sibling_dataverse"][0]

        # push should work now
        ds.push(to="git_remote")
        # drop content and retrieve again
        ds.drop("somefile.txt")
        ds.get("somefile.txt")

        # And we should be able to clone
        cloned_ds = clone(source=clone_url, path=clone_path,
                          result_xfm='datasets')
        cloned_ds.repo.enable_remote('special_remote')
        cloned_ds.get("somefile.txt")


@skip_if(cond='testadmin' not in DATAVERSE_TEST_APITOKENS)
@with_tempfile
@with_tempfile
def test_basic_export(path=None, clone_path=None):
    ds = Dataset(path).create()
    (ds.pathobj / 'somefile.txt').write_text('content')
    ds.save()
    admin_api = get_native_api(DATAVERSE_TEST_URL, DATAVERSE_TEST_APITOKENS['testadmin'])
    create_test_dataverse_collection(admin_api, 'basetest')
    _check_basic_creation(ds, 'basetest', 'testadmin', clone_path)


@with_credential(
    'dataverse',
    secret=DATAVERSE_TEST_APITOKENS.get('testadmin'),
    realm=f'{DATAVERSE_TEST_URL.rstrip("/")}/dataverse',
)
def _check_basic_export_creation(ds, collection_alias, user, clone_path):

    with patch.dict('os.environ', {
            'DATALAD_CREDENTIAL_TESTCRED_TOKEN': DATAVERSE_TEST_APITOKENS[user],
            'DATALAD_CREDENTIAL_TESTCRED_REALM': DATAVERSE_TEST_URL}):

        results = ds.create_sibling_dataverse(url=DATAVERSE_TEST_URL,
                                              collection=collection_alias,
                                              name='git_remote',
                                              storage_name='special_remote',
                                              mode='filetree',
                                              credential='testcred',
                                              existing='error',
                                              recursive=False,
                                              recursion_limit=None,
                                              metadata=None)
        assert_result_count(results, 0, status='error')
        assert_result_count(results, 1,
                            status='ok',
                            action='create_sibling_dataverse')
        assert_result_count(results, 1,
                            status='ok',
                            action='create_sibling_dataverse.storage')
        assert_result_count(results, 2)

        assert_in('doi', results[0])
        assert_in('doi', results[1])

        clone_url = [r['url'] for r in results
                     if r['action'] == "create_sibling_dataverse"][0]

        # push should work now
        ds.push(to="git_remote")
        # drop content and retrieve again
        ds.drop("somefile.txt")
        ds.get("somefile.txt")

        # And we should be able to clone
        cloned_ds = clone(source=clone_url, path=clone_path,
                          result_xfm='datasets')
        cloned_ds.repo.enable_remote('special_remote')
        cloned_ds.get("somefile.txt")
