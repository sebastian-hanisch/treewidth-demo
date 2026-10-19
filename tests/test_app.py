"""End-to-end Smoke-Test via Streamlits offiziellem AppTest-Framework: laedt app.py mit den
Standardeinstellungen, klickt jeden Preset-Button und faehrt jeden Slider an seine Grenzen und prueft, dass
kein Python-Fehler auftritt - insbesondere `streamlit.errors.StreamlitDuplicateElementId` (mehrere
st.plotly_chart-Aufrufe ohne eindeutiges key= koennen zufaellig identischen Inhalt rendern und kollidieren)
und `StreamlitAPIException` bei Slidern mit berechneten Grenzen (min == max)."""

import os

from streamlit.testing.v1 import AppTest

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))  # unter Last (parallele Läufe) reichen 180 s nicht immer; Umgebungsvariable zum Anpassen
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


def test_every_slider_at_its_min_and_max_does_not_raise():
    labels = [s.label for s in _fresh_app().slider]
    assert labels, "keine Slider gefunden"
    for index, label in enumerate(labels):
        for edge in ("min", "max"):
            at = _fresh_app()
            slider = at.slider[index]
            value = slider.min if edge == "min" else slider.max
            if isinstance(slider.value, int):
                value = int(value)
            slider.set_value(value).run(timeout=TIMEOUT)
            assert not at.exception, (label, edge, [str(e) for e in at.exception])


# --- Zusätzlich: die echten Regler dieser Demo (Auswahlfelder, Optionsfelder, Seed, Permalink, Schritt-Regler) --------------------------------------

def _slider(at, label_start):
    """Slider nach Beschriftung."""
    return next(s for s in at.slider if s.label.startswith(label_start))


def _selectbox(at, label):
    return next(s for s in at.selectbox if s.label == label)


def _radio(at, label_start):
    return next(r for r in at.radio if r.label.startswith(label_start))


def _texts(at):
    return [x.value for x in at.success] + [x.value for x in at.info] + [x.value for x in at.warning]


def test_every_net_type_and_order_renders_without_exception():
    for key in ("grid", "tree", "cycle", "random", "chordal", "toronto"):
        at = _fresh_app()
        _selectbox(at, "Netztyp").set_value(key).run(timeout=TIMEOUT)         # roher Schlüssel (select_index kollidiert in AppTest mit format_func)
        assert not at.exception, (key, [str(e) for e in at.exception])
    for key in ("minfill", "mindegree", "random"):
        at = _fresh_app()
        _radio(at, "Ordnungsverfahren").set_value(key).run(timeout=TIMEOUT)
        assert not at.exception, (key, [str(e) for e in at.exception])


def test_extreme_seeds_do_not_raise():
    for seed in (0, 999999):
        at = _fresh_app()
        at.number_input[0].set_value(seed).run(timeout=TIMEOUT)
        assert not at.exception, (seed, [str(e) for e in at.exception])


def test_slowest_corner_dense_large_random_net_still_renders():
    at = _fresh_app()
    _selectbox(at, "Netztyp").set_value("random").run(timeout=TIMEOUT)
    _slider(at, "Knoten").set_value(600).run(timeout=TIMEOUT)
    _slider(at, "Störung").set_value(60).run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]


def test_permalink_parameters_are_applied():
    at = AppTest.from_file(APP_PATH)
    for k, v in (("net", "tree"), ("n", "30"), ("p", "40"), ("seed", "5"), ("o", "mindegree")):
        at.query_params[k] = v
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    assert _slider(at, "Knoten").value == 30 and _slider(at, "Störung").value == 40 and at.number_input[0].value == 5
    assert _selectbox(at, "Netztyp").value == "tree" and _radio(at, "Ordnungsverfahren").value == "mindegree"


def test_the_core_question_verdict_and_the_experiment_verdicts_are_shown():
    at = _fresh_app()
    texts = _texts(at)
    assert any(t.startswith("Die Baumweite ist **4** (exakt") for t in texts)               # Standardfall: Gitter 4×4
    assert any("treffen den bekannten Wert" in t for t in texts) and any("Bis zum 6×6-Gitter" in t for t in texts)
    assert any("Min-Fill trifft den exakten Wert in" in t for t in texts) and any("Beim Zufallsnetz" in t for t in texts)


def test_toronto_preset_shows_an_interval_and_a_valid_decomposition():
    at = _fresh_app()
    at.sidebar.button(key="preset_Toronto: wie breit ist ein echtes Netz?").click().run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    assert any("liegt zwischen" in t for t in _texts(at))
    assert any("Die Zerlegung ist gültig" in s.value for s in at.success)
    assert next(m for m in at.metric if m.label == "Baumweite exakt").value == "–"


def test_chordal_preset_reports_that_nothing_was_added():
    at = _fresh_app()
    at.sidebar.button(key="preset_Chordal: nichts ergänzen").click().run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    assert any(t.startswith("Der Graph ist chordal: Min-Fill ergänzt keine Kante") for t in _texts(at))
    assert next(m for m in at.metric if m.label == "Eigener Graph chordal?").value == "Ja"


def test_the_step_slider_runs_over_all_steps_and_its_state_follows_n():
    at = _fresh_app()
    step = _slider(at, "Schritt der Eliminationsordnung")
    assert step.min == 0 and step.max == 16 and step.value == 1
    for value in (0, 8, 16):
        step.set_value(value).run(timeout=TIMEOUT)
        assert not at.exception, (value, [str(e) for e in at.exception])
        step = _slider(at, "Schritt der Eliminationsordnung")
    _slider(at, "Knoten").set_value(36).run(timeout=TIMEOUT)
    assert _slider(at, "Schritt der Eliminationsordnung").max == 36 and not at.exception


def test_the_bag_tree_is_drawn_up_to_the_limit_and_replaced_by_a_note_beyond():
    at = _fresh_app()
    assert not any("wird bis n = 60 gezeichnet" in i.value for i in at.info)
    _slider(at, "Knoten").set_value(100).run(timeout=TIMEOUT)
    assert any("wird bis n = 60 gezeichnet" in i.value for i in at.info)
