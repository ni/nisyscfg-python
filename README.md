# NI System Configuration Python API

**Author:** National Instruments

## Table of Contents

- [About](#about)
- [Installation](#installation)
- [Usage](#usage)

## About

The **nisyscfg** package contains an API (Application Programming Interface)
for interacting with NI System Configuration. The package is implemented in Python.
This package was created by NI. The package is implemented as a complex, highly
object-oriented wrapper around the NI System Configuration C API using the
[ctypes](https://docs.python.org/3/library/ctypes.html) Python library.

**nisyscfg** supports only the Windows and Linux operating systems.

**nisyscfg** supports CPython 3.9+.

## Installation

Note: Running **nisyscfg** requires the NI System Configuration Runtime. Visit the
[NI downloads](https://www.ni.com/downloads/) to download the latest version of
NI System Configuration.

Install **nisyscfg** from PyPI:

```bash
pip install nisyscfg
```

Or, install **nisyscfg** by cloning the main branch and running the following command in the directory of setup.py:

```bash
pip install --pre .
```

## Usage

The following is a basic example of using an **nisyscfg.Session** object.

```python
import nisyscfg

with nisyscfg.Session() as session:
    # Print user aliases for all National Instruments devices in the local system
    filter = session.create_filter()
    filter.is_present = True
    filter.is_ni_product = True
    filter.is_device = True
    for resource in session.find_hardware(filter):
        print(resource.expert_user_alias[0])
```
