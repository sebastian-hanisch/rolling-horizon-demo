"""Einheiten: Pfade, bedingte Stichproben, Niveau, Block-Mengen und die Bestandssimulation an einem Mini-Pfad von Hand."""

import numpy as np
import pytest

import rol_algorithm as A
import rol_constants as C
import rol_evaluation as ev
from rol_rng import normal_block


def test_paths_are_deterministic_and_lognormal_with_the_right_mean():
    m = A.Model(lead=0, phi=0.8)
    z1, d1 = A.simulate_paths(m, 20000, 5)
    z2, d2 = A.simulate_paths(m, 20000, 5)
    assert np.array_equal(d1, d2) and d1.shape == (20000, C.T)
    assert d1.mean() == pytest.approx(m.mu, rel=0.02)           # Mittel mu für jedes phi
    assert np.log(d1).std() == pytest.approx(m.sigma, rel=0.03)


def test_persistence_shows_up_in_the_autocorrelation_of_the_log_demand():
    for phi in (0.0, 0.5, 0.95):
        _, d = A.simulate_paths(A.Model(phi=phi), 20000, 9)
        x = np.log(d)
        corr = np.corrcoef(x[:, 4], x[:, 5])[0, 1]
        assert corr == pytest.approx(phi, abs=0.03)


def test_conditional_samples_collapse_to_the_expected_value_without_noise():
    m = A.Model(lead=0, phi=0.5, sigma=0.3)
    z_last = np.array([0.0, 0.6])
    samples = A.conditional_samples(m, z_last, 3, np.zeros((4, 3)))
    # ohne Innovation: z_{t+1} = phi * z_t, Nachfrage mu * exp(z - sigma^2/2)
    expected = m.mu * np.exp(np.array([[0.0, 0.0, 0.0], [0.3, 0.15, 0.075]]) - 0.5 * 0.09)
    assert samples[0] == pytest.approx(expected, rel=1e-12)


def test_static_policy_hand_calculation(mini_model, mini_demand):
    # Niveau 100, Nachfrage 80, 120, 100: Bestand 20 (Kosten 20), dann -20 (Kosten 60), dann 0
    z = np.zeros((1, 4))
    cost = A.simulate_policy(mini_model, z, mini_demand, "static", 1, np.zeros((2, 4)), level=100.0)
    assert cost[0] == pytest.approx(80.0)


def test_seer_pays_nothing_without_lead_time(mini_model, mini_demand):
    assert A.seer_cost(mini_model, mini_demand)[0] == pytest.approx(0.0)


def test_seer_with_lead_time_pays_nothing_when_demand_equals_the_initial_pipeline():
    for lead in (1, 2):
        m = A.Model(lead=lead, phi=0.0, horizon=5)
        assert A.seer_cost(m, np.full((1, 5), 100.0))[0] == pytest.approx(0.0)


def test_level_policy_with_a_single_block_never_orders_negative_and_costs_are_nonnegative():
    m = A.Model(lead=1, phi=0.8)
    z, d = A.simulate_paths(m, 500, 3)
    eps = normal_block(1, 100 * (C.T + 1)).reshape(100, C.T + 1)
    for kind in ("quantity", "level"):
        for r in (1, 3, 12):
            cost = A.simulate_policy(m, z, d, kind, r, eps)
            assert (cost >= 0).all()


def test_a_block_of_one_period_makes_quantity_and_level_policies_identical():
    m = A.Model(lead=0, phi=0.8)
    z, d = A.simulate_paths(m, 400, 3)
    eps = normal_block(1, 200 * (C.T + 1)).reshape(200, C.T + 1)
    q = A.simulate_policy(m, z, d, "quantity", 1, eps)
    lv = A.simulate_policy(m, z, d, "level", 1, eps)
    assert q == pytest.approx(lv, rel=1e-9)


def test_order_up_to_level_grows_with_the_last_observation():
    m = A.Model(lead=1, phi=0.8)
    eps = normal_block(2, 400 * (C.T + 1)).reshape(400, C.T + 1)
    z_last = np.array([-0.5, 0.0, 0.5])
    levels = A.order_up_to_level(m, A.conditional_samples(m, z_last, 2, eps), 0)
    assert levels[0] < levels[1] < levels[2]


def test_settings_defaults_are_consistent_with_the_choices():
    s = ev.Settings()
    assert s.phi in C.PHI_CHOICES and s.lead in C.LEAD_CHOICES and s.r in C.R_CHOICES
    assert C.T % 1 == 0 and C.T in C.R_CHOICES
