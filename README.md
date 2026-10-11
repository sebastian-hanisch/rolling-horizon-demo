# Rollierend planen: Rückkopplung oder Neuprognose? – Streamlit-Demo

Sechstes und letztes Stück der **Optimierung-unter-Unsicherheit-Linie** der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“.
Anders als die Fall-Demos (ein Anwendungsfall, mehrere Verfahren im Vergleich) zeigt sie **ein** Verfahren, die **rollierende Planung**, an einem wachsenden Beispiel.
**Kante in der Linie:** Die Wurzel [newsvendor-evpi-demo](https://github.com/sebastian-hanisch/newsvendor-evpi-demo) kennt eine Entscheidung vor der Nachfrage. Hier wiederholt sie sich über
12 Perioden, und zwischen den Entscheidungen wird beobachtet. Das Vehikel ist das der Linie in der Zeit: ein Artikel mit Bestandskosten 1 und Rückstandskosten 3 je Einheit (wie Vorhaltung
und Fehlmenge im Kapazitäts-Vehikel), lognormaler Nachfrage mit **Persistenz φ**, Lieferzeit 0 bis 2.

## Warum dieses Problem

„Starr gegen reaktiv“ ist in den Fall-Demos der Portfolios ein wiederkehrendes Muster: Wer neu plant, schlägt den starren Plan. Offen bleibt, **woher der Gewinn kommt**. Die Demo zerlegt ihn in
**Rückkopplung** (die Bestellung berücksichtigt den beobachteten Bestand) und **Neuprognose** (die Nachfrage der nächsten Perioden wird mit der letzten Beobachtung neu geschätzt) und fragt,
**wie oft** man neu planen muss.

## Modell

Ein Artikel, T = 12 Perioden, Nachfrage D_t = μ · exp(z_t − σ²/2) mit AR(1)-Prozess z_t = φ z_{t−1} + Innovation (Randverteilung je Periode lognormal mit Mittel μ = 100 für jedes φ, σ = 0,35).
Bestellung q_t in Periode t trifft L Perioden später ein, Rückstand wird nachgeliefert, Kosten 1 · Bestand + 3 · Rückstand je Periode; Bestellkosten sind ein Durchlaufposten. Formeln im 📐-Expander.

## Methodik

Alle Politiken sehen dieselben 1 000 Nachfragepfade und dieselben bedingten Zufallszahlen (gepaart); bestellt wird aus dem **bedingten Quantil** zum kritischen Verhältnis 3 : 4 (Stichprobe von 300 Fortsetzungen).

- **Offen:** alle Mengen zu Beginn geplant, nie angepasst.
- **Mengen alle r Perioden:** alle r Perioden neu geplant, dazwischen laufen die Mengen unverändert (klassischer rollierender Plan).
- **Niveaus alle r Perioden:** die Bestellziele werden alle r Perioden neu berechnet; je Periode wird Ziel minus Bestandsposition bestellt (Rückkopplung bleibt).
- **Statisch:** ein festes Niveau aus der unbedingten Verteilung.
- **Hellseher:** kennt den Pfad (untere Schranke).
- **Zerlegung:** Offen → Niveaus einmal gesetzt = Rückkopplung; Niveaus einmal → Niveaus jede Periode = Neuprognose.

## Befunde (gemessen, keine Behauptungen)

Voreinstellung (φ = 0,8, Lieferzeit 0, r = 3, Seed 1; Kosten über 12 Perioden, Mittel über 1 000 Pfade; ± ist der Standardfehler der gepaarten Differenz); jede Aussage in `tests/test_claims.py` als Band belegt.

| Frage | Befund |
|---|---|
| **Was kostet welche Politik?** | Offen 2 484; Mengen alle 3: 815; Niveaus alle 3: 444; Niveaus einmal: 556; Niveaus jede Periode: 349; statisch: 609; Hellseher 0. |
| **Woher kommt der Gewinn?** | Rückkopplung holt 1 929 (78 % der offenen Kosten). Die Neuprognose holt danach 206 ± 8, das sind 37 % der Kosten mit Rückkopplung. |
| **Ohne Persistenz?** | φ = 0: Die Neuprognose bringt nichts (0 ± 1), eine statische Politik ist genauso gut wie die beste (je 595). Es bleibt allein die Rückkopplung: 58 % der offenen Kosten. |
| **Wächst der Wert der Neuprognose mit φ?** | Relativ zu den Kosten mit Rückkopplung: 0 % (φ = 0), 14 % (0,5), 37 % (0,8), 55 % (0,95). Die statische Politik kostet in jedem Fall 595 bis 609, von φ unabhängig: Die Persistenz ist ihr Wert. |
| **Wie oft neu planen?** | Mit Rückkopplung und φ = 0: egal (595 bei jedem r). Bei φ = 0,8 steigen die Kosten von 349 (jede Periode) auf 556 (einmal), bei φ = 0,95 von 178 auf 393. |
| **Was kosten eingefrorene Mengen?** | Auch ohne Persistenz viel: bei φ = 0 kostet r = 6 mit Mengen 1 105 gegen 596 mit Niveaus. Sie verlieren die Beobachtung des **Bestands**, nicht die der Nachfrage. |
| **Lieferzeit?** | Bei 2 Perioden und φ = 0,8: Neuprognose 323 ± 18 (23 % der Kosten mit Rückkopplung, mehr als bei Lieferzeit 0 in absoluten Zahlen). Der Hellseher kostet 166, weil er die ersten zwei Eingänge nicht ändern kann (feste Anfangspipeline). |

## Ehrliche Grenzen

- **Ein Artikel, keine Bestellgrenzen.** Mit Grenzen, Mindestlosgrößen oder mehreren Artikeln ist die Quantilregel nicht mehr optimal; dann ist ein Optimierungsmodell je Planung sinnvoll. Der Planungshorizont wurde vorab mit
  einem Szenario-LP gemessen und brachte im Grundmodell keinen Unterschied; die Demo bildet ihn nicht ab.
- **Prozessparameter bekannt.** φ, σ und μ sind gegeben; die Schätzung aus Daten kommt in der Praxis hinzu.
- **Quantil, nicht Risikomaß.** Die Niveaus zielen auf den Erwartungswert (kritisches Verhältnis).
- **Neuplanen kostet hier nichts.** Aufwand und Nervosität in der Kette zählen nicht.
- **Gleiche Familie von Pfaden.** Eine Instanz (Seed), 1 000 Pfade; gepaarte Differenzen sind genau, absolute Kosten tragen 1 bis 3 % Standardfehler.

## Verifikation

- **Kern:** Pfade deterministisch, lognormal mit Mittel μ, Autokorrelation gleich φ (Messung an 20 000 Pfaden), bedingte Stichproben ohne Rauschen gleich dem Erwartungswertpfad, statische Politik an einem Mini-Pfad von Hand
  (80 Kosten), Hellseher kostet bei Lieferzeit 0 nichts und bei konstanter Nachfrage auch mit Lieferzeit nichts, Blocklänge 1 macht Mengen- und Niveau-Politik identisch, Niveau wächst mit der Beobachtung.
- **Orakel (`tests/test_oracle_rolling_horizon.py`):** bei φ = 0 und Lieferzeit 0 zerfällt die Aufgabe in T Newsvendor-Probleme (Kosten T · G(y*) in geschlossener Form, lognormal); der Hellseher gegen ein
  eigenes LP je Pfad (Lieferzeit 0, 1, 2, 1e-6); das bedingte Quantil gegen eine Stichprobe von 400 000 aus eigener Zufallszahlenquelle; die Niveau-Politik gegen eine dynamische Programmierung
  über (Beobachtung, Bestand) für Lieferzeit 0 und φ = 0 und 0,8 (höchstens 2 %).
- **Claims (`tests/test_claims.py`):** Rückkopplung, Neuprognose über φ, statische Politik, Rhythmus, eingefrorene Mengen, Lieferzeit, Verdikte.
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jede Radio-Option), Footer.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `app.py` | Streamlit-App |
| `rol_rng.py` | SplitMix64, Standardnormale per Inversion |
| `rol_algorithm.py` | Pfade, bedingte Stichproben, Niveau, Block-Mengen, Bestandssimulation, Hellseher |
| `rol_evaluation.py` | Politiken auf gepaarten Pfaden, Zerlegung, Rhythmus-Sweep, Verdikt |
| `rol_constants.py` | Modellparameter, Regler-Optionen, Farben, Presets |
| `rol_presets.py` | Permalink (Begrenzen, Einrasten), Presets, Zufalls-Seed-Button |
| `rol_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tools/measure_stueck6.py` | Messreihe für README und Claims |
| `tests/` | Mini-Pfad, Orakel, Claims, Presets, AppTest-Smoke-Test, Footer |

## Bewusst nicht umgesetzt

- **Planungshorizont als Regler:** im Grundmodell ohne Wirkung, mit Bestellgrenze und bekannter Saison gering; wäre ein Szenario-LP je Planung und kein klares Bild.
- **Bestellgrenzen und Mehr-Artikel-Planung:** eigenes Optimierungsproblem je Planung, nicht die Frage dieses Stücks.
- **Kosten der Neuplanung:** hier nicht modelliert.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und SciPy.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Unsicherheit: von EVPI bis rollierend](https://sebastianhanisch.net/konzepte-optimierung-unsicherheit.html).
