# HYDraulic Depth eXtrema via Smoothing (HydXS) bank full identification package

This package builds of of work from Derosa et al 2018 () to improve the automatic detection of bankfull boundaries in river cross sections.

## Installing the package

To install the package, first clone the repository

```bash
git clone
```
### creating the conda environment
right now we suggest creating a conda environment for the package via the comman line command (Note your shell or command prompt must be in the package directory)

```bash
conda env create -f environment.yml
```

Then you need to activate the environment

```bash
conda activate hydxs-env
```

or if on a windows machine:

```cmd
activate hydxs-env
```

### Install the package

next you must install the package from the command line (make sure you are still in the code repository)

```bash
python setup.py install
```
**Note** if you want to make changes in the code, you will have to rerun this command with the conda environment active to reinstall the package after you do, you can also run `python setup.py develop` to have it auto update itself

## run the package

You can run the package via the command line, or with python:

### command line usage:

You can see all the options in the HydXS/cli_interface.py file, (or by running `HydXS run --help`) but here is a basic example:

```bash
HydXS run data/small_test_ds.csv --out-data-path data/test_outs --xs-order-col Sort_Value
```

### python program usage:

in python you can run similar code as such:

```python
from HydXS import run_hydxs

results = run_hydxs("data/small_test_ds.csv", out_data_path = 'data/outputs', xs_order_col = "Sort_Value")

```

there are lots more optional arguments you can edit specified in the HydXS/run_HydXS file