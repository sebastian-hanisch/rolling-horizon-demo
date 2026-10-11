"""Rollierend planen: Rückkopplung oder Neuprognose? - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import rol_constants as C
from rol_evaluation import Settings, analyse, rhythm_sweep
from rol_presets import (
    apply_preset,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sync_query_params,
)
from rol_visualization import build_decomposition, build_policies, build_rhythm

st.set_page_config(page_title="Rollierend planen – Sebastian Hanisch", layout="wide")


def _de(value: float, digits: int = 0) -> str:
    return f"{value:,.{digits}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _pct(value: float, digits: int = 0) -> str:
    return f"{100.0 * value:.{digits}f} %".replace(".", ",")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _sweep(settings):
    return rhythm_sweep(settings)


st.title("🔁 Rollierend planen: Rückkopplung oder Neuprognose?")
st.markdown(
    """
Wer einmal plant und dann nur noch ausführt, verschenkt viel, das zeigt jeder Vergleich „starr gegen reaktiv“. Diese Demo zerlegt, **woher der Gewinn der Neuplanung kommt**:
aus der **Rückkopplung** auf den Bestand (der Plan merkt, was wirklich verbraucht wurde) oder aus der **Neuprognose** (die Nachfrage der nächsten Perioden wird mit der letzten
Beobachtung neu geschätzt). Und sie fragt: **Wie oft muss man neu planen?**

Anders als die Fall-Demos zeigt sie **ein** Verfahren an einem wachsenden Beispiel: ein Artikel über 12 Perioden, die Nachfrage ist lognormal mit **Persistenz φ** (hoch heißt: gestern hoch,
heute wahrscheinlich auch), Bestandskosten 1 und Rückstandskosten 3 je Einheit, wie Vorhaltung und Fehlmenge im Kapazitäts-Vehikel der Linie.
Weiter unten: der Rhythmus über Persistenz und Blocklänge, **🚧 Wo die Annahmen enden** und **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert die rollierende Planung", expanded=True):
    st.markdown(
        """
Alle Politiken sehen dieselben 1 000 Nachfragepfade und bestellen aus den **bedingten Quantilen** der Nachfrage (kritisches Verhältnis 3 : 4 = 75 %):

1. **Offen:** zu Beginn werden alle Bestellmengen geplant und nie angepasst.
2. **Mengen alle r Perioden:** alle r Perioden wird neu geplant; zwischen den Plänen laufen die **Mengen** unverändert weiter (klassischer rollierender Plan).
3. **Niveaus alle r Perioden:** alle r Perioden werden die **Bestellziele** (Niveaus) neu berechnet; bestellt wird jede Periode Ziel minus Bestand und Bestellung unterwegs (Rückkopplung).
4. **Statisch:** ein festes Niveau aus der unbedingten Verteilung; es nutzt keine Beobachtung.
5. **Hellseher:** kennt den ganzen Pfad (untere Schranke).

Zerlegung: **Offen → Niveaus einmal gesetzt** misst die Rückkopplung, **Niveaus einmal → Niveaus jede Periode** misst die Neuprognose.
        """
    )

