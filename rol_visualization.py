"""Plotly-Figuren: Kosten der Politiken, Zerlegung, Rhythmus. Alle Achsen fest (fixedrange)."""

import plotly.graph_objects as go

import rol_constants as C


def _fixed(fig, height=340):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=-0.26))
    return fig


def build_policies(a, r) -> go.Figure:
    """Kosten je Politik (gesamt über 12 Perioden), Balken mit Standardfehler."""
    items = [
        ("Offen: Mengen einmal geplant", a.open, C.COLOR_OPEN),
        (f"Mengen, alle {r} Perioden neu", a.quantity, C.COLOR_QUANTITY),
        ("Niveaus einmal gesetzt", a.level_once, C.COLOR_LEVEL),
        (f"Niveaus, alle {r} Perioden neu", a.level_r, C.COLOR_LEVEL),
        ("Niveaus, jede Periode neu", a.level_each, C.COLOR_LEVEL),
        ("Statisch: ein festes Niveau", a.static, C.COLOR_STATIC),
        ("Hellseher (kennt den Pfad)", a.seer, C.COLOR_SEER),
    ]
    fig = go.Figure(go.Bar(
        y=[i[0] for i in items], x=[i[1].mean for i in items], orientation="h", marker_color=[i[2] for i in items],
        error_x=dict(type="data", array=[1.96 * i[1].se for i in items], thickness=1, width=3),
        text=[f"{i[1].mean:,.0f}".replace(",", ".") for i in items], textposition="outside", showlegend=False,
    ))
    fig.update_xaxes(title="Kosten über 12 Perioden (Mittel, Balken: 95 %-Intervall des Mittels)")
    fig.update_yaxes(autorange="reversed")
    return _fixed(fig, 360)


def build_decomposition(a) -> go.Figure:
    """Von den Kosten der offenen Planung zu den Kosten mit Neuplanung: erst Rückkopplung, dann Neuprognose."""
    names = ["Offen", "Rückkopplung auf den Bestand", "Neuprognose", "Niveaus, jede Periode neu"]
    start = a.open.mean
    fb, up = a.feedback.mean, a.update.mean
    fig = go.Figure(go.Waterfall(
        x=names, y=[start, -fb, -up, 0], measure=["absolute", "relative", "relative", "total"],
        text=[f"{start:,.0f}", f"−{fb:,.0f}", f"−{up:,.0f}", f"{start - fb - up:,.0f}"], textposition="outside",
        decreasing=dict(marker_color=C.COLOR_LEVEL), totals=dict(marker_color=C.COLOR_LEVEL), increasing=dict(marker_color=C.COLOR_OPEN),
        connector=dict(line=dict(color=C.COLOR_GRID)),
    ))
    fig.update_yaxes(title="Kosten über 12 Perioden")
    return _fixed(fig, 340)


def build_rhythm(rows, selected_phi) -> go.Figure:
    """Kosten gegen die Blocklänge r je Persistenz; durchgezogen: Niveaus mit Rückkopplung, gestrichelt: eingefrorene Mengen."""
    palette = {0.0: "#4c78a8", 0.5: "#8c6bb1", 0.8: "#2F6B65", 0.95: "#B5651D"}
    fig = go.Figure()
    for phi in C.SWEEP_PHI:
        sub = [r for r in rows if r["phi"] == phi]
        w = 4 if phi == selected_phi else 2
        label = f"φ = {str(phi).replace('.', ',')}"
        fig.add_trace(go.Scatter(x=[r["r"] for r in sub], y=[r["level"] for r in sub], mode="lines+markers", name=f"{label}, Niveaus",
                                 line=dict(color=palette[phi], width=w)))
        fig.add_trace(go.Scatter(x=[r["r"] for r in sub], y=[r["quantity"] for r in sub], mode="lines+markers", name=f"{label}, Mengen",
                                 line=dict(color=palette[phi], width=w, dash="dash"), marker=dict(symbol="x"), showlegend=False))
    fig.update_xaxes(title="Neuplanung alle r Perioden", tickvals=list(C.SWEEP_R))
    fig.update_yaxes(title="Kosten über 12 Perioden", type="log")
    return _fixed(fig, 380)
