"""Zweige (Nullspalten-Lehre): Jede Variante und jede Regel läuft auf mindestens einer Instanz wirklich und führt zu einem anderen Ergebnis als die Alternative.

Eine Spalte mit lauter gleichen Werten wäre das Zeichen, dass eine Variante nie anders arbeitet als die andere."""

import random
from dataclasses import replace

import twd_algorithm as A
import twd_constants as C
import twd_evaluation as ev
import twd_scenario as S


def _width(adj, order):
    return A.eliminate(adj, order).width


def test_min_fill_beats_min_degree_on_some_graph_and_loses_on_another():
    adj = S.random_graph_p(12, 25, 131)
    assert _width(adj, A.min_fill_order(adj)) == 3 and _width(adj, A.min_degree_order(adj)) == 4
    adj = S.random_graph_p(16, 25, 44)
    assert _width(adj, A.min_degree_order(adj)) == 5 and _width(adj, A.min_fill_order(adj)) == 6


def test_the_two_heuristics_differ_in_width_on_some_graphs_and_agree_on_others():
    widths = [(_width(adj, A.min_fill_order(adj)), _width(adj, A.min_degree_order(adj))) for adj in (S.random_graph_p(16, 25, s) for s in range(60))]
    assert any(f != d for f, d in widths) and any(f == d for f, d in widths)


def test_the_heuristic_can_be_above_the_exact_value():
    adj = S.random_graph_p(14, 60, 14 * 60)
    tw = A.exact_treewidth(adj)[0]
    assert tw == 8 and min(_width(adj, A.min_fill_order(adj)), _width(adj, A.min_degree_order(adj))) >= tw
    assert max(_width(adj, A.min_fill_order(adj)), _width(adj, A.min_degree_order(adj))) == 9        # mindestens eine Heuristik liegt über dem Wert


def test_a_random_order_is_much_worse_than_min_fill_on_a_grid():
    adj = S.exact_grid(8).adj
    best = _width(adj, A.min_fill_order(adj))
    widths = [_width(adj, A.random_order(64, random.Random(s))) for s in range(5)]
    assert best == 10 and min(widths) > best


def test_mmd_plus_hits_on_complete_graphs_and_misses_on_grids():
    for k in (4, 6, 8):
        g = S.complete_graph(k).adj
        assert A.mmd_plus(g) == A.exact_treewidth(g)[0] == k - 1
    assert A.mmd_plus(S.exact_grid(6).adj) < 6 and A.mmd_plus(S.exact_grid(5).adj) < 5


def test_the_bounds_meet_on_some_graphs_and_stay_apart_on_others():
    k5 = S.complete_graph(5).adj
    assert A.mmd_plus(k5) == _width(k5, A.min_fill_order(k5))
    grid = S.exact_grid(5).adj
    assert A.mmd_plus(grid) < _width(grid, A.min_fill_order(grid))


def test_fill_is_needed_on_cycles_and_not_on_trees():
    assert A.eliminate(S.ring_graph(6).adj, A.min_fill_order(S.ring_graph(6).adj)).fill == 3
    t = S.random_tree(20, 2).adj
    assert A.eliminate(t, A.min_fill_order(t)).fill == 0


def test_every_net_and_order_gives_a_valid_decomposition_and_a_chordal_completion():
    for net in C.NET_TYPES:
        for order in C.ORDERS:
            a = ev.analyse(ev.Settings(net=net, n=24, pct=25, seed=3, order=order))
            assert a.violations == [] and a.completion_chordal and a.omega_completion == a.elim.width + 1, (net, order)


def test_order_functions_and_seeded_random_order():
    assert set(A.ORDER_FUNCS) == set(C.ORDERS)
    a1 = ev.analyse(ev.Settings(order="random", seed=3))
    a2 = ev.analyse(ev.Settings(order="random", seed=3))
    a3 = ev.analyse(ev.Settings(order="random", seed=4))
    assert a1.elim.order == a2.elim.order and a1.elim.order != a3.elim.order
    assert a1.graph.adj == ev.analyse(ev.Settings(order="minfill", seed=3)).graph.adj          # die zufällige Reihenfolge ändert das Netz nicht


def test_analysis_reuses_the_chosen_order_when_it_is_a_heuristic():
    for order in ("minfill", "mindegree"):
        a = ev.analyse(ev.Settings(net="random", n=40, pct=30, order=order))
        assert (a.minfill if order == "minfill" else a.mindeg) is a.elim


def test_main_verdict_branches():
    exact = ev.analyse(ev.Settings())
    assert ev.verdict_main(exact)[0] == "success" and "(exakt, Teilmengen-DP" in ev.verdict_main(exact)[1]
    chordal = ev.analyse(ev.Settings(net="chordal", n=40, pct=20))
    assert "chordal" in ev.verdict_main(chordal)[1] and "exakt" in ev.verdict_main(chordal)[1]
    certified = ev.analyse(ev.Settings(net="tree", n=30, pct=15))
    assert "fallen zusammen" in ev.verdict_main(certified)[1]
    interval = ev.analyse(ev.Settings(net="grid", n=144))
    assert ev.verdict_main(interval)[0] == "info" and "liegt zwischen" in ev.verdict_main(interval)[1]
    worse = ev.analyse(ev.Settings(net="grid", n=100, seed=8, order="random"))
    assert "breiter als Min-Fill" in ev.verdict_main(worse)[1]
    above = replace(exact, minfill=replace(exact.minfill, width=5), mindeg=replace(exact.mindeg, width=6))
    assert "Min-Fill liegt mit 5 um 1 darüber" in ev.verdict_main(above)[1]
    assert ev.best_upper(above) == (5, "Min-Fill") and ev.best_upper(replace(above, minfill=replace(above.minfill, width=7))) == (6, "Min-Grad")
