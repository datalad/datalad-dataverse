"""Integration tests for lazy/deferred authentication in the special
remote: a published, public Dataverse dataset must be clonable and its
content retrievable via `git annex get` / `datalad clone` without any
credential ever being configured or prompted for.
"""

from urllib.parse import quote as urlquote

from datalad.api import clone

ckwa = dict(result_renderer='disabled')


def test_anonymous_clone_and_get_from_published_dataset(
        dataverse_admin_credential_setup,
        dataverse_admin_api,
        publishable_collection,
        publishable_dataset,
        dataverse_instance_url,
        existing_dataset,
        tmp_path,
):
    ds = existing_dataset
    payload = 'anon content'
    (ds.pathobj / 'somefile.txt').write_text(payload)
    ds.save(**ckwa)

    res = ds.add_sibling_dataverse(
        dv_url=dataverse_instance_url,
        ds_pid=publishable_dataset,
        name='git_remote',
        storage_name='special_remote',
        mode='annex',
        credential="dataverse",
        **ckwa
    )
    ds.push(to='git_remote', **ckwa)

    resp = dataverse_admin_api.publish_dataverse(publishable_collection)
    resp.raise_for_status()
    resp = dataverse_admin_api.publish_dataset(
        publishable_dataset, release_type='major')
    resp.raise_for_status()

    clone_url = [
        r['url'] for r in res
        if r['action'] == "add_sibling_dataverse"
    ][0]
    anon_clone_url = \
        clone_url + '&credential=no-such-credential-for-anon-test'

    cloned_ds = clone(anon_clone_url, tmp_path, **ckwa)
    cloned_ds.repo.enable_remote('special_remote')
    cloned_ds.get('somefile.txt', **ckwa)
    assert (cloned_ds.pathobj / 'somefile.txt').read_text() == payload