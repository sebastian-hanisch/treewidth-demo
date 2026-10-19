"""Szenarien: Netze, deren Baumweite gefragt ist (Straßenraster, Baum plus Zusatzkanten, Kreis plus Sehnen, dünnes Zufallsnetz, Konfliktgraph von Teilstrecken, Toronto) und feste Vergleichsgraphen.

Ein Graph ist eine Adjazenzliste `adj` (Tupel von Mengen; Knoten 0 .. n-1, ungerichtet, ohne Schleifen) plus Anzeige-Positionen. Die Störung (`pct`) bedeutet je Netztyp etwas anderes
(Sperrungen, Zusatzkanten, mittlerer Grad, Streckenlänge); die Hilfe der App nennt es. Alle Knoten bleiben erhalten (Komponenten dürfen zerfallen)."""

import json
import math
import random
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"


@dataclass(frozen=True)
class Graph:
    n: int
    adj: tuple          # adj[v] = frozenset der Nachbarn von v
    positions: tuple    # (x, y) je Knoten
    labels: tuple       # Hover-Text je Knoten
    kind: str           # "grid", "tree", "cycle", "random", "chordal", "toronto", "family"

    @property
    def m(self):
        return sum(len(a) for a in self.adj) // 2

    def edges(self):
        return [(u, v) for u in range(self.n) for v in sorted(self.adj[u]) if u < v]


def adjacency_from_edges(n, edges):
    """Adjazenzliste aus ungerichteten Kanten; Schleifen und doppelte Kanten werden ignoriert."""
    adj = [set() for _ in range(n)]
    for u, v in edges:
        if u != v:
            adj[u].add(v)
            adj[v].add(u)
    return tuple(frozenset(a) for a in adj)


def edges_of(adj):
    return [(u, v) for u in range(len(adj)) for v in sorted(adj[u]) if u < v]


def circle_positions(n):
    """Knoten 0 .. n-1 der Reihe nach auf einen Kreis (Radius 1, Start oben)."""
    return tuple((round(math.cos(math.pi / 2 - 2 * math.pi * i / max(n, 1)), 6), round(math.sin(math.pi / 2 - 2 * math.pi * i / max(n, 1)), 6)) for i in range(n))


def normalize(points):
    """Punkte in das Quadrat [-1, 1] einpassen, Seitenverhältnis erhalten."""
    if not points:
        return ()
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    half = max(max(xs) - min(xs), max(ys) - min(ys)) / 2 or 1.0
    return tuple((round((x - cx) / half, 6), round((y - cy) / half, 6)) for x, y in points)


def layered_positions(adj):
    """Schichtenzeichnung für Bäume und baumartige Graphen: Tiefe von Knoten 0 (weitere Komponenten von ihrem kleinsten Knoten aus), innerhalb einer Schicht gleichmäßig verteilt."""
    n = len(adj)
    depth = [-1] * n
    for root in range(n):
        if depth[root] >= 0:
            continue
        depth[root] = 0
        queue = [root]
        for x in queue:
            for y in sorted(adj[x]):
                if depth[y] < 0:
                    depth[y] = depth[x] + 1
                    queue.append(y)
    layers = {}
    for v in range(n):
        layers.setdefault(depth[v], []).append(v)
    pos = [None] * n
    for d, vs in layers.items():
        for i, v in enumerate(vs):
            pos[v] = ((i + 0.5) / len(vs) * 2 - 1, 1 - 2 * d / max(len(layers), 1))
    return normalize(tuple(pos)) if pos else ()


def _labels(n, prefix="Knoten"):
    return tuple(f"{prefix} {i + 1}" for i in range(n))


def _remove_pct(edges, pct, rng):
    """Zufällig `pct` Prozent der Kanten sperren (entfernen); die Auswahl ist eine feste Stichprobe."""
    k = round(len(edges) * pct / 100.0)
    drop = set(rng.sample(range(len(edges)), min(k, len(edges)))) if k else set()
    return [e for i, e in enumerate(edges) if i not in drop]


# --- Netztypen --------------------------------------------------------------------------------------------------------------------------------

def grid_side(n):
    """Seitenlänge des Gitters mit ungefähr n Kreuzungen."""
    return max(2, round(math.sqrt(n)))


def grid_edges(k):
    edges = []
    for r in range(k):
        for c in range(k):
            v = r * k + c
            if c + 1 < k:
                edges.append((v, v + 1))
            if r + 1 < k:
                edges.append((v, v + k))
    return edges


