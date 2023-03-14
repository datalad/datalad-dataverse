from __future__ import annotations

from pyDataverse.models import (
    Dataverse,
    Dataset as DvDataset,
)
from pyDataverse.exceptions import OperationFailedError

from datalad_next.exceptions import CapturedException


class InvalidDatasetMetadata(ValueError):
    pass


def _get_dv_collection(api, alias):
    # TODO: this should be able to deal with different identifiers not just the
    # alias, I guess
    try:
        response = api.get_dataverse(alias)
    except OperationFailedError as e:
        try:
            # fetch all collection IDs and titles in the root collection
            # to give people an immediate choice
            # how long do we want an individual collection title to be
            # in the exception message
            max_title = 15
            collections = [
                f"{d['title'][:max_title]}"
                f"{'…' if len(d['title']) > max_title else ''} "
                f"({d['id']})"
                for d in api.get_dataverse_contents(':root').json().get(
                    'data', [])
                if d.get('type') == 'dataverse'
            ]
            raise ValueError(
                f'No collection {alias!r} found among existing: '
                f"{', '.join(collections) if collections else 'none'}") from e
        except ValueError:
            raise
        except Exception as unexpected_exc:
            # our best effort failed
            CapturedException(unexpected_exc)
            raise e

    # we are only catching the pyDataverse error above
    # be safe and error for any request failure too
    response.raise_for_status()
    return response.json()


def _create_dv_dataset(api, collection, dataset_meta):
    """

    Parameters
    ----------
    api: NativeApi
    collection: Dataverse
    dataset_meta: dict

    Returns
    -------
    DvDataset
     """
    dv_dataset = DvDataset()
    dv_dataset.set(dataset_meta)
    if not dv_dataset.validate_json():
        raise InvalidDatasetMetadata
    dv_dataset = api.create_dataset(collection['data']['alias'],
                                    dv_dataset.json())
    dv_dataset.raise_for_status()
    return dv_dataset


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


def get_dvfile_with_md5(
        listing: list, md5: str, all_matching=False) -> dict | list:
    """With all_matching=True, more than one record might be returned"""
    frec = [f for f in listing
            if f.get('dataFile', {}).get('md5') == md5]
    if not frec:
        raise ValueError(f'no file record with MD5 {md5!r}')

    if all_matching:
        return frec
    else:
        return frec[0]
