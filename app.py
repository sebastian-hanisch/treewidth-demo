"""Baumweite: Eliminationsordnung und Baumzerlegung - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Fünftes Stück der Härte-und-Struktur-Reihe: Wie baumartig ist ein Netz? Eine Eliminationsordnung füllt fehlende Kanten auf, ihre Breite ist eine obere Schranke für die Baumweite,
ihre Beutel bilden eine Baumzerlegung. Dazu eine untere Schranke, der exakte Wert für kleine Netze und ein echtes Straßennetz.

Lauffähig mit: streamlit run app.py
"""

import pandas as pd
import streamlit as st

import twd_algorithm as A
import twd_constants as C
import twd_evaluation as ev
from twd_layout import dunkles_design, kopf_css
from twd_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from twd_visualization import (
    build_bag_tree_figure,
    build_family_figure,
    build_grid_figure,
    build_growth_figure,
    build_small_figure,
    build_step_figure,
    build_width_figure,
)

st.set_page_config(page_title="Baumweite – Sebastian Hanisch", layout="wide")


def _i(x):
    """Ganze Zahl mit Punkt als Tausendertrenner."""
    return f"{x:,.0f}".replace(",", ".")


def _show(verdict):
    kind, text = verdict
    {"success": st.success, "info": st.info, "warning": st.warning}[kind](text)


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return ev.analyse(settings)


@st.cache_data(show_spinner=False)
def _families():
    return ev.family_rows()


@st.cache_data(show_spinner=False)
def _grids():
    return ev.grid_rows()


@st.cache_data(show_spinner=False)
def _smalls():
    return ev.small_rows()


