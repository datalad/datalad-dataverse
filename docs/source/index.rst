DataLad Dataverse
*****************

.. image:: _static/logo.png
   :width: 400
   :alt: Datalad Dataverse extension logo

`Dataverse <https://dataverse.org>`__ is open source research data repository 
software that is deployed all over the world in data or metadata repositories, 
so called Dataverse collections. It supports sharing, preserving, citing, 
exploring, and analyzing research data with descriptive metadata, and thus 
contributes greatly to open, reproducible, and FAIR science. `DataLad <http://datalad.org>`__, 
on the other hand, is a data management and data publication tool build on 
`Git <https://git-scm.org>`__ and `git-annex <https://git-annex.branchable.com>`__. Its core data 
structure, DataLad datasets, can version control files of any size, and 
streamline data sharing, updating, and collaboration. 

The aim of this project is to make DataLad interoperable with Dataverse to 
support dataset transport from and to Dataverse instances. It originates 
from `OHBM BrainHack 2022 <https://github.com/ohbm/hackathon2022/issues/43>`__.  

Documentation overview
======================

.. toctree::
   :maxdepth: 1

   glossary

API
===

High-level API commands
-----------------------

.. currentmodule:: datalad.api
.. autosummary::
   :toctree: generated

   create_sibling_dataverse


Command line reference
----------------------

.. toctree::
   :maxdepth: 1

   generated/man/datalad-create-sibling-dataverse


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. |---| unicode:: U+02014 .. em dash
