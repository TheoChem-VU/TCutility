TCutility.results package
=========================

The TCutility.results package enables you to easily retrieve information and results from a calculation done using AMS.
This includes results and settings from AMS as well as the calculation engine used (e.g. ADF, BAND, DFTB, ...).
Recommended usage is to use the :func:`TCutility.results.read` function to read the information. 
One can also access specific information by calling one the functions in the submodules below.
Information will be given as :class:`TCutility.results.result.Result` objects and can be used just like a `dict`_.


TCutility.results
-----------------

.. automodule:: TCutility.results
   :members:
   :undoc-members:
   :show-inheritance:

TCutility.results.adf
---------------------

.. automodule:: TCutility.results.adf
   :members:
   :undoc-members:
   :show-inheritance:

TCutility.results.ams
---------------------

.. automodule:: TCutility.results.ams
   :members:
   :undoc-members:
   :show-inheritance:

TCutility.results.cache
-----------------------

.. automodule:: TCutility.results.cache
   :members:
   :undoc-members:
   :show-inheritance:

TCutility.results.dftb
----------------------

.. automodule:: TCutility.results.dftb
   :members:
   :undoc-members:
   :show-inheritance:

TCutility.results.result
------------------------

.. automodule:: TCutility.results.result
   :members:
   :undoc-members:
   :show-inheritance:


.. _dict: https://docs.python.org/3.8/library/stdtypes.html#dict
