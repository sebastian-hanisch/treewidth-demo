"""Orakel-Tests (ORACLE-PLAYBOOK): exakte Baumweite, Heuristiken, untere Schranke, Zerlegung und Abschluss gegen unabhängige Rechenwege.

Orakel: Brute Force über alle Eliminationsordnungen (n <= 7), bekannte Familienwerte (Baum 1, Kreis 2, K_n n−1, K_{a,b} min(a, b), Gitter k, Petersen 4, Q4 6), networkx
(`chordal_graph_treewidth`, `chordal_graph_cliques`, `is_chordal`, `treewidth_min_degree`/`treewidth_min_fill_in` nur als Plausibilität), eine eigene, vom Bau getrennte Prüfung der drei
Eigenschaften einer Zerlegung und der Satz tw <= Bandbreite. Alle Instanzen sind fest, zusammen wenige Sekunden."""

import random

import pytest

import twd_algorithm as A
import twd_scenario as S

nx = pytest.importorskip("networkx")


def _nxg(adj):
    g = nx.Graph()
    g.add_nodes_from(range(len(adj)))
    g.add_edges_from((u, v) for u in range(len(adj)) for v in adj[u] if u < v)
    return g


def _random_adj(n, p, seed):
    rng = random.Random(seed)
    return S.adjacency_from_edges(n, [(i, j) for i in range(n) for j in range(i + 1, n) if rng.random() < p / 100])


def _mixed():
    """Gemischte feste Instanzen: Zufall verschiedener Dichte, Bäume mit Zusatzkanten, Gitter mit Sperrungen, Kreise mit Sehnen, Konfliktgraphen."""
    out = []
    for seed in range(90):
        n = 5 + seed % 8
        out.append(("random", _random_adj(n, 15 + (seed * 11) % 70, seed)))
        out.append(("tree", S.tree_graph(n, 10 + seed % 5 * 15, seed).adj))
        out.append(("cycle", S.cycle_graph(max(n, 4), seed % 4 * 20, seed).adj))
        out.append(("chordal", S.chordal_graph(n, 10 + seed % 6 * 8, seed).adj))
    for seed in range(10):
        out.append(("grid", S.grid_graph(9 + seed * 3, seed % 3 * 15, seed).adj))
    return out


MIXED = _mixed()


# --- exakter Wert ------------------------------------------------------------------------------------------------------------------------------


def test_exact_treewidth_equals_brute_force_over_all_orders():
    count = 0
    for seed in range(330):
        n = 2 + seed % 5                                           # 2 bis 6 Knoten: höchstens 720 Ordnungen
        adj = _random_adj(n, 20 + (seed * 17) % 70, seed)
        assert A.exact_treewidth(adj)[0] == A.brute_force_treewidth(adj), (n, seed)
        count += 1
    for seed in range(25):
        adj = _random_adj(7, 25 + seed * 2, 1000 + seed)           # 7 Knoten: 5 040 Ordnungen
        assert A.exact_treewidth(adj)[0] == A.brute_force_treewidth(adj), seed
        count += 1
    assert count >= 300


def test_exact_treewidth_matches_the_known_family_values():
    for k in (2, 3, 4):
        assert A.exact_treewidth(S.exact_grid(k).adj)[0] == k
    for n in (2, 5, 9, 16):
        assert A.exact_treewidth(S.random_tree(n, n).adj)[0] == (1 if n > 1 else 0)
    for k in range(3, 13):
        assert A.exact_treewidth(S.ring_graph(k).adj)[0] == 2
    for k in range(2, 9):
        assert A.exact_treewidth(S.complete_graph(k).adj)[0] == k - 1
    for a, b in ((2, 3), (3, 3), (3, 5), (4, 4)):
        assert A.exact_treewidth(S.complete_bipartite_graph(a, b).adj)[0] == min(a, b)
    assert A.exact_treewidth(S.petersen_graph().adj)[0] == 4 and A.exact_treewidth(S.hypercube_graph(4).adj)[0] == 6
    assert A.exact_treewidth(S.hypercube_graph(3).adj)[0] == 3


def test_exact_order_attains_the_value_on_every_instance():
    for name, adj in MIXED:
        if len(adj) <= 12:
            tw, order = A.exact_treewidth(adj)
            assert A.eliminate(adj, order).width == tw, name


# --- Schranken: untere <= exakt <= obere -----------------------------------------------------------------------------------------------------------


def test_lower_bound_exact_value_and_heuristics_are_ordered_on_every_instance():
    count = 0
    for name, adj in MIXED:
        if len(adj) > 12:
            continue
        tw = A.exact_treewidth(adj)[0]
        lb = A.mmd_plus(adj)
        ub_d = A.eliminate(adj, A.min_degree_order(adj)).width
        ub_f = A.eliminate(adj, A.min_fill_order(adj)).width
        assert lb <= tw <= min(ub_d, ub_f), (name, lb, tw, ub_d, ub_f)
        count += 1
    assert count >= 300


def test_networkx_heuristics_are_never_below_the_exact_value():
    for name, adj in MIXED[::3]:
        if len(adj) > 12:
            continue
        tw = A.exact_treewidth(adj)[0]
        g = _nxg(adj)
        assert nx.algorithms.approximation.treewidth_min_degree(g)[0] >= tw and nx.algorithms.approximation.treewidth_min_fill_in(g)[0] >= tw, name


