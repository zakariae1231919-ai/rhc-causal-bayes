# Data dictionary — RHC dataset

## Source

- **File:** `data/raw/rhc.csv` — 5,735 patients × 63 columns (the first, unnamed column is a row index).
- **Distributor:** Vanderbilt Department of Biostatistics, <https://hbiostat.org/data/repo/rhc>.
- **Study:** SUPPORT (*Study to Understand Prognoses and Preferences for Outcomes and Risks of Treatments*), five US teaching hospitals, admissions from June 1989 to January 1994.
- **Original analysis:** Connors A.F. et al. (1996). *The effectiveness of right heart catheterization in the initial care of critically ill patients.* JAMA 276:889–897.

Descriptions come from the distributor's page. Items marked **(verified)** were checked directly against the data; items marked **(unverified)** are our best interpretation and still need confirmation.

## Clinical context

Right heart catheterization (RHC, also called Swan-Ganz or pulmonary artery catheterization) threads a catheter through a large vein into the right heart and the pulmonary artery. It measures intracardiac pressures and cardiac output, which clinicians use to guide fluid and vasopressor therapy. It is invasive, and its benefit has never been clearly established.

RHC is not assigned at random: clinicians choose it for the patients they judge to be sickest. This **confounding by indication** is the central difficulty of the analysis.

## Roles

| Role | Meaning | Use in the analysis |
|---|---|---|
| Treatment | RHC within the first 24 hours | `A` |
| Outcome | Death within 30 days | `Y` |
| Pre-treatment | Measured on day 1 or before admission | candidate confounders `X` |
| Post-treatment | Measured after the treatment decision | **must be excluded** from `X` |
| Identifier | Row / patient identifiers | excluded |

Dates are stored as **SAS dates**, i.e. days since 1960-01-01 (verified: `sadmdte` spans 1989-06-11 to 1994-01-23).

## Treatment and outcome

| Variable | Description | Coding | Role | Notes |
|---|---|---|---|---|
| `swang1` | Right heart catheterization on day 1 | `RHC` / `No RHC` | Treatment | 2,184 RHC, 3,551 no RHC |
| `dth30` | Death within 30 days of admission | `Yes` / `No` | Outcome | Not documented by the distributor. **(verified)** Equals `dthdte − sadmdte ≤ 30` for every patient. 1,918 deaths (33.4%) |

## Post-treatment variables and identifiers (excluded)

| Variable | Description | Notes |
|---|---|---|
| `death` | Death at any time up to 180 days | Another outcome, not ours: 1,804 patients died between day 31 and day 180 |
| `t3d30` | Days until death, truncated at 30 | **(verified)** Days to death if `dth30 = Yes`, otherwise 30 |
| `dthdte` | Date of death | Missing ⇔ patient alive at 180 days **(verified)** |
| `dschdte` | Hospital discharge date | Gives length of stay (post-treatment) |
| `lstctdte` | Date of last contact | Follow-up information |
| `ptid` | Patient identifier | Unique per row **(verified)** |
| *(unnamed)* | Row index 1…5735 | Artifact of the CSV export |

## Admission

| Variable | Description | Notes |
|---|---|---|
| `sadmdte` | Study admission date | Pre-treatment. Captures calendar time, i.e. changes in practice between 1989 and 1994 |

## Demographics and socio-economic status

| Variable | Description | Coding / units | Notes |
|---|---|---|---|
| `age` | Age | years | 18.0–101.8 |
| `sex` | Sex | `Male` / `Female` | |
| `race` | Race | `white` / `black` / `other` | |
| `edu` | Years of education | years | 0–30; values above 25 are implausible |
| `income` | Annual income | 4 brackets, from `Under $11k` to `> $50k` | 56% under $11k |
| `ninsclas` | Medical insurance | `Private`, `Medicare`, `Private & Medicare`, `Medicaid`, `Medicare & Medicaid`, `No insurance` | Medicare: age ≥ 65 or disability. Medicaid: low income |

## Disease category

| Variable | Description | Levels |
|---|---|---|
| `cat1` | Primary disease category | `ARF` acute respiratory failure (2,490) · `MOSF w/Sepsis` multiple organ system failure with sepsis (1,227) · `COPD` chronic obstructive pulmonary disease (457) · `CHF` congestive heart failure (456) · `Coma` non-traumatic coma (436) · `MOSF w/Malignancy` (399) · `Cirrhosis` (224) · `Lung Cancer` (39) · `Colon Cancer` (7) |
| `cat2` | Secondary disease category | Same levels (a subset). Missing for 79%, which means *no secondary category*, not an unknown value |
| `ca` | Cancer | `No` / `Yes` / `Metastatic` |

## Admission diagnoses (`Yes` / `No`)

| Variable | Diagnosis category | n `Yes` |
|---|---|---|
| `resp` | Respiratory | 2,113 |
| `card` | Cardiovascular | 1,931 |
| `neuro` | Neurological | 693 |
| `gastr` | Gastrointestinal | 942 |
| `renal` | Renal | 295 |
| `meta` | Metabolic | 265 |
| `hema` | Hematological | 354 |
| `seps` | Sepsis | 1,031 |
| `trauma` | Trauma | 52 |
| `ortho` | Orthopedic | 7 |

Beware of name clashes: `resp` (diagnosis) vs `resp1` (respiratory rate), `hema` vs `hema1`, `renal` vs `renalhx`.

## Comorbidities and history (`0` / `1`)

