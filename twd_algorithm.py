"""Baumweite: Eliminationsordnung mit Auffüllen, Heuristiken (Min-Grad, Min-Fill), untere Schranke (MMD+), exakter Wert für kleine Graphen und die Baumzerlegung samt Prüfung.

Jede Regel ist eine eigene kleine Funktion mit expliziten Ein- und Ausgaben (DEMO-PLAYBOOK 1b). Reine Python-Mengen, feste Reihenfolgen (Gleichstand: kleinster Index), kein Zufall:
das Ergebnis ist vollständig deterministisch. Die einzige Zufallsquelle ist die zufällige Reihenfolge (`random_order`), die einen `random.Random` bekommt.

Eine *Eliminationsordnung* ist eine Reihenfolge der Knoten. Beim Eliminieren eines Knotens v werden seine noch nicht eliminierten Nachbarn paarweise verbunden (*Auffüllen*, die ergänzten
Kanten heißen auch Sehnen); der *Beutel* von v ist v samt diesen Nachbarn. Die *Breite* der Ordnung ist die größte Beutelgröße minus 1, die *Baumweite* die kleinste Breite über alle Ordnungen.
Die Beutel bilden, verbunden mit dem Beutel des frühesten späteren Nachbarn, eine Baumzerlegung; der aufgefüllte Graph ist chordal (Demo zu den chordalen Graphen)."""

import heapq
import itertools
from dataclasses import dataclass

import twd_constants as C

# --- Eliminieren ------------------------------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Elimination:
    order: tuple          # Eliminationsordnung
    width: int            # größte Beutelgröße minus 1
    fill: int             # Zahl ergänzter Kanten
    bags: tuple           # je Knoten (Index = Knotennummer): seine Beutel-Nachbarn beim Eliminieren, sortiert
    added: tuple          # je Schritt (Index = Position in der Ordnung): die dabei ergänzten Kanten (u, v), u < v
    sizes: tuple          # je Schritt: Beutelgröße (1 + Zahl der Nachbarn)


def eliminate(adj, order):
    """Eliminiert die Knoten in der Reihenfolge `order` und füllt auf. Gibt Breite, Zahl der Sehnen, Beutel je Knoten und die Sehnen je Schritt zurück."""
    n = len(adj)
    if sorted(order) != list(range(n)):
        raise ValueError("die Ordnung muss jeden Knoten genau einmal enthalten")
    h = [set(a) for a in adj]
    bags = [()] * n
    added, sizes = [], []
    fill = 0
    for v in order:
        nb = sorted(h[v])
        bags[v] = tuple(nb)
        sizes.append(len(nb) + 1)
        step_added = []
        for i in range(len(nb)):
            for j in range(i + 1, len(nb)):
                if nb[j] not in h[nb[i]]:
                    h[nb[i]].add(nb[j])
                    h[nb[j]].add(nb[i])
                    step_added.append((nb[i], nb[j]))
        fill += len(step_added)
        added.append(tuple(step_added))
        for w in nb:
            h[w].discard(v)
        h[v] = set()
    width = max(sizes) - 1 if sizes else 0
    return Elimination(tuple(order), width, fill, tuple(bags), tuple(added), tuple(sizes))


def fill_count(h, v):
    """Zahl der Kanten, die beim Eliminieren von v fehlen: Paare seiner Nachbarn, die nicht verbunden sind (alle Paare minus die vorhandenen Kanten unter den Nachbarn)."""
    nb = h[v]
    d = len(nb)
    present = sum(len(h[w] & nb) for w in nb) // 2
    return d * (d - 1) // 2 - present


def _simulate_pick(adj, score, affected_of):
    """Gemeinsamer Rahmen der beiden Heuristiken: immer den Knoten mit dem kleinsten Wert (Gleichstand: kleinster Index) eliminieren; nach dem Eliminieren werden die Werte der betroffenen Knoten neu bestimmt."""
    n = len(adj)
    h = [set(a) for a in adj]
    value = [score(h, v) for v in range(n)]
    heap = [(value[v], v) for v in range(n)]
    heapq.heapify(heap)
    alive = set(range(n))
    order = []
    while alive:
        s, v = heapq.heappop(heap)
        if v not in alive or s != value[v]:
            continue
        nb = sorted(h[v])
        for i in range(len(nb)):
            for j in range(i + 1, len(nb)):
                if nb[j] not in h[nb[i]]:
                    h[nb[i]].add(nb[j])
                    h[nb[j]].add(nb[i])
        for w in nb:
            h[w].discard(v)
        h[v] = set()
        alive.discard(v)
        order.append(v)
        for w in affected_of(h, nb):
            if w in alive:
                value[w] = score(h, w)
                heapq.heappush(heap, (value[w], w))
    return tuple(order)


def min_degree_order(adj):
    """Min-Grad: immer den Knoten mit den wenigsten noch nicht eliminierten Nachbarn eliminieren (Gleichstand: kleinster Index)."""
    return _simulate_pick(adj, lambda h, v: len(h[v]), lambda h, nb: nb)