if C.PRESETS:
    st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
    cols = st.columns(len(C.PRESETS))
    for col, name in zip(cols, C.PRESETS):
        with col:
            st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}")

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    st.markdown("**Nachfrage**")
    phi = st.radio("Persistenz φ", C.PHI_CHOICES, key="phi_radio", horizontal=True, format_func=lambda v: str(v).replace(".", ","),
                   help="0: jede Periode unabhängig. Nahe 1: eine hohe Nachfrage bleibt lange hoch, die Neuprognose lohnt.")
    lead = st.radio("Lieferzeit", C.LEAD_CHOICES, key="lead_radio", horizontal=True, format_func=lambda v: f"{v} Perioden",
                    help="Wie viele Perioden eine Bestellung unterwegs ist. Bei 0 wirkt sie sofort.")
    st.markdown("**Neuplanung**")
    r = st.radio("Neuplanung alle r Perioden", C.R_CHOICES, key="r_radio", horizontal=True,
                 help="Blocklänge der Politiken „Mengen“ und „Niveaus“. 12 heißt: einmal zu Beginn.")
    st.markdown("**Instanz**")
    seed = st.number_input("Zufalls-Seed der Pfade", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Pfade generieren", width="stretch", on_click=randomize_seed)

sync_query_params({"phi_radio": phi, "lead_radio": int(lead), "r_radio": int(r), "seed_input": int(seed)})
settings = Settings(phi=float(phi), lead=int(lead), r=int(r), seed=int(seed))

# --- Ergebnis ----------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Was kostet welche Politik?")
with st.spinner("Simuliere 1 000 Pfade je Politik …"):
    a = _analysis(settings)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Offen geplant", _de(a.open.mean), delta="Referenz", delta_color="off")
m2.metric("Rückkopplung holt", _de(a.feedback.mean), delta=f"{_pct(a.feedback.mean / a.open.mean)} der offenen Kosten", delta_color="off")
m3.metric("Neuprognose holt danach", _de(a.update.mean), delta=f"{_pct(a.update.mean / a.level_once.mean)} der Kosten mit Rückkopplung", delta_color="off")
m4.metric("Hellseher", _de(a.seer.mean), delta="untere Schranke", delta_color="off")

left, right = st.columns(2)
with left:
    st.plotly_chart(build_policies(a, settings.r), width="stretch", key="policies_chart")
    st.caption("Kosten über 12 Perioden, Mittel über die gepaarten Pfade. Politiken mit „Niveaus“ nutzen Rückkopplung, „Mengen“ nicht.")
with right:
    st.plotly_chart(build_decomposition(a), width="stretch", key="decomposition_chart")
    st.caption("Vom offenen Plan zur Neuplanung jede Periode: erst die Rückkopplung auf den Bestand, dann die Neuprognose.")

# --- Kernfrage ---------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Woher kommt der Gewinn der Neuplanung?")
total = a.feedback.mean + a.update.mean
rel_update = a.update.mean / a.level_once.mean
if a.verdict == "nur_rueckkopplung":
    st.info(
        f"**Es ist die Rückkopplung:** Sie holt {_de(a.feedback.mean)} Kosteneinheiten ({_pct(a.feedback.mean / a.open.mean)} der offenen Kosten). "
        f"Die Neuprognose bringt zusätzlich nur {_de(a.update.mean)} ({_pct(rel_update, 1)} der Kosten mit Rückkopplung): bei φ = {str(settings.phi).replace('.', ',')} lohnt es nicht, die Nachfrage neu zu schätzen."
    )
elif a.verdict == "etwas":
    st.success(
        f"**Rückkopplung zuerst, Neuprognose obendrauf:** Die Rückkopplung holt {_de(a.feedback.mean)} ({_pct(a.feedback.mean / a.open.mean)} der offenen Kosten), "
        f"die Neuprognose danach {_de(a.update.mean)} ({_pct(rel_update)} der Kosten mit Rückkopplung)."
    )
else:
    st.success(
        f"**Auch die Neuprognose lohnt deutlich:** Die Rückkopplung holt {_de(a.feedback.mean)} ({_pct(a.feedback.mean / a.open.mean)} der offenen Kosten), "
        f"die Neuprognose danach noch {_de(a.update.mean)}: {_pct(rel_update)} der Kosten mit Rückkopplung. Eine statische Politik kostet {_de(a.persistence.mean)} mehr als die mit Neuprognose: "
        "das ist der Wert der Persistenz."
    )
st.caption(
    f"Der Hellseher kostet {_de(a.seer.mean)}; die beste Politik liegt bei {_de(a.level_each.mean)}. Die Lücke ist der Preis der Unsicherheit über die Zukunft, "
    "nicht der Planung."
)

st.markdown("---")

# --- Rhythmus -----------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Wie oft muss man neu planen?")
st.caption(
    "Kosten gegen die Blocklänge r, je Persistenz (Linienstärke: gewählte Persistenz). Durchgezogen: **Niveaus** mit Rückkopplung. Gestrichelt: **Mengen**, dazwischen eingefroren. "
    "Lieferzeit und Pfade wie in der Seitenleiste; die Persistenz läuft über den Bereich."
)
with st.spinner("Rechne 40 Simulationen …"):
    rows = _sweep(settings)
st.plotly_chart(build_rhythm(rows, settings.phi), width="stretch", key="rhythm_chart")
def _row(phi, r_, key):
    return next(x[key] for x in rows if x["phi"] == phi and x["r"] == r_)


zero_gap = _row(0.0, C.T, "level") - _row(0.0, 1, "level")
frozen_gap = _row(0.0, 6, "quantity") - _row(0.0, 1, "quantity")
high_gap = _row(0.95, C.T, "level") - _row(0.95, 1, "level")
st.info(
    f"**Ohne Persistenz (φ = 0)** kostet seltenes Neuplanen mit Rückkopplung nichts: Niveaus alle {C.T} Perioden weichen um höchstens {_de(abs(zero_gap))} von „jede Periode neu“ ab. "
    f"**Eingefrorene Mengen** kosten dagegen auch dort {_de(frozen_gap)} mehr bei r = 6: Sie verlieren die Beobachtung des Bestands, nicht die der Nachfrage. "
    f"Bei φ = 0,95 kostet seltenes Neuplanen mit Rückkopplung {_de(high_gap)}."
)

st.markdown("---")

# --- Grenzen -----------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Ein Artikel, eine Entscheidung je Periode** | Mit Bestellgrenzen, Mindestlosgrößen oder mehreren Artikeln ist die Quantilregel nicht mehr optimal; dann lohnt ein Optimierungsmodell je Planung. | – |
| **Die Nachfrageprozess-Parameter sind bekannt** | φ, σ und Mittel sind hier gegeben. In der Praxis werden sie aus Daten geschätzt, und der Schätzfehler kommt zur Unsicherheit hinzu. | [Stichproben-Demo (SAA)](https://github.com/sebastian-hanisch/saa-demo): was eine Stichprobe über die Verteilung sagt |
| **Der Erwartungswert (Quantil) ist das Ziel** | Ein Risikomaß oder eine harte Garantie verlangt andere Niveaus. | [CVaR-Demo](https://github.com/sebastian-hanisch/cvar-demo) und [Szenario-Ansatz](https://github.com/sebastian-hanisch/scenario-approach-demo) |
| **Die Neuplanung ist kostenlos** | Jede Neuplanung hat Aufwand und kann Instabilität in der Kette erzeugen. Hier zählt nur die Bestandskostensumme. | – |
| **Starr gegen reaktiv ist der Vergleich** | Dieselbe Frage („wie viel bringt Neuplanen?“) steht in den Fall-Demos zu Störungen und Kaiplatz; hier wird zerlegt, woher der Gewinn kommt. | [Robuste Kaiplatzplanung](https://github.com/sebastian-hanisch/robuste-kaiplatz-demo), [Hof-Disposition](https://github.com/sebastian-hanisch/hofrobust-demo) |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Nachfrage.** Mit $z_0\sim N(0,\sigma^2)$ und $z_t=\varphi z_{t-1}+\sigma\sqrt{1-\varphi^2}\,\varepsilon_t$ ist

$$D_t=\mu\,\exp\!\big(z_t-\tfrac12\sigma^2\big)$$

lognormal mit Erwartungswert $\mu$ für jedes $\varphi$; $\varphi$ steuert nur die Abhängigkeit von Periode zu Periode.

**Kosten.** Mit Bestand $I_t$ nach der Nachfrage der Periode $t$ (Rückstand negativ):

$$\sum_{t=1}^{T}\big(h\,I_t^{+}+p\,I_t^{-}\big),\qquad I_t=I_{t-1}+q_{t-L}-D_t$$

Bestellkosten sind ein Durchlaufposten. Für Lieferzeit $L=0$ und $\varphi=0$ zerfällt die Aufgabe in $T$ unabhängige Newsvendor-Probleme mit dem kritischen Verhältnis $p/(p+h)$.

**Niveau-Politik.** Zum Planungszeitpunkt $t_0$ mit der Beobachtung $z_{t_0-1}$ ist das Niveau für die Periode $t$ das Quantil

$$y_t(z_{t_0-1})=Q_{p/(p+h)}\!\Big(\sum_{s=t}^{t+L}D_s\;\Big|\;z_{t_0-1}\Big),\qquad q_t=\max\big(0,\;y_t-\text{Bestandsposition}_t\big)$$

mit der Bestandsposition aus Bestand und Bestellungen unterwegs. Die bedingten Quantile werden mit festen Zufallszahlen aus $S=300$ Stichproben der AR(1)-Fortsetzung geschätzt.

**Mengen-Politik.** Die Mengen eines Blocks sind Differenzen kumulierter bedingter Quantile; dazwischen werden sie unverändert bestellt (keine Rückkopplung innerhalb des Blocks).

**Literatur.** Das Newsvendor-Verhältnis und die Niveau-Politik sind Lehrbuchwissen der Bestandsplanung (z. B. Zipkin, *Foundations of Inventory Management*, 2000); die Optimalität der
Quantilregel bei $L=0$ wird hier gegen eine dynamische Programmierung nachgerechnet, nicht zitiert.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Unsicherheit: von EVPI bis rollierend](https://sebastianhanisch.net/konzepte-optimierung-unsicherheit.html)."
)
