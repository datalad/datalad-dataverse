# we are not using datalad's directly, because we are practically
# requiring whatever setup datalad_next prefers, because we employ
# its tooling
from datalad_next.conftest import setup_package

pytest_plugins = "datalad_next.tests.fixtures"

from datalad_dataverse.tests.fixtures import (
    dataverse_admin_api,
    dataverse_admin_credential_setup,
    dataverse_admin_token,
    dataverse_dataaccess_api,
    dataverse_collection,
    dataverse_dataset,
    dataverse_demoinstance_url,
    dataverse_instance_url,
)
