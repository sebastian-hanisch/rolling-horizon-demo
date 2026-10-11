"""Jede Aussage aus README und App-Text wird hier nachgerechnet (Bänder statt exakter Werte: CI installiert die neuesten numpy/scipy)."""

import pytest

import rol_constants as C
import rol_evaluation as ev


@pytest.fixture(scope="module")
def grid():
    return {(lead, phi): ev.analyse(ev.Settings(phi=phi, lead=lead)) for lead in (0, 2) for phi in C.PHI_CHOICES}


def test_without_persistence_only_the_feedback_matters(grid):
    a = grid[(0, 0.0)]
    assert abs(a.update.mean) <= 3 * a.update.se + 0.01 * a.level_once.mean
    assert a.verdict == "nur_rueckkopplung"
    assert a.level_once.mean == pytest.approx(a.static.mean, rel=0.02)     # eine statische Politik ist dort genauso gut
    assert 0.5 <= a.feedback.mean / a.open.mean <= 0.7


def test_feedback_is_a_large_part_of_the_open_plan_cost_everywhere(grid):
    for key, a in grid.items():
        assert a.feedback.mean / a.open.mean >= 0.3, key
    assert grid[(0, 0.8)].feedback.mean / grid[(0, 0.8)].open.mean >= 0.7


def test_the_value_of_re_forecasting_grows_with_persistence(grid):
    rel = [grid[(0, phi)].update.mean / grid[(0, phi)].level_once.mean for phi in C.PHI_CHOICES]
    assert rel == sorted(rel)
    assert rel[0] < 0.02 and 0.08 <= rel[1] <= 0.25 and 0.25 <= rel[2] <= 0.5 and rel[3] >= 0.4


def test_the_static_policy_does_not_depend_on_persistence_but_the_good_policy_does(grid):
    static = [grid[(0, phi)].static.mean for phi in C.PHI_CHOICES]
    assert max(static) / min(static) < 1.05
    best = [grid[(0, phi)].level_each.mean for phi in C.PHI_CHOICES]
    assert best == sorted(best, reverse=True)
    assert grid[(0, 0.95)].persistence.mean > 3 * grid[(0, 0.5)].persistence.mean


def test_frozen_quantities_lose_even_without_persistence():
    s = ev.Settings(phi=0.0, lead=0)
    rows = {(r["phi"], r["r"]): r for r in ev.rhythm_sweep(s)}
    assert rows[(0.0, 6)]["quantity"] >= 1.5 * rows[(0.0, 6)]["level"]
    assert rows[(0.0, 12)]["level"] == pytest.approx(rows[(0.0, 1)]["level"], rel=0.02)      # Niveaus: Rhythmus egal bei phi = 0
    assert rows[(0.95, 12)]["level"] >= 1.8 * rows[(0.95, 1)]["level"]                         # mit Persistenz zählt der Rhythmus
    for phi in C.SWEEP_PHI:
        assert rows[(phi, 1)]["quantity"] == pytest.approx(rows[(phi, 1)]["level"], rel=1e-6)


def test_lead_time_raises_the_value_of_re_forecasting_and_leaves_a_seer_gap(grid):
    assert grid[(2, 0.8)].update.mean > grid[(0, 0.8)].update.mean
    assert grid[(0, 0.8)].seer.mean == pytest.approx(0.0, abs=1e-6)
    assert grid[(2, 0.8)].seer.mean >= 100.0


def test_verdicts_match_the_measured_shares(grid):
    assert grid[(0, 0.0)].verdict == "nur_rueckkopplung"
    assert grid[(0, 0.5)].verdict == "etwas"
    assert grid[(0, 0.8)].verdict == "deutlich"
    assert grid[(0, 0.95)].verdict == "deutlich"
