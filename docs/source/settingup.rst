.. include:: ./links.inc

.. _install:

Quickstart
==========

Requirements
^^^^^^^^^^^^

DataLad and ``datalad-dataverse`` are available for all major operating systems
(Linux, MacOS, Windows 10).  The relevant requirements are listed below.

An account on a Dataverse site and an API token
   An API token can be obtained from the user account settings of web UI of
   a Dataverse site.

DataLad
   If you don't have DataLad_ and its underlying tools (`git`_, `git-annex`_)
   installed yet, please follow the instructions from `the datalad handbook
   <http://handbook.datalad.org/en/latest/intro/installation.html>`_.


.. _feature_support:

Dataverse feature support
^^^^^^^^^^^^^^^^^^^^^^^^^

``datalad-dataverse`` is developed to be compatible with recent Dataverse
releases (`version 5.13`_ at the time of this writing). Adding supporting for
(incompatible) historic Dataverse releases does not have any priority.

This extension package does not support all Dataverse features. Here is a
list of notable unsupported features.

- This package is focusing on depositing information on the Dataverse datasets
  in "DRAFT mode", i.e., before they are published for data preservation on
  Dataverse. Publishing is a dedicated procedure for Dataverse that applies to
  complete datasets, and is not identical with an upload of one or more files.
  Updating such published datasets is presently unsupported. It is expected to
  work, but due to the missing ability to test this feature reliably and
  automatically, it is not officially supported.

If you are interested in working on adding support for any of them, please get
in touch.


Dataverse limitations
^^^^^^^^^^^^^^^^^^^^^

Dataverse enforces strict limitations on the names of files and directories
in a dataset. In particular for directory labels, it is prohibited to use any
non-latin characters, thereby ruling out path names with words in the native
alphabets of most languages on this planet (details are on the note below).

DataLad on the other hand, does not impose particular limits on file and
directory names.  Due to this conflict, this extension package is forced to
mangle file and directory names prior deposition on Dataverse.  This mangling
has no impact on the representation in the DataLad dataset.  In particular, it
does not impose Dataverse's limitations on other services hosting the same
DataLad dataset. It does, however, impact the representation of the dataset
rendering in the Dataverse web UI.

.. note::

   Here are some more details on the peculiarities of name mangling.

   Dataverse only allows for directory names that have characters from the
   english alphabet, numbers, and the characters `` ``, ``-``, ``_``, ``.``.
   There are also restrictions for file names.

   That means, Dataverse will not accept names like ``Änderungen`` or
   ``Déchiffrer``, due to the ``Ä`` and ``é`` in them.

   In order to enable the conflict-free representation of any unicode name,
   forbidden characters are "encoded". In short, every character that is not
   supported by Dataverse is encoded as ``-<X><X>-``, where the ``<X>`` are
   hexadecimal digits (``[0-9A-F]``). Depending on the character there might
   be two or more such digits. This encoding is revertible to ensure reliable
   conflict-free file access by (mangled) path through this extension package.

   In addition, Dataverse "swallows" all `` `` (space), ``-``, and ``.`` at
   the beginning of a directory name. Therefore, we further mangle such names
   ames by prepending `_`.

   The necessity to mangle, in particular, non-english names is an unavoidable
   consequence of the character limitations imposed by Dataverse. Mangling
   enables representation, but at the cost of reduced legibility, an
   disadvantage, disproportionally impacting datasets of non-english origin.


Installation
^^^^^^^^^^^^

``datalad-dataverse`` is a Python package available on `pypi
<https://pypi.org/project/datalad-dataverse/>`_ and installable via pip_.

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


The ``datalad-dataverse`` software allows publishing a DataLad dataset to a
Dataverse instance. First you have to create an empty Dataverse dataset with a
dedicated DOI, which will be used in the code below (see how to do this in the
:ref:`tutorial`).

Next, ensure that your dataset is packaged as a DataLad dataset:

.. code-block:: bash

    datalad create -d [dataset_location] --force

Then create a dataverse `sibling` to the DataLad dataset:

.. code-block:: bash

    datalad add-sibling-dataverse \
      -d [dataset_location] \
      -s dataverse \
      https://demo.dataverse.org doi:10.70122/MYT/ESTDOI

This command will report both the URL of the dataverse instance and its DOI as
well as a long URL starting with ``datalad-annex::``.  This URL is what will be
relevant for cloning the dataset from Dataverse.

Finally, push the DataLad dataset to Dataverse:

.. code-block:: bash
   
    datalad push --to dataverse

Once the dataset is available on Dataverse, it can also be cloned using the
``datalad-annex::`` URL provided by ``add-sibling-dataverse``:

.. code-block:: bash
   
    datalad clone \
      'datalad-annex::?type=external&externaltype=dataverse&encryption=none&exporttree=no&url=https%3A//demo.dataverse.org&doi=doi:10.70122/MYT/ESTDOI'


.. admonition:: HELP! I'm new to this!

   If this is your reaction to reading the words DataLad dataset, sibling, or dataset publishing,  please head over to the `DataLad Handbook`_ for an introduction to DataLad.

   .. image:: ./_static/clueless.gif
