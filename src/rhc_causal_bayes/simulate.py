"""Simulated data with a known causal effect, used to validate the estimators.

Data-generating process (DGP), with X ~ N(0, I_5):

    e(X)   = P(A = 1 | X) = expit(-0.5 + 0.8 X0 + 0.9 X2)
    p0(X)  = P(Y = 1 | A = 0, X) = expit(-0.4 + 0.7 X0 + 0.5 X1 - 0.3 X3)
    p1(X)  = P(Y = 1 | A = 1, X) = expit(-0.4 + 0.7 X0 + 0.5 X1 - 0.3 X3 + (-0.3 + 0.4 X1))

Roles of the covariates:
    X0  confounder: affects both A and Y
    X1  prognostic (affects Y) and effect modifier (the effect depends on X1)
    X2  affects A only (instrument-like)
    X3  prognostic only
    X4  pure noise

The individual effect on the risk-difference scale is tau(x) = p1(x) - p0(x).
"""

from dataclasses import dataclass

import numpy as np
from scipy.special import expit

N_COVARIATES = 5
PS_INTERCEPT, PS_COEF = -0.5, np.array([0.8, 0.0, 0.9, 0.0, 0.0])
OUTCOME_INTERCEPT, OUTCOME_COEF = -0.4, np.array([0.7, 0.5, 0.0, -0.3, 0.0])
EFFECT_INTERCEPT, EFFECT_X1 = -0.3, 0.4  # treatment effect on the logit scale


@dataclass
class SimulatedData:
    """One simulated dataset. Arrays have n rows; X has N_COVARIATES columns."""

    X: np.ndarray  # covariates, shape (n, 5)
    a: np.ndarray  # treatment in {0, 1}, shape (n,)
    y: np.ndarray  # outcome in {0, 1}, shape (n,)
    e: np.ndarray  # true propensity score e(X), shape (n,)
    tau: np.ndarray  # true individual effects p1(X) - p0(X), shape (n,)

    @property
    def sample_ate(self) -> float:
        """Mean of the true individual effects over this sample's X."""
        return float(self.tau.mean())


def true_probabilities(X: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """True e(X), p0(X), p1(X) for covariates X of shape (n, 5)."""
    e = expit(PS_INTERCEPT + X @ PS_COEF)
    linear = OUTCOME_INTERCEPT + X @ OUTCOME_COEF
    effect = EFFECT_INTERCEPT + EFFECT_X1 * X[:, 1]
    return e, expit(linear), expit(linear + effect)


def simulate(n: int, seed: int = 0) -> SimulatedData:
    """Draw n patients from the DGP."""
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, N_COVARIATES))
    e, p0, p1 = true_probabilities(X)
    a = rng.binomial(1, e)
    y = rng.binomial(1, np.where(a == 1, p1, p0))
    return SimulatedData(X=X, a=a, y=y, e=e, tau=p1 - p0)


def true_ate(n_mc: int = 1_000_000, seed: int = 12345) -> float:
    """Population ATE E[p1(X) - p0(X)], by Monte Carlo integration over X.

    No A or Y is drawn: the only error is the Monte Carlo error on the mean of
    tau(X), about sd(tau) / sqrt(n_mc), i.e. below 1e-4 for the default n_mc.
    """
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n_mc, N_COVARIATES))
    _, p0, p1 = true_probabilities(X)
    return float((p1 - p0).mean())
