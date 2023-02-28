from os import environ
import pytest


@pytest.fixture(autouse=False, scope="function")
def dataverse_admin_token():
    try:
        token = environ['DATAVERSE_TEST_APITOKEN_TESTADMIN']
    except KeyError:
        pytest.skip('No DATAVERSE_TEST_APITOKEN_TESTADMIN declared')
        return

    yield token
