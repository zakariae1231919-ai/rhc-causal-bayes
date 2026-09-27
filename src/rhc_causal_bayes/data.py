"""Load the raw RHC data, apply the cleaning decisions of the EDA, and build model-ready tables.

The cleaning decisions are justified in `notebooks/01_eda.ipynb` (section 1.11) and
the variables are described in `docs/data_dictionary.md`.

Run `make data` (or `python -m rhc_causal_bayes.data`) to write:
- `data/processed/rhc_clean.parquet`: one row per patient, readable columns, categoricals kept;
- `data/processed/rhc_model.parquet`: numeric design matrix X, plus treatment `A`,
  outcome `Y` and diagnostic-group code `group`.
"""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW_PATH = ROOT / "data" / "raw" / "rhc.csv"
PROCESSED_DIR = ROOT / "data" / "processed"

# --- Variable roles --------------------------------------------------------------------

TREATMENT = "swang1"
OUTCOME = "dth30"
POST_TREATMENT = ["death", "t3d30", "dthdte", "dschdte", "lstctdte"]
# Observed only for patients alive at the day-3 interview (post-treatment selection)
SURVIVAL_DEPENDENT = ["adld3p"]

YES_NO = [
    "resp", "card", "neuro", "gastr", "renal", "meta", "hema", "seps", "trauma", "ortho",
    "dnr1",
]  # fmt: skip
COMORBIDITIES = [
    "cardiohx", "chfhx", "dementhx", "psychhx", "chrpulhx", "renalhx",
    "liverhx", "gibledhx", "malighx", "immunhx", "amihx", "transhx",
]  # fmt: skip
CONTINUOUS = [
    "age", "edu", "aps1", "scoma1", "surv2md1", "das2d3pc",
    "meanbp1", "hrt1", "resp1", "temp1", "pafi1", "paco21", "ph1", "wblc1",
    "hema1", "sod1", "pot1", "crea1", "bili1", "alb1", "urin1", "wtkilo1",
]  # fmt: skip

# Levels of each categorical variable; the first level is the reference category
CATEGORY_LEVELS = {
    "cat1": [
        "ARF", "MOSF w/Sepsis", "COPD", "CHF", "Coma", "MOSF w/Malignancy",
        "Cirrhosis", "Lung Cancer", "Colon Cancer",
    ],
    "cat2": [
        "None", "MOSF w/Sepsis", "MOSF w/Malignancy", "Coma",
        "Cirrhosis", "Lung Cancer", "Colon Cancer",
    ],
    "ca": ["No", "Yes", "Metastatic"],
    "sex": ["Female", "Male"],
    "race": ["white", "black", "other"],
    "income": ["Under $11k", "$11-$25k", "$25-$50k", "> $50k"],
    "ninsclas": [
        "Private", "Medicare", "Private & Medicare", "Medicaid",
        "Medicare & Medicaid", "No insurance",
    ],
}  # fmt: skip

# --- Cleaning rules (EDA, section 1.11) -------------------------------------------------

# Default values written by SUPPORT when a lab was not measured (exact stored values)
FILL_IN_VALUES = {"alb1": 3.5, "bili1": 1.00976562, "pafi1": 333.3125}
# Values above these bounds are physiologically impossible or implausible
UPPER_BOUNDS = {"alb1": 10.0, "edu": 25.0}
# Right-skewed positive labs, log1p-transformed in the design matrix
LOG_VARIABLES = ["bili1", "crea1", "wblc1", "paco21"]

SAS_ORIGIN = "1960-01-01"


def load_raw(path: Path = RAW_PATH) -> pd.DataFrame:
    """Read rhc.csv, drop the unnamed row-index column, check one row per patient."""
    raw = pd.read_csv(path)
    raw = raw.drop(columns=raw.columns[0])
    if not raw["ptid"].is_unique:
        raise ValueError("ptid is not unique: expected one row per patient")
    return raw


