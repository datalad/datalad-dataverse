import pytest
from urllib.parse import quote as urlquote

from datalad.api import clone

from datalad_next.exceptions import CommandError
from datalad_next.utils import (
    on_windows,
    rmtree,
)

from ..utils import mangle_path
from .utils import (
    list_dataset_files,
    get_dvfile_with_md5,
)

ckwa = dict(result_renderer='disabled')


@pytest.mark.parametrize("exporttree", ["yes", "no"])
def test_remote(dataverse_admin_credential_setup,
                dataverse_admin_api,
                dataverse_dataset,
                dataverse_instance_url,
                existing_dataset,
                *, exporttree):
    ds = existing_dataset
    payload = 'content'
    payload_md5 = '9a0364b9e99bb480dd25e1f0284c8555'
    payload_fname = 'somefile.txt'
    (ds.pathobj / payload_fname).write_text(payload)
    ds.save(**ckwa)
    repo = ds.repo
    repo.call_annex([
        'initremote', 'mydv', 'encryption=none', 'type=external',
        'externaltype=dataverse', f'url={dataverse_instance_url}',
        f'doi={dataverse_dataset}', f'exporttree={exporttree}'
    ])
    # check initial file naming on export and copy-to
    if exporttree == "yes":
        repo.call_annex([
            'export', 'HEAD', '--to', 'mydv'
        ])
        flist = list_dataset_files(dataverse_admin_api, dataverse_dataset)
        # more than one file, we also exported all files in Git
        assert len(flist) > 1
        frec = get_dvfile_with_md5(flist, payload_md5)
        assert frec['label'] == payload_fname
    else:
        repo.call_annex([
            'copy', '--to', 'mydv', 'somefile.txt',
        ])
        flist = list_dataset_files(dataverse_admin_api, dataverse_dataset)
        # one key
        assert len(flist) == 1
        frec = get_dvfile_with_md5(flist, payload_md5)
        # dataverse file label equals the key
        assert frec['label'] == \
            str(mangle_path(
                repo.get_content_annexinfo(
                    paths=[payload_fname]).popitem()[1]['key']
            ))
        # keys are placed in a hashtree, in a dedicated directory
        assert frec['directoryLabel'] == 'annex/1f1/8cc'
    repo.call_annex([
        'fsck', '-f', 'mydv',
    ])
    repo.call_annex([
        'drop', '--force', 'somefile.txt',
    ])
    repo.call_annex([
        'get', '-f', 'mydv', 'somefile.txt',
    ])
    if exporttree == "no":
        # One cannot drop from an export remote - annex will complain and
        # suggest exporting a tree w/o the file instead.
        repo.call_annex([
            'drop', '--from', 'mydv', 'somefile.txt',
        ])
    # run git-annex own testsuite
    # since Dataverse version 5.0, "storeKey when already present" will
    # fail, as Dataverse forbids replacing files with identical names and
    # checksums: https://guides.dataverse.org/en/latest/user/dataset-management.html#duplicate-files
    with pytest.raises(CommandError, match='4 out of 125 tests failed'):
        ds.repo.call_annex([
            'testremote', '--fast', 'mydv',
        ])


def test_datalad_annex(dataverse_admin_credential_setup,
                       dataverse_dataset,
                       dataverse_instance_url,
                       existing_dataset,
                       tmp_path):
    ds = existing_dataset
    clonepath = tmp_path
    repo = ds.repo
    # this is the raw datalad-annex URL, convenience could be added on top
    git_remote_url = \
        'datalad-annex::?type=external&externaltype=dataverse&' \
        f'url={urlquote(dataverse_instance_url)}' \
        f'&doi={urlquote(dataverse_dataset)}&' \
        'encryption=none'

    repo.call_git(['remote', 'add', 'mydv', git_remote_url])
    repo.call_git(['push', 'mydv', '--all'])

    for url in (
        # generic monster URL
        git_remote_url,
        # actual dataset landing page
        f'{dataverse_instance_url}/dataset.xhtml?persistentId={dataverse_dataset}&version=DRAFT',
    ):
        dsclone = clone(git_remote_url, clonepath, **ckwa)
        cloned_repo = dsclone.repo

        # we got the same thing
        assert repo.get_hexsha(repo.get_corresponding_branch()) == \
            cloned_repo.get_hexsha(cloned_repo.get_corresponding_branch())

        # cleanup for the next iteration
        rmtree(clonepath)


# this tests is simply an indicator for dataverse potentially making it
# possible to export two identical files with the same content.
# presently this is not the case, and this tests merely checks that
def test_export_identical_unsupported(
        dataverse_admin_credential_setup,
        dataverse_admin_api,
        dataverse_dataset,
        dataverse_instance_url,
        existing_dataset):
    # dataset with two identical files
    ds = existing_dataset
    payload = 'identical'
    payload_md5 = 'ee0cbdbacdada19376449799774976e8'
    for fname in ('one.txt', 'two.txt'):
        (ds.pathobj / fname).write_text(payload)
    ds.save(**ckwa)
    repo = ds.repo
    repo.call_annex([
        'initremote', 'mydv', 'encryption=none', 'type=external',
        'externaltype=dataverse', f'url={dataverse_instance_url}',
        f'doi={dataverse_dataset}', 'exporttree=yes'
    ])
    repo.call_annex([
        'export', 'HEAD', '--to', 'mydv'
    ])
    flist = list_dataset_files(dataverse_admin_api, dataverse_dataset)
    identicals = get_dvfile_with_md5(flist, payload_md5, all_matching=True)
    assert len(identicals) == 2
