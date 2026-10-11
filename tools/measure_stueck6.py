"""Messreihe für README und tests/test_claims.py (Python: _venvs/test). Gibt alle Zahlen aus, die im README stehen."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import rol_constants as C  # noqa: E402
import rol_evaluation as ev  # noqa: E402


def main():
    print("== Presets")
    for name, p in C.PRESETS.items():
        a = ev.analyse(ev.Settings(**p))
        tot = a.feedback.mean + a.update.mean
        print(f"{name:<32} offen {a.open.mean:6.0f} Mengen_r {a.quantity.mean:6.0f} Niveaus_r {a.level_r.mean:6.0f} einmal {a.level_once.mean:6.0f} "
              f"jede {a.level_each.mean:6.0f} statisch {a.static.mean:6.0f} Seher {a.seer.mean:5.0f} | Rueck {a.feedback.mean:6.0f} ({100*a.feedback.mean/tot:.0f} %) "
              f"Neuprog {a.update.mean:5.0f} ± {a.update.se:.0f} ({100*a.update.mean/tot:.0f} %) Persistenz {a.persistence.mean:5.0f} -> {a.verdict} rel {100*a.update.mean/a.level_once.mean:.0f} %")
    print("== Alle phi x Lieferzeit (r = 3)")
    for lead in C.LEAD_CHOICES:
        for phi in C.PHI_CHOICES:
            a = ev.analyse(ev.Settings(phi=phi, lead=lead))
            print(f"L={lead} phi={phi}: offen {a.open.mean:5.0f} einmal {a.level_once.mean:5.0f} jede {a.level_each.mean:5.0f} stat {a.static.mean:5.0f} Seher {a.seer.mean:4.0f} "
                  f"Rueck {a.feedback.mean:5.0f} Neuprog {a.update.mean:4.0f} ± {a.update.se:.0f} Pers {a.persistence.mean:5.0f}", flush=True)
    print("== Rhythmus (L = 0)")
    t = time.time()
    rows = ev.rhythm_sweep(ev.Settings())
    print("Dauer", round(time.time() - t), "s")
    for phi in C.SWEEP_PHI:
        sub = [r for r in rows if r["phi"] == phi]
        print(f"phi={phi}: Niveaus " + " ".join(f"r{r['r']}:{r['level']:.0f}" for r in sub) + " | Mengen " + " ".join(f"r{r['r']}:{r['quantity']:.0f}" for r in sub))


if __name__ == "__main__":
    main()