@st.cache_data(show_spinner=False)
def _growth():
    return ev.growth_rows(), ev.toronto_rows()


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in twd_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🌳 Baumweite: Eliminationsordnung und Baumzerlegung")
st.markdown(
    """
Wie **baumartig** ist ein Netz? Auf einem Baum sind viele schwere Aufgaben leicht, auf einem Kreis kaum schwerer, auf einem dichten Gitter nicht mehr. Ein Maß dafür ist die **Baumweite**: die kleinste Zahl, die man braucht, um das Netz in einen **Baum aus kleinen Beuteln** zu zerlegen. Sie ist selbst schwer zu berechnen; diese Demo zeigt, wie man sie von oben **eingrenzt** (eine Eliminationsordnung, die fehlende Kanten ergänzt), von unten (eine untere Schranke), **exakt für kleine Netze** und wie breit ein **echtes Straßennetz** ist.

Das ist das fünfte Stück der **Härte-und-Struktur-Reihe**: Das vierte Stück ordnete Graphen ohne Kreis ohne Sehne (chordal); hier werden fehlende Sehnen **ergänzt**, und die Beutel der Ordnung bilden die Zerlegung, auf der das nächste Stück rechnet. Anders als die Fall-Demos zeigt diese Demo ein Verfahren an einem wachsenden Beispiel. Weiter unten: die vier Experimente **🔬**, **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert die Baumzerlegung", expanded=True):
    st.markdown(
        """
1. **Eliminieren:** Knoten für Knoten in einer gewählten Reihenfolge entfernen. Vor dem Entfernen werden seine noch vorhandenen Nachbarn **paarweise verbunden** (Auffüllen), damit der Rest dieselben Wege behält. Der Knoten samt diesen Nachbarn ist sein **Beutel**.
2. **Breite:** die größte Beutelgröße minus 1. Die **Baumweite** ist die kleinste Breite über alle Reihenfolgen; jede Reihenfolge liefert also eine **obere Schranke**.
3. **Zerlegung:** Jeder Beutel hängt am Beutel seines frühesten späteren Nachbarn. So entsteht ein **Baum aus Beuteln**, in dem jede Kante in einem Beutel liegt und jeder Knoten in einem zusammenhängenden Teilbaum von Beuteln.

| Begriff | Bedeutung |
|---|---|
| **Min-Grad** | immer den Knoten mit den wenigsten Nachbarn eliminieren |
| **Min-Fill** | immer den Knoten eliminieren, dessen Nachbarn die wenigsten fehlenden Kanten haben |
| **MMD+** | untere Schranke: Knoten kleinsten Grades in einen Nachbarn kontrahieren; der größte dabei gesehene kleinste Grad |
| **exakt** | Teilmengen-DP über alle Teilmengen der Knoten (nur bis n = 16) |
| **Sehne** | eine beim Auffüllen ergänzte Kante; der aufgefüllte Graph ist chordal |
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Netz**")
    net = st.selectbox("Netztyp", list(C.NET_TYPES), format_func=C.NET_TYPES.get, key="net_select", help=C.NET_HELP)
    n = st.slider("Knoten n", *bounds("n_slider"), key="n_slider", help="Zahl der Knoten (Gitter: ungefähr, Seitenlänge ⌊√n⌉; Toronto: die n Kreuzungen um den Mittelpunkt, höchstens so viele, wie der Ausschnitt hat).")
    pct = st.slider(C.PCT_LABEL, *bounds("pct_slider"), key="pct_slider", help=C.NET_HELP)
    seed = st.number_input("Zufalls-Seed des Netzes", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neues Netz erzeugen", width="stretch", on_click=randomize_seed)
    st.markdown("**Ordnung**")
    order = st.radio("Ordnungsverfahren", list(C.ORDERS), format_func=C.ORDERS.get, key="order_radio",
                     help="Mit welchem Verfahren eliminiert wird. Min-Fill und Min-Grad sind Heuristiken ohne Garantie; die zufällige Reihenfolge zeigt, wie viel die Heuristik bringt.")

sync_query_params({"net_select": net, "n_slider": int(n), "pct_slider": int(pct), "seed_input": int(seed), "order_radio": order})

settings = ev.Settings(net=net, n=int(n), pct=int(pct), seed=int(seed), order=order)
with st.spinner("Rechne..."):
    a = _analysis(settings)
g = a.graph
ub, who = ev.best_upper(a)

tab_elim, tab_dec = st.tabs(["✂️ Eliminieren", "🌳 Zerlegung"])

# --- Tab 1: Eliminieren -----------------------------------------------------------------------------------------------------------------------

with tab_elim:
    st.markdown("## ✂️ Wie breit wird die Ordnung?")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Breite der Ordnung", _i(a.elim.width), delta=f"{_i(a.elim.fill)} Sehnen ergänzt", delta_color="off",
              help="Größte Beutelgröße minus 1: eine obere Schranke für die Baumweite.")
    m2.metric("Beste obere Schranke", _i(ub), delta=who, delta_color="off", help="Die kleinere Breite von Min-Fill und Min-Grad.")
    m3.metric("Untere Schranke", _i(a.lower), delta="MMD+", delta_color="off", help="Min-Grad-Kontraktion: Die Baumweite ist mindestens so groß.")
    m4.metric("Baumweite exakt", _i(a.exact[0]) if a.exact else "–", delta=("Teilmengen-DP" if a.exact else f"nur bis n = {C.EXACT_MAX_N}"), delta_color="off",
              help="Exakter Wert durch Teilmengen-DP über alle 2^n Teilmengen; nur für kleine Netze berechnet.")
    st.caption(f"{_i(g.n)} Knoten, {_i(g.m)} Kanten, {_i(a.components)} Komponente{'n' if a.components != 1 else ''}"
               + ("; der Graph ist chordal." if a.chordal else "; der Graph ist nicht chordal."))
    step = st.slider("Schritt der Eliminationsordnung", 0, g.n, min(1, g.n), key=f"step_slider_{g.n}",
                     help="Schritt k: Die ersten k Knoten der Ordnung sind eliminiert; der zuletzt eliminierte ist rot, sein Beutel orange, die dabei ergänzten Kanten gestrichelt.")
    st.plotly_chart(build_step_figure(g, a.elim, step), width="stretch", key="graph_step")
    if step == 0:
        st.caption("Noch nichts eliminiert.")
    else:
        cur = a.elim.order[step - 1]
        bag = a.elim.bags[cur]
        added = a.elim.added[step - 1]
        st.caption(f"Schritt {step}: Knoten {cur + 1} hat {len(bag)} noch vorhandene Nachbarn" + (f" ({', '.join(str(w + 1) for w in bag[:12])}{' …' if len(bag) > 12 else ''})" if bag else "")
                   + f"; sein Beutel hat {len(bag) + 1} Knoten. " + (f"Dafür wurden {len(added)} Kante{'n' if len(added) != 1 else ''} ergänzt." if added else "Es musste keine Kante ergänzt werden."))
    st.plotly_chart(build_width_figure(a.elim, step), width="stretch", key="width_curve")
    with st.expander("Heuristiken im Vergleich"):
        st.dataframe(pd.DataFrame({
            "Ordnung": ["Min-Fill", "Min-Grad", C.ORDERS[settings.order] + " (gewählt)"], "Breite": [a.minfill.width, a.mindeg.width, a.elim.width],
            "ergänzte Kanten": [a.minfill.fill, a.mindeg.fill, a.elim.fill]}), hide_index=True, width="stretch")

    st.markdown("## ❓ Kernfrage: Wie baumartig ist dieses Netz, und wie sicher ist die Aussage?")
    _show(ev.verdict_main(a))

# --- Tab 2: Zerlegung -------------------------------------------------------------------------------------------------------------------------

with tab_dec:
    st.markdown("## 🌳 Der Baum aus Beuteln")
    if not a.violations:
        st.success("Die Zerlegung ist gültig: ✅ jeder Knoten liegt in einem Beutel, ✅ jede Kante liegt in einem Beutel, ✅ die Beutel bilden einen Baum, ✅ die Beutel mit einem Knoten sind zusammenhängend.")
    else:
        st.error(f"Die Zerlegung ist NICHT gültig: {a.violations[:5]}. Das darf nicht passieren, bitte melden.")
    if g.n <= C.DRAW_MAX_N:
        st.plotly_chart(build_bag_tree_figure(a.dec, a.elim.order[-1]), width="stretch", key="bag_tree")
        st.caption("Ein Punkt je Beutel; Größe und Farbe zeigen die Beutelgröße (die Zahl im Punkt), beim Überfahren erscheinen die Knoten. Jeder Beutel hängt am Beutel seines frühesten späteren Nachbarn; "
                   "bei mehreren Komponenten sind deren Wurzeln der Reihe nach verbunden.")
    else:
        st.info(f"Der Beutelbaum wird bis n = {C.DRAW_MAX_N} gezeichnet; bei n = {g.n} gibt es {_i(len(a.dec.bags))} Beutel, der größte hat {_i(max(len(b) for b in a.dec.bags))} Knoten.")
    sizes = sorted((len(b) for b in a.dec.bags), reverse=True)
    st.caption(f"Breite der Zerlegung: {_i(a.dec.width)} (größter Beutel {_i(sizes[0]) if sizes else 0} Knoten). Auf dieser Zerlegung rechnet das nächste Stück der Reihe die schweren Aufgaben in 2^Breite mal n Schritten.")

st.markdown("---")

# --- Experiment 1 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 1: Treffen die Heuristiken die bekannten Werte?")
st.caption("Familien mit bekannter Baumweite: Baum 1, Kreis 2, Gitter k, vollständiger Graph n − 1, K_{a,b} min(a, b), Petersen-Graph 4, Hyperwürfel Q4 6. Der rote Ring ist der exakte Wert aus dem Teilmengen-DP, wo er berechnet wurde (n ≤ 16).")
with st.spinner("Rechne die Familien..."):
    rows1 = _families()
st.plotly_chart(build_family_figure(rows1), width="stretch", key="family_chart")
_show(ev.verdict_families(rows1))

st.markdown("---")

# --- Experiment 2 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 2: Die Lücke auf dem Gitter")
st.caption("Gitter k × k haben die Baumweite k. Verglichen werden Min-Fill, Min-Grad, die untere Schranke MMD+ und eine zufällige Reihenfolge (Median über 5 feste Reihenfolgen).")
rows2 = _grids()
st.plotly_chart(build_grid_figure(rows2), width="stretch", key="grid_chart")
_show(ev.verdict_grid(rows2))

st.markdown("---")

# --- Experiment 3 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 3: Kleine Zufallsnetze, exakt gegen Heuristiken")
st.caption(f"Je Kantenwahrscheinlichkeit {C.SMALL_SAMPLES} feste Zufallsgraphen mit {C.SMALL_N} Knoten; der exakte Wert kommt aus dem Teilmengen-DP. „Schranken fallen zusammen“ heißt: untere Schranke gleich bester oberer Schranke, der Wert ist dann ohne den DP bewiesen.")
with st.spinner("Rechne den exakten Wert (Teilmengen-DP)..."):
    rows3 = _smalls()
st.plotly_chart(build_small_figure(rows3), width="stretch", key="small_chart")
_show(ev.verdict_small(rows3))
with st.expander("Tabelle zu Experiment 3"):
    st.dataframe(pd.DataFrame({
        "p (%)": [r["p"] for r in rows3], "Baumweite (Median)": [r["tw"] for r in rows3], "Min-Grad exakt": [r["mindeg_exact"] for r in rows3], "Min-Fill exakt": [r["minfill_exact"] for r in rows3],
        "MMD+ exakt": [r["lower_exact"] for r in rows3], "größte Lücke MMD+": [r["lower_gap"] for r in rows3], "Schranken fallen zusammen": [r["certified"] for r in rows3]}), hide_index=True, width="stretch")

st.markdown("---")

# --- Experiment 4 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 4: Wie wächst die Breite, und wie breit ist ein echtes Netz?")
st.caption("Links dünne Zufallsnetze (mittlerer Grad 3, Riesenkomponente, Median über 5 feste Graphen), rechts die Kreuzungen um den Mittelpunkt des Toronto-Ausschnitts (echte OpenStreetMap-Daten aus der Demo zur Breitensuche, 5 072 Kreuzungen insgesamt).")
with st.spinner("Rechne das Wachstum..."):
    grow, tor = _growth()
c1, c2 = st.columns(2)
c1.markdown("**Zufallsnetz, mittlerer Grad 3**")
c1.plotly_chart(build_growth_figure(grow, "giant", "Knoten der Riesenkomponente"), width="stretch", key="growth_random")
c2.markdown("**Toronto-Ausschnitt**")
c2.plotly_chart(build_growth_figure(tor, "n", "Kreuzungen (die n nächsten zum Mittelpunkt)"), width="stretch", key="growth_toronto")
_show(ev.verdict_growth(grow, tor))
with st.expander("Tabelle zu Experiment 4"):
    st.dataframe(pd.DataFrame({
        "Netz": ["Zufall"] * len(grow) + ["Toronto"] * len(tor), "Knoten": [r["giant"] for r in grow] + [r["n"] for r in tor], "Min-Fill": [r["minfill"] for r in grow] + [r["minfill"] for r in tor],
        "Min-Grad": [r["mindeg"] for r in grow] + [r["mindeg"] for r in tor], "MMD+": [r["lower"] for r in grow] + [r["lower"] for r in tor]}), hide_index=True, width="stretch")

st.markdown("---")

# --- Brücken -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🔗 Brücken: chordale Graphen und die Bandbreite")
b1, b2, b3, b4 = st.columns(4)
b1.metric("Aufgefüllter Graph chordal?", "Ja" if a.completion_chordal else "Nein", help="Der Graph mit allen ergänzten Kanten ist immer chordal; die Ordnung ist für ihn eine perfekte Eliminationsordnung.")
b2.metric("ω des aufgefüllten Graphen", _i(a.omega_completion), delta=("= Breite + 1" if a.omega_completion == a.elim.width + 1 else "≠ Breite + 1"), delta_color="off",
          help="Die größte Clique des aufgefüllten Graphen ist ein größter Beutel: Breite + 1.")
b3.metric("Eigener Graph chordal?", "Ja" if a.chordal else "Nein", delta=("nichts ergänzt" if a.elim.fill == 0 else f"{_i(a.elim.fill)} Sehnen ergänzt"), delta_color="off",
          help="Bei Min-Fill gilt: Es werden genau dann keine Kanten ergänzt, wenn der Graph chordal ist.")
b4.metric("Bandbreite", _i(a.bandwidth) if a.bandwidth is not None else "–", delta=("Baumweite ≤ Bandbreite" if a.bandwidth is not None else f"nur bis n = {C.BANDWIDTH_MAX_N}"), delta_color="off",
          help="Kleinste größte Positionsdifferenz über die Kanten (Brute Force über alle Anordnungen): Die Baumweite ist nie größer.")
if a.completion_chordal and a.omega_completion == a.elim.width + 1:
    st.success(f"Der aufgefüllte Graph ist chordal, und seine größte Clique hat {_i(a.omega_completion)} Knoten, genau Breite + 1: Die Beutel der Ordnung sind die Cliquen des vierten Stücks. "
               + ("Der Graph war schon chordal, es wurde nichts ergänzt." if a.elim.fill == 0 else f"Dafür wurden {_i(a.elim.fill)} Kanten ergänzt."))
else:
    st.error("Der aufgefüllte Graph ist nicht chordal oder seine Clique passt nicht zur Breite: Das darf nicht passieren, bitte melden.")
if a.bandwidth is not None and a.exact is not None:
    st.caption(f"Baumweite {a.exact[0]} ≤ Bandbreite {a.bandwidth}: " + ("erfüllt." if a.exact[0] <= a.bandwidth else "VERLETZT, bitte melden."))

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    f"""
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Heuristiken ohne Garantie** | Min-Grad und Min-Fill liefern nur obere Schranken; auf Gittern ab 7×7 liegen sie über dem Wert, und die Lücke wächst mit der Größe. | – |
| **Untere Schranke einfach** | MMD+ ist auf Gittern und echten Straßennetzen weit unter dem Wert (Toronto: nur 6 bei oberer Schranke 50). Stärkere Schranken und exakte Verfahren (PID-Algorithmus von Tamaki, Wettbewerb PACE) gibt es, sie sind hier nur Einordnung. | – |
| **Exakt nur klein** | Der Teilmengen-DP braucht 2^n Zustände: hier bis n = {C.EXACT_MAX_N} (etwa ein bis zwei Sekunden). | – |
| **Ungerichtet, ohne Gewichte** | Beim Toronto-Ausschnitt zählen nur die Kreuzungen und Straßenstücke; Einbahnstraßen, Längen und Zeiten fehlen. Die Baumweite hängt auch davon ab, wie dicht digitalisiert wurde. | – |
| **Ausschnitt, nicht die Stadt** | Der Ausschnitt hat 5 072 Kreuzungen im Umkreis von 1 km; die Breite eines größeren Netzes kann anders wachsen. | – |
| **Baumweite ist ein Strukturmaß** | Eine kleine Breite verspricht kleine Beutel, aber noch keine schnelle Lösung der Aufgabe; das zeigt erst das nächste Stück. | Dynamische Programmierung auf der Baumzerlegung |
| **Synthetische Netze** | Die Zufallsnetze und Gitter sind erzeugt; echt ist nur der Toronto-Ausschnitt. | – |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Baumzerlegung.** Gegeben ein ungerichteter Graph $G = (V, E)$. Eine Baumzerlegung ist ein Baum $T$, dessen Knoten Teilmengen $B_t \subseteq V$ (Beutel) sind, mit

$$\bigcup_{t} B_t = V, \qquad \forall \{u, v\} \in E\ \exists t: \{u, v\} \subseteq B_t,$$

und für jeden Knoten $v$ bilden die Beutel, die $v$ enthalten, einen zusammenhängenden Teilbaum von $T$. Ihre **Breite** ist $\max_t |B_t| - 1$, die **Baumweite** $\operatorname{tw}(G)$ die kleinste Breite über alle Zerlegungen.

**Eliminationsordnung.** Für eine Reihenfolge $v_1, \dots, v_n$ sei $G_0 = G$ und $G_i$ der Graph, der aus $G_{i-1}$ entsteht, indem die Nachbarn $N_i$ von $v_i$ paarweise verbunden und $v_i$ gelöscht wird. Der Beutel von $v_i$ ist $B_i = \{v_i\} \cup N_i$, die Breite der Ordnung

$$w(\pi) = \max_i |N_i|, \qquad \operatorname{tw}(G) = \min_\pi w(\pi).$$

Die Beutel bilden mit der Kante von $B_i$ zum Beutel des frühesten Knotens von $N_i$ eine Baumzerlegung der Breite $w(\pi)$. Der aufgefüllte Graph $H \supseteq G$ ist chordal, $\pi$ ist für ihn eine perfekte Eliminationsordnung, und

$$\omega(H) = w(\pi) + 1, \qquad \operatorname{tw}(G) = \min_{H \supseteq G \text{ chordal}} \omega(H) - 1.$$

**Untere Schranke.** Ist $G'$ aus $G$ durch Kontraktion von Kanten entstanden (ein Minor), so gilt $\operatorname{tw}(G') \le \operatorname{tw}(G)$, und die Baumweite ist mindestens der kleinste Grad:

$$\operatorname{tw}(G) \ge \delta(G') \quad \text{für jeden Minor } G' \text{ von } G.$$

MMD+ kontrahiert immer einen Knoten kleinsten Grades in einen Nachbarn mit den wenigsten gemeinsamen Nachbarn und merkt sich den größten dabei gesehenen kleinsten Grad.

**Exakter Wert.** Für eine Knotenmenge $S$ sei $Q(S, v)$ die Menge der Knoten außerhalb von $S \cup \{v\}$, die von $v$ über Knoten in $S$ erreichbar sind. Dann gilt

$$f(S) = \min_{v \in S} \max\bigl(f(S \setminus \{v\}),\ |Q(S \setminus \{v\}, v)|\bigr), \qquad f(\emptyset) = 0,$$

und $\operatorname{tw}(G) = f(V)$. Der Aufwand ist $O(2^n \cdot n)$ Zustandsauswertungen.

**Bekannte Werte.** Ein Baum hat die Baumweite 1, ein Kreis 2, ein $k \times k$-Gitter $k$, der vollständige Graph $K_n$ den Wert $n - 1$ und $K_{a,b}$ den Wert $\min(a, b)$. Für die Bandbreite $\operatorname{bw}(G)$ gilt $\operatorname{tw}(G) \le \operatorname{bw}(G)$.

**Annahmen.**

| Annahme | Inhalt | Wer setzt an |
|---|---|---|
| Ungerichtet, einfach | keine Schleifen, keine Mehrfachkanten, keine Richtungen | – |
| Heuristik | die Ordnung ist nicht optimal, nur eine obere Schranke | – |
| Schritte statt Laufzeit | die Experimente messen Breiten, keine Laufzeiten | – |

**Literatur.** Alle Angaben sind vor dem Zitieren geprüft:
- Bodlaender, H. L. (1993). *A tourist guide through treewidth.* Acta Cybernetica 11(1–2), 1–21.
- Arnborg, S., Corneil, D. G., & Proskurowski, A. (1987). *Complexity of finding embeddings in a k-tree.* SIAM Journal on Algebraic and Discrete Methods 8(2), 277–284.
- Bodlaender, H. L., Fomin, F. V., Koster, A. M. C. A., Kratsch, D., & Thilikos, D. M. (2012). *On exact algorithms for treewidth.* ACM Transactions on Algorithms 9(1), Art. 12.
- Bodlaender, H. L., & Koster, A. M. C. A. (2011). *Treewidth computations II. Lower bounds.* Information and Computation 209(7), 1103–1119.
- Tamaki, H. (2017). *Positive-instance driven dynamic programming for treewidth.* ESA 2017.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
