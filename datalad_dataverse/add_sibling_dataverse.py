"""High-level interface for creating a combi-target on a Dataverse server
 """

import logging
from typing import (
    Optional,
    Union,
)
from urllib.parse import (
    quote as urlquote,
)

from datalad.distribution.dataset import Dataset
from datalad.interface.results import get_status_dict
from datalad.interface.utils import (
    generic_result_renderer,
    eval_results,
)
from datalad.support.param import Parameter
from datalad_next.commands import (
    build_doc,
    datasetmethod,
    EnsureCommandParameterization,
    ValidatedInterface,
)
from datalad_next.constraints import (
    EnsureChoice,
    EnsureStr,
    EnsureURL
)

from datalad_next.constraints.dataset import EnsureDataset

__docformat__ = "restructuredtext"

lgr = logging.getLogger('datalad.dataverse.add_sibling_dataverse')


@build_doc
class AddSiblingDataverse(ValidatedInterface):
    """Create a dataset sibling(-tandem) on a Dataverse instance.

    Dataverse is a web application to share and cite research data.

    Research data published in Dataverse receives an academic citation which
    allows to grant full credit and increases visibility of your work.

    In order to be able to use this command, a personal access token has to be
    generated on the Dataverse platform. You can find it by clicking on your
    name at the top right corner, and then clicking on Api Token>Create Token.
    """

    _examples_ = [
        dict(text="Create a dataverse dataset sibling for sharing and citing",
             code_py="""\
                 > ds = Dataset('.')
                 > ds.add_sibling_dataverse(url='https://demo.dataverse.org', name='dataverse')
             """,
             code_cmd="datalad add-sibling-dataverse demo.dataverse.org -s dataverse",
        ),
    ]

    _validator_ = EnsureCommandParameterization(dict(
        dv_url=EnsureURL(required=['scheme']),
        ds_pid=EnsureStr(),
        dataset=EnsureDataset(installed=True, purpose="add dataverse sibling"),
        name=EnsureStr(),
        storage_name=EnsureStr(),
        existing=EnsureChoice('skip', 'error', 'reconfigure'),
        mode=EnsureChoice(
                'annex', 'filetree', 'annex-only', 'filetree-only',
                'git-only')),
        validate_defaults=("dataset",)
    )

    _params_ = dict(
        dv_url=Parameter(
            args=("dv_url",),
            metavar='URL',
            doc="URL identifying the dataverse instance to connect to",),
        ds_pid=Parameter(
            args=("ds_pid",),
            doc="""""",
        ),
        dataset=Parameter(
            args=("-d", "--dataset"),
            doc="""specify the dataset to process.  If
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
            The credential can be supplied via
            configuration setting 'datalad.credential.<name>.token', or
            environment variable DATALAD_CREDENTIAL_<NAME>_TOKEN, or will
            be queried from the active credential store using the provided
            name. If none is provided, the last-used credential for the
            dataverse url will be used. Only if a credential name was given, it 
            will be encoded in the URL of the created dataverse Git remote, 
            credential auto-discovery will be performed on each remote access.""",
        ),
        existing=Parameter(
            args=("--existing",),
            doc="""action to perform, if a (storage) sibling is already
            configured under the given name.
            In this case, sibling creation can be skipped ('skip') or the
            sibling (re-)configured ('reconfigure') in the dataset, or the
            command be instructed to fail ('error').""", ),
        mode=Parameter(
            args=("--mode",),
            doc="""
            TODO: Not sure yet, what modes we can/want support here.

            Siblings can be created in various modes:
            full-featured sibling tandem, one for a dataset's Git history
            and one storage sibling to host any number of file versions
            ('annex').
            A single sibling for the Git history only ('git-only').
            A single annex sibling for multi-version file storage only
            ('annex-only').
            As an alternative to the standard (annex) storage sibling setup
            that is capable of storing any number of historical file versions
            using a content hash layout ('annex'|'annex-only'), the 'filetree'
            mode can used.
            This mode offers a human-readable data organization on the WebDAV
            remote that matches the file tree of a dataset (branch).
            However, it can, consequently, only store a single version of each
            file in the file tree.
            This mode is useful for depositing a single dataset
            snapshot for consumption without DataLad. The 'filetree' mode
            nevertheless allows for cloning such a single-version dataset,
            because the full dataset history can still be pushed to the WebDAV
            server.
            Git history hosting can also be turned off for this setup
            ('filetree-only').
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
            dataset: Optional[Union[str, Dataset]] = None,
            name: Optional[str] = 'dataverse',
            storage_name: Optional[str] = None,
            mode: str = 'annex',
            credential: Optional[str] = None,
            existing: str = 'error',
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

    if mode != 'git-only':
        yield from _add_storage_sibling(
            ds=ds,
            url=url,
            doi=ds_pid,
            name=storage_name,
            credential_name=credential_name,
            export=export_storage,
            existing=existing,
            known=storage_name in sibling_conflicts,
        )

    if mode not in ('annex-only', 'filetree-only'):
        yield from _add_git_sibling(
            ds=ds,
            url=url,
            doi=ds_pid,
            name=name,
            credential_name=credential_name,
            export=export_storage,
            existing=existing,
            known=name in sibling_conflicts,
            publish_depends=storage_name if mode != 'git-only'
            else None
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


def _add_git_sibling(ds, url, doi, name, credential_name, export, existing,
                     known, publish_depends=None):
    """
    Parameters
    ----------
    ds: Dataset
    url: str
    name: str
    credential_name: str
        originally given credential reference - needed to decide whether or not
        to incude in datalad-annex URL
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
        ds, url, doi, name, credential_name, export, existing, known=False):
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
        necessary existance of content on the remote).
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
