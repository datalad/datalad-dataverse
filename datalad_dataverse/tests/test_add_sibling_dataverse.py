import pytest

from datalad.api import clone

from datalad_next.tests.utils import assert_result_count
from datalad_next.exceptions import CommandError


ckwa = dict(result_renderer='disabled')


# TODO despaghettify this monster
@pytest.mark.parametrize("mode", ["annex", "filetree"])
def test_workflow(dataverse_admin_api,
                  dataverse_admin_credential_setup,
                  dataverse_demoinstance_url,
                  dataverse_instance_url,
                  dataverse_dataset,
                  existing_dataset,
                  tmp_path,
                  *, mode):
    clone_path = tmp_path / 'clone'

    # some local dataset to play with
    ds = existing_dataset
    (ds.pathobj / 'somefile.txt').write_text('content')
    ds.save(**ckwa)

    with pytest.raises(CommandError) as ve:
        ds.add_sibling_dataverse(
            dv_url=dataverse_instance_url,
            ds_pid='no-ffing-datalad-way-this-exists',
            credential="dataverse",
            **ckwa
        )
    assert 'doi:no-ffing-datalad-way-this-exists not found' in str(ve.value)

    ds_repo = ds.repo
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
