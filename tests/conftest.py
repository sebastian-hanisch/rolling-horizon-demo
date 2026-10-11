"""Gemeinsame Fixtures: eine kurze Mini-Reihe (drei Perioden), an der jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import rol_algorithm as A  # noqa: E402


@pytest.fixture
def mini_model():
    """Drei Perioden, Lieferzeit 0, mu 100, Bestandskosten 1, Rückstandskosten 3."""
    return A.Model(lead=0, phi=0.0, horizon=3)


@pytest.fixture
def mini_demand():
    """Ein Pfad: 80, 120, 100 (Handrechnung in test_algorithm)."""
    return np.array([[80.0, 120.0, 100.0]])
