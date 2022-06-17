"""High-level interface for creating a combi-target on a Dataverse server
 """

from functools import partial
import logging
from pyDataverse.api import NativeApi
from pyDataverse.models import (
    Dataset as DvDataset,
    Dataverse,
)
from typing import (
    Optional,
    Union,
)
from urllib.parse import (
    quote as urlquote,
    urlparse,
    urlunparse,
)

from datalad.distribution.dataset import (
    Dataset,
    EnsureDataset,
    datasetmethod,
    require_dataset,
)
from datalad.interface.base import (
    Interface,
    build_doc,
)
from datalad.interface.common_opts import (
    recursion_flag,
    recursion_limit
)
from datalad.interface.results import get_status_dict
from datalad.interface.utils import (
    generic_result_renderer,
    eval_results,
)
from datalad.log import log_progress
from datalad.support.param import Parameter
from datalad.support.constraints import (
    EnsureChoice,
    EnsureNone,
    EnsureStr,
)
from datalad.support.exceptions import CapturedException
from datalad.support.json_py import (
    jsonload,
    json_loads,
)
from datalad.distribution.utils import _yield_ds_w_matching_siblings
from datalad_next.credman import CredentialManager
from datalad.utils import Path

__docformat__ = "restructuredtext"

lgr = logging.getLogger('datalad.distributed.create_sibling_dataverse')


class InvalidDatasetMetadata(ValueError):
    pass


