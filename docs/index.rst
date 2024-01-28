.. TCutility documentation master file, created by
   sphinx-quickstart on Sun Aug 27 13:58:34 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

TCutility |ProjectVersion| documentation
========================================

**TCutility** is a Python library containing many helper functions and classes for use in programs written in the `TheoCheM group <https://www.theochem.nl/>`_.


.. toctree::
   :maxdepth: 2
   :caption: Analyse calculations with tcutility.results

   tcutility.results

The main results reading package. Use this to analyse and retrieve results from your calculations. We currently support ADF, DFTB and ORCA calculations.

.. toctree::
   :maxdepth: 2

   tcutility.job

The job running package is used to easily set up workflows for your projects.

.. toctree::
   :maxdepth: 2
   :caption: Extra utility packages

   tcutility.constants
   tcutility.data


TCutility |ProjectVersion| API documentation
--------------------------------------------

.. toctree::
   :maxdepth: 1

   api/tcutility
   api/tcutility.results
   api/tcutility.job
   api/tcutility.data


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. note::

   This library is under heavy development, so there are no guarantees that older code will work with newer versions.
