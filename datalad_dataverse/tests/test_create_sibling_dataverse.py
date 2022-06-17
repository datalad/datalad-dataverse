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


@skip_if(cond=not DATAVERSE_URL)
@with_tempfile
def test_dummy(path=None):

    # This test is nonsense! For now just proves that create-sibing can make a
    # connection to the CI dataverse

    ds = Dataset(path).create()

    assert_raises(ConnectionError, ds.create_sibling_dataverse,
                  url="http://doesnot-exi.st", existing="skip")
    ds.create_sibling_dataverse(url="http://localhost:8080", existing="skip")
