"""Known-truth tests: the estimators recover the causal effect of the simulator."""

import numpy as np
import pytest

from rhc_causal_bayes.frequentist import aipw
from rhc_causal_bayes.simulate import simulate, true_ate


@pytest.fixture(scope="module")
def truth() -> float:
    return true_ate()


@pytest.fixture(scope="module")
def sim():
    return simulate(20_000, seed=1)


@pytest.fixture(scope="module")
def aipw_result(sim):
    return aipw(sim.X, sim.a, sim.y)


# --- Simulator ---------------------------------------------------------------------------


def test_simulation_is_reproducible():
    first, second = simulate(500, seed=3), simulate(500, seed=3)
    assert np.array_equal(first.X, second.X)
    assert np.array_equal(first.y, second.y)


def test_simulated_quantities_are_valid(sim):
    n = 20_000
    assert sim.X.shape == (n, 5)
    assert sim.a.shape == sim.y.shape == sim.e.shape == sim.tau.shape == (n,)
    assert set(np.unique(sim.a)) == {0, 1}
    assert set(np.unique(sim.y)) == {0, 1}
    assert ((sim.e > 0) & (sim.e < 1)).all()
    assert ((sim.tau > -1) & (sim.tau < 1)).all()


def test_true_ate_monte_carlo_error_is_negligible(truth):
    assert abs(true_ate(seed=999) - truth) < 5e-4


# --- Estimators --------------------------------------------------------------------------


def test_naive_difference_is_biased_upwards(sim, truth):
    # X0 raises both P(A = 1) and P(Y = 1): treated patients are at higher baseline risk
    naive = sim.y[sim.a == 1].mean() - sim.y[sim.a == 0].mean()
    assert naive - truth > 0.05


def test_aipw_recovers_truth(aipw_result, truth):
    assert abs(aipw_result.estimate - truth) < 3 * aipw_result.se


def test_aipw_outputs_are_consistent(aipw_result):
    r = aipw_result
    assert r.estimate == pytest.approx(r.phi.mean())
    assert ((r.e >= 0.01) & (r.e <= 0.99)).all()
    assert ((r.mu0 > 0) & (r.mu0 < 1) & (r.mu1 > 0) & (r.mu1 < 1)).all()
    low, high = r.ci()
    assert low < r.estimate < high
    assert high - low == pytest.approx(2 * 1.959964 * r.se)


def test_aipw_is_reproducible():
    small = simulate(1_000, seed=5)
    first = aipw(small.X, small.a, small.y, seed=7)
    second = aipw(small.X, small.a, small.y, seed=7)
    assert first.estimate == second.estimate
