import pytest

from datalad.tests.utils_pytest import (
    assert_in,
    assert_raises,
    assert_result_count,
)
from datalad.api import (
    clone,
)
from datalad.distribution.dataset import (
    Dataset,
)
from datalad.support.exceptions import CommandError


ckwa = dict(result_renderer='disabled')


# TODO despaghettify this monster
@pytest.mark.parametrize("mode", ["annex", "filetree"])
def test_workflow(dataverse_admin_api,
                  dataverse_admin_credential_setup,
                  dataverse_demoinstance_url,
                  dataverse_instance_url,
                  dataverse_published_collection,
                  tmp_path,
                  *, mode):
    path = tmp_path / 'ds'
    clone_path = tmp_path / 'clone'

    # some local dataset to play with
    ds = Dataset(path).create(**ckwa)
    (ds.pathobj / 'somefile.txt').write_text('content')
    ds.save(**ckwa)

    with assert_raises(ValueError) as ve:
        ds.create_sibling_dataverse(
            url=dataverse_instance_url,
            collection='no-ffing-datalad-way-this-exists',
            credential="dataverse",
            **ckwa
        )
    assert 'among existing' in str(ve)

    ds_repo = ds.repo
    dspid = None
    try:
        results = ds.create_sibling_dataverse(
            url=dataverse_instance_url,
            collection=dataverse_published_collection,
            name='git_remote',
            storage_name='special_remote',
            mode=mode,
            existing='error',
            recursive=False,
            recursion_limit=None,
            metadata=None,
            credential="dataverse",
            **ckwa
        )
        # make dataset removal work in `finally`
        # no being careful and get(), we really require it
        dspid = results[0]['doi']

        assert_result_count(results, 0, status='error')
        assert_result_count(results, 1,
                            status='ok',
                            action='create_sibling_dataverse')
        assert_result_count(results, 1,
                            status='ok',
                            action='create_sibling_dataverse.storage')
        assert_result_count(results, 2)

        assert_in('doi', results[0])
        assert_in('doi', results[1])

        clone_url = [r['url'] for r in results
                     if r['action'] == "create_sibling_dataverse"][0]

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

        # Publish this version (if we can):
        # May fail due to same reasons as the publication of the collection in
        # `_prep_test`.
        # Plus: Somehow this doesn't workout on demo.dataverse.org
        #       Looks like we can't modify a published dataset there?
        #       (In local docker setup that automatically creates a new draft
        #       version)
        # However, at least when possible (docker setup with published root
        # collection), test some aspect of dealing with this.
        if dataverse_instance_url != dataverse_demoinstance_url:
            try:
                response = dataverse_admin_api.publish_dataset(dspid, release_type='major')
            except Exception as e:
                # nothing to do - we test what we can test, but print the reason
                print(str(e))
            published = response is not None and response.status_code == 200
            if not published and response is not None:
                # Publishing didn't succeed, but gave a json reponse not an
                # exception - print in this case, too.
                print(f"{response.json()}")
        else:
            published = False

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
            assert_raises(CommandError,
                          ds_repo.call_annex_records,
                          ['get', '--key', newfile_key])
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

    finally:
        if dspid:
            dataverse_admin_api.destroy_dataset(dspid)
