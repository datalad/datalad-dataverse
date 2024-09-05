import pytest

from pathlib import PurePosixPath

from datalad.api import clone

from datalad_next.tests.utils import assert_result_count
from datalad_next.exceptions import CommandError


ckwa = dict(result_renderer='disabled')


def test_asdv_invalid_calls(
        dataverse_admin_credential_setup,
        dataverse_instance_url,
        existing_dataset,
):
    ds = existing_dataset

    with pytest.raises(CommandError) as ve:
        ds.add_sibling_dataverse(
            dv_url=dataverse_instance_url,
            ds_pid='no-ffing-datalad-way-this-exists',
            credential="dataverse",
            **ckwa
        )
    assert 'Cannot find dataset' in str(ve.value)


@pytest.mark.parametrize("mode", ["annex", "filetree"])
def test_asdv_addpushclone(
    dataverse_admin_credential_setup,
    dataverse_instance_url,
    dataverse_dataset,
    existing_dataset,
    tmp_path,
    *,
    mode,
):
    dspid = dataverse_dataset

    # some local dataset to play with
    ds = existing_dataset
    ds_repo = ds.repo
    (ds.pathobj / 'somefile.txt').write_text('content')
    ds.save(**ckwa)

    # use everything on default, except a dedicated credential
    # for this test and the test param itself
    res = ds.add_sibling_dataverse(
        dv_url=dataverse_instance_url,
        ds_pid=dspid,
        mode=mode,
        credential="dataverse",
        **ckwa
    )

    # one result reported the URL
    clone_url = [
        r['url'] for r in res
        if r['action'] == "add_sibling_dataverse"
    ][0]

    # push should establish something cloneable at dataverse
    # 'dataverse' is the default remote name
    ds.push(to='dataverse', **ckwa)

    # And we should be able to clone
    cloned_ds = clone(
        source=clone_url,
        path=tmp_path / 'clone',
        result_xfm='datasets',
        **ckwa
    )
    cloned_repo = cloned_ds.repo
    # we got the same thing
    assert ds_repo.get_hexsha(ds_repo.get_corresponding_branch()) == \
        cloned_repo.get_hexsha(cloned_repo.get_corresponding_branch())


def test_asdv_multiple_ds(
    dataverse_admin_credential_setup,
    dataverse_instance_url,
    dataverse_dataset,
    existing_dataset,
    tmp_path,
):
    dspid = dataverse_dataset

    ds = existing_dataset
    ds_repo = ds.repo
    # create two-levels of nested datasets
    subds = ds.create('subds', **ckwa)
    subsubds = ds.create(subds.pathobj / 'subsubds', **ckwa)

    # now add siblings for all of them in the same dataverse dataset
    common_add_args = dict(
        ckwa,
        dv_url=dataverse_instance_url,
        ds_pid=dspid,
        credential="dataverse",
    )

    res = ds.add_sibling_dataverse(**common_add_args)
    clone_url = [
        r['url'] for r in res
        if r['action'] == "add_sibling_dataverse"
    ][0]

    # deposit all subdatasets regardless of nesting level under their
    # (UU)ID. This is nohow mandatory or the best way. It could also
    # be by relative path, or someother measure. But this gives
    # a conflict free layout
    for d in (subds, subsubds):
        d.add_sibling_dataverse(
            root_path=d.id,
            **common_add_args,
        )

    # let the superdataset know about the origination of subdatasets
    # to enable a recursive installation
    ds.configuration(
        'set',
        spec=[(
            'datalad.get.subdataset-source-candidate-100dv',
            clone_url + '&rootpath={id}',
        )],
        scope='branch',
        **ckwa
    )
    # safe the config update
    ds.save(**ckwa)

    ds.push(to='dataverse', recursive=True, **ckwa)

    # And we should be able to clone
    cloned_ds = clone(
        source=clone_url,
        path=tmp_path,
        result_xfm='datasets',
        **ckwa
    )
    # and perform a recursive get of subdatasets
    cloned_ds.get(get_data=False, recursive=True, **ckwa)
    # and we have two subdatasets (all levels)
    assert_result_count(
        cloned_ds.subdatasets(state='present', recursive=True, **ckwa),
        2,
        type='dataset',
        status='ok',
    )


