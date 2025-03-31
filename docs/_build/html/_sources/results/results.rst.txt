tcutility.results
=================

Overview
--------

The ``tcutility.results`` package allows you to easily retrieve information and results from a calculation performed using AMS, ORCA, CREST, etc.
For AMS calculations this includes general results and settings from AMS as well as from the calculation engine used (e.g. ADF, BAND, DFTB, ...).
Recommended usage is to use the |read| function to read all available information.
One can also access specific information by calling one the functions in the submodules below.
To only obtain the status of a calculation we recommend usage of the `tcutility.results.quick_status` function.
Information will be given as |result| objects and can be used just like a `dict`_.

.. code-block:: python

    >>> import tcutility.results
    >>> calc_dir = '../../test/fixtures/ethanol'
    >>> info = tcutility.results.read(calc_dir)
    >>> info.engine
    adf
    >>> info.ams_version.full
    2022.103 r104886 (2022-06-17)
    >>> info.adf.symmetry
    {'group': 'C(S)', 'labels': ['AA', 'AAA']}
    >>> info.properties.energy.orbint
    {'AA': -2738.644830445246,
    'AAA': -1056.9706925183411,
    'total': -3795.615522963587}
    >>> info.properties.vibrations.number_of_imag_modes
    0


Available keys present in the |result| object
----------------------------------------------

After reading a calculation, different keys may be present in the |result| object depending on the engine used. Think of reading an adf calculation, or an orca calculation.
Below you can find a list of keys that are present in the |result| object for each type of calculation.

ADF calculation
***************

.. literalinclude:: ../_static/result/adf_multikeys.txt
    :language: text



.. _dict: https://docs.python.org/3.12/library/stdtypes.html#dict
