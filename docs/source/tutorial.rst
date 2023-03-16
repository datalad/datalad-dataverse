.. include:: ./links.inc

.. _tutorial:

Tutorial
========

1. Create a Dataverse dataset
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Firstly, we will need a dedicated location that we will publish our dataset to. For this,
Dataverse provides the functionality to create a draft dataset and assign it a dedicated DOI.
Go to your Dataverse instance, log in, and create a new Dataset via the `Add Data` header:

.. image:: ./_static/tutorial/dv_add_dataset.png

Provide all relevant details and metadata entries in the form.
Importantly, **don't** upload any of your data files.

.. image:: ./_static/tutorial/dv_add_dataset_2.png

Once you have clicked ``Save Dataset``, you'll have a Draft Dataset.
It already has a DOI you can find under the `metadata` tab:

.. image:: ./_static/tutorial/dv_obtain_doi.png

Make a note of the URL of your dataverse instance (e.g., ``https://demo.dataverse.org``), and the DOI of your draft dataset.

2. Create a DataLad dataset
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Next, you'll need a DataLad dataset to push to your Dataverse Dataset.
If you already have one, skip this step.
If not, use ``datalad create <dataset-name-of-your-choice>`` to create a new dataset to populate, or transform an existing directory into a DataLad dataset using

.. code-block:: bash

   $ datalad create -d <path-to-directory> --force

In both cases, any files you add into the dataset can be saved using ``datalad save``.
If you have never done this before, its a good idea to give the first pages of the `DataLad handbook <http://handbook.datalad.org/r.html?install>`__ a quick read first.

Here's a toy example dataset with a single saved file:

.. code-block:: bash

   $ datalad create my-test-dataset
   create(ok): /tmp/my-test-dataset (dataset)
   $ cd my-test-dataset
   $ echo 12345 > my-file
   $ datalad save -m "Saving my first file"
   add(ok): my-file (file)
   save(ok): . (dataset)
   action summary:
      add (ok: 1)
      save (ok: 1)


3. Add a Dataverse sibling to your dataset
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Now that you have a draft dataset on Dataverse and a local DataLad dataset, let them get to know each other using the ``datalad add-sibling-dataverse`` command.
This command registers the remote Dataverse Dataset as a known remote location to your Dataset and will allow you to publish the entire Dataset (Git history and annexed data) or parts of it to Dataverse.

Depending on what you want to transfer to Dataverse, you need to configure the command with the correct ``--mode``.
Two popular choices are `annex` and `filetree`.
The former, which is also the default, will prepare the Dataverse dataset to contain both the Git revision history of your dataset as well as its annexed contents (if your Dataverse instance supports this, and your data doesn't exceed file size limits).
The latter will publish a single snapshot of your dataset ("as it currently is", without version history).
Let's illustrate the differences in detail:

annex mode
**********


.. code-block:: bash

   $ datalad add-sibling-dataverse https://demo.dataverse.org doi:10.70122/FK2/NQPP6A --mode annex
   add_sibling_dataverse.storage(ok): . [dataverse-storage: https://demo.dataverse.org (DOI: doi:10.70122/FK2/NQPP6A)]
   [INFO   ] Configure additional publication dependency on "dataverse-storage"
   add_sibling_dataverse(ok): . [dataverse: datalad-annex::?type=external&externaltype=dataverse&encryption=none&exporttree=no&url=https%3A//demo.dataverse.org&doi=doi:10.70122/FK2/NQPP6A (DOI: doi:10.70122/FK2/NQPP6A)]

Now, you can push:

.. code-block:: bash

    $ datalad push --to dataverse
    copy(ok): my-file (file) [to dataverse-storage...]
    publish(ok): . (dataset) [refs/heads/master->dataverse:refs/heads/master [new branch]]
    publish(ok): . (dataset) [refs/heads/git-annex->dataverse:refs/heads/git-annex [new branch]]

    action summary:
       copy (ok: 1)
       publish (ok: 2)


And this is the result on Dataverse:

.. image:: ./_static/tutorial/dv_dataset_annex.png

filetree mode
*************


.. code-block:: bash

   $ datalad add-sibling-dataverse https://demo.dataverse.org doi:10.70122/FK2/ZS0YL3 --mode filetree
   add_sibling_dataverse.storage(ok): . [dataverse-storage: https://demo.dataverse.org (DOI: doi:10.70122/FK2/ZS0YL3)]
   [INFO   ] Configure additional publication dependency on "dataverse-storage"
   add_sibling_dataverse(ok): . [dataverse: datalad-annex::?type=external&externaltype=dataverse&encryption=none&exporttree=yes&url=https%3A//demo.dataverse.org&doi=doi:10.70122/FK2/ZS0YL3 (DOI: doi:10.70122/FK2/ZS0YL3)]

Now, you can push:

.. code-block:: bash

    $ datalad push --to dataverse
    copy(ok): .datalad/.gitattributes (dataset)
    copy(ok): .datalad/config (dataset)
    copy(ok): .gitattributes (dataset)
    copy(ok): my-file (dataset)
    publish(ok): . (dataset) [refs/heads/master->dataverse:refs/heads/master [new branch]]
    publish(ok): . (dataset) [refs/heads/git-annex->dataverse:refs/heads/git-annex [new branch]]
    action summary:
      copy (ok: 4)
      publish (ok: 2)


And this is the result on Dataverse:

.. image:: ./_static/tutorial/dv_dataset_filetree.png


4. Making your dataset public
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Your dataset on Dataverse will be in draft mode after you've pushed content into it.
Use the webinterface to make it public and share it.


5. Cloning
^^^^^^^^^^

Finally, you or others can clone your datasets from Dataverse.
They'll need a special type of URL and the ``datalad clone`` command for this.

The URL required for cloning starts with ``datalad-annex::?`` and is provided to you by the ``datalad add-dataverse-sibling`` command.
Alternatively, you can also copy-paste it from the configuration of your remotes:

.. code-block:: bash

	$ git remote -v
	dataverse	datalad-annex::?type=external&externaltype=dataverse&encryption=none&exporttree=yes&url=https%3A//demo.dataverse.org&doi=doi:10.70122/FK2/ZS0YL3 (fetch)
	dataverse	datalad-annex::?type=external&externaltype=dataverse&encryption=none&exporttree=yes&url=https%3A//demo.dataverse.org&doi=doi:10.70122/FK2/ZS0YL3 (push)

Once you have this URL, anyone with an account on the Dataverse instance and the correct permissions for the dataset can clone it:

.. code-block:: bash

   $ datalad clone 'datalad-annex::?type=external&externaltype=dataverse&encryption=none&exporttree=no&url=https%3A//demo.dataverse.org&doi=doi:10.70122/FK2/NQPP6A' my-clone
   [INFO   ] Remote origin uses a protocol not supported by git-annex; setting annex-ignore
   [INFO   ] access to 1 dataset sibling dataverse-storage not auto-enabled, enable with:
   | 		datalad siblings -d "/tmp/my-clone" enable -s dataverse-storage
   install(ok): /tmp/tmp/my-clone-of-annex-mode (dataset)

Afterwards, enable the special remote in the clone with the provided command, and retrieve file content using ``datalad get``:

.. code-block:: bash

   $ cd my-clone
   $ datalad siblings -d "/tmp/my-clone" enable -s dataverse-storage
    .: dataverse-storage(?) [git]
   $ datalad get my-file
   get(ok): my-file (file) [from dataverse-storage...]
