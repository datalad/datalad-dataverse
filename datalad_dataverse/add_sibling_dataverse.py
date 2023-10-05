"""High-level interface for creating a combi-target on a Dataverse server
 """

from __future__ import annotations

__docformat__ = "numpy"

import logging
from pathlib import PurePosixPath
from urllib.parse import quote as urlquote

from datalad_next.commands import (
    EnsureCommandParameterization,
    Parameter,
    ValidatedInterface,
    build_doc,
    datasetmethod,
    generic_result_renderer,
    get_status_dict,
    eval_results,
)
from datalad_next.constraints import (
    DatasetParameter,
    EnsureChoice,
    EnsureStr,
    EnsureURL
)
from datalad_next.constraints.dataset import EnsureDataset


lgr = logging.getLogger('datalad.dataverse.add_sibling_dataverse')


@build_doc
class AddSiblingDataverse(ValidatedInterface):
    """Add a Dataverse dataset as a sibling(-tandem)

    Dataverse is a web application to share and cite research data.

    This command registers an existing Dataverse dataset as a sibling of a
    DataLad dataset. Both dataset version history and file content can then be
    deposited at a Dataverse site via the standard ``push`` command.

    Dataverse imposes strict limits on directory names (and to some degree also
    file name). Therefore, names of files that conflict with these rules (e.g.,
    a directory name with any character not found in the English alphabet) are
    mangled on-push. This mangling does not impact file names in the DataLad
    dataset (also not for clones from Dataverse). See the package documentation
    for details.

    If a DataLad's dataset version history was deposited on Dataverse, a
    dataset can also be cloned from Dataverse again, via the standard ``clone``
    command.

    In order to be able to use this command, a personal access token has to be
    generated on the Dataverse platform. You can find it by clicking on your
    name at the top right corner, and then clicking on API Token>Create Token.
    """

    _examples_ = [
        dict(
            text="Add a dataverse dataset sibling for sharing and citing",
            code_py="""\
            > ds = Dataset('.')
            > ds.add_sibling_dataverse(
            .   url='https://demo.dataverse.org',
            .   name='dataverse',
            .   ds_pid='doi:10.5072/FK2/PMPMZM')
            """,
            code_cmd="""\
            datalad add-sibling-dataverse \\
              -s dataverse \\
              https://demo.dataverse.org doi:10.5072/FK2/PMPMZM \\
            """,
        ),
    ]

    _validator_ = EnsureCommandParameterization(
        param_constraints=dict(
            dv_url=EnsureURL(required=['scheme']),
            ds_pid=EnsureStr(),
            dataset=EnsureDataset(
                installed=True, purpose="add dataverse sibling"),
            name=EnsureStr(),
            storage_name=EnsureStr(),
            existing=EnsureChoice('skip', 'error', 'reconfigure'),
            mode=EnsureChoice(
                'annex', 'filetree', 'annex-only', 'filetree-only',
                'git-only')
        ),
        validate_defaults=("dataset",),
    )

    _params_ = dict(
        dv_url=Parameter(
            args=("dv_url",),
            metavar='URL',
            doc="""URL identifying the dataverse instance to connect to
            (e.g., https://demo.dataverse.org)""",),
        ds_pid=Parameter(
            args=("ds_pid",),
            metavar=("PID",),
            doc="""Persistent identifier of the dataverse dataset to
            use as a sibling. This PID can be found on the dataset's
            landing page on Dataverse. Either right at the top
            underneath the title of the dataset as an URL or in the dataset's
            metadata. Both formats (doi:10.5072/FK2/PMPMZM and
            https://doi.org/10.5072/FK2/PMPMZM) are supported for this
            parameter.""",
        ),
        root_path=Parameter(
            args=('--root-path',),
            metavar='PATH',
            doc="""optional alternative root path for the sibling inside the
            Dataverse dataset. This can be used to represent multiple DataLad
            datasets within a single Dataverse dataset without conflict.
            Must be given in POSIX notation."""),
        dataset=Parameter(
            args=("-d", "--dataset"),
            doc="""specify the dataset to add the sibling to.  If
            no dataset is given, an attempt is made to identify the dataset
            based on the current working directory""",),
        name=Parameter(
            args=('-s', '--name',),
            metavar='NAME',
            doc="""name of the sibling. If none is given, the hostname-part
            of the URL will be used.""",),
        storage_name=Parameter(
            args=("--storage-name",),
            metavar="NAME",
            doc="""name of the storage sibling (git-annex special remote).
            Must not be identical to the sibling name. If not specified,
            defaults to the sibling name plus '-storage' suffix. If only
            a storage sibling is created, this setting is ignored, and
            the primary sibling name is used.""",),
        credential=Parameter(
            args=("--credential",),
            metavar='NAME',
            doc="""
            name of the credential providing an API token for the dataverse
            installation of your choice, to be used for authorization.
            If no credential is given or known, a credential discovery will
            attempted based on the Dataverse URL. If no credential can be
            found, a token is prompted for.""",
        ),
        existing=Parameter(
            args=("--existing",),
            choices=('skip', 'reconfigure', 'error'),
            doc="""action to perform, if a (storage) sibling is already
            configured under the given name.
            In this case, sibling creation can be skipped ('skip') or the
            sibling (re-)configured ('reconfigure') in the dataset, or the
            command be instructed to fail ('error').""", ),
        mode=Parameter(
            args=("--mode",),
            choices=('annex', 'filetree', 'annex-only', 'filetree-only',
                     'git-only'),
            doc="""
            Different sibling setups with varying ability to accept file
            content and dataset versions are supported:
            'annex' for a sibling tandem, one for a dataset's Git history
            and one storage sibling to host any number of file versions;
            'git-only' for a single sibling for the Git history only;
            'annex-only' for a single annex sibling for multi-version file
            storage, but no dataset Git history;
            'filetree' for a human-readable data organization on the dataverse
            end that matches the file tree of a dataset branch. This mode
            is useful for depositing a single dataset snapshot for consumption
            without DataLad. A dataset's Git history is included in the export
            and enabled cloning from Dataverse.
            'filetree-only' disables the Git history export, and removes the
            ability to clone from Dataverse.
            When both a storage sibling and a regular sibling are created
            together, a publication dependency on the storage sibling is
            configured for the regular sibling in the local dataset clone.
            """),
    )

    @staticmethod
    @datasetmethod(name='add_sibling_dataverse')
    @eval_results
    def __call__(
            dv_url: str,
            ds_pid: str,
            *,
            dataset: DatasetParameter | None = None,
            name: str = 'dataverse',
            storage_name: str | None = None,
            mode: str = 'annex',
            credential: str | None = None,
            existing: str = 'error',
            root_path: PurePosixPath | None = None,
    ):
        # dataset is a next' DatasetParameter
        ds = dataset.ds

        # shared result properties
        res_kwargs = dict(
            action='add_sibling_dataverse',
            logger=lgr,
            refds=ds.path,
        )

        if mode != 'git-only' and not storage_name:
            storage_name = "{}-storage".format(name)

        sibling_names = set(
            r['name'] for r in ds.siblings(result_renderer='disabled'))
        sibling_conflicts = \
            set((name, storage_name)).intersection(sibling_names)
        # TODO this should be implemented as a joint-validation
        # if instructed to error on any existing sibling with a
        # matching name, do immediately
        if existing == 'error' and sibling_conflicts:
            raise ValueError('found existing siblings with conflicting names')

        for res in _add_sibling_dataverse(
                ds=ds,
                url=dv_url,
                credential_name=credential,
                ds_pid=ds_pid,
                root_path=root_path,
                mode=mode,
                name=name,
                storage_name=storage_name,
                existing=existing,
                sibling_conflicts=sibling_conflicts,
        ):
            yield dict(res_kwargs, **res)

    @staticmethod
    def custom_result_renderer(res, **kwargs):
        from datalad.ui import ui
        from os.path import relpath
        import datalad.support.ansi_colors as ac

        if res['status'] != 'ok' or 'sibling_dataverse' not in res['action'] or \
                res['type'] != 'sibling':
            # It's either 'notneeded' (not rendered), an `error`/`impossible` or
            # something unspecific to this command. No special rendering
            # needed.
            generic_result_renderer(res)
            return

        ui.message('{action}({status}): {path} [{name}{url}{doi}]'.format(
            action=ac.color_word(res['action'], ac.BOLD),
            path=relpath(res['path'], res['refds'])
            if 'refds' in res else res['path'],
            name=ac.color_word(res.get('name', ''), ac.MAGENTA),
            url=f": {res['url']}" if 'url' in res else '',
            doi=f" (DOI: {res['doi']})" if 'doi' in res else '',
            status=ac.color_status(res['status']),
        ))


