# DataLad extension template

[![Travis tests status](https://secure.travis-ci.org/datalad/datalad-extension-template.png?branch=master)](https://travis-ci.org/datalad/datalad-extension-template) [![codecov.io](https://codecov.io/github/datalad/datalad-extension-template/coverage.svg?branch=master)](https://codecov.io/github/datalad/datalad-extension-template?branch=master) [![crippledfs](https://github.com/datalad/datalad-extension-template/workflows/crippledfs/badge.svg)](https://github.com/datalad/datalad-extension-template/actions?query=workflow%3Acrippled-filesystems) [![win2019](https://github.com/datalad/datalad-extension-template/workflows/win2019/badge.svg)](https://github.com/datalad/datalad-extension-template/actions?query=workflow%3Awin2019)  [![docs](https://github.com/datalad/datalad-extension-template/workflows/docs/badge.svg)](https://github.com/datalad/datalad-extension-template/actions?query=workflow%3Adocs)


This repository contains an extension template that can serve as a starting point
for implementing a [DataLad](http://datalad.org) extension. An extension can
provide any number of additional DataLad commands that are automatically
included in DataLad's command line and Python API.

For a demo, clone this repository and install the demo extension via

    pip install -e .

DataLad will now expose a new command suite with `hello...` commands.

    % datalad --help |grep -B2 -A2 hello
    *Demo DataLad command suite*

      hello-cmd
          Short description of the command

To start implementing your own extension, fork this project and adjust
as necessary. The comments in [setup.py](setup.py) and
[__init__.py](datalad_helloworld/__init__.py) illustrate the purpose of the various
aspects of a command implementation and the setup of an extension package. 
