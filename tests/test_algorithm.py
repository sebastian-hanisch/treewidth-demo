"""Einheiten an Mini-Instanzen von Hand gerechnet (DEMO-PLAYBOOK §1b): Eliminieren, Min-Grad, Min-Fill, MMD+, exakter Wert, Zerlegung und Prüfung, Abschluss, Bandbreite.

Ordnungen, Beutel und Sehnen sind auf Papier nachgerechnet (Gleichstand: kleinster Index); die Orakel-Tests vergleichen später mit Brute Force und networkx."""

import pytest

import twd_algorithm as A
import twd_scenario as S

# --- Eliminieren ------------------------------------------------------------------------------------------------------------------------------


def test_eliminate_the_path_from_the_end(path4):
    el = A.eliminate(path4, (0, 1, 2, 3))
    assert el.width == 1 and el.fill == 0 and el.sizes == (2, 2, 2, 1)
    assert el.bags == ((1,), (2,), (3,), ()) and el.added == ((), (), (), ())


def test_eliminate_the_path_from_the_inside_adds_a_chord(path4):
    # Knoten 1 zuerst: seine Nachbarn 0 und 2 sind nicht verbunden: Sehne (0, 2), Beutel {1, 0, 2}
    el = A.eliminate(path4, (1, 0, 2, 3))
    assert el.width == 2 and el.fill == 1 and el.added[0] == ((0, 2),) and el.bags[1] == (0, 2) and el.sizes[0] == 3


def test_eliminate_rejects_orders_that_are_not_permutations(path4):
    for bad in ((0, 1, 2), (0, 1, 2, 2), (0, 1, 2, 4)):
        with pytest.raises(ValueError):
            A.eliminate(path4, bad)


def test_eliminate_the_square_adds_one_chord(c4):
    el = A.eliminate(c4, (0, 1, 2, 3))
    assert el.width == 2 and el.fill == 1 and el.added == (((1, 3),), (), (), ()) and el.sizes == (3, 3, 2, 1)


def test_eliminate_the_complete_graph_needs_no_chords(k4):
    el = A.eliminate(k4, (0, 1, 2, 3))
    assert el.width == 3 and el.fill == 0 and el.sizes == (4, 3, 2, 1)


def test_fill_count_by_hand(path4, c4):
    h = [set(a) for a in path4]
    assert [A.fill_count(h, v) for v in range(4)] == [0, 1, 1, 0]       # Knoten 1 hat die Nachbarn 0 und 2, die nicht verbunden sind
    assert [A.fill_count([set(a) for a in c4], v) for v in range(4)] == [1, 1, 1, 1]


# --- Heuristiken ------------------------------------------------------------------------------------------------------------------------------


def test_min_degree_on_the_path_and_square(path4, c4):
    assert A.min_degree_order(path4) == (0, 1, 2, 3)
    # C4: alle Grad 2, Knoten 0 zuerst (Sehne 1-3); dann haben 1, 2, 3 Grad 2 und 1 kommt zuerst, dann 2, dann 3
    assert A.min_degree_order(c4) == (0, 1, 2, 3)


def test_min_degree_on_the_triangle_with_pendant(paw):
    # Grade 2, 2, 3, 1: das Pendel 3 zuerst (Beutel {3, 2}), dann ist der Rest ein Dreieck: 0, 1, 2
    order = A.min_degree_order(paw)
    assert order == (3, 0, 1, 2)
    el = A.eliminate(paw, order)
    assert el.width == 2 and el.fill == 0 and el.sizes == (2, 3, 2, 1)


def test_min_fill_on_the_path_and_pentagon(path4, c5):
    assert A.min_fill_order(path4) == (0, 1, 2, 3)
    # C5: überall Auffüllung 1, Knoten 0 zuerst (Sehne 1-4); der Rest ist ein Viereck 1-2-3-4, überall Auffüllung 1: Knoten 1 (Sehne 2-4); dann ein Dreieck
    order = A.min_fill_order(c5)
    assert order == (0, 1, 2, 3, 4)
    el = A.eliminate(c5, order)
    assert el.width == 2 and el.fill == 2 and el.added[0] == ((1, 4),) and el.added[1] == ((2, 4),)