def grid_graph(n, pct, seed):
    """Straßenraster k × k mit k = round(√n); die Störung sperrt zufällig `pct` Prozent der Kanten."""
    k = grid_side(n)
    rng = random.Random(seed)
    edges = _remove_pct(grid_edges(k), pct, rng)
    pos = normalize(tuple((c, -r) for r in range(k) for c in range(k)))
    return Graph(k * k, adjacency_from_edges(k * k, edges), pos, tuple(f"Kreuzung {i + 1}" for i in range(k * k)), "grid")


def random_tree_edges(t, rng):
    """Zufälliger Baum auf t Knoten: Knoten i >= 1 hängt an einem gleichverteilt gewählten früheren Knoten."""
    return [(i, rng.randrange(i)) for i in range(1, t)]


def _add_random_edges(n, edges, count, rng):
    """`count` zusätzliche Kanten zwischen bisher nicht verbundenen Paaren (soweit es so viele gibt)."""
    have = {(min(u, v), max(u, v)) for u, v in edges}
    free = [(i, j) for i in range(n) for j in range(i + 1, n) if (i, j) not in have]
    return list(edges) + rng.sample(free, min(count, len(free)))


def tree_graph(n, pct, seed):
    """Zufälliger Baum plus round(pct · n / 100) Zusatzkanten; Schichtenzeichnung des zugrunde liegenden Baumes."""
    rng = random.Random(seed)
    base = random_tree_edges(n, rng)
    edges = _add_random_edges(n, base, round(pct * n / 100.0), rng)
    return Graph(n, adjacency_from_edges(n, edges), layered_positions(adjacency_from_edges(n, base)), _labels(n), "tree")


def cycle_graph(n, pct, seed):
    """Kreis auf n Knoten plus round(pct · n / 100) Zusatzsehnen."""
    rng = random.Random(seed)
    edges = _add_random_edges(n, [(i, (i + 1) % n) for i in range(n)], round(pct * n / 100.0), rng)
    return Graph(n, adjacency_from_edges(n, edges), circle_positions(n), _labels(n), "cycle")


def mean_degree(pct):
    """Mittlerer Grad des Zufallsnetzes: 1,5 plus Störung durch 20."""
    return 1.5 + pct / 20.0


def random_graph(n, pct, seed):
    """G(n, p) mit p = mittlerer Grad / (n − 1); jedes Paar unabhängig."""
    rng = random.Random(seed)
    p = min(1.0, mean_degree(pct) / max(n - 1, 1))
    edges = [(i, j) for i in range(n) for j in range(i + 1, n) if rng.random() < p]
    return Graph(n, adjacency_from_edges(n, edges), circle_positions(n), _labels(n), "random")


def random_graph_p(n, p_pct, seed):
    """G(n, p) mit p in Prozent (für die Vergleiche auf kleinen Graphen): jedes Paar unabhängig; gibt nur die Adjazenzliste zurück."""
    rng = random.Random(seed)
    return adjacency_from_edges(n, [(i, j) for i in range(n) for j in range(i + 1, n) if rng.random() < p_pct / 100.0])


def line_segments(n, density_pct, seed):
    """Strecken (Start, Länge) auf einer Geraden: Start gleichverteilt in [0, 1], Länge gleichverteilt in [L/2, 3L/2] mit L = density_pct / 100, nach Start sortiert."""
    rng = random.Random(seed)
    base = density_pct / 100.0
    return sorted((rng.random(), base * (0.5 + rng.random())) for _ in range(n))


def chordal_graph(n, pct, seed):
    """Konfliktgraph von Sendungen, die Teilstrecken einer Linie belegen (ein Intervallgraph, chordal): zwei Sendungen stehen im Konflikt, wenn die Strecken überlappen."""
    segs = line_segments(n, pct, seed)
    edges = [(i, j) for i in range(n) for j in range(i + 1, n) if segs[j][0] <= segs[i][0] + segs[i][1]]
    labels = tuple(f"Sendung {i + 1}: Strecke {s:.2f} bis {s + l:.2f}" for i, (s, l) in enumerate(segs))
    return Graph(n, adjacency_from_edges(n, edges), circle_positions(n), labels, "chordal")


@lru_cache(maxsize=1)
def _toronto_payload():
    return json.loads((DATA / "toronto_campus.json").read_text(encoding="utf-8"))


def toronto_size():
    """Zahl der Kreuzungen des Toronto-Ausschnitts."""
    return len(_toronto_payload()["nodes_xy_m"])


