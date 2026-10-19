"""Jede Zahl aus README und App wird hier nachgerechnet (DEMO-PLAYBOOK §4: erst messen, dann Text schreiben).
Alle Werte sind ganzzahlig und plattformunabhängig exakt (Breiten, Kanten, Beutel); Anteile sind Verhältnisse ganzer Zahlen."""

import pytest

import twd_algorithm as A
import twd_constants as C
import twd_evaluation as ev
import twd_scenario as S


def _preset(name):
    p = C.PRESETS[name]
    return ev.analyse(ev.Settings(net=p["net"], n=p["n"], pct=p["pct"], seed=p["seed"], order=p["order"]))


def _facts(a):
    return {"n": a.graph.n, "m": a.graph.m, "comps": a.components, "elim": (a.elim.width, a.elim.fill), "minfill": (a.minfill.width, a.minfill.fill), "mindeg": (a.mindeg.width, a.mindeg.fill),
            "lower": a.lower, "exact": a.exact[0] if a.exact else None, "omega_h": a.omega_completion, "bags": len(a.dec.bags), "maxbag": max(len(b) for b in a.dec.bags)}


# --- Standardfall = Lehrbeispiel: Gitter 4×4 ----------------------------------------------------------------------------------------------------------

def test_default_case_numbers():
    a = ev.analyse(ev.Settings())
    assert _facts(a) == {"n": 16, "m": 24, "comps": 1, "elim": (4, 18), "minfill": (4, 18), "mindeg": (4, 18), "lower": 4, "exact": 4, "omega_h": 5, "bags": 16, "maxbag": 5}
    assert a.violations == [] and a.completion_chordal and not a.chordal and a.bandwidth is None


# --- Presets -------------------------------------------------------------------------------------------------------------------------------------

def test_preset_grid_gap():
    assert _facts(_preset("Gitter: die Lücke wächst")) == {"n": 144, "m": 264, "comps": 1, "elim": (16, 604), "minfill": (16, 604), "mindeg": (16, 618), "lower": 5, "exact": None,
                                                           "omega_h": 17, "bags": 144, "maxbag": 17}


def test_preset_tree_with_extras():
    assert _facts(_preset("Baum: fast baumartig")) == {"n": 30, "m": 33, "comps": 1, "elim": (2, 7), "minfill": (2, 7), "mindeg": (2, 7), "lower": 2, "exact": None, "omega_h": 3, "bags": 30, "maxbag": 3}


def test_preset_thin_random_net():
    assert _facts(_preset("Dünner Zufall: lineare Breite")) == {"n": 400, "m": 622, "comps": 14, "elim": (55, 2575), "minfill": (55, 2575), "mindeg": (56, 2593), "lower": 14, "exact": None,
                                                                 "omega_h": 56, "bags": 400, "maxbag": 56}


def test_preset_toronto():
    assert _facts(_preset("Toronto: wie breit ist ein echtes Netz?")) == {"n": 600, "m": 779, "comps": 4, "elim": (11, 769), "minfill": (11, 769), "mindeg": (11, 814), "lower": 5, "exact": None,
                                                                          "omega_h": 12, "bags": 600, "maxbag": 12}


def test_preset_chordal_needs_no_fill_with_min_fill_but_min_degree_adds_four():
    a = _preset("Chordal: nichts ergänzen")
    assert _facts(a) == {"n": 40, "m": 254, "comps": 1, "elim": (10, 0), "minfill": (10, 0), "mindeg": (10, 4), "lower": 10, "exact": None, "omega_h": 11, "bags": 40, "maxbag": 11}
    assert a.chordal


def test_preset_random_order():
    assert _facts(_preset("Zufällige Reihenfolge: viel breiter")) == {"n": 100, "m": 180, "comps": 1, "elim": (34, 1094), "minfill": (13, 355), "mindeg": (13, 376), "lower": 5, "exact": None,
                                                                      "omega_h": 35, "bags": 100, "maxbag": 35}


# --- Experiment 1: Familien -------------------------------------------------------------------------------------------------------------------------

def test_experiment_1_rows():
    rows = ev.family_rows()
    got = [(r["name"], r["n"], r["known"], r["mindeg"], r["minfill"], r["lower"], r["exact"], r["certified"]) for r in rows]
    assert got == [
        ("Baum (20 Knoten)", 20, 1, 1, 1, 1, None, True), ("Kreis C12", 12, 2, 2, 2, 2, 2, True), ("Gitter 3×3", 9, 3, 3, 3, 3, 3, True), ("Gitter 4×4", 16, 4, 4, 4, 4, 4, True),
        ("Gitter 5×5", 25, 5, 5, 5, 4, None, False), ("Gitter 6×6", 36, 6, 6, 6, 4, None, False), ("vollständiger Graph K8", 8, 7, 7, 7, 7, 7, True),
        ("K_{3,5}", 8, 3, 3, 3, 3, 3, True), ("Petersen-Graph", 10, 4, 4, 4, 4, 4, True), ("Hyperwürfel Q4", 16, 6, 6, 6, 6, 6, True)]
    _, text = ev.verdict_families(rows)
    assert text.startswith("Min-Grad oder Min-Fill treffen den bekannten Wert bei 10 von 10 Familien.") and "beweist ihn bei 8 davon" in text and "bei „Gitter 6×6“ liegt sie mit 2" in text