def test_min_fill_prefers_the_cheaper_vertex_over_the_lower_index():
    # Dreieck 1-2-3 mit Pendel 0 an Knoten 1 und Pendel 4 an Knoten 2... Knoten 0 hat 1 Nachbarn (Auffüllung 0), Knoten 1 hat 3 Nachbarn (0, 2, 3; fehlend 0-2 und 0-3)
    g = S.adjacency_from_edges(5, [(1, 2), (1, 3), (2, 3), (0, 1), (4, 2)])
    order = A.min_fill_order(g)
    assert order[0] == 0 and A.eliminate(g, order).fill == 0           # beide Pendel zuerst, dann das Dreieck: keine Sehne nötig


def test_random_order_is_a_seeded_permutation():
    import random
    a, b = A.random_order(8, random.Random(3)), A.random_order(8, random.Random(3))
    assert a == b and sorted(a) == list(range(8)) and A.random_order(8, random.Random(4)) != a


def test_order_functions_cover_the_three_orders():
    import twd_constants as C
    assert set(A.ORDER_FUNCS) == set(C.ORDERS)


# --- untere Schranke --------------------------------------------------------------------------------------------------------------------------


def test_mmd_plus_by_hand(path4, c4, k4):
    assert A.mmd_plus(path4) == 1                                   # kleinster Grad 1, kontrahieren, wieder 1, ...
    assert A.mmd_plus(c4) == 2                                      # alle Grad 2; nach der Kontraktion ein Dreieck, Grad 2
    assert A.mmd_plus(k4) == 3                                      # alle Grad 3, danach K3 (2), K2 (1): der Maximalwert ist 3
    assert A.mmd_plus(S.star_graph(4).adj) == 1


def test_mmd_plus_is_a_lower_bound_and_can_be_strictly_below_the_truth():
    g = S.exact_grid(4).adj                                         # Baumweite 4, aber die Kontraktion verliert Kanten
    assert A.mmd_plus(g) <= 4
    assert A.mmd_plus(S.exact_grid(6).adj) < 6


# --- exakt ------------------------------------------------------------------------------------------------------------------------------------


def test_exact_values_by_hand(path4, paw, c4, c5, k4):
    assert A.exact_treewidth(path4)[0] == 1 and A.exact_treewidth(paw)[0] == 2
    assert A.exact_treewidth(c4)[0] == 2 and A.exact_treewidth(c5)[0] == 2 and A.exact_treewidth(k4)[0] == 3
    assert A.exact_treewidth(S.star_graph(5).adj)[0] == 1
    assert A.exact_treewidth(S.exact_grid(3).adj)[0] == 3
    assert A.exact_treewidth(S.petersen_graph().adj)[0] == 4
    assert A.exact_treewidth(S.complete_bipartite_graph(2, 4).adj)[0] == 2


def test_exact_order_attains_the_value():
    for g in (S.ring_graph(6), S.petersen_graph(), S.exact_grid(3), S.complete_bipartite_graph(3, 3), S.triangle_with_pendant()):
        tw, order = A.exact_treewidth(g.adj)
        assert sorted(order) == list(range(g.n)) and A.eliminate(g.adj, order).width == tw


def test_exact_refuses_graphs_above_the_limit():
    with pytest.raises(ValueError):
        A.exact_treewidth(S.path_graph(5).adj, limit=4)


# --- Zerlegung --------------------------------------------------------------------------------------------------------------------------------


def test_decomposition_of_the_triangle_with_pendant_by_hand(paw):
    dec = A.tree_decomposition(paw, (3, 0, 1, 2))
    assert dec.bags == (frozenset({0, 1, 2}), frozenset({1, 2}), frozenset({2}), frozenset({2, 3}))
    assert dec.edges == ((0, 1), (1, 2), (3, 2)) and dec.width == 2
    assert A.validate_decomposition(paw, dec.bags, dec.edges) == []


