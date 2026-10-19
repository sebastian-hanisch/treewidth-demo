"""Presets: Vollständigkeit, gültige Werte, erstes Preset = Standardeinstellungen; Permalink-Begrenzung."""

import pytest
from streamlit.testing.v1 import AppTest

import twd_constants as C
import twd_evaluation as ev
import twd_presets as P


def _settings(p):
    return ev.Settings(net=p["net"], n=p["n"], pct=p["pct"], seed=p["seed"], order=p["order"])


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds_and_options():
    for name, p in C.PRESETS.items():
        assert C.N_MIN <= p["n"] <= C.N_MAX and C.PCT_MIN <= p["pct"] <= C.PCT_MAX and 0 <= p["seed"] <= C.SEED_MAX, name
        assert p["net"] in C.NET_TYPES and p["order"] in C.ORDERS, name


def test_first_preset_equals_the_default_settings():
    assert _settings(C.PRESETS[next(iter(C.PRESETS))]) == ev.Settings()


def test_setting_specs_cover_every_preset_key_and_url_params_are_unique():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)
    params = [spec.url_param for spec in P.SETTING_SPECS.values()]
    assert len(params) == len(set(params))


def test_every_preset_shows_what_its_name_promises():
    got = {name: ev.analyse(_settings(p)) for name, p in C.PRESETS.items()}
    lehr = got["Lehrbeispiel (Gitter 4×4)"]
    assert lehr.exact[0] == 4 and lehr.minfill.width == 4 and lehr.lower == 4
    luecke = got["Gitter: die Lücke wächst"]
    assert luecke.exact is None and luecke.minfill.width == 16 > 12 and luecke.lower < 12          # 12×12-Gitter: Baumweite 12
    baum = got["Baum: fast baumartig"]
    assert baum.lower == baum.minfill.width == 2 and baum.minfill.fill > 0
    zufall = got["Dünner Zufall: lineare Breite"]
    assert zufall.graph.n == 400 and zufall.minfill.width > 40 > zufall.lower
    toronto = got["Toronto: wie breit ist ein echtes Netz?"]
    assert toronto.graph.kind == "toronto" and toronto.lower < toronto.minfill.width
    chordal = got["Chordal: nichts ergänzen"]
    assert chordal.chordal and chordal.elim.fill == 0 and chordal.exact is None
    rnd = got["Zufällige Reihenfolge: viel breiter"]
    assert rnd.elim.width > 2 * rnd.minfill.width and rnd.settings.order == "random"


def test_coerce_clamps_numbers_and_rejects_unknown_choices():
    n_spec = P.SETTING_SPECS["n_slider"]
    assert P._coerce(n_spec, "9999") == C.N_MAX and P._coerce(n_spec, "-5") == C.N_MIN and P._coerce(n_spec, "abc") is None
    assert P._coerce(P.SETTING_SPECS["net_select"], "toronto") == "toronto" and P._coerce(P.SETTING_SPECS["net_select"], "zzz") is None
    assert P._coerce(n_spec, ["12"]) == 12


def _probe():
    import streamlit as st

    import twd_presets as P
    P.load_permalink_settings()
    P.init_session_state_defaults()
    st.session_state["seen"] = {k: st.session_state[k] for k in P.SETTING_SPECS}


def test_permalink_is_clamped_to_the_bounds_and_invalid_values_fall_back():
    at = AppTest.from_function(_probe)
    at.query_params["n"] = "9999"
    at.query_params["d"] = "-3"
    at.query_params["net"] = "toronto"
    at.query_params["o"] = "nonsense"
    at.run()
    assert not at.exception
    seen = at.session_state["seen"]
    assert seen["n_slider"] == C.N_MAX and seen["pct_slider"] == C.PCT_MIN
    assert seen["net_select"] == "toronto" and seen["order_radio"] == C.DEFAULT_ORDER


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_apply_preset_writes_every_state_key(name):
    def _apply(preset_name):
        import streamlit as st

        import twd_presets as P
        P.init_session_state_defaults()
        P.apply_preset(preset_name)
        st.session_state["seen"] = {k: st.session_state[k] for k in P.SETTING_SPECS}

    at = AppTest.from_function(_apply, args=(name,))
    at.run()
    assert not at.exception
    p = C.PRESETS[name]
    seen = at.session_state["seen"]
    assert (seen["n_slider"], seen["net_select"], seen["pct_slider"], seen["seed_input"], seen["order_radio"]) == (p["n"], p["net"], p["pct"], p["seed"], p["order"])