def _add_sibling_dataverse(
        ds, url, credential_name, ds_pid,
        *,
        root_path=None,
        mode='git-only',
        name=None,
        storage_name=None,
        existing='error',
        sibling_conflicts=set(),
):
    """
    meant to be executed via foreach-dataset

    Parameters
    ----------
    ds: Dataset
    url: Dataverse API Base URL
    ds_pid: dataverse dataset PID
    mode: str, optional
    name: str, optional
    storage_name: str, optional
    existing: str, optional
    sibling_conflicts: set, optional
    """
    # Set up the actual remotes
    # simplify downstream logic, export yes or no
    export_storage = 'filetree' in mode

    # identical kwargs for both sibing types
    kwa = dict(
        ds=ds,
        url=url,
        doi=ds_pid,
        root_path=root_path,
        credential_name=credential_name,
        export=export_storage,
        existing=existing,
    )
    if mode != 'git-only':
        yield from _add_storage_sibling(
            name=storage_name,
            known=storage_name in sibling_conflicts,
            **kwa
        )

    if mode not in ('annex-only', 'filetree-only'):
        yield from _add_git_sibling(
            name=name,
            known=name in sibling_conflicts,
            publish_depends=storage_name if mode != 'git-only'
            else None,
            **kwa
        )


def _get_skip_sibling_result(name, ds, type_):
    return get_status_dict(
        action='add_sibling_dataverse{}'.format(
            '.storage' if type_ == 'storage' else ''),
        ds=ds,
        status='notneeded',
        message=("skipped creating %r sibling %r, already exists",
                 type_, name),
        name=name,
        type='sibling',
    )


