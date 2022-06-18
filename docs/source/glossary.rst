..  _glossary:

Glossary
========

DataLad and Dataverse have a few central concepts that are similar, but not synonymous.
The overview below can help you delineate and map the two software's key concepts, and you can find more information in the respective tool's documentation (`Dataverse docs <https://guides.dataverse.org/en/latest/user>`_, `DataLad docs <http://handbook.datalad.org/en/latest/>`_).


.. Glossary::

  Dataverse dataset
     Dataverse datasets contain digital files (research data, code, ...), amended with additional metadata. They typically live inside of dataverse collections.

  DataLad dataset
     DataLad datasets are joint Git/git-annex repositories that can version control digital files. The datalad-dataverse extension allows you to publish DataLad datasets as Dataverse datasets.

  Dataverse collection.
     A Dataverse collection (sometimes only referred to as "Dataverse") can contain other Dataverse collections or Dataverse datasets.

  DataLad superdataset
     A DataLad superdataset contains other DataLad datasets. This linkage can be arbitrarily deep.

  Dataverse linking
     Dataverse can link to other dataverses, or datasets in other collections.

  DataLad nesting
     DataLad datasets can be nested in one another in arbitrarily deep hierarchies of super- and subdatasets