@build_doc
class CreateSiblingDataverse(Interface):
    """Create a sibling(-tandem) on a Dataverse server

    TODO: command doc
    """
    _examples_ = []

    _params_ = dict(
        url=Parameter(
            args=("url",),
            metavar='URL',
            doc="URL identifying the dataverse instance to connect to",
            constraints=EnsureStr()),
        dataset=Parameter(
            args=("-d", "--dataset"),
            doc="""specify the dataset to process.  If
            no dataset is given, an attempt is made to identify the dataset
            based on the current working directory""",
            constraints=EnsureDataset() | EnsureNone()),
        name=Parameter(
            args=('-s', '--name',),
            metavar='NAME',
            doc="""name of the sibling. If none is given, the hostname-part
            of the URL will be used.
            With `recursive`, the same name will be used to label all
            the subdatasets' siblings.""",
            constraints=EnsureStr() | EnsureNone()),
        storage_name=Parameter(
            args=("--storage-name",),
            metavar="NAME",
            doc="""name of the storage sibling (git-annex special remote).
            Must not be identical to the sibling name. If not specified,
            defaults to the sibling name plus '-storage' suffix. If only
            a storage sibling is created, this setting is ignored, and
            the primary sibling name is used.""",
            constraints=EnsureStr() | EnsureNone()),
        credential=Parameter(
            args=("--credential",),
            metavar='NAME',
            doc="""
            TODO: This doc needs to be adjusted as we need an API token, not a 
            user/secret combination.
            
            name of the credential providing a user/password credential
            to be used for authorization. The credential can be supplied via
            configuration setting 'datalad.credential.<name>.user|secret', or
            environment variable DATALAD_CREDENTIAL_<NAME>_USER|SECRET, or will
            be queried from the active credential store using the provided
            name. If none is provided, the last-used credential for the
            authentication realm associated with the WebDAV URL will be used.
            Only if a credential name was given, it will be encoded in the
            URL of the created WebDAV Git remote, credential auto-discovery
            will be performed on each remote access.""",
        ),
        existing=Parameter(
            args=("--existing",),
            constraints=EnsureChoice('skip', 'error', 'reconfigure'),
            doc="""action to perform, if a (storage) sibling is already
            configured under the given name.
            In this case, sibling creation can be skipped ('skip') or the
            sibling (re-)configured ('reconfigure') in the dataset, or the
            command be instructed to fail ('error').""", ),
        recursive=recursion_flag,
        recursion_limit=recursion_limit,
        mode=Parameter(
            args=("--mode",),
            constraints=EnsureChoice(
                'annex', 'filetree', 'annex-only', 'filetree-only',
                'git-only'),
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
        collection=Parameter(
            args=("--collection",),
            constraints=EnsureStr() | EnsureNone(),
            doc="""TODO

            I think this likely needs to become several options to specify a
            mode of operation (at least 'use an existing' vs 'create one') and
            the respective specification.
            """
        ),
        metadata=Parameter(
            args=("--metadata",),
            constraints=EnsureStr() | EnsureNone(),
            doc="""TODO
            
            For now intended to be either a path or JSON dictionary or 
            'interactive'. In python API could be an actual dict in CLI would be 
            string to be interpreted as such. Not fully implemented yet.
            
            Re path:
            - absolute only works in non-recursive operation, I suppose
            - relative would be relative to the (sub-)dataset's root
            
            I guess it may be useful to have substitutions available for the 
            path to be replaced by the command (dataset id, dataset basepath, 
            whatever)
            """
        ),
    )
    # TODO: - This command needs to be pointed to an existing dataverse
    #         collection. Even if it creates one itself, that in turn is likely
    #         to not be the root of the dataverse instance

    @staticmethod
    @datasetmethod(name='create_sibling_dataverse')
    @eval_results
    def __call__(
            url: str,
            metadata: str,  # Not yet optional. Would require an auto-guess.
            *,
            dataset: Optional[Union[str, Dataset]] = None,
            name: Optional[str] = None,
            storage_name: Optional[str] = None,
            mode: str = 'annex',
            credential: Optional[str] = None,
            existing: str = 'error',
            recursive: bool = False,
            recursion_limit: Optional[int] = None,
            collection: Optional[str] = None,
    ):

        # Make sure we actually have a dataset to operate on
        ds = require_dataset(
            dataset,
            check_installed=True,
            purpose='create Dataverse sibling(s)')

        # shared result properties
        res_kwargs = dict(
            action='create_sibling_dataverse',
            logger=lgr,
            refds=ds.path,
        )

        # 1. validate parameters
        _validate_parameters(url, metadata, dataset, name, storage_name, mode,
                             credential, existing, recursive, recursion_limit,
                             collection)

        # Handle metadata option
        if isinstance(metadata, dict):
            # nothing to do here
            pass
        elif metadata == 'interactive':
            raise NotImplementedError
        else:
            # Should be either a path to JSON file or a JSON string.
            # Try to detect and pass on either as is or as a `Path` instance for
            # the create_dataset function to consider (it may need some further
            # resolution per dataset in recursive operation)
            try:
                meta_path = Path(metadata)
                # delay assignment to not destroy original value prematurely:
                metadata = meta_path
            except Exception as e:
                ce = CapturedException(e)
                # Apparently not a path; try to interprete as JSON directly.

        # 2. check existing siblings upfront to fail early on --existing=error
        if existing == 'error':
            failed = False
            for r in _fail_on_existing_sibling(
                    ds,
                    (name, storage_name),
                    recursive=recursive,
                    recursion_limit=recursion_limit,
                    **res_kwargs):
                failed = True
                yield r
            if failed:
                return

        # 3. get API Token
        credential_name, token = _get_api_token(ds, credential, url)
        api = NativeApi(url, token)

        # temporary; just make sure we can actually connect:
        response = api.get_info_version()
        response.raise_for_status()

        # 4. Get the collection to put the dataset(s) in
        # TODO: This may need a switch to either create one or just get an
        #       existing one for use with _create_sibling_dataverse;
        #       Either way, result is pydataverse.models.Dataverse
        dv_collection = _get_dv_collection(api, collection)

        # 5. use datalad-foreach-dataset command with a wrapper function to
        #    operate in a singe dataset to address recursive behavior and yield
        #    results from there
        def _dummy(ds, refds, **kwargs):
            """wrapper for use with foreach-dataset"""

            return _create_sibling_dataverse(ds=ds,
                                             api=api,
                                             credential_name=credential_name,
                                             collection=dv_collection,
                                             mode=mode,
                                             name=name,
                                             storage_name=storage_name,
                                             existing=existing,
                                             metadata=metadata)
        for res in ds.foreach_dataset(
                _dummy,
                return_type='generator',
                result_renderer='disabled',
                recursive=recursive,
                # recursive False is not enough to disable recursion
                # https://github.com/datalad/datalad/issues/6659
                recursion_limit=0 if not recursive else recursion_limit,
        ):
            # unwind result generator
            for partial_result in res.get('result', []):
                yield dict(res_kwargs, **partial_result)

        # 6. if everything went well, save credential?

        # Dummy implementation:
        return get_status_dict(status='ok',
                               message="This command is not yet implemented",
                               type='sibling',
                               name=storage_name,
                               ds=ds,
                               **res_kwargs,
                               )

    @staticmethod
    def custom_result_renderer(res, **kwargs):
        from datalad.ui import ui
        from os.path import relpath
        import datalad.support.ansi_colors as ac

        # TODO: Actually nothing "custom" yet:
        generic_result_renderer(res)
        return


def _validate_parameters(url: str,
                         metadata: str,
                         dataset: Optional[Union[str, Dataset]] = None,
                         name: Optional[str] = None,
                         storage_name: Optional[str] = None,
                         mode: str = 'annex',
                         credential: Optional[str] = None,
                         existing: str = 'error',
                         recursive: bool = False,
                         recursion_limit: Optional[int] = None,
                         collection: Optional[str] = None):
    """This function is supposed to validate the given parameters of
    create_sibling_dataverse invocation"""
    pass


def _fail_on_existing_sibling(ds, names, recursive=False, recursion_limit=None,
                              **res_kwargs):
    """yield error results whenever sibling(s) with one of `names` already
    exists"""

    for dpath, sname in _yield_ds_w_matching_siblings(
            ds, names, recursive=recursive, recursion_limit=recursion_limit):

        yield get_status_dict(
            status='error',
            message=("a sibling %r is already configured in dataset %r",
                     sname, dpath),
            type='sibling',
            name=sname,
            ds=ds,
            **res_kwargs)


def _get_api_token(ds, credential, url):
    """get an API token"""

    # TODO:
    # Not a valid implementation! This just takes the admin token from the CI
    # environment!
    from os import environ

    # return the credential name as well as the token, since the name is needed
    # for encoding in the datalad-annex URL and for potentially storing the
    # credential later on.
    credential_name = credential or "dummy"
    return credential_name, environ["TESTS_TOKEN_TESTADMIN"]


def _get_dv_collection(api, alias):

    # TODO: this should be able to deal with different identifiers not just the
    # alias, I guess
    response = api.get_dataverse(alias)
    response.raise_for_status()
    return response.json()


def _create_dv_dataset(api, collection, dataset_meta):
    """

    Parameters
    ----------
    api: NativeApi
    collection: Dataverse
    dataset_meta: dict

    Returns
    -------
    DvDataset
    """
    dv_dataset = DvDataset()
    dv_dataset.set(dataset_meta)
    if not dv_dataset.validate_json():
        raise InvalidDatasetMetadata
    dv_dataset = api.create_dataset(collection['data']['alias'],
                                    dv_dataset.json())
    dv_dataset.raise_for_status()
    return dv_dataset


def _create_sibling_dataverse(ds, api, credential_name, collection, metadata, *,
                              mode='git-only',
                              name=None,
                              storage_name=None,
                              existing='error'):
    """

    meant to be executed via foreach-dataset

    Parameters
    ----------
    ds: Dataset
    api: pydataverse.api.NativeApi
    collection: pydataverse.models.Dataverse
    mode: str, optional
    name: str, optional
    storage_name: str, optional
    existing: str, optional
    """

    # 1. figure dataset metadata to use
    dataset_meta = _get_ds_metadata(ds, metadata)

    # 2. create the actual dataset on dataverse; we need one independently on
    # `mode`.
    try:
        dv_dataset = _create_dv_dataset(api, collection, dataset_meta)
    except InvalidDatasetMetadata:
        yield get_status_dict(status='error',
                              message=f"Invalid metadata for dataset {ds}")

    # 3. Set up the actual remotes
    # simplify downstream logic, export yes or no
    export_storage = 'filetree' in mode

    url = api.base_url
    doi = dv_dataset.json()['data']['persistentId']

    existing_siblings = [
        r[1] for r in _yield_ds_w_matching_siblings(
            ds,
            (name, storage_name),
            recursive=False)
    ]

    if mode != 'git-only':
        yield from _create_storage_sibling(
            ds=ds,
            url=url,
            doi=doi,
            name=storage_name,
            credential_name=credential_name,
            export=export_storage,
            existing=existing,
            known=storage_name in existing_siblings,
        )

    if mode not in ('annex-only', 'filetree-only'):
        yield from _create_git_sibling(
            ds,
            url,
            name,
            credential_name,
            export=export_storage,
            existing=existing,
            known=name in existing_siblings,
            publish_depends=storage_name if mode != 'git-only'
            else None
        )


def _get_skip_sibling_result(name, ds, type_):
    return get_status_dict(
        action='create_sibling_dataverse{}'.format(
            '.storage' if type_ == 'storage' else ''),
        ds=ds,
        status='notneeded',
        message=("skipped creating %r sibling %r, already exists",
                 type_, name),
        name=name,
        type='sibling',
    )


def _create_git_sibling(ds, url, doi, name, credential_name, export, existing,
                        known, publish_depends=None):
    """
    Parameters
    ----------
    ds: Dataset
    url: str
    name: str
    credential_name: str
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
        "datalad-annex::?type=dataverse&encryption=none" \
        "&exporttree={export}&url={url}&doi={doi}".format(
            export='yes' if export else 'no',
            # urlquote, because it goes into the query part of another URL
            url=urlquote(url),
            doi=doi)
    if credential_name:
        # we need to quote the credential name too.
        # e.g., it is not uncommon for credentials to be named after URLs
        remote_url += f'&dlacredential={urlquote(credential_name)}'

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
                else 'create_sibling_dataverse'
        yield r


def _create_storage_sibling(
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

    # TODO: How is the credential provided to the special remote?

    cmd_args = [
        'enableremote' if known and existing == 'reconfigure'
        else 'initremote',
        name,
        "type=dataverse",
        f"url={url}",
        f"doi={doi}"
        f"exporttree={'yes' if export else 'no'}",
        "encryption=none",
        # for now, no autoenable. It would result in unconditional
        # error messages on clone
        #https://github.com/datalad/datalad/issues/6634
        #"autoenable=true"
    ]
    ds.repo.call_annex(cmd_args)
    yield get_status_dict(
        ds=ds,
        status='ok',
        action='reconfigure_sibling_dataverse.storage'
               if known and existing == 'reconfigure' else
        'create_sibling_dataverse.storage',
        name=name,
        type='sibling',
        url=url,
    )


def _get_ds_metadata(ds, metadata):
    """Determine metadata for a given datalad dataset

    Parameters
    ----------
    ds: Dataset
    metadata: str or Path or dict
    """

    if isinstance(metadata, dict):
        # nothing to do here
        mdata = metadata
    elif isinstance(metadata, Path):
        if not metadata.is_absolute():
            metadata = ds.pathobj / metadata
        with open(metadata, 'r') as f:
            mdata = jsonload(f)
    else:
        mdata = json_loads(metadata)

    return mdata
