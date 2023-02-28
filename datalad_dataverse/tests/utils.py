from pyDataverse.models import Dataverse
from pyDataverse.exceptions import OperationFailedError
from ..create_sibling_dataverse import (
    _create_dv_dataset,
    _get_dv_collection,
)


def create_test_dataverse_collection(api, alias, collection):
    dvmeta = Dataverse(dict(
        name="DataLad Test Dataverse",
        alias=alias,
        dataverseContacts=[dict(
            contactEmail='team@datalad.org',
        )]
    ))
    # create under the 'root' collection
    try:
        req = api.create_dataverse(collection, dvmeta.json())
    except OperationFailedError as e:
        if hasattr(e, 'args') \
                and len(e.args) \
                and 'already exists' in e.args[0]:
            # we have this collection, all good
            pass


def create_test_dataverse_dataset(api, collection, name):
    """
    Returns
    -------
    str
      The persistent DOI for the dataset
    """
    meta = dict(
        title=name,
        author=[dict(authorName='DataLad')],
        datasetContact=[dict(
            datasetContactEmail='team@datalad.org',
            datasetContactName='DataLad')],
        dsDescription=[dict(dsDescriptionValue='no description')],
        subject=['Medicine, Health and Life Sciences']
    )
    col = _get_dv_collection(api, collection)
    req = _create_dv_dataset(api, col, meta)
    req.raise_for_status()
    return req.json()['data']['persistentId']
