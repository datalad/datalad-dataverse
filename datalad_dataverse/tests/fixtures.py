from os import environ
import pytest

from datalad_dataverse.utils import get_native_api

from .utils import (
    create_test_dataverse_collection,
    create_test_dataverse_dataset,
)


@pytest.fixture(autouse=False, scope="session")
def dataverse_admin_token():
    try:
        token = environ['DATAVERSE_TEST_APITOKEN_TESTADMIN']
    except KeyError:
        pytest.skip('No DATAVERSE_TEST_APITOKEN_TESTADMIN declared')
        return

    yield token


@pytest.fixture(autouse=False, scope="session")
def dataverse_demoinstance_url():
    # the demo deployment of dataverse where anyone can have an account
    # slow, but no setup cost
    return 'https://demo.dataverse.org'


@pytest.fixture(autouse=False, scope="session")
def dataverse_instance_url(dataverse_demoinstance_url):
    # use a custom instance if declared, otherwise fall back on
    # standard demo instance
    return environ.get("DATAVERSE_TEST_BASEURL",
                       dataverse_demoinstance_url)


@pytest.fixture(autouse=False, scope="session")
def dataverse_admin_api(dataverse_admin_token, dataverse_instance_url):
    return get_native_api(dataverse_instance_url, dataverse_admin_token)


@pytest.fixture(autouse=False, scope='session')
def dataverse_collection(dataverse_admin_api,
                         dataverse_demoinstance_url,
                         dataverse_instance_url):
    base_collection = 'demo' \
        if dataverse_instance_url == dataverse_demoinstance_url else 'root'

    # use a UUID1 to get a host and time-specific UI, such that we get
    # non-conflicting collections on the same dataverse instances
    # for CI running in parallel
    from uuid import uuid1
    collection_alias = f'dv-{uuid1()}'

    create_test_dataverse_collection(
        dataverse_admin_api,
        collection_alias,
        collection=base_collection,
    )
    yield collection_alias

    # if all other fixtures and tests have properly cleaned-up after
    # themselves we can now simply delete the collection
    dataverse_admin_api.delete_dataverse(collection_alias)


@pytest.fixture(autouse=False, scope='session')
def dataverse_published_collection(dataverse_admin_api, dataverse_collection):
    # This may not work in all test setups due to lack of permissions or /root
    # not being published or it being published already. Try though, since it's
    # necessary to publish datasets in order to test against dataverse datasets
    # with several versions.
    from pyDataverse.exceptions import (
        ApiAuthorizationError,
        OperationFailedError,
    )
    try:
        dataverse_admin_api.publish_dataverse(dataverse_collection)
    except ApiAuthorizationError:
        # Test setup doesn't allow for it
        pass
    except OperationFailedError as e:
        print(str(e))

    yield dataverse_collection


@pytest.fixture(autouse=False, scope='function')
def dataverse_dataset(dataverse_admin_api, dataverse_collection):
    dspid = create_test_dataverse_dataset(
        dataverse_admin_api, dataverse_collection, 'testds')

    yield dspid

    # cleanup
    dataverse_admin_api.destroy_dataset(dspid)


@pytest.fixture(autouse=False, scope='function')
def dataverse_admin_credential_setup(
        dataverse_admin_token, dataverse_instance_url, credman):
    credman.set('dataverse', secret=dataverse_admin_token,
                realm=f'{dataverse_instance_url.rstrip("/")}/dataverse')
    yield credman
