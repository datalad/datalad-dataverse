import logging
from os import environ

lgr = logging.getLogger('datalad.dataverse')

# Retrieve user API tokens from env vars DATAVERSE_TEST_APITOKEN_*,
# where * is the user name (uppercase);
# This is how the docker-based CI setup is currently passing them
# into the test environment.
DATAVERSE_TEST_APITOKENS = {
    k.split('_')[-1].lower(): v
    for k, v in environ.items()
    if k.startswith("DATAVERSE_TEST_APITOKEN_")
}

if 'testadmin' not in DATAVERSE_TEST_APITOKENS:
    lgr.warning(
        'Most tests require a dataverse admin token, '
        'set DATAVERSE_TEST_APITOKEN_TESTADMIN environment variable to specify'
    )

# the demo deployment of dataverse where anyone can have an account
# slow, but no setup cost
DEMO_DATAVERSE_URL = 'https://demo.dataverse.org'

# allow for dataverse test target instance specification
DATAVERSE_TEST_URL = environ.get("DATAVERSE_TEST_BASEURL", DEMO_DATAVERSE_URL)

# allow for base collection specification, all operations are executed
# in this collection
DATAVERSE_TEST_BASECOLLECTION = environ.get(
    "DATAVERSE_TEST_BASECOLLECTION",
    # 'demo' is what demo.dataverse uses,
    # 'root' is for a plain docker-based deployment
    'demo' if DATAVERSE_TEST_URL == DEMO_DATAVERSE_URL else 'root',
)

DATAVERSE_TEST_COLLECTION_NAME = 'dataladtester'
