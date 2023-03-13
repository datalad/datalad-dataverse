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


def list_dataset_files(api, doi: str) -> list:
    """Returns a list of file records in a dataverse dataset given by its DOI
    """
    return api.get_dataset(doi).json()['data']['latestVersion']['files']


def get_dvfile_with_md5(listing: list, md5: str) -> dict:
    frec = [f for f in listing
            if f.get('dataFile', {}).get('md5') == md5]
    if not frec:
        raise ValueError(f'no file record with MD5 {md5!r}')

    return frec[0]
