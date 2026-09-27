"""Data invariants: the cleaning decisions of the EDA hold on the real data."""

import numpy as np
import pandas as pd
import pytest

from rhc_causal_bayes.data import (
    CATEGORY_LEVELS,
    CONTINUOUS,
    POST_TREATMENT,
    RAW_PATH,
    SURVIVAL_DEPENDENT,
    clean,
    design_matrix,
    load_raw,
)

pytestmark = pytest.mark.skipif(not RAW_PATH.exists(), reason="raw data not available")


@pytest.fixture(scope="module")
def raw() -> pd.DataFrame:
    return load_raw()


@pytest.fixture(scope="module")
def cleaned(raw) -> pd.DataFrame:
    return clean(raw)


def test_one_row_per_patient(raw, cleaned):
    assert len(raw) == 5735
    assert len(cleaned) == 5735
    assert cleaned.index.is_unique


def test_no_post_treatment_variable(cleaned):
    X, *_ = design_matrix(cleaned)
    forbidden = set(POST_TREATMENT) | set(SURVIVAL_DEPENDENT) | {"swang1", "dth30"}
    assert forbidden.isdisjoint(cleaned.columns)
    assert forbidden.isdisjoint(X.columns)
    assert {"A", "Y"}.isdisjoint(X.columns)


def test_no_missing_values(cleaned):
    assert cleaned.notna().all().all()


def test_treatment_and_outcome_are_binary_and_unchanged(raw, cleaned):
    assert set(cleaned["A"].unique()) == {0, 1}
    assert set(cleaned["Y"].unique()) == {0, 1}
    assert cleaned["A"].sum() == (raw["swang1"] == "RHC").sum() == 2184
    assert cleaned["Y"].sum() == (raw["dth30"] == "Yes").sum() == 1918


def test_impossible_values_removed(cleaned):
    assert (cleaned["wtkilo1"] > 0).all()
    assert (cleaned["alb1"] <= 10).all()
    assert (cleaned["edu"] <= 25).all()


def test_indicator_counts_match_eda(cleaned):
    expected = {
        "alb1_filled": 2509,
        "bili1_filled": 2043,
        "pafi1_filled": 554,
        "cardiac_arrest": 60,
        "wtkilo1_missing": 515,
        "urin1_missing": 3028,
    }
    for col, n in expected.items():
        assert cleaned[col].sum() == n, col


def test_zero_vital_signs_are_kept(cleaned):
    # Real cardiac arrests: the zeros are information, not missing values
    assert (cleaned.loc[cleaned["cardiac_arrest"] == 1, "meanbp1"] == 0).all()


def test_design_matrix_shapes_and_types(cleaned):
    X, a, y, group = design_matrix(cleaned)
    n = len(cleaned)
    assert X.shape[0] == a.shape[0] == y.shape[0] == group.shape[0] == n
    assert X.columns.is_unique
    assert all(dtype == np.float64 for dtype in X.dtypes)
    assert np.isfinite(X.to_numpy()).all()
    assert group.min() == 0 and group.max() == len(CATEGORY_LEVELS["cat1"]) - 1


def test_design_matrix_columns(cleaned):
    X, *_ = design_matrix(cleaned)
    # Reference levels are dropped, other levels are one-hot encoded
    assert "cat1_ARF" not in X.columns
    assert "cat1_Colon Cancer" in X.columns
    # Skewed labs are log-transformed, the other continuous variables are kept as is
    assert {"log_bili1", "log_crea1", "log_wblc1", "log_paco21"} <= set(X.columns)
    assert "bili1" not in X.columns
    assert {"aps1", "meanbp1", "age"} <= set(X.columns)
    assert set(CONTINUOUS) - {"bili1", "crea1", "wblc1", "paco21"} <= set(X.columns)