def test_every_elimination_order_gives_an_upper_bound():
    rng = random.Random(7)
    for name, adj in MIXED[::5]:
        if len(adj) > 10:
            continue
        tw = A.exact_treewidth(adj)[0]
        order = list(range(len(adj)))
        rng.shuffle(order)
        assert A.eliminate(adj, tuple(order)).width >= tw, name


# --- Zerlegung ----------------------------------------------------------------------------------------------------------------------------------


def _independent_validity(adj, bags, edges):
    """Eigene, von `validate_decomposition` getrennte Prüfung über networkx: Baum, Kantenabdeckung, Teilbaum-Eigenschaft."""
    t = nx.Graph()
    t.add_nodes_from(range(len(bags)))
    t.add_edges_from(edges)
    if len(bags) and not nx.is_tree(t):
        return False
    for u in range(len(adj)):
        for v in adj[u]:
            if not any(u in b and v in b for b in bags):
                return False
    for v in range(len(adj)):
        containing = [i for i, b in enumerate(bags) if v in b]
        if not containing or not nx.is_connected(t.subgraph(containing)):
            return False
    return True


def test_every_decomposition_from_an_order_is_valid_by_both_checks():
    rng = random.Random(3)
    for name, adj in MIXED:
        orders = [A.min_degree_order(adj), A.min_fill_order(adj), A.random_order(len(adj), rng)]
        for order in orders:
            dec = A.tree_decomposition(adj, order)
            assert A.validate_decomposition(adj, dec.bags, dec.edges) == [], name
            assert _independent_validity(adj, dec.bags, dec.edges), name
            assert dec.width == max(len(b) for b in dec.bags) - 1 == A.eliminate(adj, order).width


def test_the_independent_check_also_rejects_broken_decompositions():
    adj = S.exact_grid(3).adj
    dec = A.tree_decomposition(adj, A.min_fill_order(adj))
    assert _independent_validity(adj, dec.bags, dec.edges)
    assert not _independent_validity(adj, dec.bags, dec.edges[:-1])
    bags = list(dec.bags)
    bags[0] = frozenset({0})
    assert not _independent_validity(adj, tuple(bags), dec.edges)


# --- chordale Graphen, Abschluss --------------------------------------------------------------------------------------------------------------------


def test_chordal_graphs_need_no_fill_and_width_equals_omega_minus_one():
    checked = 0
    for name, adj in MIXED:
        g = _nxg(adj)
        if not nx.is_chordal(g) or g.number_of_edges() == 0:
            continue
        el = A.eliminate(adj, A.min_fill_order(adj))
        assert el.fill == 0 and el.width == nx.chordal_graph_treewidth(g), name
        assert el.width + 1 == max(len(c) for c in nx.chordal_graph_cliques(g)) == A.clique_number_chordal(adj), name
        checked += 1
    assert checked > 40


def test_fill_is_zero_exactly_for_chordal_graphs_under_min_fill():
    for name, adj in MIXED:
        assert (A.eliminate(adj, A.min_fill_order(adj)).fill == 0) == nx.is_chordal(_nxg(adj)), name


def test_the_completion_is_chordal_and_its_clique_number_is_width_plus_one():
    for name, adj in MIXED[::2]:
        for order in (A.min_degree_order(adj), A.min_fill_order(adj)):
            h = A.completion(adj, order)
            hg = _nxg(h)
            assert nx.is_chordal(hg) and A.is_chordal(h), name
            assert max(len(c) for c in nx.chordal_graph_cliques(hg)) == A.eliminate(adj, order).width + 1 or len(adj) == 0, name


# --- Invarianten ----------------------------------------------------------------------------------------------------------------------------------


def test_deleting_an_edge_never_raises_the_treewidth():
    rng = random.Random(11)
    for seed in range(100):
        n = 5 + seed % 6
        adj = _random_adj(n, 30 + seed % 50, seed)
        edges = S.edges_of(adj)
        if not edges:
            continue
        dropped = S.adjacency_from_edges(n, [e for e in edges if e != edges[rng.randrange(len(edges))]])
        assert A.exact_treewidth(dropped)[0] <= A.exact_treewidth(adj)[0], seed


def test_treewidth_is_at_most_the_bandwidth():
    for seed in range(60):
        n = 4 + seed % 4
        adj = _random_adj(n, 20 + (seed * 13) % 60, seed)
        assert A.exact_treewidth(adj)[0] <= A.bandwidth_small(adj), seed
    for g in (S.path_graph(6), S.ring_graph(7), S.star_graph(5), S.complete_bipartite_graph(2, 3), S.exact_grid(2), S.exact_grid(3)):
        if g.n <= 9:
            assert A.exact_treewidth(g.adj)[0] <= A.bandwidth_small(g.adj, limit=9)


def test_treewidth_of_a_disjoint_union_is_the_maximum():
    a, b = S.ring_graph(5).adj, S.complete_graph(4).adj
    edges = S.edges_of(a) + [(u + 5, v + 5) for u, v in S.edges_of(b)]
    both = S.adjacency_from_edges(9, edges)
    assert A.exact_treewidth(both)[0] == max(A.exact_treewidth(a)[0], A.exact_treewidth(b)[0]) == 3
