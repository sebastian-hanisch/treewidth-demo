"""Auswertung: Einstellungen, Analyse der Hauptansicht, Experimente und Verdikte (alle Zahlen kommen aus diesen Funktionen, nie von Hand)."""

import random
import statistics
from dataclasses import dataclass

import twd_algorithm as A
import twd_constants as C
import twd_scenario as S


@dataclass(frozen=True)
class Settings:
    """Alle Regler der Seitenleiste. Immer mit Schlüsselwörtern bauen (ein eingefügtes Feld verschob früher still Werte)."""
    net: str = C.DEFAULT_NET
    n: int = C.DEFAULT_N
    pct: int = C.DEFAULT_PCT
    seed: int = C.DEFAULT_SEED
    order: str = C.DEFAULT_ORDER


@dataclass(frozen=True)
class Analysis:
    settings: Settings
    graph: S.Graph
    elim: A.Elimination            # die gewählte Ordnung
    mindeg: A.Elimination          # Min-Grad (immer berechnet)
    minfill: A.Elimination         # Min-Fill (immer berechnet)
    lower: int                     # untere Schranke MMD+
    exact: object                  # (Baumweite, optimale Ordnung) oder None (n über der Grenze)
    dec: A.Decomposition           # Zerlegung der gewählten Ordnung
    violations: list               # Verletzungen der Zerlegungs-Eigenschaften (leer = gültig)
    chordal: bool                  # ist G selbst chordal?
    completion_chordal: bool       # ist der aufgefüllte Graph chordal? (muss immer wahr sein)
    omega_completion: int          # größte Clique des aufgefüllten Graphen
    bandwidth: object              # Bandbreite (n <= BANDWIDTH_MAX_N) oder None
    components: int


def order_of(settings, adj):
    """Die gewählte Ordnung; die zufällige Reihenfolge bekommt einen eigenen Generator (der Graph bleibt beim selben Seed unverändert)."""
    rng = random.Random(settings.seed * 7919 + 13)
    return A.ORDER_FUNCS[settings.order](adj, rng)


def build_instance(settings):
    return S.build_graph(settings.net, settings.n, settings.pct, settings.seed)


def count_components(adj):
    n, seen, k = len(adj), [False] * len(adj), 0
    for s in range(n):
        if seen[s]:
            continue
        k += 1
        stack = [s]
        seen[s] = True
        while stack:
            x = stack.pop()
            for y in adj[x]:
                if not seen[y]:
                    seen[y] = True
                    stack.append(y)
    return k


def analyse(settings):
    g = build_instance(settings)
    adj = g.adj
    order = order_of(settings, adj)
    elim = A.eliminate(adj, order)
    mindeg = elim if settings.order == "mindegree" else A.eliminate(adj, A.min_degree_order(adj))
    minfill = elim if settings.order == "minfill" else A.eliminate(adj, A.min_fill_order(adj))
    exact = A.exact_treewidth(adj) if g.n <= C.EXACT_MAX_N else None
    dec = A.tree_decomposition(adj, order)
    h = A.completion(adj, order)
    return Analysis(settings, g, elim, mindeg, minfill, A.mmd_plus(adj), exact, dec, A.validate_decomposition(adj, dec.bags, dec.edges), A.is_chordal(adj), A.is_chordal(h),
                    A.clique_number_chordal(h), A.bandwidth_small(adj) if g.n <= C.BANDWIDTH_MAX_N else None, count_components(adj))


def med(xs):
    return statistics.median(xs)


def _i(x):
    return f"{x:,.0f}".replace(",", ".")


def _f(x, digits=1):
    return f"{x:.{digits}f}".replace(".", ",")


def best_upper(a):
    """Beste obere Schranke der beiden Heuristiken und welche sie liefert."""
    if a.minfill.width <= a.mindeg.width:
        return a.minfill.width, "Min-Fill"
    return a.mindeg.width, "Min-Grad"


# --- Verdikt der Hauptansicht -----------------------------------------------------------------------------------------------------------------

