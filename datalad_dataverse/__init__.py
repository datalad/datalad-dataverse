"""DataLad Dataverse extension"""

__docformat__ = 'restructuredtext'

import logging
lgr = logging.getLogger('datalad.dataverse')

# Defines a datalad command suite.
# This variable must be bound as a setuptools entrypoint
# to be found by datalad
command_suite = (
    # description of the command suite, displayed in cmdline help
    "DataLad Dataverse command suite",
    [
        # specification of a command, any number of commands can be defined
        (
            # importable module that contains the command implementation
            'datalad_dataverse.add_sibling_dataverse',
            # name of the command class implementation in above module
            'AddSiblingDataverse',
            # must make CLI name explicit
            # due to limitations of manpage generation
            'add-sibling-dataverse',
        ),
    ]
)

from datalad.support.extensions import register_config
register_config(
    'datalad.clone.url-substitute.dataverse',
    'clone URL substitution for dataverse dataset landing pages',
    description="Convenience conversion of Dataverse dataset landing page "
    "URLs to git-cloneable 'datalad-annex::'-type URLs. It enables cloning "
    "from dataset webpage directly, and implies a remote sibling in 'annex' "
    "mode (i.e., with keys, not exports) and no alternative root path being used"
    "See https://docs.datalad.org/design/url_substitution.html for details",
    dialog='question',
    scope='global',
    default=(
        r',^(http[s]*://.*)/dataset.xhtml\?persistentId=(doi:[^&]+)(.*)$'
        r',datalad-annex::?type=external&externaltype=dataverse'
        r'&url=\1&doi=\2&encryption=none',
    ),
)


from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
