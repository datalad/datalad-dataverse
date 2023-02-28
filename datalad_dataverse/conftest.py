# we are not using datalad's directly, because we are practically
# requiring whatever setup datalad_next prefers, because we employ
# its tooling
from datalad_next.conftest import setup_package

pytest_plugins = "datalad_next.tests.fixtures"

from datalad_dataverse.tests.fixtures import (
    dataverse_admin_token,
)