def verdict_main(a):
    """(Art, Text) zur Kernfrage: Wie baumartig ist dieser Graph, und wie sicher ist die Aussage?"""
    name = C.ORDERS[a.settings.order]
    ub, who = best_upper(a)
    chosen = a.elim.width
    extra = ""
    if chosen > ub:
        extra = f" Die gewählte Reihenfolge ({name}) ist mit Breite {chosen} um {chosen - ub} breiter als {who}."
    if a.exact is not None:
        tw = a.exact[0]
        gap = f"{who} trifft den Wert" if ub == tw else f"{who} liegt mit {ub} um {ub - tw} darüber"
        return "success", (f"Die Baumweite ist **{tw}** (exakt, Teilmengen-DP über alle 2^{a.graph.n} Teilmengen). {gap}; die untere Schranke MMD+ ist {a.lower}.{extra}")
    if a.chordal and a.minfill.fill == 0:
        return "success", (f"Der Graph ist chordal: Min-Fill ergänzt keine Kante, die Baumweite ist **{a.minfill.width}** (größte Clique minus 1, exakt).{extra}")
    if ub == a.lower:
        return "success", (f"Die Baumweite ist **{ub}**: obere Schranke ({who}) und untere Schranke (MMD+) fallen zusammen.{extra}")
    return "info", (f"Die Baumweite liegt zwischen **{a.lower}** (untere Schranke MMD+) und **{ub}** (obere Schranke, {who}); mehr lässt sich hier nicht sagen, "
                    f"denn der exakte Wert wird nur bis n = {C.EXACT_MAX_N} berechnet.{extra}")


# --- Experiment 1: Familien -------------------------------------------------------------------------------------------------------------------

def family_graphs():
    """Graphen mit bekannter Baumweite: (Name, Graph, bekannter Wert)."""
    out = [("Baum (20 Knoten)", S.random_tree(20, 1), 1), ("Kreis C12", S.ring_graph(12), 2)]
    out += [(f"Gitter {k}×{k}", S.exact_grid(k), k) for k in C.FAMILY_GRIDS]
    out += [("vollständiger Graph K8", S.complete_graph(8), 7), ("K_{3,5}", S.complete_bipartite_graph(3, 5), 3), ("Petersen-Graph", S.petersen_graph(), 4),
            ("Hyperwürfel Q4", S.hypercube_graph(4), 6)]
    return out


def family_rows():
    """Je Familie: bekannter Wert, Breite von Min-Grad und Min-Fill, untere Schranke MMD+ und (bis zur Grenze) der exakte Wert aus dem DP."""
    rows = []
    for name, g, known in family_graphs():
        md = A.eliminate(g.adj, A.min_degree_order(g.adj)).width
        mf = A.eliminate(g.adj, A.min_fill_order(g.adj)).width
        lb = A.mmd_plus(g.adj)
        exact = A.exact_treewidth(g.adj)[0] if g.n <= C.EXACT_MAX_N else None
        rows.append({"name": name, "n": g.n, "known": known, "mindeg": md, "minfill": mf, "lower": lb, "exact": exact, "certified": lb == min(md, mf)})
    return rows


def verdict_families(rows):
    """(Art, Text): wo die Heuristiken den bekannten Wert treffen, wo die untere Schranke ihn beweist."""
    hit = [r for r in rows if min(r["mindeg"], r["minfill"]) == r["known"]]
    miss = [r for r in rows if min(r["mindeg"], r["minfill"]) != r["known"]]
    certified = [r for r in rows if r["certified"] and min(r["mindeg"], r["minfill"]) == r["known"]]
    text = (f"Min-Grad oder Min-Fill treffen den bekannten Wert bei {len(hit)} von {len(rows)} Familien"
            + (f"; ausgenommen {', '.join(r['name'] for r in miss)}" if miss else "")
            + f". Die untere Schranke MMD+ beweist ihn bei {len(certified)} davon ({', '.join(r['name'] for r in certified)}); "
            + (f"bei „{max(rows, key=lambda r: r['known'] - r['lower'])['name']}“ liegt sie mit {max(r['known'] - r['lower'] for r in rows)} am weitesten unter dem Wert."))
    return "info", text


