"""DataLad demo extension"""

__docformat__ = 'restructuredtext'

import logging
lgr = logging.getLogger('datalad.helloworld')

# Defines a datalad command suite.
# This variable must be bound as a setuptools entrypoint
# to be found by datalad
command_suite = (
    # description of the command suite, displayed in cmdline help
    "Demo DataLad command suite",
    [
        # specification of a command, any number of commands can be defined
        (
            # importable module that contains the command implementation
            'datalad_helloworld.hello_cmd',
            # name of the command class implementation in above module
            'HelloWorld',
            # optional name of the command in the cmdline API
            'hello-cmd',
            # optional name of the command in the Python API
            'hello_cmd'
        ),
    ]
)

from . import _version
__version__ = _version.get_versions()['version']
