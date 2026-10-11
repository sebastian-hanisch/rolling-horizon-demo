"""Kern: Bestandsplanung über T Perioden mit AR(1)-Nachfrage, Lieferzeit L und Rückstand; Politiken mit und ohne Neuplanung.

Ablauf je Periode t (Index 1..T): Wareneingang (Bestellung aus t - L), Bestellung q_t treffen (kennt die Nachfragen bis t - 1), Nachfrage D_t,
Kosten h * Bestand + p * Rückstand. Bestellkosten sind ein Durchlaufposten (Endbestand wird mit dem Bestellpreis bewertet) und stehen nicht in der Summe.
Anfangsbestand 0, Anfangspipeline mu je Eingang in 1..L. Bestellt wird nur, wenn die Lieferung noch in den Horizont fällt (t + L <= T).

Einheiten (je eine Regel, DEMO-PLAYBOOK §1b):
  simulate_paths        AR(1)-Pfade im Log, Randverteilung je Periode lognormal mit Mittel mu
  conditional_samples   bedingte Nachfragestichproben ab Periode t0 gegeben den letzten Beobachtungswert
  order_up_to_level     Quantil der Nachfrage über Lieferzeit plus Periode, bedingt auf die Beobachtung
  block_quantities      geplante Bestellmengen eines Blocks aus kumulierten bedingten Quantilen
  simulate_policy       Bestandssimulation einer Politik: 'quantity' (Mengen je Block eingefroren), 'level' (Niveaus je Block, Bestellung = Niveau - Position),
                        'static' (ein festes Niveau)
  seer_cost             Hellseher: kennt den ganzen Pfad (untere Schranke)"""

from dataclasses import dataclass

import numpy as np

import rol_constants as C
from rol_rng import normal_block


@dataclass(frozen=True)
class Model:
    lead: int = 0
    phi: float = 0.8
    horizon: int = C.T
    mu: float = C.MU
    sigma: float = C.SIGMA
    hold: float = C.HOLD
    short: float = C.SHORT

    @property
    def critical_ratio(self) -> float:
        return self.short / (self.short + self.hold)

    @property
    def innovation_sd(self) -> float:
        return self.sigma * np.sqrt(1.0 - self.phi ** 2)


def simulate_paths(m: Model, paths: int, seed: int):
    """(z (N, T + 1), D (N, T)): z_0 ~ N(0, sigma^2), z_t = phi z_{t-1} + innovation; D_t = mu exp(z_t - sigma^2 / 2)."""
    e = normal_block(seed, paths * (m.horizon + 1)).reshape(paths, m.horizon + 1)
    z = np.empty((paths, m.horizon + 1))
    z[:, 0] = m.sigma * e[:, 0]
    for t in range(1, m.horizon + 1):
        z[:, t] = m.phi * z[:, t - 1] + m.innovation_sd * e[:, t]
    return z, m.mu * np.exp(z[:, 1:] - 0.5 * m.sigma ** 2)


def conditional_samples(m: Model, z_last: np.ndarray, width: int, eps: np.ndarray) -> np.ndarray:
    """(S, N, width): Nachfragen der nächsten `width` Perioden gegeben z_last (N,); eps (S, >= width) feste Standardnormale."""
    s_count = eps.shape[0]
    zp = np.broadcast_to(z_last[None, :], (s_count, len(z_last)))
    out = np.empty((s_count, len(z_last), width))
    for j in range(width):
        zp = m.phi * zp + m.innovation_sd * eps[:, j][:, None]
        out[:, :, j] = m.mu * np.exp(zp - 0.5 * m.sigma ** 2)
    return out


def order_up_to_level(m: Model, samples: np.ndarray, offset: int) -> np.ndarray:
    """(N,): Quantil (kritisches Verhältnis) der Summe D_{offset} .. D_{offset + L} über die Stichproben."""
    window = samples[:, :, offset:offset + m.lead + 1].sum(axis=2)
    return np.quantile(window, m.critical_ratio, axis=0)