# TODO despaghettify this monster
@pytest.mark.parametrize("mode", ["annex", "filetree"])
def test_workflow(dataverse_admin_credential_setup,
                  dataverse_instance_url,
                  dataverse_dataset,
                  existing_dataset,
                  tmp_path,
                  *, mode):
    clone_path = tmp_path / 'clone'

    # some local dataset to play with
    ds = existing_dataset
    ds_repo = ds.repo
    (ds.pathobj / 'somefile.txt').write_text('content')
    ds.save(**ckwa)

    dspid = dataverse_dataset

    results = ds.add_sibling_dataverse(
        dv_url=dataverse_instance_url,
        ds_pid=dspid,
        name='git_remote',
        storage_name='special_remote',
        mode=mode,
        existing='error',
        credential="dataverse",
        **ckwa
    )
    assert_result_count(results, 0, status='error')
    assert_result_count(results, 1,
                        status='ok',
                        action='add_sibling_dataverse')
    assert_result_count(results, 1,
                        status='ok',
                        action='add_sibling_dataverse.storage')
    assert_result_count(results, 2)

    assert 'doi' in results[0]
    assert 'doi' in results[1]

    clone_url = [r['url'] for r in results
                 if r['action'] == "add_sibling_dataverse"][0]

    # push should work now
    ds.push(to="git_remote", **ckwa)
    # drop content and retrieve again
    # (reckless drop in export mode, since export is untrusted)
    drop_param = dict(reckless='availability') if mode == 'filetree' else {}
    ds.drop("somefile.txt", **drop_param, **ckwa)
    ds.get("somefile.txt", **ckwa)

    # Move file:
    (ds.pathobj / "subdir").mkdir()
    (ds.pathobj / "somefile.txt").rename(ds.pathobj / "subdir" / "newname.md")
    ds.save(message="Move a file")
    ds.push(to="git_remote", **ckwa)

    # Add a file and push again (creating new draft version)
    (ds.pathobj / "newfile.txt").write_text("Whatever new content")
    ds.save(message="Add a file")
    ds.push(to="git_remote", **ckwa)

    # Remove the file and push again (into same draft version):
    newfile_key = ds_repo.call_annex(['lookupkey', 'newfile.txt']).strip()
    ds.drop("newfile.txt", **drop_param, **ckwa)
    (ds.pathobj / "newfile.txt").unlink()
    ds.save(message="Remove newfile.txt again")
    ds.push(to="git_remote", **ckwa)

    # The removal also is a content removal in export mode:
    # Note: Getting the key, since in forced adjusted mode (windows), we
    # can't simply checkout HEAD~1 and refer to the unfulfilled path.
    # In filetree mode the `get` is supposed to fail, in annex mode the
    # previous push doesn't affect the key file (we'd need to drop from the
    # remote for that).
    if mode == 'filetree':
        with pytest.raises(CommandError):
            ds_repo.call_annex_records(['get', '--key', newfile_key])
    else:
        ds_repo.call_annex_records(['get', '--key', newfile_key])

    # And we should be able to clone
    cloned_ds = clone(source=clone_url, path=clone_path,
                      result_xfm='datasets', **ckwa)
    cloned_repo = cloned_ds.repo
    # we got the same thing
    assert ds_repo.get_hexsha(ds_repo.get_corresponding_branch()) == \
        cloned_repo.get_hexsha(cloned_repo.get_corresponding_branch())

    cloned_repo.enable_remote('special_remote')
    cloned_ds.get(str(cloned_ds.pathobj / "subdir" / "newname.md"), **ckwa)
