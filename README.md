# TCutility

[![Documentation](https://github.com/TheoChem-VU/TCutility/actions/workflows/build_docs.yml/badge.svg)](https://github.com/TheoChem-VU/TCutility/actions/workflows/build_docs.yml) [![Testing](https://github.com/TheoChem-VU/TCutility/actions/workflows/build_python_versions.yml/badge.svg)](https://github.com/TheoChem-VU/TCutility/actions/workflows/build_python_versions.yml) [![Publishing to PyPI](https://github.com/TheoChem-VU/TCutility/actions/workflows/pypi_publish.yml/badge.svg?branch=main)](https://github.com/TheoChem-VU/TCutility/actions/workflows/pypi_publish.yml)

[![TCutility version](https://badge.fury.io/py/TCutility.svg)](https://pypi.org/project/TCutility/)

Utility functions/classes for the TheoCheM programs

## Installation

The easiest and recommended installation method is via pip:

```python -m pip install tcutility```

To update the package, please run:

```python -m pip install --upgrade tcutility```

<details>
<summary><h4>Manual Installation</h4></summary>
The following is for people who would like to install the repository themselves. For example, to edit and/or contribute code to the project.

First clone this repository:

``` git clone https://github.com/TheoChem-VU/TCutility.git ```

Then move into the new directory and install the package:

```python
cd TCutility
python -m pip install --upgrade build
python -m build
python -m pip install -e .
```

To get new updates, simply run:

``` git pull ```

</details>

## Documentation

Documentation of TCutility is hosted at <https://theochem-vu.github.io/TCutility/> (work in progress)

## Usage

List of available utilities and their usage:

- tcutility.results | Read information from AMS calculations such as timings, settings, results, etc. from files in the calculation directory. Currently supports the ADF and DFTB engines.
- tcutility.molecule | Read and write rich xyz files. These are used to conveniently supply extra information with your xyz files, for example to let a program know what calculations to perform, or to include properties such as charge and spin-polarization.
- tcutility.analysis | Useful functions that are used for further analysis of calculation results. Currently includes vibrational mode checking to obtain or verify the reaction coordinate of an imaginary mode.
