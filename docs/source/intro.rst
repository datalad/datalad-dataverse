.. include:: ./links.inc
.. _intro:

Introduction
============

The Dataverse project
---------------------

Dataverse (Dataverse_) is an open source web application to share, preserve, cite, explore and analyze research data.
Researchers, data authors, publishers, data distributors, and affiliated institutions all receive appropriate credit via a data citation with a persistent identifier (e.g., DOI, or handle).
Many universities and research institutions have Dataverse installations.
For example, the `Harvard Dataverse <https://dataverse.harvard.edu/>`_, open to all scientific data from all disciplines worldwide, or `DataverseNL <https://dataverse.nl/>`_, located in the Netherlands providing data management services for a number of Dutch Universities.


A Dataverse repository hosts multiple dataverses. Each dataverse contains dataset(s) or other dataverses, and each dataset contains descriptive metadata and data files (including documentation and code that accompany the data).
The :ref:`glossary` delineates core Dataverse terminology from core DataLad concepts.


Goal of the extension
---------------------

This extension allows DataLad_ to work with Dataverse installations to make sharing and collaboration on data or DataLad datasets even easier.
It comes with several features that enable the following main use cases:

#. Export existing datasets to a Dataverse dataset in a human readable fashion
#. Clone published datasets from Dataverse

Typically, DataLad workflows for publishing data to external providers
involve some repository hosting service (like GitHub or GitLab). This
service holds the "Git" part of the dataset: dataset history (commit
messages), non-annexed files (usually code, text), and file identity
information for all annexed files (file name, but not content). These
workflows will often pair the repository hosting service with a
non-specialized hosting service (like Dropbox or AWS S3), which
doesn't understand Git, but can hold annexed file content (however,
some services are able to store both parts, e.g. GIN):


.. image:: https://handbook.datalad.org/en/latest/_images/publishing_network_publishparts2.svg
   :width: 100 %
   :alt: DataLad publishing: git and git-annex parts are separate

With ``datalad-dataverse``, the entire dataset is deposited on a Dataverse installation.
Internally, this is achieved by packaging the "Git" part and depositing it alongside the annexed data, similar to how the `datalad-next <http://docs.datalad.org/projects/next/en/latest/?badge=latest>`_ extensions allows to do this for webdav based services.

The primary use case for dataverse siblings is dataset deposition, where only one site is uploading dataset and file content updates for others to reuse.
Compared to workflows which use repository hosting services, this solution will be less flexible for collaboration (because it's not able to utilise features for controlling dataset history offered by repository hosting services, such as pull requests and conflict resolution), and might be slower (when it comes to file transfer).
What it offers, however, is the ability to make the published dataset browsable like regular directories and amendable with metadata on the Dataverse instance while being cloneable through DataLad.

What can I use this extension for?
----------------------------------

You can use this extension to publish and share your dataset via Dataverse_, and you can use it to clone published DataLad datasets from Dataverse_.
Here is some inspiration on what you could do:

- Publish your study (including its version history, data, code, results, and provenance) as a DataLad dataset to Dataverse to share it with collaborators or get a DOI for it.
- Share a published datasets' URL with colleagues and collaborators to give them easy access to your work with a single ``datalad clone``.
- Clone a friend's DataLad dataset -- from Dataverse!


``datalad-dataverse`` comes with a range of hidden convenience functions for Dataverse interactions.
Importantly, you will not need to create Dataverse datasets via the Dataverse web interface -- given appropriate credentials, ``datalad create-sibling-dataverse`` will create new datasets under your user account and specified Dataverse collection, and report back what it generated.


What can I **not** use this extension for?
------------------------------------------

- This tool does not work for datasets stored in a service other than Dataverse_.
  Please refer to the list of `special remotes`_ as hosted by the `git-annex`_ website for other storage services and how to use them with DataLad.
- Dataverse installations may have upload or storage limits - exceeding those limits is not possible with this tool. However, you will be able to at least publish the revision history of your dataset even if annexed files are too large.
- The starting point for working with this extension is a (published) DataLad dataset, not a regular Dataverse dataset.
  This extension will not transform normal Dataverse datasets projects into DataLad datasets, but expose DataLad datasets as Dataverse datasets.