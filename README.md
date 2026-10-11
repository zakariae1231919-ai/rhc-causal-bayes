# Effect of right heart catheterization on 30-day mortality

> 🚧 **Work in progress.** Nothing below is a final result yet.

**Question.** Among critically ill ICU patients, does right heart catheterization (RHC) within the first 24 hours change 30-day mortality?

**Why it is hard.** RHC is not randomized: clinicians choose it for the sickest patients. The crude mortality is 38.0% with RHC and 30.6% without (+7.4 points), but part of this gap reflects **confounding by indication**, not an effect of the catheter. The project estimates the causal effect under explicit assumptions, validates every estimator on simulations with a known truth, and quantifies sensitivity to unmeasured confounding.

**Data.** SUPPORT study, 5,735 ICU patients admitted between 1989 and 1994 (Connors et al., *JAMA* 1996), distributed by [Vanderbilt Biostatistics](https://hbiostat.org/data/repo/rhc). Variable definitions and known data-quality issues: [`docs/data_dictionary.md`](docs/data_dictionary.md).

## Planned methods

- DAG and selection of pre-treatment covariates
- Validation on simulations: empirical coverage of each estimator
- Cross-fitted AIPW (reference) and Double Machine Learning (boosting nuisances)
- Hierarchical Bayesian g-computation (NumPyro)
- Heterogeneity: DR-learner, causal forest, GATES calibration
- Sensitivity to unmeasured confounding (E-value)

## Roadmap

- [x] Project skeleton: `uv`, `ruff`, `pytest`, CI, Docker
- [x] Data dictionary
- [x] Exploratory data analysis: data quality, confounding, prognostic factors, overlap ([`notebooks/01_eda.ipynb`](notebooks/01_eda.ipynb))
- [x] Data cleaning module with tests (`make data`)
- [x] Known-truth simulator and cross-fitted AIPW, with tests
- [ ] DAG, propensity score, balance (SMD), IPW, g-computation
- [ ] Coverage study on simulations
- [ ] Double Machine Learning, including a non-linear simulation scenario
- [ ] Hierarchical Bayesian model
- [ ] Heterogeneous effects and E-value
- [ ] Streamlit app and deployment

## Reproduce

```bash
uv sync          # install the exact locked environment
make data        # clean the raw data -> data/processed/*.parquet
make test        # run the tests
make lint        # ruff checks
```

## Repository structure

```
src/rhc_causal_bayes/   package code
tests/                  tests
notebooks/              exploration only
docs/                   data dictionary
data/raw/               raw data (rhc.csv)
data/processed/         model-ready data, rebuilt by `make data` (not versioned)
```