# --- Experiment 2: Gitter ---------------------------------------------------------------------------------------------------------------------

def grid_rows(sides=C.GRID_SIDES, orders=C.GRID_RANDOM_ORDERS):
    """Gitter k × k (Baumweite k): Breite von Min-Grad, Min-Fill, MMD+ und zufälliger Reihenfolge (Median über `orders` feste Reihenfolgen)."""
    rows = []
    for k in sides:
        g = S.exact_grid(k)
        md = A.eliminate(g.adj, A.min_degree_order(g.adj)).width
        mf = A.eliminate(g.adj, A.min_fill_order(g.adj)).width
        rnd = [A.eliminate(g.adj, A.random_order(g.n, random.Random(seed))).width for seed in range(orders)]
        rows.append({"k": k, "n": g.n, "mindeg": md, "minfill": mf, "lower": A.mmd_plus(g.adj), "random": med(rnd)})
    return rows


def verdict_grid(rows):
    """(Art, Text): ab welcher Größe die Heuristik über k liegt und wie weit unter k die untere Schranke bleibt."""
    def best(r):
        return min(r["mindeg"], r["minfill"])

    first = next((i for i, r in enumerate(rows) if best(r) > r["k"]), None)
    last = rows[-1]
    if first is None:
        lead = "Min-Grad und Min-Fill treffen k bei allen Größen. "
    elif first == 0:
        lead = "Die Heuristiken liegen schon beim kleinsten Gitter über k. "
    else:
        prev, cur = rows[first - 1]["k"], rows[first]
        lead = (f"Bis zum {prev}×{prev}-Gitter treffen Min-Grad und Min-Fill die Baumweite k, ab dem {cur['k']}×{cur['k']}-Gitter liegen sie darüber "
                f"({best(cur)} statt {cur['k']}). ")
    text = (lead + f"Beim {last['k']}×{last['k']}-Gitter sind es {last['minfill']} (Min-Fill) und {last['mindeg']} (Min-Grad) statt {last['k']}, eine zufällige Reihenfolge braucht im Median "
            f"{_f(last['random'], 0)}; die untere Schranke MMD+ bleibt bei {last['lower']}.")
    return "info", text


# --- Experiment 3: kleine Zufallsgraphen ------------------------------------------------------------------------------------------------------

def small_rows(n=C.SMALL_N, ps=C.SMALL_PS, samples=C.SMALL_SAMPLES):
    """Je Kantenwahrscheinlichkeit `samples` feste Zufallsgraphen mit n Knoten: Median der Baumweite, wie oft Min-Grad, Min-Fill und MMD+ den exakten Wert treffen, größte Lücken und wie oft die Schranken
    zusammenfallen (dann ist der Wert ohne den DP bewiesen). `ordered`: lb <= tw <= ub gilt in jedem Graphen."""
    rows = []
    for p in ps:
        tws, gd, gf, gl, cert, ordered = [], [], [], [], 0, True
        for s in range(samples):
            adj = S.random_graph_p(n, p, s * 13 + 5)
            tw = A.exact_treewidth(adj)[0]
            d = A.eliminate(adj, A.min_degree_order(adj)).width
            f = A.eliminate(adj, A.min_fill_order(adj)).width
            lb = A.mmd_plus(adj)
            ordered = ordered and lb <= tw <= min(d, f)
            tws.append(tw)
            gd.append(d - tw)
            gf.append(f - tw)
            gl.append(tw - lb)
            cert += lb == min(d, f)
        rows.append({"p": p, "tw": med(tws), "mindeg_exact": sum(1 for x in gd if x == 0), "minfill_exact": sum(1 for x in gf if x == 0), "lower_exact": sum(1 for x in gl if x == 0),
                     "mindeg_gap": max(gd), "minfill_gap": max(gf), "lower_gap": max(gl), "lower_gap_mean": statistics.mean(gl), "certified": cert, "ordered": ordered, "samples": samples})
    return rows


