.. include:: ./links.inc
.. _intro:

Introduction
============

The Dataverse project
---------------------

Dataverse (Dataverse_) is an open source web application to share, preserve,
cite, explore and analyze research data.  Researchers, data authors,
publishers, data distributors, and affiliated institutions can receive
appropriate credit via a data citation with a persistent identifier (e.g.,
DOIs).  Many universities and research institutions have Dataverse
installations.  For example, the `Harvard Dataverse
<https://dataverse.harvard.edu/>`_, open to all scientific data from all
disciplines worldwide, or `DataverseNL <https://dataverse.nl/>`_, located in
the Netherlands providing data management services for a number of Dutch
Universities.

A Dataverse site hosts multiple dataverses. Each dataverse contains datasets or
other dataverses, and each dataset contains descriptive metadata and data files
(including possibly documentation and code that accompany the data).  The
:ref:`glossary` delineates core Dataverse terminology from core DataLad
concepts.


Goal of this DataLad extension package
--------------------------------------

This DataLad extension package provides interoperability with Dataverse for the
purpose of depositing DataLad dataset on Dataverse, and for retrieving DataLad
datasets from Dataverse instances, together with their full version history.
It comes with several features that enable the following main use cases:

#. Deposit file content for any number of file versions tracked in a DataLad
   dataset on dataverse, including the dataset's history, for retrieval with
   DataLad
#. Export a single version of a DataLad dataset to Dataverse, with all files
   organized in a matching human readable directory tree, for consumption via
   the Dataverse web UI, or tools other than DataLad

Typically, DataLad workflows for publishing data to external providers involve
some repository hosting service (like GitHub or GitLab). This service holds the
"Git" or version-control-system part of the dataset: dataset history (commit
messages), non-annexed files (usually code, text), and file identity
information for all annexed files (file name, but not content). These workflows
will often pair the repository hosting service with a non-specialized hosting
service (like Dropbox or AWS S3), which doesn't understand Git, but can hold
annexed file content (however, some services are able to store both parts, e.g.
GIN):


.. image:: https://handbook.datalad.org/en/latest/_images/publishing_network_publishparts2.svg
   :width: 100 %
   :alt: DataLad publishing: git and git-annex parts are separate

With ``datalad-dataverse``, the entire dataset can be deposited at a Dataverse
site, forming a so-called dataset *sibling*.  Internally, this is achieved by
packaging the "Git" part and depositing it alongside the annexed data, similar
to how the `datalad-next
<http://docs.datalad.org/projects/next/en/latest/?badge=latest>`_ extensions
allows to do this for webdav based services.

The primary use case for Dataverse dataset siblings is dataset deposition for
example for the purpose of data preservation, and the possibility to cite a
dataset via Dataverse's persistent identifiers.  Typically, only one site will
upload a dataset and file content (updates) for others to reuse.  Compared to
workflows which use repository hosting services, this solution will be less
flexible for collaboration (because it's not able to utilize features for
controlling dataset history offered by repository hosting services, such as
pull requests and conflict resolution), and might be slower (when it comes to
file transfer).  What it offers, however, is the ability to make the published
dataset browsable like regular directories and amendable with metadata on the
Dataverse instance while still being cloneable via DataLad.


.. _usecases:

What can I use this extension for?
----------------------------------

You can use this extension to publish and share your dataset via Dataverse_, and you can use it to clone published DataLad datasets from Dataverse_.
Here is some inspiration on what you could do:

- **Publish your study** (including its version history, data, code, results,
  and provenance) as a DataLad dataset to Dataverse to share it with
  collaborators

- **DOIify** your work by getting a DOI for it from Dataverse.

- **Share a published dataset's URL** with colleagues and collaborators to give
  them easy access to your work with a single ``datalad clone``.

- **Clone a friend's DataLad dataset** -- from Dataverse!

The combination of DataLad and Dataverse enables the additional use case of a
data-less dataset deposition. A DataLad dataset can be conceptualized as an
actionable metadata collection with precise information on identity and
availability of all components of a dataset. So precise, that DataLad can use
this information to retrieve any component from any physical storage location,
and verify its identity. So even without depositing a physical copy of all data
associated with a dataset, a DataLad dataset on Dataverse is a precise and
verifiable deposit that allows for the *location* of its components to change,
but not their content or *identity*.


What can I **not** use this extension for?
------------------------------------------

- This particular extension package does not work for datasets stored in a
  service other than Dataverse_. Please refer, for example, to the list of
  `special remotes`_ as hosted by the `git-annex`_ website for other storage
  services and how to use them with DataLad, and to the `DataLad handbook
  <http://handbook.datalad.org>`__ for an overview of other extension packages.
- Dataverse installations may have upload or storage limits. Exceeding those
  limits is not possible with this tool. However, you will be able to at least
  deposit the revision history of your dataset even if dataset content is too large.
- The starting point for working with this extension is a DataLad dataset, not
  only a collection of files in a directory. This extension package will also not
  transform existing Dataverse dataset into DataLad datasets, but expose DataLad
  datasets as Dataverse datasets.
- Please see the :ref:`feature support <feature_support>` section for details
  on what is and is not supported by this extension package.
