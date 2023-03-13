from pathlib import Path
from datalad_next.utils import rmtree

ckwa = dict(result_renderer='disabled')


def test_XDLRA_key(
        dataverse_admin_credential_setup,
        dataverse_dataset,
        dataverse_instance_url,
        existing_dataset,
):
    """Test purpose of this test is to verify correct operations with a key
    that points to changing content with no change in the key (name) itself.
    """
    # a demo dataset with one file
    ds = existing_dataset
    fpath = (ds.pathobj / 'somefile.txt')
    # this specific format of content is needed for backend verification
    # we will track multiple versions
    probe_content = [
        '1st HEAD\n',
        '2nd HEAD\n',
    ]
    fpath.write_text(probe_content[0])
    # but we are using a specific key for the content
    # it belongs to a specific backend, and has the special property
    # that it points to changing content
    repo = ds.repo
    xdlra_key = 'XDLRA--refs'
    # inject into annex
    repo.call_annex(['setkey', xdlra_key, str(fpath)])
    # register in worktree
    repo.call_annex(['fromkey', xdlra_key, str(fpath)])
    ds.save(**ckwa)
    # make sure we are good re starting point
    status = ds.status(
        path=fpath,
        annex='availability',
        return_type='item-or-list',
        **ckwa
    )
    for prop, target in (
        ('state', 'clean'),
        ('key', xdlra_key),
        ('status', 'ok'),
        ('type', 'file'),
        ('has_content', True),
    ):
        assert status[prop] == target

    key_in_annex = Path(status['objloc'])

    # link dataverse
    repo.call_annex([
        'initremote', 'mydv', 'encryption=none', 'type=external',
        'externaltype=dataverse', f'url={dataverse_instance_url}',
        f'doi={dataverse_dataset}'
    ])

    def _check_updown_cycle(verify_content):
        # drop everything from dataverse
        # runs special remote's REMOVE
        repo.call_annex(['drop', '-f', 'mydv', '--all'])
        # put all keys on dataverse
        # runs special remote's TRANSFER_STORE
        repo.call_annex(['copy', '--all', '--to', 'mydv'])
        # let git-annex verify result integrity
        # runs special remote's CHECKPRESENT
        repo.call_annex(['fsck', '-f', 'mydv', '--fast'])
        # and bring it to a manual test (local drop, manual download)
        repo.call_annex(['drop', '--key', xdlra_key])
        # really gone
        assert not fpath.exists() or fpath.read_text() != verify_content
        # now get back from dataverse
        # runs special remote's TRANSFER_RETRIEVE
        repo.call_annex(['get', str(fpath)])
        assert fpath.read_text() == verify_content

    # no cycle through changing content for the very same key, and verify
    # that it is deposited and available a the correct version afterwards.
    # the first iteration intentionally set the same content that has already
    # been set
    for pcontent in probe_content:
        tpath = ds.pathobj / 'tmpcontent'
        tpath.write_text(pcontent)
        rmtree(key_in_annex.parent)
        repo.call_annex(['setkey', xdlra_key, str(tpath)])
        # no undesired change in key for the test file
        assert ds.status(
            path=fpath,
            annex='basic',
            return_type='item-or-list',
            **ckwa)['key'] == xdlra_key
        _check_updown_cycle(pcontent)