def verdict_small(rows):
    """(Art, Text): auf kleinen Graphen sind die Heuristiken fast immer exakt, Min-Fill besser als Min-Grad; die Schranken fallen oft zusammen."""
    k = rows[0]["samples"]
    worst = min(rows, key=lambda r: r["minfill_exact"])
    best_gap = max(max(r["mindeg_gap"], r["minfill_gap"]) for r in rows)
    text = (f"Min-Fill trifft den exakten Wert in {sum(r['minfill_exact'] for r in rows)} von {k * len(rows)} Graphen, Min-Grad in {sum(r['mindeg_exact'] for r in rows)}; "
            f"am schwersten ist p = {worst['p']} % ({worst['minfill_exact']} von {k}). Die Lücke beträgt nie mehr als {best_gap}. "
            f"Die untere Schranke MMD+ trifft in {sum(r['lower_exact'] for r in rows)} von {k * len(rows)} Graphen, und in {sum(r['certified'] for r in rows)} fallen untere und obere Schranke zusammen: "
            "dort ist der Wert auch ohne den DP bewiesen.")
    if not all(r["ordered"] for r in rows):
        return "warning", text + " ACHTUNG: untere ≤ exakt ≤ obere Schranke wurde verletzt."
    return "info", text


# --- Experiment 4: Wachstum -------------------------------------------------------------------------------------------------------------------

def growth_rows(ns=C.GROWTH_NS, seeds=C.SWEEP_SEEDS):
    """Zufallsnetz mit mittlerem Grad 3 (Riesenkomponente): Breite von Min-Fill, Min-Grad und MMD+ über n, Median über die festen Graphen."""
    rows = []
    for n in ns:
        data = {k: [] for k in ("giant", "minfill", "mindeg", "lower")}
        for seed in seeds:
            adj = S.giant_component(S.random_graph(n, 30, seed).adj)
            data["giant"].append(len(adj))
            data["minfill"].append(A.eliminate(adj, A.min_fill_order(adj)).width)
            data["mindeg"].append(A.eliminate(adj, A.min_degree_order(adj)).width)
            data["lower"].append(A.mmd_plus(adj))
        rows.append({"n": n, "giant": med(data["giant"]), "minfill": med(data["minfill"]), "mindeg": med(data["mindeg"]), "lower": med(data["lower"]),
                     "ratio": med(m / g for m, g in zip(data["minfill"], data["giant"]))})
    return rows


def toronto_rows(ns=C.TORONTO_NS):
    """Die n Kreuzungen um den Mittelpunkt des Toronto-Ausschnitts: Breite von Min-Fill, Min-Grad und MMD+."""
    rows = []
    for n in ns:
        g = S.toronto_graph(n, 0, 0)
        rows.append({"n": g.n, "m": g.m, "minfill": A.eliminate(g.adj, A.min_fill_order(g.adj)).width, "mindeg": A.eliminate(g.adj, A.min_degree_order(g.adj)).width,
                     "lower": A.mmd_plus(g.adj)})
    return rows


def verdict_growth(random_rows, toronto):
    """(Art, Text): lineare Breite bei Zufallsnetzen; beim echten Netz nur ein Intervall."""
    lo, hi = min(r["ratio"] for r in random_rows), max(r["ratio"] for r in random_rows)
    last = toronto[-1]
    text = (f"Beim Zufallsnetz mit mittlerem Grad 3 wächst die Breite etwa linear: {_f(lo, 2)} bis {_f(hi, 2)} mal so viel wie die Knotenzahl der Riesenkomponente (n = {random_rows[0]['n']} bis {random_rows[-1]['n']}). "
            f"Beim Toronto-Ausschnitt wächst die obere Schranke von {toronto[0]['minfill']} bei {toronto[0]['n']} Kreuzungen auf {last['minfill']} bei {_i(last['n'])}, die untere bleibt bei {last['lower']}: "
            f"die Baumweite des ganzen Netzes liegt zwischen {last['lower']} und {min(last['minfill'], last['mindeg'])}, mehr sagt die Demo nicht.")
    return "info", text
