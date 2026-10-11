"""Kennzahlen: Kosten der Politiken auf denselben Pfaden, Zerlegung des Werts der Neuplanung, Rhythmus-Sweep, Verdikt.

Alle Verfahren sehen dieselben Nachfragepfade und dieselben bedingten Zufallszahlen (gepaart); Standardfehler von Differenzen sind gepaarte.
Zerlegung (je Pfad): offen -> Niveaus einmal gesetzt (Rückkopplung auf den Bestand) -> Niveaus jede Periode neu (Neuprognose)."""

from dataclasses import dataclass

import numpy as np

import rol_algorithm as A
import rol_constants as C
from rol_rng import normal_block


@dataclass(frozen=True)
class Settings:
    phi: float = C.DEFAULT_PHI
    lead: int = C.DEFAULT_LEAD
    r: int = C.DEFAULT_R
    seed: int = C.DEFAULT_SEED


@dataclass(frozen=True)
class Cost:
    mean: float
    se: float


@dataclass(frozen=True)
class Analysis:
    settings: Settings
    open: Cost               # Mengen einmal geplant, nie angepasst
    quantity: Cost           # Mengen alle r Perioden neu geplant, dazwischen eingefroren
    level_r: Cost            # Niveaus alle r Perioden neu berechnet, Bestellung = Niveau - Position (Rückkopplung)
    level_once: Cost         # Niveaus einmal berechnet, Rückkopplung bleibt
    level_each: Cost         # Niveaus jede Periode neu
    static: Cost             # ein festes Niveau aus der unbedingten Verteilung
    seer: Cost               # Hellseher
    feedback: Cost           # offen - Niveaus einmal
    update: Cost             # Niveaus einmal - Niveaus jede Periode
    persistence: Cost        # statisch - Niveaus jede Periode: Wert der Persistenz
    verdict: str             # 'nur_rueckkopplung' | 'etwas' | 'deutlich'


def _cost(v: np.ndarray) -> Cost:
    return Cost(float(v.mean()), float(v.std(ddof=1) / np.sqrt(len(v))))


def _eps(seed: int) -> np.ndarray:
    return normal_block(C.SAMPLE_SEED + int(seed), C.SAMPLES * (C.T + 1)).reshape(C.SAMPLES, C.T + 1)


def _paths(m: A.Model, seed: int):
    return A.simulate_paths(m, C.PATHS, C.PATH_SEED + int(seed))


def verdict_of(update: float, level_once: float) -> str:
    """Wie viel bringt die Neuprognose ZUSÄTZLICH zur Rückkopplung, relativ zu den Kosten mit Rückkopplung?"""
    share = update / level_once if level_once > 0 else 0.0
    if share < 0.05:
        return "nur_rueckkopplung"
    return "etwas" if share < 0.25 else "deutlich"


def analyse(settings: Settings) -> Analysis:
    m = A.Model(lead=settings.lead, phi=settings.phi)
    z, d = _paths(m, settings.seed)
    eps = _eps(settings.seed)
    open_ = A.simulate_policy(m, z, d, "quantity", C.T, eps)
    quantity = A.simulate_policy(m, z, d, "quantity", settings.r, eps)
    level_r = A.simulate_policy(m, z, d, "level", settings.r, eps)
    level_once = A.simulate_policy(m, z, d, "level", C.T, eps)
    level_each = A.simulate_policy(m, z, d, "level", 1, eps)
    static = A.simulate_policy(m, z, d, "static", 1, eps, level=A.static_level(m, eps))
    seer = A.seer_cost(m, d)
    fb, up = open_ - level_once, level_once - level_each
    return Analysis(
        settings, _cost(open_), _cost(quantity), _cost(level_r), _cost(level_once), _cost(level_each), _cost(static), _cost(seer),
        _cost(fb), _cost(up), _cost(static - level_each), verdict_of(float(up.mean()), float(level_once.mean())),
    )


def rhythm_sweep(settings: Settings) -> list[dict]:
    """Je Persistenz und Blocklänge r die Kosten der Niveau- und der Mengen-Politik (gleiche Lieferzeit und Pfade wie die Einstellung)."""
    rows = []
    eps = _eps(settings.seed)
    for phi in C.SWEEP_PHI:
        m = A.Model(lead=settings.lead, phi=phi)
        z, d = _paths(m, settings.seed)
        base = A.simulate_policy(m, z, d, "level", 1, eps).mean()
        for r in C.SWEEP_R:
            level = A.simulate_policy(m, z, d, "level", r, eps).mean()
            quantity = A.simulate_policy(m, z, d, "quantity", r, eps).mean()
            rows.append({"phi": phi, "r": r, "level": float(level), "quantity": float(quantity), "base": float(base)})
    return rows
