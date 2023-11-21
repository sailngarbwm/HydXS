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

The docstring is here:

```
Main function to run the entire pipeline on a set of cross section point data.

Args:
        point_df (geopandas.GeoDataFrame | pandas.DataFrame): input dataframe or GeoDataFrame with points along cross sections
        input_type (str, optional): type of Dataframe, "DF" if Dataframe, "GDF" if GeoDataFrame. Defaults to "DF".
        xy_col (tuple[str, str], optional): tuple of x and y column names. Defaults to ("POINT_X", "POINT_Y").
        z_col (str, optional): name of column that holds elevation data for each point. Defaults to "POINT_Z".
        xs_id_col (str, optional): Name of column that holds an integer cross section ID. Defaults to "x_sec_id".
        xs_order_col (str, optional): Name of column that holds the position of that point in the order of the cross section. Defaults to "x_sec_order".
        riv_centre (str, optional): name of Boolean column, where the point closest to the centre of the river is True. Defaults to "RivCentre".
        exclude (list[int], optional): list of cross section ID's to skip. Defaults to ().
        first (int, optional): First cross section ID to run. Defaults to 1.
        last (int, optional): Last cross section ID to run. Defaults to 648.
        window (int, optional): Window in map units to cut out from other minimums far away from . Defaults to 10.
        nVsteps (int, optional): Number of vertical steps to iterate over starting at minVdep. Defaults to 200.
        minVdep (float, optional): Minimum height above river centre (the thalweg) where the first hydraulic depth is measured. Defaults to 0.2.
        maxr (int, optional): Maximum number of sub runs for each cross section per run. Defaults to 3.
        nruns (int, optional): Number of runs over entire set of cross sections. Defaults to 11.
        out_data_path (str | Path, optional): data path where intermediate outputs are stored. Defaults to "model_outputs/test01/".

    Returns:
        pandas.DataFrame: output aggregate dataframe, it will have a value for each point, though some of them are cross section aggregated values.

            Note that it aggregates all 11 runs, and only shows either the mode (most often bankfull value arrived at) or the mean
            Output columns:
                x_sec_id - Cross section id
                x_sec_order - Order of point in the cross section
                POINT_X - x coordinate
                POINT_Y - y coordinate
                POINT_Z - z coordinate
                PointXY - XY shapely point
                Distance - Distance along cross section at that point
                PointDZ - Shapely point of (Distance, Z)
                RivCentre - True fals as whether at the centre of the river
                riverMin - Minimum elevation in the river
                inXS - True if point is in the Bankfull Cross section (includes point next to bankfull)
                InRiver - True if point is in the river (doesn't include bankfull point)
                BankFull - Bankfull width
                BankLeft - Distance along cross section where first non river point is on left
                BankRight - Distance along cross section where first non river point is on right
                CountAtBankFull - Number of runs that produces this bankfull measurement (only usefull for Mode outputs)

```
