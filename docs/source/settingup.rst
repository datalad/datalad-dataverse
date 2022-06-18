.. include:: ./links.inc

.. _install:

Quickstart
==========

Requirements
^^^^^^^^^^^^

DataLad and ``datalad-dataverse`` are available for all major operating systems (Linux, MacOS, Windows 10 [#f1]_).
The relevant requirements are listed below.

   An account on a Dataverse installation and an API token
       You need a Dataverse installation and an account on it to be able to interact with it. If you have an account, you can manually generate or automatically retrieve an API token for authentication

   DataLad
       If you don't have DataLad_ and its underlying tools (`git`_, `git-annex`_) installed yet, please follow the instructions from `the datalad handbook <http://handbook.datalad.org/en/latest/intro/installation.html>`_.


Installation
^^^^^^^^^^^^

``datalad-dataverse`` is a Python package available on `pypi <https://pypi.org/project/datalad-dataverse/>`_ and installable via pip_.

.. code-block:: bash

   # create and enter a new virtual environment (optional)
   $ virtualenv --python=python3 ~/env/dl-dataverse
   $ . ~/env/dl-dataverse/bin/activate
   # install from PyPi
   $ pip install datalad-dataverse

Getting started
^^^^^^^^^^^^^^^

Here's the gist of some of this extension's functionality.
Checkout the Tutorial for more detailed demonstrations.


.. admonition:: HELP! I'm new to this!

   If this is your reaction to reading the words DataLad dataset, sibling, or dataset publishing,  please head over to the `DataLad Handbook`_ for an introduction to DataLad.

   .. image:: ./_static/clueless.gif

.. rubric:: Footnotes

.. [#f1] While installable for Windows 10, the extension may not be able to perform all functionality documented here. Please get in touch if you are familiar with Windows `to help us fix bugs <https://github.com/datalad/datalad-osf/issues?q=is%3Aissue+is%3Aopen+windows>`_.
