"""Orakel-Tests (DEMO-PLAYBOOK §12): anderer Rechenweg als der Kern.

1. Persistenz 0, Lieferzeit 0: die Aufgabe zerfällt in T unabhängige Newsvendor-Probleme; Kosten = T * G(y*) in geschlossener Form (lognormal).
2. Hellseher: das Greedy-Verfahren gegen ein eigenes LP je Pfad (Lieferzeit 0, 1, 2).
3. Bedingtes Quantil: die Stichprobenschätzung gegen eine große Stichprobe mit eigener Zufallszahlenquelle.
4. Lieferzeit 0: die Niveau-Politik gegen eine dynamische Programmierung über (letzte Beobachtung, Bestand)."""

import numpy as np
import pytest
from scipy.interpolate import RegularGridInterpolator
from scipy.optimize import linprog
from scipy.stats import norm

import rol_algorithm as A
import rol_constants as C
from rol_rng import normal_block


def _newsvendor_cost(m: A.Model, y: float) -> float:
    """h E[(y - D)+] + p E[(D - y)+] für D lognormal mit Mittel mu und Streuung sigma, geschlossen."""
    s = m.sigma
    mean_log = np.log(m.mu) - 0.5 * s * s
    over = m.mu * norm.cdf((mean_log + s * s - np.log(y)) / s) - y * norm.cdf((mean_log - np.log(y)) / s)   # E[(D - y)+]
    under = over - m.mu + y                                                                                # E[(y - D)+]
    return m.hold * under + m.short * over


def test_without_persistence_and_lead_time_the_cost_is_t_times_the_newsvendor_cost():
    m = A.Model(lead=0, phi=0.0)
    y_star = float(np.exp(np.log(m.mu) - 0.5 * m.sigma ** 2 + m.sigma * norm.ppf(m.critical_ratio)))
    closed = m.horizon * _newsvendor_cost(m, y_star)
    z, d = A.simulate_paths(m, 6000, 11)
    eps = normal_block(5, 600 * (C.T + 1)).reshape(600, C.T + 1)
    cost = A.simulate_policy(m, z, d, "level", 1, eps)
    se = cost.std(ddof=1) / np.sqrt(len(cost))
    # Stichprobenniveau (600 Stichproben) und Pfadrauschen: drei Standardfehler plus 1 % für das geschätzte Niveau
    assert abs(cost.mean() - closed) <= 3 * se + 0.01 * closed


def _seer_lp(m: A.Model, d: np.ndarray) -> float:
    """Kosten des Hellsehers als LP: q_k >= 0 (k = 1..T-L), Bestand I_t = Pipeline_t + Summe_{k+L<=t} q_k - kumulierte Nachfrage_t."""
    horizon, lead = m.horizon, m.lead
    nq = max(0, horizon - lead)
    nv = nq + 2 * horizon
    c = np.concatenate([np.zeros(nq), np.full(horizon, m.hold), np.full(horizon, m.short)])
    a = np.zeros((horizon, nv))
    b = np.zeros(horizon)
    for t in range(1, horizon + 1):
        a[t - 1, nq + t - 1] = 1.0
        a[t - 1, nq + horizon + t - 1] = -1.0
        for k in range(1, nq + 1):
            if k + lead <= t:
                a[t - 1, k - 1] = -1.0
        b[t - 1] = m.mu * min(t, lead) - d[:t].sum()
    res = linprog(c, A_eq=a, b_eq=b, bounds=[(0, None)] * nv, method="highs")
    assert res.status == 0
    return float(res.fun)


@pytest.mark.parametrize("lead", [0, 1, 2])
def test_seer_greedy_matches_the_lp_per_path(lead):
    m = A.Model(lead=lead, phi=0.8)
    _, d = A.simulate_paths(m, 12, 17)
    greedy = A.seer_cost(m, d)
    for i in range(len(d)):
        assert greedy[i] == pytest.approx(_seer_lp(m, d[i]), abs=1e-6)


def test_conditional_quantile_matches_an_independent_large_sample():
    m = A.Model(lead=1, phi=0.8)
    z_last = np.array([-0.4, 0.0, 0.5])
    eps = normal_block(2, 3000 * (C.T + 1)).reshape(3000, C.T + 1)
    est = A.order_up_to_level(m, A.conditional_samples(m, z_last, 2, eps), 0)
    rng = np.random.default_rng(99)
    n = 400_000
    for i, z0 in enumerate(z_last):
        z1 = m.phi * z0 + m.innovation_sd * rng.standard_normal(n)
        z2 = m.phi * z1 + m.innovation_sd * rng.standard_normal(n)
        s = m.mu * (np.exp(z1 - 0.5 * m.sigma ** 2) + np.exp(z2 - 0.5 * m.sigma ** 2))
        assert est[i] == pytest.approx(np.quantile(s, m.critical_ratio), rel=0.02)


def _dp_policy(m: A.Model, nz=25, ni=301, nk=101, ilo=-250.0, ihi=450.0):
    """Optimale Politik für Lieferzeit 0 über (z_{t-1}, Bestand vor Bestellung) durch rückwärtige Rekursion; Rückgabe: Zielniveau je (t, z)."""
    zg = np.linspace(-4 * m.sigma, 4 * m.sigma, nz)
    ig = np.linspace(ilo, ihi, ni)
    eps = norm.ppf((np.arange(nk) + 0.5) / nk)
    v = np.zeros((nz, ni))
    ystar = np.zeros((m.horizon + 1, nz))
    for t in range(m.horizon, 0, -1):
        zn = m.phi * zg[:, None] + m.innovation_sd * eps[None, :]
        dk = m.mu * np.exp(zn - 0.5 * m.sigma ** 2)
        interp = RegularGridInterpolator((zg, ig), v, bounds_error=False, fill_value=None)
        w = np.zeros((nz, ni))
        zn_c = np.clip(zn, zg[0], zg[-1])
        for iy, y in enumerate(ig):
            inew = y - dk
            now = m.hold * np.maximum(inew, 0.0) + m.short * np.maximum(-inew, 0.0)
            pts = np.stack([zn_c.ravel(), np.clip(inew, ilo, ihi).ravel()], axis=1)
            w[:, iy] = ((now + interp(pts).reshape(nz, nk)) / nk).sum(axis=1)
        v = np.minimum.accumulate(w[:, ::-1], axis=1)[:, ::-1]
        ystar[t] = ig[np.argmin(w, axis=1)]
    return zg, ystar


def _run_dp(m: A.Model, z, d, zg, ystar):
    inv = np.zeros(d.shape[0])
    cost = np.zeros(d.shape[0])
    for t in range(1, m.horizon + 1):
        y = np.maximum(inv, np.interp(z[:, t - 1], zg, ystar[t]))
        inv = y - d[:, t - 1]
        cost += m.hold * np.maximum(inv, 0.0) + m.short * np.maximum(-inv, 0.0)
    return cost


@pytest.mark.parametrize("phi", [0.0, 0.8])
def test_level_policy_is_close_to_the_dynamic_programming_optimum_for_lead_time_zero(phi):
    m = A.Model(lead=0, phi=phi)
    zg, ystar = _dp_policy(m)
    z, d = A.simulate_paths(m, 3000, 23)
    eps = normal_block(7, 500 * (C.T + 1)).reshape(500, C.T + 1)
    rule = A.simulate_policy(m, z, d, "level", 1, eps)
    dp = _run_dp(m, z, d, zg, ystar)
    gap = (rule - dp).mean() / dp.mean()
    assert abs(gap) < 0.02                    # die Quantilregel ist hier praktisch optimal (Gitter und Stichprobe: höchstens 2 %)
