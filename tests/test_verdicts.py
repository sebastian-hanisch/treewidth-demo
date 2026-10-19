"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jede Schwelle der Art steht hier.

Ein Verdikt ist eine reine Funktion (Art, Text) und bekommt Zeilen, nicht Seeds. Damit prüft der Test die Zweige und jede genannte Zahl direkt; ohne diese Datei überleben
fast alle Mutanten der Verdikt-Arithmetik (Schwellen, Vorzeichen, Zähler im Text), weil der Sweep sie nicht trifft."""

from dataclasses import replace

import twd_evaluation as ev

# --- Hauptansicht -------------------------------------------------------------------------------------------------------------------------------


def test_main_verdict_exact_names_value_heuristic_and_lower_bound():
    a = ev.analyse(ev.Settings())                                         # Gitter 4×4: Baumweite 4
    kind, text = ev.verdict_main(a)
    assert kind == "success"
    assert text == "Die Baumweite ist **4** (exakt, Teilmengen-DP über alle 2^16 Teilmengen). Min-Fill trifft den Wert; die untere Schranke MMD+ ist 4."


def test_main_verdict_exact_with_the_heuristic_above_and_a_worse_chosen_order():
    a = ev.analyse(ev.Settings())
    above = replace(a, minfill=replace(a.minfill, width=6), mindeg=replace(a.mindeg, width=7), elim=replace(a.elim, width=9))
    kind, text = ev.verdict_main(above)
    assert kind == "success" and "Min-Fill liegt mit 6 um 2 darüber" in text
    assert text.endswith("Die gewählte Reihenfolge (Min-Fill (wenigste ergänzte Kanten)) ist mit Breite 9 um 3 breiter als Min-Fill.")


def test_main_verdict_chordal_and_certified_and_interval():
    chordal = ev.analyse(ev.Settings(net="chordal", n=40, pct=20))
    assert ev.verdict_main(chordal) == ("success", "Der Graph ist chordal: Min-Fill ergänzt keine Kante, die Baumweite ist **10** (größte Clique minus 1, exakt).")
    tree = ev.analyse(ev.Settings(net="tree", n=30, pct=15))
    assert ev.verdict_main(tree) == ("success", "Die Baumweite ist **2**: obere Schranke (Min-Fill) und untere Schranke (MMD+) fallen zusammen.")
    grid = ev.analyse(ev.Settings(net="grid", n=144))
    kind, text = ev.verdict_main(grid)
    assert kind == "info" and text.startswith("Die Baumweite liegt zwischen **5** (untere Schranke MMD+) und **16** (obere Schranke, Min-Fill); mehr lässt sich hier nicht sagen")
    assert "nur bis n = 16 berechnet." in text


def test_main_verdict_names_min_degree_when_it_is_the_better_heuristic():
    a = ev.analyse(ev.Settings(net="grid", n=144))
    swapped = replace(a, minfill=replace(a.minfill, width=20), mindeg=replace(a.mindeg, width=18))
    assert "obere Schranke, Min-Grad)" in ev.verdict_main(swapped)[1] and "**18**" in ev.verdict_main(swapped)[1]


# --- Experiment 1 -------------------------------------------------------------------------------------------------------------------------------


def _frow(name, known, mindeg, minfill, lower, certified):
    return {"name": name, "n": 10, "known": known, "mindeg": mindeg, "minfill": minfill, "lower": lower, "exact": None, "certified": certified}


def test_verdict_families_counts_hits_certificates_and_the_widest_gap():
    rows = [_frow("A", 2, 2, 2, 2, True), _frow("B", 6, 7, 6, 4, False), _frow("C", 5, 6, 6, 3, False)]
    kind, text = ev.verdict_families(rows)
    assert kind == "info"
    assert text == ("Min-Grad oder Min-Fill treffen den bekannten Wert bei 2 von 3 Familien; ausgenommen C. Die untere Schranke MMD+ beweist ihn bei 1 davon (A); "
                    "bei „B“ liegt sie mit 2 am weitesten unter dem Wert.")


def test_verdict_families_without_misses_has_no_exception_clause():
    rows = [_frow("A", 2, 2, 2, 2, True), _frow("B", 6, 6, 6, 4, False)]
    assert "ausgenommen" not in ev.verdict_families(rows)[1] and "bei 2 von 2 Familien" in ev.verdict_families(rows)[1]


# --- Experiment 2 -------------------------------------------------------------------------------------------------------------------------------


def _grow(k, mindeg, minfill, lower, random):
    return {"k": k, "n": k * k, "mindeg": mindeg, "minfill": minfill, "lower": lower, "random": random}


def test_verdict_grid_names_the_first_overshoot_and_the_last_size():
    rows = [_grow(3, 3, 3, 3, 4), _grow(4, 4, 4, 4, 7), _grow(6, 8, 7, 4, 12)]
    kind, text = ev.verdict_grid(rows)
    assert kind == "info"
    assert text == ("Bis zum 4×4-Gitter treffen Min-Grad und Min-Fill die Baumweite k, ab dem 6×6-Gitter liegen sie darüber (7 statt 6). "
                    "Beim 6×6-Gitter sind es 7 (Min-Fill) und 8 (Min-Grad) statt 6, eine zufällige Reihenfolge braucht im Median 12; die untere Schranke MMD+ bleibt bei 4.")


def test_verdict_grid_threshold_is_strict_and_covers_the_other_two_branches():
    assert ev.verdict_grid([_grow(3, 3, 3, 3, 4), _grow(4, 5, 4, 4, 7)])[1].startswith("Min-Grad und Min-Fill treffen k bei allen Größen.")      # beste Heuristik genau k: kein Überschuss
    assert ev.verdict_grid([_grow(3, 4, 5, 3, 4), _grow(4, 6, 6, 4, 7)])[1].startswith("Die Heuristiken liegen schon beim kleinsten Gitter über k.")


# --- Experiment 3 -------------------------------------------------------------------------------------------------------------------------------


def _srow(p, md, mf, lo, gaps, cert, ordered=True):
    return {"p": p, "tw": 3.0, "mindeg_exact": md, "minfill_exact": mf, "lower_exact": lo, "mindeg_gap": gaps[0], "minfill_gap": gaps[1], "lower_gap": gaps[2], "lower_gap_mean": 0.1,
            "certified": cert, "ordered": ordered, "samples": 100}


def test_verdict_small_sums_over_all_rows_and_names_the_hardest_density():
    rows = [_srow(20, 100, 100, 100, (0, 0, 0), 100), _srow(50, 90, 98, 89, (1, 1, 1), 87)]
    kind, text = ev.verdict_small(rows)
    assert kind == "info"
    assert text == ("Min-Fill trifft den exakten Wert in 198 von 200 Graphen, Min-Grad in 190; am schwersten ist p = 50 % (98 von 100). Die Lücke beträgt nie mehr als 1. "
                    "Die untere Schranke MMD+ trifft in 189 von 200 Graphen, und in 187 fallen untere und obere Schranke zusammen: dort ist der Wert auch ohne den DP bewiesen.")


def test_verdict_small_warns_when_the_bounds_are_violated():
    rows = [_srow(20, 100, 100, 100, (0, 0, 0), 100), _srow(50, 90, 98, 89, (1, 1, 1), 87, ordered=False)]
    kind, text = ev.verdict_small(rows)
    assert kind == "warning" and text.endswith("ACHTUNG: untere ≤ exakt ≤ obere Schranke wurde verletzt.")


def test_verdict_small_gap_is_the_maximum_over_both_heuristics():
    rows = [_srow(20, 100, 100, 100, (2, 0, 0), 100), _srow(50, 90, 98, 89, (1, 1, 1), 87)]
    assert "Die Lücke beträgt nie mehr als 2." in ev.verdict_small(rows)[1]


# --- Experiment 4 -------------------------------------------------------------------------------------------------------------------------------


def test_verdict_growth_names_ratios_and_the_interval():
    rnd = [{"n": 50, "giant": 47, "minfill": 7, "mindeg": 8, "lower": 6, "ratio": 0.14}, {"n": 400, "giant": 377, "minfill": 49, "mindeg": 50, "lower": 14, "ratio": 0.13}]
    tor = [{"n": 200, "m": 245, "minfill": 4, "mindeg": 5, "lower": 4}, {"n": 5072, "m": 7621, "minfill": 50, "mindeg": 57, "lower": 6}]
    kind, text = ev.verdict_growth(rnd, tor)
    assert kind == "info"
    assert text == ("Beim Zufallsnetz mit mittlerem Grad 3 wächst die Breite etwa linear: 0,13 bis 0,14 mal so viel wie die Knotenzahl der Riesenkomponente (n = 50 bis 400). "
                    "Beim Toronto-Ausschnitt wächst die obere Schranke von 4 bei 200 Kreuzungen auf 50 bei 5.072, die untere bleibt bei 6: die Baumweite des ganzen Netzes liegt zwischen 6 und 50, mehr sagt die Demo nicht.")


def test_verdict_growth_uses_the_better_heuristic_for_the_interval():
    rnd = [{"n": 50, "giant": 47, "minfill": 7, "mindeg": 8, "lower": 6, "ratio": 0.14}]
    tor = [{"n": 200, "m": 245, "minfill": 4, "mindeg": 5, "lower": 4}, {"n": 5072, "m": 7621, "minfill": 60, "mindeg": 57, "lower": 6}]
    assert "liegt zwischen 6 und 57" in ev.verdict_growth(rnd, tor)[1]


def test_number_formatting_uses_german_separators():
    assert ev._i(1234567) == "1.234.567" and ev._f(3.14159, 2) == "3,14" and ev._f(2.0, 0) == "2"
