"""Tests for token-less (anonymous) access to public Dataverse datasets.

These tests verify the behavior introduced to allow reading publicly
available Dataverse content without requiring an API token, while still
requiring one for any operation that Dataverse itself does not permit
anonymously (draft/restricted datasets, and all write operations).
"""

from pathlib import PurePosixPath

import pytest
from pyDataverse.api import ApiAuthorizationError
from httpx import HTTPStatusError

from ..dataset import OnlineDataverseDataset as ODD
from ..utils import get_native_api


import time


def _publish(api, dsid, collection_alias):
    resp = api.publish_dataverse(collection_alias)
    resp.raise_for_status()
    resp = api.publish_dataset(dsid, release_type="major")
    resp.raise_for_status()


def _wait_until_anonymously_readable(anon_api, dsid, timeout=30, interval=1):
    """Dataverse publication is asynchronous: the HTTP response for
    publish can return before permission/index propagation completes.
    Poll anonymous access until it succeeds or timeout is reached.
    """
    deadline = time.monotonic() + timeout
    last_exc = None
    while time.monotonic() < deadline:
        try:
            resp = anon_api.get_dataset(identifier=dsid)
            if resp.status_code < 400:
                return
        except Exception as e:
            last_exc = e
        time.sleep(interval)
    raise TimeoutError(
        f"Dataset {dsid} still not anonymously readable after "
        f"{timeout}s"
    ) from last_exc

def test_odd_construction_anonymous_fails_for_draft(
        dataverse_dataset,
        dataverse_instance_url,
):
    """A freshly created (draft, unpublished) dataset must not be
    readable anonymously. Construction must raise a clean
    ApiAuthorizationError rather than some other/opaque error.
    """
    anon_api = get_native_api(dataverse_instance_url, None)
    with pytest.raises(ApiAuthorizationError):
        ODD(anon_api, dataverse_dataset)


def test_odd_anonymous_read_after_publish(
        dataverse_admin_api,
        publishable_collection,
        publishable_dataset,
        dataverse_instance_url,
        tmp_path,
):
    """Once a dataset is published (hence public), anonymous
    construction, file lookup, and download must all work without any
    credential.
    """
    fcontent = 'anonymous access test content'
    fpath = tmp_path / 'somefile.txt'
    fpath.write_text(fcontent)
    resp = dataverse_admin_api.upload_datafile(
        identifier=publishable_dataset,
        filename=fpath,
    )
    resp.raise_for_status()

    _publish(dataverse_admin_api, publishable_dataset, publishable_collection)

    anon_api = get_native_api(dataverse_instance_url, None)
    _wait_until_anonymously_readable(anon_api, publishable_dataset)
    odd = ODD(anon_api, publishable_dataset)

    fileid = odd.get_fileid_from_path(
        PurePosixPath('somefile.txt'), latest_only=True)
    assert fileid is not None

    outpath = tmp_path / 'downloaded.txt'
    odd.download_file(fileid, outpath)
    assert outpath.read_text() == fcontent



def test_odd_anonymous_write_still_forbidden(
        dataverse_admin_api,
        publishable_collection,
        publishable_dataset,
        dataverse_instance_url,
        tmp_path,
):
    """Regression guard: anonymous access must remain read-only.
    Even on a published/public dataset, uploading must fail with an
    authorization error rather than silently succeeding.
    """
    _publish(dataverse_admin_api, publishable_dataset, publishable_collection)

    anon_api = get_native_api(dataverse_instance_url, None)
    _wait_until_anonymously_readable(anon_api, publishable_dataset)
    odd = ODD(anon_api, publishable_dataset)

    fpath = tmp_path / 'should_not_upload.txt'
    fpath.write_text('nope')
    with pytest.raises(HTTPStatusError) as exc_info:
        odd.upload_file(fpath, PurePosixPath(fpath.name))
    assert exc_info.value.response.status_code in (401, 403)