"""Frequentist estimators of the average treatment effect (risk-difference scale)."""

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from scipy.stats import norm
from sklearn.base import ClassifierMixin
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import StandardScaler

ModelFactory = Callable[[], ClassifierMixin | Pipeline]


def make_logit() -> Pipeline:
    """Logistic regression on standardized covariates (default mild L2 penalty, C=1)."""
    return make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))


@dataclass
class AIPWResult:
    """AIPW estimate with its influence-function standard error and nuisances.

    All arrays have shape (n,) and are out-of-fold (cross-fitted) predictions.
    """

    estimate: float
    se: float
    phi: np.ndarray  # influence-function values: estimate = mean(phi)
    e: np.ndarray  # propensity score, after clipping
    mu0: np.ndarray  # predicted P(Y = 1 | A = 0, X)
    mu1: np.ndarray  # predicted P(Y = 1 | A = 1, X)

    def ci(self, level: float = 0.95) -> tuple[float, float]:
        """Wald confidence interval estimate +/- z * se."""
        z = norm.ppf(0.5 + level / 2)
        return float(self.estimate - z * self.se), float(self.estimate + z * self.se)


def aipw(
    X: np.ndarray,
    a: np.ndarray,
    y: np.ndarray,
    ps_model: ModelFactory = make_logit,
    outcome_model: ModelFactory = make_logit,
    k: int = 5,
    clip: float = 0.01,
    seed: int = 0,
) -> AIPWResult:
    """Cross-fitted AIPW estimate of the ATE E[Y(1)] - E[Y(0)].

    X: covariates (n, p); a, y: treatment and outcome in {0, 1}, shape (n,).
    ps_model, outcome_model: functions returning a new unfitted sklearn classifier.
    k: number of folds; clip: propensity scores are clipped to [clip, 1 - clip].
    """
    X, a, y = np.asarray(X, dtype=float), np.asarray(a), np.asarray(y)
    n = len(y)
    e, mu0, mu1 = np.empty(n), np.empty(n), np.empty(n)

    # Stratify on (A, Y) so that every training fold contains the four (A, Y) cells
    folds = StratifiedKFold(n_splits=k, shuffle=True, random_state=seed)
    for train, test in folds.split(X, 2 * a + y):
        e[test] = ps_model().fit(X[train], a[train]).predict_proba(X[test])[:, 1]
        # One outcome model per arm, each fitted on the patients of that arm only
        train1, train0 = train[a[train] == 1], train[a[train] == 0]
        mu1[test] = (
            outcome_model().fit(X[train1], y[train1]).predict_proba(X[test])[:, 1]
        )
        mu0[test] = (
            outcome_model().fit(X[train0], y[train0]).predict_proba(X[test])[:, 1]
        )

    e = np.clip(e, clip, 1 - clip)
    phi = mu1 - mu0 + a * (y - mu1) / e - (1 - a) * (y - mu0) / (1 - e)
    return AIPWResult(
        estimate=float(phi.mean()),
        se=float(phi.std(ddof=1) / np.sqrt(n)),
        phi=phi,
        e=e,
        mu0=mu0,
        mu1=mu1,
    )