def test_decomposition_of_a_disconnected_graph_chains_the_roots():
    g = S.adjacency_from_edges(4, [(0, 1), (2, 3)])
    dec = A.tree_decomposition(g, (0, 1, 2, 3))
    assert len(dec.edges) == 3 and A.validate_decomposition(g, dec.bags, dec.edges) == []


def test_validation_detects_each_kind_of_violation(paw):
    dec = A.tree_decomposition(paw, (3, 0, 1, 2))
    bags = list(dec.bags)
    bags[3] = frozenset({2})                                         # Knoten 3 verschwindet: kein Beutel enthält ihn, die Kante 2-3 ebenso
    got = A.validate_decomposition(paw, tuple(bags), dec.edges)
    assert ("knoten", 3) in got and ("kante", (2, 3)) in got
    # eine Baumkante fehlt: kein Baum mehr, und der Beutel {2, 3} ist von den anderen Beuteln mit Knoten 2 getrennt
    assert A.validate_decomposition(paw, dec.bags, dec.edges[:-1]) == [("baum", (4, 2)), ("teilbaum", 2)]
    bags = list(dec.bags)
    bags[3] = frozenset({0, 2, 3})                                   # Knoten 0 liegt im Beutel 0 und im Beutel 3, aber nicht dazwischen
    assert A.validate_decomposition(paw, tuple(bags), dec.edges) == [("teilbaum", 0)]
    cyclic = dec.edges + ((0, 3),)                                   # ein Kreis statt eines Baumes
    assert ("baum", (4, 4)) in A.validate_decomposition(paw, dec.bags, cyclic)


def test_decomposition_width_is_the_elimination_width(c5):
    order = A.min_fill_order(c5)
    dec = A.tree_decomposition(c5, order)
    assert dec.width == A.eliminate(c5, order).width == max(len(b) for b in dec.bags) - 1


# --- Abschluss und Brücke zu den chordalen Graphen ------------------------------------------------------------------------------------------------


def test_completion_of_the_square_and_pentagon(c4, c5):
    h = A.completion(c4, (0, 1, 2, 3))
    assert sum(len(a) for a in h) // 2 == 5 and 3 in h[1]
    assert not A.is_chordal(c4) and A.is_chordal(h)
    h5 = A.completion(c5, (0, 1, 2, 3, 4))
    assert sum(len(a) for a in h5) // 2 == 7 and A.is_chordal(h5) and not A.is_chordal(c5)


def test_clique_number_of_chordal_graphs(path4, paw, k4):
    assert A.clique_number_chordal(path4) == 2 and A.clique_number_chordal(paw) == 3 and A.clique_number_chordal(k4) == 4
    assert A.clique_number_chordal(S.adjacency_from_edges(0, [])) == 0 and A.clique_number_chordal(S.adjacency_from_edges(3, [])) == 1


def test_mcs_order_by_hand(c5):
    assert A.mcs_order(c5) == (4, 3, 2, 1, 0)                       # Besuch 0, 1, 2, 3, 4 (Gleichstände: kleinster Index), umgekehrt gelesen


def test_chordal_check_by_order(path4, c4):
    assert A.is_perfect_order(path4, (3, 2, 1, 0)) and not A.is_perfect_order(c4, (3, 2, 1, 0))


# --- Bandbreite und Brute Force ----------------------------------------------------------------------------------------------------------------


def test_bandwidth_by_hand(path4, c4, k4):
    assert A.bandwidth_small(path4) == 1 and A.bandwidth_small(c4) == 2 and A.bandwidth_small(k4) == 3
    assert A.bandwidth_small(S.star_graph(3).adj) == 2               # eine Mitte mit drei Blättern: zwei Blätter liegen auf derselben Seite
    assert A.bandwidth_small(S.adjacency_from_edges(3, [])) == 0
    with pytest.raises(ValueError):
        A.bandwidth_small(S.path_graph(9).adj)


