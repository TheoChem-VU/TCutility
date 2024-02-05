tcutility.results
=================

Overview
--------

The ``tcutility.results`` package allows you to easily retrieve information and results from a calculation performed using AMS, ORCA or CREST.
This includes results and settings from AMS as well as the calculation engine used (e.g. ADF, BAND, DFTB, ...).
Recommended usage is to use the |read| function to read the information.
One can also access specific information by calling one the functions in the submodules below.
Information will be given as :class:`tcutility.results.result.Result` objects and can be used just like a `dict`_.

.. code-block:: python

    >>> import TCutility.results
    >>> calc_dir = '../test/fixtures/ethanol'
    >>> info = TCutility.results.read(calc_dir)
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


.. _dict: https://docs.python.org/3.8/library/stdtypes.html#dict
