# DISPATCHES data packages

## Introduction

### What is it?

A simple way to distribute and refer to data files that cannot be included directly in the DISPATCHES repository.

### Goals

- Provide a reliable way to access the location of data files from DISPATCHES client code, regardless of the specifics of how DISPATCHES is installed (editable vs non-editable installation, local development vs CI, etc)
- Leverage as much as possible the built-in Python package distribution infrastructure to distribute collections of related non-code-files of small to moderate size (< 100 MB compressed)
- Allow using multiple repositories/package distributions to be used in a seamless way, so that the size limits only apply to each data package independently

### Non-goals

- Manage the packaged data in any way beyond the file-system level
  - i.e. the data package infrastructure only provide paths, which the client code uses to load the data in memory according to its specific needs
- Manage and/or expose metadata beyond the name of the package and the Python package distribution used to installed it
- Automatically enforce data distribution compliance requirements (LICENSE, COPYRIGHT, etc)
  - This **MUST** still be done, but the process shall be manual rather than automatic

### Requirements and Conventions

- DISPATCHES data packages SHALL be available on GitHub as repositories owned by the `https://github.com/gmlc-dispatches` organization
- DISPATCHES data packages MAY be available on PyPI
- The naming scheme SHOULD be consistent and follow this convention (using `my-example` as a placeholder):
  - Repository URL: `https://github.com/gmlc-dispatches/my-example-data`
  - Python package distribution name: `dispatches-my-example-data`
- The repository SHOULD register itself by adding the `dispatches-data-package` topic so that all data packages repositories can be browsed at the URL <https://github.com/topics/dispatches-data-package>
- The repository MUST follow this directory structure:

  ```txt
  my-example-data/
  `- .git/
  `- pyproject.toml
  `- src/
    `- dispatches_data/
      `- packages/
        `- my_example/
          `- __init__.py
          `- README.md

  ```

- Once installed, the data files SHALL be stored within the Python environment's `site-packages` directory as `.../lib/python3.8/site-packages/dispatches_data/packages/my_example`, i.e. the data package directory
- The name of the data package directory (`my_example`) SHALL be used to refer to the data package
- Users should access the data package and its contents using the functions available in the `dispatches_data.api` module
- The Python package directory (i.e. `.../lib/python3.8/site-packages/dispatches_data/packages/my_example`) MUST contain ALL information required for distribution of the data
  - This includes, but is not limited to:
    - License
    - Copyright
- The same information MAY be _repeated_ at the top level of the repository, but it MUST be in the package directory
  - This is to ensure that all required information is always present when the data files are installed (which might not be the case if the information is stored at the top level of the repository)
- More than one data packages MAY be distributed together (i.e. as part of the same repository and/or Python package distribution)
- In this case, all of the above requirements apply to each data package individually (i.e. each separate data package directory MUST contain the appropriate required information)

## Usage

### Step 1

Locate the data package(s) required by your application. In general, unless otherwise indicated, the naming conventions described above apply.

Using the same `my_example` placeholder as above, the data package repository will be located at <https://github.com/gmlc-dispatches/my-example-data.git>

### Step 2

Install the data package(s) required by your application, using `pip`.

```sh
pip install git+https://github.com/gmlc-dispatches/my-example-data.git
```

### Step 3

Verify that the data packages where installed correctly, e.g.:

```sh
pip show dispatches-my-example-data
```

### Step 4

It should now be possible to access the data package from the client code, i.e. the DISPATCHES code that will load and use the data files, using the functions exposed in the `dispatches_data.api` module. These are simple functions that typically take the data package name (`my_example`) as a `str` argument.

#### Example

Let's assume we want to create a dataframe from a file named `mydata.csv` in the `my_example` data package.

In a Python file or Jupyter notebook:

```py
import pandas as pd

from dispatches_data.api import path


def load_data() -> pd.DataFrame:
    path_to_csv_file = path("my_example") / "mydata.csv"
    df = pd.read_csv(path_to_csv_file)
    # process df as needed
    return df


def main():
    df = load_data()
    ...  # rest of the code
```

## API Reference

See the documentation for the `dispatches_data.api` module on [ReadTheDocs](https://dispatches-data-packages.readthedocs.io/en/latest/).
