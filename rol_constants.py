"""Konstanten: Modell (ein Artikel über 12 Perioden), Regler-Grenzen, Experiment, Farben und Presets."""

# --- Modell: ein Artikel, AR(1) im Log, Rückstand wird nachgeliefert ------------------------------------------------------------------------
T = 12                          # Perioden
MU = 100.0                      # mittlere Nachfrage je Periode (für jedes phi, die Randverteilung ist lognormal)
SIGMA = 0.35                    # Log-Streuung je Periode
HOLD = 1.0                      # Bestandskosten je Einheit und Periode (wie die Vorhaltung im Vehikel der Linie)
SHORT = 3.0                     # Rückstandskosten je Einheit und Periode (wie die Fehlmenge im Vehikel: 1 : 3)
PATHS = 1000                    # Nachfragepfade je Messung (gepaart: alle Verfahren sehen dieselben)
SAMPLES = 300                   # bedingte Stichproben je Planung
PATH_SEED = 4242
SAMPLE_SEED = 777

# --- Regler --------------------------------------------------------------------------------------------------------------------------------
PHI_CHOICES = (0.0, 0.5, 0.8, 0.95)
DEFAULT_PHI = 0.8
LEAD_CHOICES = (0, 1, 2)
DEFAULT_LEAD = 0
R_CHOICES = (1, 2, 3, 6, 12)
DEFAULT_R = 3
SEED_MAX, DEFAULT_SEED = 999999, 1

# --- Experiment ----------------------------------------------------------------------------------------------------------------------------
SWEEP_PHI = PHI_CHOICES
SWEEP_R = R_CHOICES

# --- Farben --------------------------------------------------------------------------------------------------------------------------------
COLOR_OPEN = "#B5651D"
COLOR_QUANTITY = "#8c6bb1"
COLOR_LEVEL = "#2F6B65"
COLOR_STATIC = "#4c78a8"
COLOR_SEER = "rgba(120,120,120,0.9)"
COLOR_GRID = "rgba(150,150,150,0.75)"

PRESETS = {
    "Standardfall (Voreinstellung)": {"phi": DEFAULT_PHI, "lead": DEFAULT_LEAD, "r": DEFAULT_R, "seed": DEFAULT_SEED},
    "Keine Persistenz (φ = 0)": {"phi": 0.0, "lead": 0, "r": DEFAULT_R, "seed": DEFAULT_SEED},
    "Sehr persistent (φ = 0,95)": {"phi": 0.95, "lead": 0, "r": DEFAULT_R, "seed": DEFAULT_SEED},
    "Lieferzeit 2": {"phi": DEFAULT_PHI, "lead": 2, "r": DEFAULT_R, "seed": DEFAULT_SEED},
}
PRESET_HELP = {
    "Standardfall (Voreinstellung)": "Nachfrage mit Persistenz 0,8, Lieferzeit 0, Neuplanung alle 3 Perioden.",
    "Keine Persistenz (φ = 0)": "Die Nachfrage ist unabhängig von Periode zu Periode: Neuprognose bringt nichts, nur die Rückkopplung auf den Bestand.",
    "Sehr persistent (φ = 0,95)": "Die Nachfrage bleibt lange hoch oder niedrig: Neuprognose bringt viel.",
    "Lieferzeit 2": "Zwei Perioden Lieferzeit: Bestellungen wirken erst später, die Neuprognose muss weiter vorausschauen.",
}
