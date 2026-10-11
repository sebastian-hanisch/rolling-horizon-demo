"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen; Permalink begrenzt und rastet ein."""

import pytest

import rol_constants as C
import rol_evaluation as ev
import rol_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_bounds_and_on_the_step_grid():
    for name, preset in C.PRESETS.items():
        for key, state_key in P.PRESET_KEYS.items():
            spec = P.SETTING_SPECS[state_key]
            value = preset[key]
            if spec.choices is not None:
                assert value in spec.choices, (name, key)
            else:
                assert spec.lo <= value <= spec.hi, (name, key)
                assert P.snap(spec, value) == pytest.approx(value), (name, key)


def test_default_preset_equals_the_default_settings():
    assert ev.Settings(**C.PRESETS["Standardfall (Voreinstellung)"]) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_snap_keeps_only_valid_choices():
    assert P.snap(P.SETTING_SPECS["phi_radio"], 0.7) == C.DEFAULT_PHI
    assert P.snap(P.SETTING_SPECS["lead_radio"], 5) == C.DEFAULT_LEAD
    assert P.snap(P.SETTING_SPECS["r_radio"], 4) == C.DEFAULT_R
    assert P.snap(P.SETTING_SPECS["seed_input"], -5) == 0


def test_whole_horizon_is_a_valid_block_length():
    assert C.T in C.R_CHOICES and 1 in C.R_CHOICES
