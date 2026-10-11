"""End-to-end Smoke-Test via Streamlits offiziellem AppTest-Framework: laedt app.py mit den
Standardeinstellungen, klickt jeden Preset-Button und stellt jede Radio-Option ein und prueft, dass
kein Python-Fehler auftritt - insbesondere `streamlit.errors.StreamlitDuplicateElementId` (mehrere
st.plotly_chart-Aufrufe ohne eindeutiges key= koennen zufaellig identischen Inhalt rendern und kollidieren)
und `StreamlitAPIException` bei Slidern mit berechneten Grenzen (min == max)."""

import os

from streamlit.testing.v1 import AppTest

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = 180
AUTOPLAY_MARKER = "\u25b6"  # Auto-Play-Buttons (Animation mit sleep) im Smoke-Test auslassen


def _fresh_app() -> AppTest:
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def test_app_loads_without_exception():
    _fresh_app()


def test_every_button_click_does_not_raise():
    labels = [b.label for b in _fresh_app().button]
    assert labels, "keine Buttons gefunden"
    for index, label in enumerate(labels):
        if AUTOPLAY_MARKER in label:
            continue
        at = _fresh_app()
        at.button[index].click().run(timeout=TIMEOUT)
        assert not at.exception, (label, [str(e) for e in at.exception])


def test_every_radio_option_does_not_raise():
    import rol_constants as C

    options = {"phi_radio": C.PHI_CHOICES, "lead_radio": C.LEAD_CHOICES, "r_radio": C.R_CHOICES}
    for key, values in options.items():
        for value in values:
            at = _fresh_app()
            at.radio(key=key).set_value(value).run(timeout=TIMEOUT)
            assert not at.exception, (key, value, [str(e) for e in at.exception])
