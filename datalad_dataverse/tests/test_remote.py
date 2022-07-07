from urllib.parse import quote as urlquote

from datalad.api import (
    Dataset,
    clone,
)
from datalad.tests.utils_pytest import (
    skip_if,
    with_tempfile,
)
from datalad.utils import (
    on_windows,
    rmtree,
)

from datalad_next.tests.utils import with_credential

from datalad_dataverse.tests.utils import (
    create_test_dataverse_collection,
    create_test_dataverse_dataset,
)
from datalad_dataverse.utils import get_native_api

from . import (
    DATAVERSE_TEST_APITOKENS,
    DATAVERSE_TEST_COLLECTION_NAME,
    DATAVERSE_TEST_URL,
)


@skip_if(cond='testadmin' not in DATAVERSE_TEST_APITOKENS)
@with_tempfile
def test_remote(path=None):
    ds = Dataset(path).create()
    (ds.pathobj / 'somefile.txt').write_text('content')
    ds.save()
    admin_api = get_native_api(DATAVERSE_TEST_URL, DATAVERSE_TEST_APITOKENS['testadmin'])
    create_test_dataverse_collection(admin_api, DATAVERSE_TEST_COLLECTION_NAME)
    dspid = create_test_dataverse_dataset(
        admin_api, DATAVERSE_TEST_COLLECTION_NAME, 'testds')
    try:
        _check_remote(ds, dspid)
    finally:
        admin_api.destroy_dataset(dspid)


@with_credential(
    'dataverse',
    secret=DATAVERSE_TEST_APITOKENS.get('testadmin'),
    realm=f'{DATAVERSE_TEST_URL.rstrip("/")}/dataverse',
)
def _check_remote(ds, dspid):
    repo = ds.repo
    repo.call_annex([
        'initremote', 'mydv', 'encryption=none', 'type=external',
        'externaltype=dataverse', f'url={DATAVERSE_TEST_URL}',
        f'doi={dspid}',
    ])
    # some smoke testing of the git-annex interface
    repo.call_annex([
        'copy', '--to', 'mydv', 'somefile.txt',
    ])
    repo.call_annex([
        'fsck', '-f', 'mydv',
    ])
    repo.call_annex([
        'drop', '--force', 'somefile.txt',
    ])
    repo.call_annex([
        'get', '-f', 'mydv', 'somefile.txt',
    ])
    repo.call_annex([
        'drop', '--from', 'mydv', 'somefile.txt',
    ])
    # Temporarily disable this until
    # https://github.com/datalad/datalad-dataverse/issues/127
    # is sorted out. Possibly via
    # https://git-annex.branchable.com/bugs/testremote_is_not_honoring_--backend
    if not on_windows:
        # run git-annex own testsuite
        ds.repo.call_annex([
            'testremote', '--fast', 'mydv',
        ])


@skip_if(cond='testadmin' not in DATAVERSE_TEST_APITOKENS)
@with_tempfile
@with_tempfile
def test_datalad_annex(dspath=None, clonepath=None):
    ds = Dataset(dspath).create()
    admin_api = get_native_api(DATAVERSE_TEST_URL, DATAVERSE_TEST_APITOKENS['testadmin'])
    create_test_dataverse_collection(admin_api, DATAVERSE_TEST_COLLECTION_NAME)
    dspid = create_test_dataverse_dataset(
        admin_api, DATAVERSE_TEST_COLLECTION_NAME, 'testds')
    try:
        _check_datalad_annex(ds, dspid, clonepath)
    finally:
        admin_api.destroy_dataset(dspid)


@with_credential(
    'dataverse',
    secret=DATAVERSE_TEST_APITOKENS.get('testadmin'),
    realm=f'{DATAVERSE_TEST_URL.rstrip("/")}/dataverse',
)
def _check_datalad_annex(ds, dspid, clonepath):
    repo = ds.repo
    # this is the raw datalad-annex URL, convenience could be added on top
    git_remote_url = 'datalad-annex::?type=external&externaltype=dataverse&' \
                     f'url={urlquote(DATAVERSE_TEST_URL)}&doi={urlquote(dspid)}&' \
                     'encryption=none'

    repo.call_git(['remote', 'add', 'mydv', git_remote_url])
    repo.call_git(['push', 'mydv', '--all'])

    for url in (
        # generic monster URL
        git_remote_url,
        # actual dataset landing page
        f'{DATAVERSE_TEST_URL}/dataset.xhtml?persistentId={dspid}&version=DRAFT',
    ):
        dsclone = clone(git_remote_url, clonepath)

        # we got the same thing
        assert repo.get_hexsha(ds.repo.get_corresponding_branch()) == \
            dsclone.repo.get_hexsha(ds.repo.get_corresponding_branch())

        # cleanup for the next iteration
        rmtree(clonepath)