def min_fill_order(adj):
    """Min-Fill: immer den Knoten eliminieren, dessen Nachbarn die wenigsten fehlenden Kanten haben (Gleichstand: kleinster Index). Betroffen sind die Nachbarn und deren Nachbarn."""
    def affected(h, nb):
        out = set(nb)
        for w in nb:
            out |= h[w]
        return out
    return _simulate_pick(adj, fill_count, affected)


def random_order(n, rng):
    """Zufällige Reihenfolge (zum Vergleich); `rng` ist ein `random.Random`."""
    order = list(range(n))
    rng.shuffle(order)
    return tuple(order)


ORDER_FUNCS = {"mindegree": lambda adj, rng: min_degree_order(adj), "minfill": lambda adj, rng: min_fill_order(adj), "random": lambda adj, rng: random_order(len(adj), rng)}


# --- untere Schranke --------------------------------------------------------------------------------------------------------------------------


def mmd_plus(adj):
    """Untere Schranke durch Min-Grad-Kontraktion (in der Literatur MMD+, Variante „least-c“): immer den Knoten kleinsten Grades v nehmen, den größten solchen Grad merken
    und v in den Nachbarn u mit den wenigsten gemeinsamen Nachbarn kontrahieren. Kontraktionen senken die Baumweite nie, der größte kleinste Grad ist eine untere Schranke."""
    h = {v: set(a) for v, a in enumerate(adj)}
    best = 0
    while len(h) > 1:
        v = min(h, key=lambda x: (len(h[x]), x))
        d = len(h[v])
        best = max(best, d)
        if d == 0:
            del h[v]
            continue
        u = min(h[v], key=lambda w: (len(h[v] & h[w]), len(h[w]), w))
        for w in h[v]:
            if w != u:
                h[w].discard(v)
                h[w].add(u)
                h[u].add(w)
        h[u].discard(v)
        h[u].discard(u)
        del h[v]
    return best


# --- exakt für kleine Graphen ----------------------------------------------------------------------------------------------------------------


def exact_treewidth(adj, limit=C.EXACT_MAX_N):
    """Exakte Baumweite durch Teilmengen-DP (Bodlaender, Fomin, Koster, Kratsch, Thilikos): f(S) = min über v in S von max(f(S ohne v), |Q(S ohne v, v)|), dabei ist Q die Menge der Knoten
    außerhalb von S, die von v über Knoten in S erreichbar sind; f(Menge aller Knoten) ist die Baumweite. Laufzeit und Speicher wachsen mit 2^n: ValueError über `limit` Knoten.
    Gibt (Baumweite, eine optimale Eliminationsordnung) zurück."""
    n = len(adj)
    if n > limit:
        raise ValueError(f"exakte Baumweite nur bis n = {limit}")
    if n == 0:
        return 0, ()
    nbr = [sum(1 << w for w in adj[v]) for v in range(n)]

    def q_size(mask, v):
        seen = 1 << v
        stack = [v]
        out = 0
        while stack:
            x = stack.pop()
            nb = nbr[x] & ~seen
            while nb:
                low = nb & -nb
                w = low.bit_length() - 1
                nb ^= low
                seen |= low
                if mask >> w & 1:
                    stack.append(w)
                else:
                    out |= low
        return bin(out).count("1")

    size = 1 << n
    f = [0] * size
    choice = [-1] * size
    for mask in range(1, size):
        best, pick = n + 1, -1
        m = mask
        while m:
            low = m & -m
            v = low.bit_length() - 1
            m ^= low
            rest = mask ^ low
            cand = max(f[rest], q_size(rest, v))
            if cand < best:
                best, pick = cand, v
        f[mask] = best
        choice[mask] = pick
    last_first, mask = [], size - 1
    while mask:
        v = choice[mask]
        last_first.append(v)                      # v ist der zuletzt eliminierte Knoten von mask
        mask ^= 1 << v
    return f[size - 1], tuple(reversed(last_first))


# --- Zerlegung --------------------------------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Decomposition:
    bags: tuple           # Beutel je Knoten des Zerlegungsbaums (Index = Knotennummer des Graphen): frozenset
    edges: tuple          # Baumkanten (u, v) zwischen Beutel-Indizes
    width: int


def tree_decomposition(adj, order):
    """Baumzerlegung aus einer Eliminationsordnung: Beutel(v) = {v} plus seine Beutel-Nachbarn; Elternbeutel von v ist der Beutel seines frühesten späteren Nachbarn.
    Hat der Graph mehrere Komponenten, werden die Wurzeln der Reihe nach durch Kanten verbunden (die Beutel sind dann disjunkt: die Eigenschaften bleiben erfüllt)."""
    el = eliminate(adj, order)
    pos = {v: i for i, v in enumerate(order)}
    bags = tuple(frozenset((v,) + el.bags[v]) for v in range(len(adj)))
    edges, roots = [], []
    for v in range(len(adj)):
        if el.bags[v]:
            edges.append((v, min(el.bags[v], key=lambda w: pos[w])))
        else:
            roots.append(v)
    for a, b in zip(roots, roots[1:]):
        edges.append((a, b))
    return Decomposition(bags, tuple(edges), el.width)