def test_brute_force_treewidth_by_hand(path4, c4, k4):
    assert A.brute_force_treewidth(path4) == 1 and A.brute_force_treewidth(c4) == 2 and A.brute_force_treewidth(k4) == 3
    assert A.brute_force_treewidth(S.adjacency_from_edges(0, [])) == 0
    with pytest.raises(ValueError):
        A.brute_force_treewidth(S.path_graph(9).adj)


def test_fill_count_counts_present_edges_among_the_neighbours(paw, k4):
    # Dreieck mit Pendel: Knoten 2 hat die Nachbarn 0, 1, 3; verbunden ist nur das Paar 0-1, also fehlen 3 − 1 = 2 Kanten
    h = [set(a) for a in paw]
    assert [A.fill_count(h, v) for v in range(4)] == [0, 0, 2, 0]
    # K4: jeder Knoten hat drei verbundene Nachbarn: nichts fehlt
    assert [A.fill_count([set(a) for a in k4], v) for v in range(4)] == [0, 0, 0, 0]
    # Stern mit drei Blättern: die Mitte hat drei Nachbarn, keine Kante dazwischen: 3 fehlen
    assert A.fill_count([set(a) for a in S.star_graph(3).adj], 0) == 3


def test_mmd_plus_takes_the_largest_minimum_degree_and_contracts_towards_few_common_neighbours():
    # Dreieck mit einem Pendel am Knoten 2 und einem weiteren an 3: die kleinsten Grade sind 1, 1, dann steigen sie auf 2: der Maximalwert (nicht der letzte) zählt
    g = S.adjacency_from_edges(5, [(0, 1), (0, 2), (1, 2), (2, 3), (3, 4)])
    assert A.mmd_plus(g) == 2
    # Zwei Dreiecke, die einen Knoten teilen (Schmetterling): Baumweite 2, kleinster Grad 2
    assert A.mmd_plus(S.adjacency_from_edges(5, [(0, 1), (0, 2), (1, 2), (2, 3), (2, 4), (3, 4)])) == 2


def test_tree_check_rejects_a_graph_with_the_right_edge_count_but_not_connected():
    g = S.adjacency_from_edges(4, [(0, 1), (2, 3)])
    bags = (frozenset({0, 1}), frozenset({0, 1}), frozenset({2, 3}), frozenset({2, 3}))
    # drei Baumkanten, aber (0,1) doppelt und der Teil {2,3} hängt nicht an: die Kantenzahl stimmt (3 = 4 − 1), der Baum ist nicht zusammenhängend
    bad = A.validate_decomposition(g, bags, ((0, 1), (0, 1), (2, 3)))
    assert ("baum", (4, 3)) in bad
    # genau n − 1 Kanten und zusammenhängend, aber mit einem Kreis ausgeschlossen: ein Pfad ist ein Baum
    assert A.validate_decomposition(g, bags, ((0, 1), (1, 2), (2, 3))) == []


def test_perfect_order_needs_two_later_neighbours_to_check_anything():
    g = S.path_graph(3).adj
    assert A.is_perfect_order(g, (0, 1, 2)) and not A.is_perfect_order(g, (1, 0, 2))          # Mitte zuerst: die beiden Enden sind nicht verbunden
    assert A.is_perfect_order(S.star_graph(1).adj, (0, 1))                                    # ein einziger späterer Nachbar: nichts zu prüfen


def test_bandwidth_looks_at_every_edge_including_the_last_vertex():
    g = S.adjacency_from_edges(4, [(0, 3), (1, 3), (2, 3)])                                  # Stern mit der Mitte 3: die Kanten laufen alle über den letzten Knoten
    assert A.bandwidth_small(g) == 2
    assert A.bandwidth_small(S.adjacency_from_edges(3, [(0, 2)])) == 1


def test_exact_treewidth_of_a_graph_with_isolated_vertices_and_the_order_covers_all_vertices():
    g = S.adjacency_from_edges(5, [(0, 1), (1, 2), (0, 2)])
    tw, order = A.exact_treewidth(g)
    assert tw == 2 and sorted(order) == [0, 1, 2, 3, 4]