def _add_git_sibling(
        *,
        ds, url, doi, root_path, name, credential_name, export, existing,
        known, publish_depends=None):
    """
    Parameters
    ----------
    ds: Dataset
    url: str
    name: str
    credential_name: str
        originally given credential reference - needed to decide whether or not
        to include in datalad-annex URL
    export: bool
    existing: {skip, error, reconfigure}
    known: bool
        Flag whether the sibling is a known remote (not implying
        necessary existence of content on the remote).
    publish_depends: str or None
        publication dependency to set
    """
    if known and existing == 'skip':
        yield _get_skip_sibling_result(name, ds, 'git')
        return

    remote_url = \
        "datalad-annex::?type=external&externaltype=dataverse&encryption=none" \
        "&exporttree={export}&url={url}&doi={doi}".format(
            export='yes' if export else 'no',
            # urlquote, because it goes into the query part of another URL
            url=urlquote(url),
            doi=doi)

    if credential_name:
        # we need to quote the credential name too.
        # e.g., it is not uncommon for credentials to be named after URLs
        remote_url += f'&credential={urlquote(credential_name)}'

    if root_path:
        remote_url += f'&rootpath={urlquote(str(root_path))}'

    # announce the sibling to not have an annex (we have a dedicated
    # storage sibling for that) to avoid needless annex-related processing
    # and speculative whining by `siblings()`
    ds.config.set(f'remote.{name}.annex-ignore', 'true', scope='local')

    for r in ds.siblings(
            # action must always be 'configure' (not 'add'), because above we just
            # made a remote {name} known, which is detected by `sibling()`. Any
            # conflict detection must have taken place separately before this call
            # https://github.com/datalad/datalad/issues/6649
            action="configure",
            name=name,
            url=remote_url,
            # this is presently the default, but it may change
            fetch=False,
            publish_depends=publish_depends,
            return_type='generator',
            result_renderer='disabled'):
        if r.get('action') == 'configure-sibling':
            r['action'] = 'reconfigure_sibling_dataverse' \
                if known and existing == 'reconfigure' \
                else 'add_sibling_dataverse'
            r['doi'] = doi
        yield r


def _add_storage_sibling(
    *, ds, url, doi, root_path, name, credential_name, export, existing,
    known=False,
):
    """
    Parameters
    ----------
    ds: Dataset
    url: str
    name: str
    credential_name: str
    export: bool
    existing: {skip, error, reconfigure}
        (Presently unused)
    known: bool
        Flag whether the sibling is a known remote (no implied
        necessary existence of content on the remote).
    """
    if known and existing == 'skip':
        yield _get_skip_sibling_result(name, ds, 'storage')
        return

    cmd_args = [
        'enableremote' if known and existing == 'reconfigure'
        else 'initremote',
        name,
        "type=external",
        "externaltype=dataverse",
        f"url={url}",
        f"doi={doi}",
        f"exporttree={'yes' if export else 'no'}",
        "encryption=none",
        # for now, no autoenable. It would result in unconditional
        # error messages on clone
        #https://github.com/datalad/datalad/issues/6634
        #"autoenable=true"
    ]
    # supply the credential identifier, if it was explicitly given
    if credential_name:
        cmd_args.append(f"credential={credential_name}")
    if root_path:
        cmd_args.append(f"rootpath={root_path}")

    ds.repo.call_annex(cmd_args)
    yield get_status_dict(
        ds=ds,
        status='ok',
        action='reconfigure_sibling_dataverse.storage'
               if known and existing == 'reconfigure' else
        'add_sibling_dataverse.storage',
        name=name,
        type='sibling',
        url=url,
        doi=doi,
    )
