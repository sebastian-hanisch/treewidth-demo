"""Randfälle, an denen Kernroutinen erfahrungsgemäß brechen (DEMO-PLAYBOOK §12): leerer Graph, ein und zwei Knoten, Gleichstände, inklusive Grenzen, Reglergrenzen."""

import pytest

import twd_algorithm as A
import twd_constants as C
import twd_evaluation as ev
import twd_scenario as S

EMPTY = S.adjacency_from_edges(0, [])


def test_empty_graph():
    el = A.eliminate(EMPTY, ())
    assert (el.width, el.fill, el.sizes) == (0, 0, ())
    assert A.mmd_plus(EMPTY) == 0 and A.exact_treewidth(EMPTY) == (0, ()) and A.completion(EMPTY, ()) == ()
    dec = A.tree_decomposition(EMPTY, ())
    assert dec.bags == () and dec.edges == () and A.validate_decomposition(EMPTY, dec.bags, dec.edges) == []
    assert A.min_degree_order(EMPTY) == () and A.min_fill_order(EMPTY) == ()


def test_single_vertex():
    g = S.adjacency_from_edges(1, [])
    assert A.eliminate(g, (0,)).width == 0 and A.mmd_plus(g) == 0 and A.exact_treewidth(g) == (0, (0,))
    dec = A.tree_decomposition(g, (0,))
    assert dec.bags == (frozenset({0}),) and dec.edges == () and A.validate_decomposition(g, dec.bags, dec.edges) == []


def test_exactly_two_vertices_with_and_without_edge():
    """n = 2: der kleinste Fall, in dem es etwas zu eliminieren gibt."""
    edge = S.adjacency_from_edges(2, [(0, 1)])
    assert A.eliminate(edge, (0, 1)).width == 1 and A.exact_treewidth(edge)[0] == 1 and A.mmd_plus(edge) == 1
    none = S.adjacency_from_edges(2, [])
    assert A.eliminate(none, (0, 1)).width == 0 and A.exact_treewidth(none)[0] == 0 and A.mmd_plus(none) == 0
    dec = A.tree_decomposition(none, (0, 1))
    assert dec.edges == ((0, 1),) and A.validate_decomposition(none, dec.bags, dec.edges) == []        # die zwei Wurzeln werden verbunden


def test_ties_are_resolved_by_the_smallest_index():
    edgeless = S.adjacency_from_edges(4, [])
    assert A.min_degree_order(edgeless) == (0, 1, 2, 3) and A.min_fill_order(edgeless) == (0, 1, 2, 3)
    k3 = S.complete_graph(3).adj
    assert A.min_degree_order(k3) == (0, 1, 2) and A.min_fill_order(k3) == (0, 1, 2)


def test_exact_size_limit_is_inclusive():
    g = S.path_graph(5).adj
    assert A.exact_treewidth(g, limit=5)[0] == 1
    with pytest.raises(ValueError):
        A.exact_treewidth(g, limit=4)
    assert A.exact_treewidth(S.exact_grid(4).adj)[0] == 4 and C.EXACT_MAX_N == 16          # 16 Knoten gehen noch, 17 nicht
    with pytest.raises(ValueError):
        A.exact_treewidth(S.path_graph(C.EXACT_MAX_N + 1).adj)


def test_bandwidth_size_limit_is_inclusive():
    assert A.bandwidth_small(S.adjacency_from_edges(C.BANDWIDTH_MAX_N, [])) == 0
    with pytest.raises(ValueError):
        A.bandwidth_small(S.adjacency_from_edges(C.BANDWIDTH_MAX_N + 1, [(0, 1)]))


def test_brute_force_size_limit_is_inclusive():
    assert A.brute_force_treewidth(S.path_graph(4).adj, limit=4) == 1
    with pytest.raises(ValueError):
        A.brute_force_treewidth(S.path_graph(4).adj, limit=3)


def test_slider_bounds_give_valid_analyses_for_every_net():
    for net in C.NET_TYPES:
        for n in (C.N_MIN, C.N_MAX):
            for pct in (C.PCT_MIN,) if n == C.N_MAX else (C.PCT_MIN, C.PCT_MAX):
                a = ev.analyse(ev.Settings(net=net, n=n, pct=pct))
                assert a.graph.n >= 4 and a.violations == [] and a.completion_chordal


def test_the_densest_large_corner_still_analyses():
    a = ev.analyse(ev.Settings(net="cycle", n=C.N_MAX, pct=C.PCT_MAX))
    assert a.violations == [] and a.elim.width >= 2 and a.lower <= a.elim.width


def test_exact_value_exists_exactly_up_to_the_limit():
    assert ev.analyse(ev.Settings(net="grid", n=16)).exact[0] == 4
    assert ev.analyse(ev.Settings(net="tree", n=C.EXACT_MAX_N)).exact is not None
    assert ev.analyse(ev.Settings(net="tree", n=C.EXACT_MAX_N + 1)).exact is None


def test_unequal_orders_raise_and_wrong_length_orders_too():
    with pytest.raises(ValueError):
        A.eliminate(S.path_graph(3).adj, (0, 1))
    with pytest.raises(ValueError):
        A.tree_decomposition(S.path_graph(3).adj, (0, 0, 1))
