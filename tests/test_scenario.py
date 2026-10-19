"""Szenarien: Generatoren, Familien mit bekanntem Wert, die Struktur der Netztypen und die Toronto-Daten (unabhängig vom Löser nachgezählt)."""

import math

import pytest

import twd_algorithm as A
import twd_constants as C
import twd_scenario as S


def test_graphs_are_symmetric_without_loops_and_deterministic():
    for net in C.NET_TYPES:
        g = S.build_graph(net, 30, 20, 7)
        assert len(g.adj) == len(g.labels) == len(g.positions) == g.n
        for v in range(g.n):
            assert v not in g.adj[v] and all(v in g.adj[w] for w in g.adj[v])
        assert S.build_graph(net, 30, 20, 7).adj == g.adj


def test_node_counts_follow_the_net_type():
    assert S.build_graph("grid", 50, 0, 1).n == 49 and S.build_graph("grid", 144, 0, 1).n == 144       # k = round(√n)
    for net in ("tree", "cycle", "random", "chordal"):
        assert S.build_graph(net, 37, 20, 1).n == 37
    assert S.build_graph("toronto", 120, 0, 1).n == 120 and S.build_graph("toronto", 99999, 0, 1).n == S.toronto_size() == 5072


def test_edges_listing_matches_the_edge_count():
    g = S.build_graph("grid", 36, 10, 3)
    assert len(g.edges()) == g.m == sum(len(a) for a in g.adj) // 2 and all(u < v for u, v in g.edges())
    assert S.edges_of(g.adj) == g.edges()


def test_grid_without_disturbance_is_the_full_raster_with_the_known_treewidth():
    for k in (2, 3, 4):
        g = S.exact_grid(k)
        assert g.n == k * k and g.m == 2 * k * (k - 1) and A.exact_treewidth(g.adj)[0] == k
    assert S.grid_side(16) == 4 and S.grid_side(2) == 2 and S.grid_side(1) == 2


def test_grid_blocking_removes_the_stated_share_of_edges():
    full = S.grid_graph(100, 0, 1).m
    assert full == 180
    for pct in (10, 30, 60):
        assert S.grid_graph(100, pct, 1).m == full - round(full * pct / 100)
    assert S.grid_graph(100, 30, 1).adj != S.grid_graph(100, 30, 2).adj


def test_tree_without_disturbance_is_a_tree_and_extras_add_exactly_that_many_edges():
    g = S.tree_graph(40, 0, 3)
    assert g.m == 39 and A.exact_treewidth(S.tree_graph(14, 0, 3).adj)[0] == 1
    assert S.tree_graph(40, 25, 3).m == 39 + round(25 * 40 / 100)
    assert all(abs(x) <= 1.0001 and abs(y) <= 1.0001 for x, y in g.positions)


def test_cycle_without_disturbance_is_a_cycle_and_chords_add_edges():
    g = S.cycle_graph(20, 0, 1)
    assert g.m == 20 and all(len(a) == 2 for a in g.adj)
    assert S.cycle_graph(20, 30, 1).m == 20 + 6


def test_random_graph_has_the_stated_mean_degree():
    assert S.mean_degree(0) == 1.5 and S.mean_degree(30) == 3.0 and S.mean_degree(60) == 4.5
    g = S.random_graph(400, 30, 5)
    assert 2.6 < 2 * g.m / g.n < 3.4


def test_chordal_net_is_always_chordal_and_omega_is_the_deepest_overlap():
    for seed in range(40):
        n, pct = 6 + seed % 20, 10 + (seed * 7) % 50
        g = S.chordal_graph(n, pct, seed)
        assert A.is_chordal(g.adj), (n, pct, seed)
        segs = S.line_segments(n, pct, seed)
        depth = max(sum(1 for s, l in segs if s <= p <= s + l) for p, _ in segs)
        assert A.clique_number_chordal(g.adj) == depth, (n, pct, seed)


def test_toronto_data_is_the_expected_extract_and_the_nearest_nodes_come_first():
    g = S.toronto_graph(5072, 0, 0)
    assert g.n == 5072 and g.m == 7621 and max(len(a) for a in g.adj) == 8
    small = S.toronto_graph(200, 0, 0)
    assert small.n == 200 and small.m == 245
    d = [float(lbl.split(": ")[1].split(" m")[0]) for lbl in small.labels]
    assert d == sorted(d) and d[-1] < 400                              # nach Abstand nummeriert, die 200 nächsten liegen im Umkreis von 400 m


def test_toronto_blocking_removes_edges():
    full = S.toronto_graph(300, 0, 1).m
    assert S.toronto_graph(300, 20, 1).m == full - round(full * 20 / 100)


def test_fixed_families():
    p = S.petersen_graph()
    assert p.n == 10 and p.m == 15 and all(len(a) == 3 for a in p.adj)
    q = S.hypercube_graph(4)
    assert q.n == 16 and q.m == 32 and all(len(a) == 4 for a in q.adj)
    assert S.complete_graph(6).m == 15 and S.complete_bipartite_graph(3, 5).m == 15 and S.star_graph(4).m == 4
    assert S.path_graph(5).m == 4 and S.ring_graph(7).m == 7 and S.triangle_with_pendant().m == 4
    assert S.random_tree(12, 3).m == 11


def test_giant_component_keeps_the_largest_and_renumbers():
    g = S.adjacency_from_edges(7, [(0, 1), (1, 2), (3, 4), (4, 5), (5, 6), (3, 6)])      # Komponenten {0,1,2} und der Kreis {3,4,5,6}
    giant = S.giant_component(g)
    assert len(giant) == 4 and all(len(a) == 2 for a in giant)
    assert S.giant_component(S.adjacency_from_edges(0, [])) == ()


def test_positions_helpers():
    pts = S.normalize(((0, 0), (10, 0), (10, 5)))
    assert pts[0] == (-1.0, -0.5) and pts[1] == (1.0, -0.5) and pts[2] == (1.0, 0.5)
    assert S.normalize(()) == () and S.circle_positions(4)[0] == (0.0, 1.0)
    lay = S.layered_positions(S.path_graph(3).adj)
    assert len(lay) == 3 and lay[0][1] > lay[1][1] > lay[2][1]


def test_random_graph_p_is_a_plain_gnp_adjacency():
    adj = S.random_graph_p(30, 50, 1)
    assert len(adj) == 30 and 0.3 < sum(len(a) for a in adj) / (30 * 29) < 0.7


def test_unknown_net_raises():
    with pytest.raises(ValueError):
        S.build_graph("mesh", 6, 20, 0)


def test_helpers_exist_for_every_declared_net():
    for net in C.NET_TYPES:
        assert math.isfinite(S.build_graph(net, 20, 10, 0).m)