@lru_cache(maxsize=1)
def _toronto_edges():
    """Ungerichtete einfache Kanten des Ausschnitts (aus den gerichteten Bögen)."""
    return tuple(sorted({(min(u, v), max(u, v)) for u, v, _ in _toronto_payload()["arcs"] if u != v}))


def toronto_graph(n, pct, seed):
    """Die n Kreuzungen, die dem Mittelpunkt des Ausschnitts am nächsten liegen (Knoten nach Abstand nummeriert), mit allen Straßen zwischen ihnen; die Störung sperrt zufällig `pct` Prozent der Kanten."""
    xy = _toronto_payload()["nodes_xy_m"]
    n = min(n, len(xy))
    keep = sorted(range(len(xy)), key=lambda i: (math.hypot(xy[i][0], xy[i][1]), i))[:n]
    index = {old: new for new, old in enumerate(keep)}
    edges = [(index[u], index[v]) for u, v in _toronto_edges() if u in index and v in index]
    rng = random.Random(seed)
    edges = _remove_pct(edges, pct, rng)
    pos = normalize(tuple(tuple(xy[old]) for old in keep))
    labels = tuple(f"Kreuzung {i + 1}: {math.hypot(xy[old][0], xy[old][1]):.0f} m vom Mittelpunkt" for i, old in enumerate(keep))
    return Graph(n, adjacency_from_edges(n, edges), pos, labels, "toronto")


def build_graph(net_type, n, pct, seed):
    """Der Graph der Hauptansicht."""
    builders = {"grid": grid_graph, "tree": tree_graph, "cycle": cycle_graph, "random": random_graph, "chordal": chordal_graph, "toronto": toronto_graph}
    if net_type not in builders:
        raise ValueError(f"unbekannter Netztyp: {net_type}")
    return builders[net_type](n, pct, seed)


def giant_component(adj):
    """Die größte Zusammenhangskomponente als Adjazenzliste (neu nummeriert in der Reihenfolge der alten Nummern)."""
    n = len(adj)
    seen, best = [False] * n, []
    for s in range(n):
        if seen[s]:
            continue
        comp, stack = [], [s]
        seen[s] = True
        while stack:
            x = stack.pop()
            comp.append(x)
            for y in adj[x]:
                if not seen[y]:
                    seen[y] = True
                    stack.append(y)
        if len(comp) > len(best):
            best = comp
    best.sort()
    index = {v: i for i, v in enumerate(best)}
    return tuple(frozenset(index[w] for w in adj[v]) for v in best)


# --- feste Vergleichsgraphen ------------------------------------------------------------------------------------------------------------------

def _family(adj, labels=None):
    n = len(adj)
    return Graph(n, adj, circle_positions(n), labels or _labels(n), "family")


def path_graph(k):
    return _family(adjacency_from_edges(k, [(i, i + 1) for i in range(k - 1)]))


def ring_graph(k):
    """Kreis C_k."""
    return _family(adjacency_from_edges(k, [(i, (i + 1) % k) for i in range(k)]))


def complete_graph(k):
    return _family(adjacency_from_edges(k, [(i, j) for i in range(k) for j in range(i + 1, k)]))


def complete_bipartite_graph(a, b):
    return _family(adjacency_from_edges(a + b, [(i, a + j) for i in range(a) for j in range(b)]))


def star_graph(leaves):
    return _family(adjacency_from_edges(leaves + 1, [(0, i + 1) for i in range(leaves)]))


def triangle_with_pendant():
    """Dreieck 0-1-2 mit Pendel 3 an Knoten 2."""
    return _family(adjacency_from_edges(4, [(0, 1), (0, 2), (1, 2), (2, 3)]))


def exact_grid(k):
    """Gitter k × k ohne Störung (Baumweite k)."""
    return grid_graph(k * k, 0, 0)


def petersen_graph():
    """Petersen-Graph: 10 Knoten, 15 Kanten, Baumweite 4."""
    edges = [(i, (i + 1) % 5) for i in range(5)] + [(i, i + 5) for i in range(5)] + [(5, 7), (7, 9), (9, 6), (6, 8), (8, 5)]
    return _family(adjacency_from_edges(10, edges))


def hypercube_graph(d):
    """Hyperwürfel Q_d: 2^d Knoten, benachbart bei genau einem verschiedenen Bit (Baumweite 6 für d = 4)."""
    n = 1 << d
    return _family(adjacency_from_edges(n, [(v, v ^ (1 << b)) for v in range(n) for b in range(d) if v < v ^ (1 << b)]))


def random_tree(n, seed):
    return _family(adjacency_from_edges(n, random_tree_edges(n, random.Random(seed))))