| Variable | Description |
|---|---|
| `cardiohx` | Acute MI, peripheral vascular disease, severe cardiovascular symptoms (NYHA class III) or very severe cardiovascular symptoms (NYHA class IV) |
| `chfhx` | Congestive heart failure |
| `dementhx` | Dementia, stroke or cerebral infarct, Parkinson's disease |
| `psychhx` | Psychiatric history, active psychosis or severe depression |
| `chrpulhx` | Chronic pulmonary disease, severe or very severe pulmonary disease |
| `renalhx` | Chronic renal disease, chronic hemodialysis or peritoneal dialysis |
| `liverhx` | Cirrhosis, hepatic failure |
| `gibledhx` | Upper GI bleeding |
| `malighx` | Solid tumor, metastatic disease, chronic leukemia/myeloma, acute leukemia, lymphoma |
| `immunhx` | Immunosuppression, organ transplant, HIV, diabetes, connective tissue disease |
| `amihx` | Definite myocardial infarction |
| `transhx` | Transfer from another hospital (> 24 h) |

The detailed definitions (unverified) follow the usual SUPPORT comorbidity groupings. The distributor's page gives shorter labels.

## Severity scores and functional status (day 1)

| Variable | Description | Scale | Observed | Notes |
|---|---|---|---|---|
| `aps1` | APACHE III Acute Physiology Score | 0–252, higher = sicker | 3–147, median 54 | |
| `scoma1` | SUPPORT coma score, derived from the Glasgow Coma Scale | 0–100, 0 = no coma | 54% at 0 | Only 11 distinct values (ordinal). Not the raw Glasgow score (3–15) **(unverified)** |
| `surv2md1` | SUPPORT model estimate of the probability of surviving 2 months | 0–1 | median 0.63 | A model output built from other covariates (redundancy) |
| `das2d3pc` | Duke Activity Status Index (functional capacity, 2 weeks before admission), collected at a day-3 interview | usually 0–58.2 | 11–33 | Range differs from the standard DASI. Round values when the patient was interviewed; non-round, model-imputed-looking values for the 75% who were not **(verified pattern)** |
| `adld3p` | Activities of Daily Living index, 2 weeks before admission, collected at a day-3 interview | 0–7 | | **75% missing.** Observed almost only for patients alive at the interview: 0.4% died by day 3 vs 7.2% when missing **(verified)**. Excluded (post-treatment selection) |
| `dnr1` | Do-not-resuscitate order on day 1 | `Yes` / `No` | 654 `Yes` | |

## Physiology and laboratory values (day 1)

| Variable | Description | Units | Typical normal range | Median | Data-quality notes |
|---|---|---|---|---|---|
| `meanbp1` | Mean arterial blood pressure | mmHg | 70–105 | 63 | 80 zeros |
| `hrt1` | Heart rate | beats/min | 60–100 | 124 | 159 zeros |
| `resp1` | Respiratory rate | breaths/min | 12–20 | 30 | 136 zeros |
| `temp1` | Temperature | °C | 36.5–37.5 | 38.1 | |
| `pafi1` | PaO₂/FiO₂ ratio (oxygenation) | mmHg | > 400 (< 200: ARDS range) | 202 | 554 values exactly 333.3 (suspected fill-in) |
| `paco21` | Arterial PaCO₂ | mmHg | 35–45 | 37 | |
| `ph1` | Arterial pH | — | 7.35–7.45 | 7.40 | |
| `wblc1` | White blood cell count | 10⁹/L | 4–11 | 14.1 | 4 zeros |
| `hema1` | Hematocrit | % | 36–50 | 30 | |
| `sod1` | Serum sodium | mmol/L | 135–145 | 136 | |
| `pot1` | Serum potassium | mmol/L | 3.5–5.0 | 3.8 | |
| `crea1` | Serum creatinine (renal function) | mg/dL | 0.6–1.2 | 1.5 | Right-skewed |
| `bili1` | Total bilirubin (liver function) | mg/dL | 0.3–1.2 | 1.01 | 2,043 values exactly 1.01 (suspected fill-in) |
| `alb1` | Serum albumin | g/dL | 3.5–5.0 | 3.5 | 2,509 values exactly 3.5 (suspected fill-in); 2 values > 10 (impossible) |
| `urin1` | Urine output | mL/24 h | 800–2,000 | 1,927 | **53% missing** |
| `wtkilo1` | Weight | kg | — | 70 | 515 zeros (impossible, likely missing) |

## Known data-quality issues

Details and analysis: `notebooks/01_eda.ipynb`.

1. **Suspected hidden missing values.** `alb1 = 3.5`, `bili1 = 1.01` and `pafi1 = 333.3` occur far too often for continuous lab values. The most likely explanation is that SUPPORT replaced unmeasured labs with a "normal" value **(unverified)**.
2. **Impossible zeros** in `wtkilo1`, `hrt1`, `resp1` and `meanbp1`.
3. **Structural vs genuine missing values.** `cat2` and `dthdte` are structurally missing. `adld3p` and `urin1` are genuinely missing.
4. **Implausible values:** `alb1 > 10` g/dL, `edu > 25` years.
5. **Worst value of the first 24 hours.** Vital signs and labs follow the APACHE convention of recording the value farthest from normal. This makes `meanbp1`, `hrt1`, `temp1`, `hema1` and `pot1` bimodal, and the risk U-shaped in these variables.
6. **Zero vital signs.** The 60 patients with `meanbp1 = 0` and `hrt1 = 0` look like real cardiopulmonary arrests: 75% also have `resp1 = 0`, median APACHE 87.5 vs 53, and 55% 30-day mortality.

The cleaning decisions derived from these findings are listed in section 1.11 of the notebook.