# --- Experiment 2: Gitter ---------------------------------------------------------------------------------------------------------------------------

def test_experiment_2_rows():
    rows = ev.grid_rows()
    assert [(r["k"], r["mindeg"], r["minfill"], r["lower"], r["random"]) for r in rows] == [
        (3, 3, 3, 3, 4), (4, 4, 4, 4, 7), (5, 5, 5, 4, 7), (6, 6, 6, 4, 12), (7, 8, 8, 4, 15), (8, 10, 10, 5, 22), (10, 13, 13, 5, 31), (12, 16, 16, 5, 43), (14, 20, 19, 5, 62)]
    _, text = ev.verdict_grid(rows)
    assert text.startswith("Bis zum 6×6-Gitter treffen Min-Grad und Min-Fill die Baumweite k, ab dem 7×7-Gitter liegen sie darüber (8 statt 7).")
    assert "Beim 14×14-Gitter sind es 19 (Min-Fill) und 20 (Min-Grad) statt 14, eine zufällige Reihenfolge braucht im Median 62; die untere Schranke MMD+ bleibt bei 5." in text


# --- Experiment 3: kleine Zufallsgraphen ------------------------------------------------------------------------------------------------------------

def test_experiment_3_rows():
    rows = ev.small_rows()
    assert [(r["p"], r["tw"], r["mindeg_exact"], r["minfill_exact"], r["lower_exact"], r["certified"], r["mindeg_gap"], r["minfill_gap"], r["lower_gap"]) for r in rows] == [
        (20, 2.0, 100, 100, 100, 100, 0, 0, 0), (30, 3.0, 100, 100, 100, 100, 0, 0, 0), (50, 5.0, 90, 98, 89, 87, 1, 1, 1), (70, 7.0, 94, 99, 73, 72, 1, 1, 1)]
    assert all(r["ordered"] for r in rows)
    _, text = ev.verdict_small(rows)
    assert text.startswith("Min-Fill trifft den exakten Wert in 397 von 400 Graphen, Min-Grad in 384; am schwersten ist p = 50 % (98 von 100). Die Lücke beträgt nie mehr als 1.")
    assert "MMD+ trifft in 362 von 400 Graphen, und in 359 fallen" in text


# --- Experiment 4: Wachstum -----------------------------------------------------------------------------------------------------------------------

def test_experiment_4_random_rows():
    rows = ev.growth_rows()
    assert [(r["n"], r["giant"], r["minfill"], r["mindeg"], r["lower"]) for r in rows] == [(50, 47, 7, 8, 6), (100, 94, 13, 13, 7), (200, 194, 26, 27, 11), (400, 377, 49, 50, 14)]
    assert [round(r["ratio"], 2) for r in rows] == [0.14, 0.14, 0.14, 0.13]


def test_experiment_4_toronto_rows():
    rows = ev.toronto_rows()
    assert [(r["n"], r["m"], r["minfill"], r["mindeg"], r["lower"]) for r in rows] == [
        (200, 245, 4, 5, 4), (400, 506, 6, 7, 4), (800, 1065, 15, 15, 5), (1600, 2220, 21, 27, 5), (3200, 4650, 38, 44, 6), (5072, 7621, 50, 57, 6)]
    _, text = ev.verdict_growth(ev.growth_rows(), rows)
    assert "0,13 bis 0,14 mal so viel" in text and "von 4 bei 200 Kreuzungen auf 50 bei 5.072, die untere bleibt bei 6" in text and "zwischen 6 und 50" in text


def test_toronto_decomposition_of_the_whole_extract_is_valid():
    g = S.toronto_graph(5072, 0, 0)
    order = A.min_fill_order(g.adj)
    dec = A.tree_decomposition(g.adj, order)
    assert dec.width == 50 and len(dec.bags) == 5072 and A.validate_decomposition(g.adj, dec.bags, dec.edges) == []


# --- Brücken ----------------------------------------------------------------------------------------------------------------------------------------

def test_bridge_omega_of_the_completion_is_width_plus_one_on_every_preset():
    for name in C.PRESETS:
        a = _preset(name)
        assert a.completion_chordal and a.omega_completion == a.elim.width + 1, name


def test_the_exact_treewidth_of_the_4x4_grid_needs_the_whole_subset_dp():
    tw, order = A.exact_treewidth(S.exact_grid(4).adj)
    assert tw == 4 and A.eliminate(S.exact_grid(4).adj, order).width == 4 and pytest.approx(1.0) == 1.0