def clean(raw: pd.DataFrame) -> pd.DataFrame:
    """Apply the EDA cleaning decisions; return one row per patient, indexed by ptid.

    Output columns: `A` (1 = RHC), `Y` (1 = death within 30 days), pre-treatment
    covariates with no missing values, and missingness / fill-in indicators (0/1).
    Post-treatment and survival-dependent variables are removed.
    """
    df = raw.set_index("ptid").copy()
    out = pd.DataFrame(index=df.index)

    out["A"] = df[TREATMENT].map({"No RHC": 0, "RHC": 1}).astype(int)
    out["Y"] = df[OUTCOME].map({"No": 0, "Yes": 1}).astype(int)

    # Categorical variables: fixed levels, "None" for the structural NaN of cat2
    df["cat2"] = df["cat2"].fillna("None")
    for col, levels in CATEGORY_LEVELS.items():
        if not df[col].isin(levels).all():
            raise ValueError(f"unexpected level in {col}")
        out[col] = pd.Categorical(df[col], categories=levels)

    for col in YES_NO:
        out[col] = df[col].map({"No": 0, "Yes": 1}).astype(int)
    for col in COMORBIDITIES:
        out[col] = df[col].astype(int)

    # Calendar time: years since 1989-01-01 (admission dates are SAS dates)
    admission = pd.to_datetime(df["sadmdte"], unit="D", origin=SAS_ORIGIN)
    out["adm_years"] = (admission - pd.Timestamp("1989-01-01")).dt.days / 365.25

    # Indicators are computed on the raw values, before any modification
    cont = df[CONTINUOUS].astype(float)
    for col, value in FILL_IN_VALUES.items():
        out[f"{col}_filled"] = (cont[col] == value).astype(int)
    out["cardiac_arrest"] = ((cont["meanbp1"] == 0) & (cont["hrt1"] == 0)).astype(int)

    # Impossible values become missing
    cont.loc[cont["wtkilo1"] == 0, "wtkilo1"] = np.nan
    for col, bound in UPPER_BOUNDS.items():
        cont.loc[cont[col] > bound, col] = np.nan

    # Genuine missing values: indicator + median imputation. The median uses neither
    # A nor Y, so imputing on the full sample does not leak outcome information.
    for col in ["urin1", "wtkilo1"]:
        out[f"{col}_missing"] = cont[col].isna().astype(int)
    out[CONTINUOUS] = cont.fillna(cont.median())

    return out


def design_matrix(
    clean_df: pd.DataFrame,
) -> tuple[pd.DataFrame, np.ndarray, np.ndarray, np.ndarray]:
    """Build the numeric inputs of the causal models.

    Returns (X, a, y, group):
    - X: covariates, shape (n, p), float. Categoricals one-hot encoded (reference level
      dropped), skewed labs log1p-transformed. Not standardized: each model does it.
    - a, y: treatment and outcome, shape (n,), values in {0, 1}.
    - group: primary disease category code (0..8, order of CATEGORY_LEVELS["cat1"]).
    """
    covariates = clean_df.drop(columns=["A", "Y"])
    for col in LOG_VARIABLES:
        covariates[col] = np.log1p(covariates[col])
    covariates = covariates.rename(columns={col: f"log_{col}" for col in LOG_VARIABLES})

    X = pd.get_dummies(
        covariates, columns=list(CATEGORY_LEVELS), drop_first=True, dtype=float
    )
    X = X.astype(float)

    a = clean_df["A"].to_numpy()
    y = clean_df["Y"].to_numpy()
    group = clean_df["cat1"].cat.codes.to_numpy()
    return X, a, y, group


def build(raw_path: Path = RAW_PATH, out_dir: Path = PROCESSED_DIR) -> None:
    """Run the full data pipeline and write the two Parquet files."""
    clean_df = clean(load_raw(raw_path))
    X, a, y, group = design_matrix(clean_df)

    out_dir.mkdir(parents=True, exist_ok=True)
    clean_df.to_parquet(out_dir / "rhc_clean.parquet")
    model_df = X.assign(A=a, Y=y, group=group)
    model_df.to_parquet(out_dir / "rhc_model.parquet")

    print(
        f"rhc_clean.parquet: {clean_df.shape[0]} patients x {clean_df.shape[1]} columns"
    )
    print(f"rhc_model.parquet: X has {X.shape[1]} covariates (+ A, Y, group)")
    print(f"written to {out_dir}")


def load_clean(path: Path = PROCESSED_DIR / "rhc_clean.parquet") -> pd.DataFrame:
    """Read the cleaned table written by `build`."""
    return pd.read_parquet(path)


if __name__ == "__main__":
    build()
