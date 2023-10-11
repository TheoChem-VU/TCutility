[![Documentation](https://github.com/TheoChem-VU/TCutility/actions/workflows/build_docs.yml/badge.svg)](https://github.com/TheoChem-VU/TCutility/actions/workflows/build_docs.yml) [![Testing](https://github.com/TheoChem-VU/TCutility/actions/workflows/build_python_versions.yml/badge.svg)](https://github.com/TheoChem-VU/TCutility/actions/workflows/build_python_versions.yml) [![TCutility version](https://badge.fury.io/py/TCutility.svg)](https://pypi.org/project/TCutility/)

[![Publishing to PyPI](https://github.com/TheoChem-VU/TCutility/actions/workflows/pypi_publish.yml/badge.svg?branch=main)](https://github.com/TheoChem-VU/TCutility/actions/workflows/pypi_publish.yml)

# TCutility
Utility functions/classes for the TheoCheM programs

# Installation

The easiest way is installing this python package via pip:
``` python -m pip install TCutility```

It is also possible to install in locally by first cloning this repository in your terminal: 

``` git clone https://github.com/TheoChem-VU/TCutility.git ```

and then moving into the new directory and installing the package:

```
cd TCutility
python -m pip install --upgrade build 
python -m build 
python -m pip install -e .
```

# Documentation
Documentation can be found here https://theochem-vu.github.io/TCutility/ (work in progress)

# Usage
List of available utilities and their usage:
- TCutility.rkf | Read information from AMS calculations such as timings, settings, etc. from files in the calculation directory. Currently supports the ADF and DFTB engines


# Examples
