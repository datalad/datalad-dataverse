"""High-level interface for creating a combi-target on a WebDAV capable server
 """
import logging
from pyDataverse.api import NativeApi
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
from datalad.distribution.utils import _yield_ds_w_matching_siblings
from datalad_next.credman import CredentialManager


__docformat__ = "restructuredtext"

lgr = logging.getLogger('datalad.distributed.create_sibling_dataverse')


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
    )
    # TODO: - This command needs to be pointed to an existing dataverse
    #         collection. Even if it creates one itself, that in turn is likely
    #         to not be the root of the dataverse instance

    @staticmethod
    @datasetmethod(name='create_sibling_dataverse')
    @eval_results
    def __call__(
            url: str,
            *,
            dataset: Optional[Union[str, Dataset]] = None,
            name: Optional[str] = None,
            storage_name: Optional[str] = None,
            mode: str = 'annex',
            credential: Optional[str] = None,
            existing: str = 'error',
            recursive: bool = False,
            recursion_limit: Optional[int] = None):

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
        _validate_parameters(url, dataset, name, storage_name, mode,
                             credential, existing, recursive, recursion_limit)

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
        token = _get_api_token(ds, credential, url)
        api = NativeApi(url, token)

        # temporary; just make sure we can actually connect:
        response = api.get_info_version()
        response.raise_for_status()

        # 4. use datalad-foreach-dataset command with a wrapper function to
        #    operates in a singe dataset to address recursive behavior and yield
        #    results from there
        # 5. if everything went well, save credential?

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
                         dataset: Optional[Union[str, Dataset]] = None,
                         name: Optional[str] = None,
                         storage_name: Optional[str] = None,
                         mode: str = 'annex',
                         credential: Optional[str] = None,
                         existing: str = 'error',
                         recursive: bool = False,
                         recursion_limit: Optional[int] = None):
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
    return environ["TESTS_TOKEN_TESTADMIN"]


def _create_sibling_dataverse(ds, api):
    # meant to be executed via foreach-dataset
    pass



