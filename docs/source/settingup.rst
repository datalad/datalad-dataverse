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


.. _feature_support:

Feature support
^^^^^^^^^^^^^^^^
``datalad-dataverse`` is developed to be compatible with Dataverse (`version 5.13`_), which
has certain limitations when integrated with DataLad. In particular:

- This extension does not support Dataverse versions prior to v5.13
- This extension does not support unicode in filenames
- Support for handling previously published Dataverse datasets is experimental


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

.. admonition:: Tutorial

   For detailed instructions, please refer to the :ref:`tutorial`.


The ``datalad-dataverse`` software allows publishing a DataLad dataset to a Dataverse
instance. First you have to create an empty Dataverse dataset with a dedicated DOI, which
will be used in the code below (see how to do this in the :ref:`tutorial`).

Next, ensure that your dataset is packaged as a DataLad dataset:

.. code-block:: bash
   
    datalad create -d [dataset_location] --force

Then create a dataverse `sibling` to the DataLad dataset:

.. code-block:: bash
   
    datalad add-sibling-dataverse -s dataverse -d [dataset_location] https://demo.dataverse.org doi:10.70122/MYT/ESTDOI

This command will report both the URL of the dataverse instance and its DOI as well as a long URL starting with ``datalad-annex::``.
This URL is what will be relevant for cloning the dataset from DataVerse.

Finally, push the DataLad dataset to Dataverse:

.. code-block:: bash
   
    datalad push --to dataverse

Once the dataset is available on Dataverse, it can also be cloned using the ``datalad-annex::`` URL provided by ``add-sibling-dataverse``:

.. code-block:: bash
   
    datalad clone 'datalad-annex::?type=external&externaltype=dataverse&encryption=none&exporttree=no&url=https%3A//demo.dataverse.org&doi=doi:10.70122/MYT/ESTDOI'


.. admonition:: HELP! I'm new to this!

   If this is your reaction to reading the words DataLad dataset, sibling, or dataset publishing,  please head over to the `DataLad Handbook`_ for an introduction to DataLad.

   .. image:: ./_static/clueless.gif

.. rubric:: Footnotes

.. [#f1] While installable for Windows 10, the extension may not be able to perform all functionality documented here. Please get in touch if you are familiar with Windows `to help us fix bugs <https://github.com/datalad/datalad-osf/issues?q=is%3Aissue+is%3Aopen+windows>`_.
