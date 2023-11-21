from pathlib import Path
import shutil

import pytest
import pandas as pd

from HydXS import run_hydxs

ROOT_PATH = Path(__file__).parent.parent.parent


@pytest.fixture
def get_example_data():
    """Load example test data."""

    return pd.read_csv(ROOT_PATH / "test_data/HydXS_test_data.csv")


@pytest.fixture
def setup_and_remove_data():
    """Remove test data after test."""
    yield
    shutil.rmtree(ROOT_PATH / "test_data/test_model_outs")


def test_001_run_basic_test(get_example_data: pd.DataFrame, setup_and_remove_data):
    """Run basic integration test."""
    out = run_hydxs(
        get_example_data,
        exclude=(),
        first=1,
        last=1,
        out_data_path="test_data/test_model_outs",
    )
    assert out["BankFull"].max() == 4.9
    assert out["BankLeft"].max() == 1.48
    assert out["BankRight"].max() == 7.0