def validate_decomposition(adj, bags, edges):
    """Prüft die Eigenschaften einer Baumzerlegung einzeln und gibt die Verletzungen als Liste (Art, Zeuge) zurück; leer heißt gültig.
    Arten: "knoten" (ein Knoten liegt in keinem Beutel), "kante" (eine Kante liegt in keinem Beutel), "baum" (die Baumkanten bilden keinen Baum), "teilbaum" (die Beutel mit einem Knoten sind nicht zusammenhängend)."""
    n, k = len(adj), len(bags)
    bad = []
    for v in range(n):
        if not any(v in b for b in bags):
            bad.append(("knoten", v))
    for u in range(n):
        for v in adj[u]:
            if u < v and not any(u in b and v in b for b in bags):
                bad.append(("kante", (u, v)))
    tree = [set() for _ in range(k)]
    for a, b in edges:
        tree[a].add(b)
        tree[b].add(a)
    if k and (len(edges) != k - 1 or len(_reach(tree, 0, set(range(k)))) != k):
        bad.append(("baum", (k, len(edges))))
    for v in range(n):
        containing = {i for i in range(k) if v in bags[i]}
        if containing and len(_reach(tree, next(iter(sorted(containing))), containing)) != len(containing):
            bad.append(("teilbaum", v))
    return bad


def _reach(tree, start, allowed):
    seen, stack = {start}, [start]
    while stack:
        x = stack.pop()
        for y in tree[x]:
            if y in allowed and y not in seen:
                seen.add(y)
                stack.append(y)
    return seen


def completion(adj, order):
    """Der aufgefüllte Graph H: G plus alle beim Eliminieren ergänzten Kanten (ein chordaler Graph; `order` ist eine perfekte Eliminationsordnung von H)."""
    el = eliminate(adj, order)
    h = [set(a) for a in adj]
    for step in el.added:
        for u, v in step:
            h[u].add(v)
            h[v].add(u)
    return tuple(frozenset(a) for a in h)


# --- Brücke zu den chordalen Graphen (gekürzte Fassung der Demo zu Stück 4) -------------------------------------------------------------------------


def mcs_order(adj):
    """Maximale Kardinalitätssuche: immer den unbesuchten Knoten mit den meisten besuchten Nachbarn besuchen (Gleichstand: kleinster Index); Eliminationsordnung = umgekehrte Besuchsreihenfolge."""
    n = len(adj)
    weight, visited, visit = [0] * n, [False] * n, []
    for _ in range(n):
        v = max((x for x in range(n) if not visited[x]), key=lambda x: (weight[x], -x))
        visited[v] = True
        visit.append(v)
        for w in adj[v]:
            if not visited[w]:
                weight[w] += 1
    return tuple(reversed(visit))


def is_perfect_order(adj, order):
    """Rose, Tarjan und Lueker: Der früheste spätere Nachbar jedes Knotens muss alle übrigen späteren Nachbarn als Nachbarn haben."""
    pos = {v: i for i, v in enumerate(order)}
    for v in order:
        later = sorted((w for w in adj[v] if pos[w] > pos[v]), key=lambda w: pos[w])
        if len(later) >= 2 and any(w not in adj[later[0]] for w in later[1:]):
            return False
    return True


def is_chordal(adj):
    """Chordal genau dann, wenn die MCS-Ordnung perfekt ist."""
    return is_perfect_order(adj, mcs_order(adj))


def clique_number_chordal(adj):
    """ω eines chordalen Graphen: 1 plus die größte Zahl späterer Nachbarn in einer perfekten Ordnung (die MCS-Ordnung); nur für chordale Graphen korrekt."""
    order = mcs_order(adj)
    pos = {v: i for i, v in enumerate(order)}
    return 1 + max((sum(1 for w in adj[v] if pos[w] > pos[v]) for v in order), default=-1) if order else 0


# --- Bandbreite (Brücke zur Demo zur Bandbreite) ----------------------------------------------------------------------------------------------


def bandwidth_small(adj, limit=C.BANDWIDTH_MAX_N):
    """Bandbreite durch Aufzählen aller Anordnungen: kleinste größte Positionsdifferenz über die Kanten (nur kleine Graphen)."""
    n = len(adj)
    if n > limit:
        raise ValueError(f"Bandbreite nur bis n = {limit}")
    edges = [(u, v) for u in range(n) for v in adj[u] if u < v]
    if not edges:
        return 0
    best = n
    for perm in itertools.permutations(range(n)):
        pos = [0] * n
        for i, v in enumerate(perm):
            pos[v] = i
        width = max(abs(pos[u] - pos[v]) for u, v in edges)
        if width < best:
            best = width
    return best


def brute_force_treewidth(adj, limit=8):
    """Baumweite durch Aufzählen aller Eliminationsordnungen (nur n <= limit): die kleinste Breite; dient als unabhängiger Rechenweg gegen den DP."""
    n = len(adj)
    if n > limit:
        raise ValueError(f"nur bis n = {limit}")
    if n == 0:
        return 0
    return min(eliminate(adj, order).width for order in itertools.permutations(range(n)))