def block_quantities(m: Model, samples: np.ndarray, position: np.ndarray, block: int) -> np.ndarray:
    """(N, block): Bestellmengen des Blocks: erste Bestellung füllt die Position bis zum Quantil der kumulierten Nachfrage auf,
    die weiteren sind Differenzen aufeinanderfolgender kumulierter Quantile (nie negativ)."""
    cum = np.cumsum(samples, axis=2)
    zq = np.quantile(cum, m.critical_ratio, axis=0)          # (N, width)
    q = np.empty((samples.shape[1], block))
    q[:, 0] = np.maximum(0.0, zq[:, m.lead] - position)
    for j in range(1, block):
        q[:, j] = np.maximum(0.0, zq[:, m.lead + j] - zq[:, m.lead + j - 1])
    return q


def static_level(m: Model, eps: np.ndarray, paths: int = 20000, seed: int = C.PATH_SEED + 99) -> float:
    """Ein festes Niveau aus der unbedingten Verteilung der Nachfrage über Lieferzeit plus Periode (stationär, ohne Beobachtung)."""
    z_last = m.sigma * normal_block(seed, paths)
    window = conditional_samples(m, z_last, m.lead + 1, eps[:, : m.lead + 1])
    return float(np.quantile(window.sum(axis=2), m.critical_ratio))


def simulate_policy(m: Model, z: np.ndarray, d: np.ndarray, kind: str, r: int, eps: np.ndarray, level: float | None = None) -> np.ndarray:
    """Gesamtkosten je Pfad (N,). kind 'quantity' | 'level' | 'static'; r: Periodenzahl je Block (Neuplanung alle r Perioden)."""
    n, horizon, lead = d.shape[0], m.horizon, m.lead
    arrivals = np.zeros((n, horizon + lead + 2))
    for k in range(1, lead + 1):
        arrivals[:, k] = m.mu
    inv = np.zeros(n)
    cost = np.zeros(n)
    plan = None
    for t in range(1, horizon + 1):
        inv = inv + arrivals[:, t]
        position = inv + arrivals[:, t + 1:t + lead].sum(axis=1) if lead > 1 else inv.copy()
        q = np.zeros(n)
        if t + lead <= horizon:
            if kind == "static":
                q = np.maximum(0.0, level - position)
            else:
                j = (t - 1) % r
                if j == 0:
                    block = min(r, horizon - lead - t + 1)
                    width = block + lead
                    samples = conditional_samples(m, z[:, t - 1], width, eps)
                    if kind == "level":
                        plan = np.stack([order_up_to_level(m, samples, jj) for jj in range(block)], axis=1)
                    else:
                        plan = block_quantities(m, samples, position, block)
                if kind == "level":
                    q = np.maximum(0.0, plan[:, j] - position)
                else:
                    q = plan[:, j]
        arrivals[:, t + lead] += q
        if lead == 0:
            inv = inv + q
        inv = inv - d[:, t - 1]
        cost += m.hold * np.maximum(inv, 0.0) + m.short * np.maximum(-inv, 0.0)
    return cost


def seer_cost(m: Model, d: np.ndarray) -> np.ndarray:
    """Hellseher (kennt den Pfad): bestellt je Periode genau so viel, dass der Bestand bei Eintreffen die Nachfrage der Ankunftsperiode deckt."""
    n, horizon, lead = d.shape[0], m.horizon, m.lead
    arrivals = np.zeros((n, horizon + lead + 2))
    for k in range(1, lead + 1):
        arrivals[:, k] = m.mu
    inv = np.zeros(n)
    cost = np.zeros(n)
    for t in range(1, horizon + 1):
        inv = inv + arrivals[:, t]
        if t + lead <= horizon:
            if lead > 0:
                projected = inv + arrivals[:, t + 1:t + lead + 1].sum(axis=1) - d[:, t - 1:t - 1 + lead].sum(axis=1)
            else:
                projected = inv
            q = np.maximum(0.0, d[:, t - 1 + lead] - projected)
            arrivals[:, t + lead] += q
            if lead == 0:
                inv = inv + q
        inv = inv - d[:, t - 1]
        cost += m.hold * np.maximum(inv, 0.0) + m.short * np.maximum(-inv, 0.0)
    return cost
