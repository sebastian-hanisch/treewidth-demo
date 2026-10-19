"""Figuren: jede lässt sich bauen, die Zustandsfarben stimmen, alle Achsen sind fest."""

import twd_algorithm as A
import twd_constants as C
import twd_evaluation as ev
import twd_scenario as S
import twd_visualization as V


def _node_trace(fig):
    return next(t for t in fig.data if t.mode in ("markers+text", "markers") and t.hovertext is not None and len(t.x) > 0 and t.x[0] is not None)


def _all_axes_fixed(fig):
    return fig.layout.xaxis.fixedrange and fig.layout.yaxis.fixedrange


def _dashed(fig):
    return [t for t in fig.data if t.mode == "lines" and t.line.dash == "dash" and t.x and t.x[0] is not None]


def test_step_figure_colours_current_bag_waiting_and_done_by_hand():
    g = S.path_graph(4)
    el = A.eliminate(g.adj, (0, 1, 2, 3))
    assert list(_node_trace(V.build_step_figure(g, el, 0)).marker.color) == [C.COLOR_WAIT] * 4
    assert list(_node_trace(V.build_step_figure(g, el, 1)).marker.color) == [C.COLOR_CURRENT, C.COLOR_BAG, C.COLOR_WAIT, C.COLOR_WAIT]
    assert list(_node_trace(V.build_step_figure(g, el, 2)).marker.color) == [C.COLOR_DONE, C.COLOR_CURRENT, C.COLOR_BAG, C.COLOR_WAIT]
    assert list(_node_trace(V.build_step_figure(g, el, 4)).marker.color) == [C.COLOR_DONE, C.COLOR_DONE, C.COLOR_DONE, C.COLOR_CURRENT]


def test_step_figure_clamps_the_step_and_marks_added_chords():
    g = S.ring_graph(4)
    el = A.eliminate(g.adj, (0, 1, 2, 3))
    assert list(_node_trace(V.build_step_figure(g, el, 99)).marker.color) == list(_node_trace(V.build_step_figure(g, el, 4)).marker.color)
    assert list(_node_trace(V.build_step_figure(g, el, -3)).marker.color) == [C.COLOR_WAIT] * 4
    now = V.build_step_figure(g, el, 1)
    assert len(_dashed(now)) == 1 and list(_dashed(now)[0].x[:2]) == [g.positions[1][0], g.positions[3][0]]      # die Sehne 1-3 entsteht beim ersten Schritt
    later = V.build_step_figure(g, el, 2)
    assert not _dashed(later) and any(t.mode == "lines" and t.line.dash == "dot" for t in later.data)           # später nur noch blass gepunktet
    assert _all_axes_fixed(now) and _all_axes_fixed(later)


def test_step_figure_for_big_graphs_has_no_labels_and_smaller_markers():
    g = S.grid_graph(196, 0, 0)
    el = A.eliminate(g.adj, A.min_fill_order(g.adj))
    fig = V.build_step_figure(g, el, 5)
    t = _node_trace(fig)
    assert t.mode == "markers" and t.marker.size == 8
    small = _node_trace(V.build_step_figure(S.grid_graph(16, 0, 0), A.eliminate(S.grid_graph(16, 0, 0).adj, (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15)), 3))
    assert small.mode == "markers+text" and small.marker.size == 22


def test_width_figure_marks_the_maximum_and_the_current_step():
    el = A.eliminate(S.ring_graph(4).adj, (0, 1, 2, 3))                    # Beutelgrößen 3, 3, 2, 1: Breite 2 beim ersten Schritt
    fig = V.build_width_figure(el, 2)
    peak = next(t for t in fig.data if t.marker.symbol == "diamond")
    assert list(peak.x) == [1] and list(peak.y) == [2] and _all_axes_fixed(fig)
    assert list(fig.data[0].y) == [2, 2, 1, 0]
    assert any(s.x0 == 2 for s in fig.layout.shapes if s.type == "line")        # senkrechte Linie beim aktuellen Schritt
    assert V.build_width_figure(A.eliminate(S.adjacency_from_edges(0, []), ()), None).data[0].y == ()


def test_tree_layout_by_hand():
    path = A.tree_decomposition(S.path_graph(4).adj, (0, 1, 2, 3))
    pos, depth, parent = V.tree_layout(path, 3)
    assert pos[3] == (0, 0) and pos[0] == (0, -3) and depth == {3: 0, 2: 1, 1: 2, 0: 3} and parent[0] == 1
    star = A.tree_decomposition(S.star_graph(3).adj, (1, 2, 3, 0))
    pos, depth, _ = V.tree_layout(star, 0)
    assert pos[0] == (1.0, 0) and sorted(pos[i] for i in (1, 2, 3)) == [(0, -1), (1, -1), (2, -1)]


def test_bag_tree_figure_builds_for_small_and_larger_trees():
    for n in (6, 30, 60):
        a = ev.analyse(ev.Settings(net="tree", n=n, pct=20))
        fig = V.build_bag_tree_figure(a.dec, a.elim.order[-1])
        t = next(t for t in fig.data if t.marker is not None and t.marker.color is not None)
        assert len(t.x) == n and _all_axes_fixed(fig) and (t.mode == "markers+text") == (n <= 40)


def test_experiment_figures_build_and_lock_their_axes():
    fam = ev.family_rows()[:4]
    grid = ev.grid_rows(sides=(3, 4), orders=2)
    small = ev.small_rows(n=7, ps=(30, 60), samples=4)
    grow = ev.growth_rows(ns=(30, 60), seeds=(1, 2))
    tor = ev.toronto_rows(ns=(50, 100))
    figs = [V.build_family_figure(fam), V.build_grid_figure(grid), V.build_small_figure(small), V.build_growth_figure(grow, "giant", "x"), V.build_growth_figure(tor, "n", "x")]
    assert all(_all_axes_fixed(f) for f in figs)


def test_family_figure_marks_exact_values_only_where_computed():
    rows = ev.family_rows()
    fig = V.build_family_figure(rows)
    exact = next(t for t in fig.data if t.name == "exakt (DP)")
    assert len(exact.x) == sum(1 for r in rows if r["exact"] is not None) and len(exact.x) < len(rows)
