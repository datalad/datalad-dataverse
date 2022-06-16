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
            'datalad_dataverse.create_sibling_dataverse',
            # name of the command class implementation in above module
            'CreateSiblingDataverse',
            # optional name of the command in the cmdline API
            'create-sibling-dataverse',
            # optional name of the command in the Python API
            'create_sibling_dataverse'
        ),
    ]
)

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
