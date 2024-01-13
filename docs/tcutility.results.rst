tcutility.results package
=========================

The tcutility.results package enables you to easily retrieve information and results from a calculation done using AMS.
This includes results and settings from AMS as well as the calculation engine used (e.g. ADF, BAND, DFTB, ...).
Recommended usage is to use the :func:`tcutility.results.read` function to read the information.
One can also access specific information by calling one the functions in the submodules below.
Information will be given as :class:`tcutility.results.result.Result` objects and can be used just like a `dict`_.


tcutility.results
-----------------

.. automodule:: tcutility.results
   :members:
   :undoc-members:
   :show-inheritance:

tcutility.results.ams
---------------------

.. automodule:: tcutility.results.ams
   :members:
   :undoc-members:
   :show-inheritance:

tcutility.results.adf
---------------------

.. automodule:: tcutility.results.adf
   :members:
   :undoc-members:
   :show-inheritance:

tcutility.results.dftb
----------------------

.. automodule:: tcutility.results.dftb
   :members:
   :undoc-members:
   :show-inheritance:

tcutility.results.result
------------------------

.. automodule:: tcutility.results.result
   :members:
   :undoc-members:
   :show-inheritance:

tcutility.results.cache
-----------------------

.. automodule:: tcutility.results.cache
   :members:
   :undoc-members:
   :show-inheritance:

.. _dict: https://docs.python.org/3.8/library/stdtypes.html#dict
