"""Plotly-Figuren: Netz in der Schritt-Ansicht, Breitenkurve, Beutelbaum und die Experimente. Alle Achsen fest (fixedrange)."""

import plotly.graph_objects as go

import twd_constants as C

_FONT = dict(size=13)
BIG_GRAPH_N = 150            # ab dieser Knotenzahl werden Knoten kleiner gezeichnet und nicht mehr beschriftet
MAX_OLD_FILL_DRAWN = 1500    # früher ergänzte Kanten werden nur bis zu dieser Zahl gezeichnet


def _fix(fig, height=420, **layout):
    layout.setdefault("margin", dict(l=40, r=20, t=30, b=40))
    fig.update_layout(height=height, font=_FONT, **layout)
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _edge_trace(pos, edges, color, width, dash=None):
    xs, ys = [], []
    for u, v in edges:
        xs += [pos[u][0], pos[v][0], None]
        ys += [pos[u][1], pos[v][1], None]
    return go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=color, width=width, dash=dash), hoverinfo="skip", showlegend=False)


def build_step_figure(graph, elim, step, height=560):
    """Schritt `step` der Eliminationsordnung (0 = Anfang, n = Ende): eliminierte Knoten grau, der gerade eliminierte rot, seine Beutel-Partner orange; die dabei ergänzten Kanten
    kräftig gestrichelt, die früher ergänzten blass gestrichelt (bis zu einer Höchstzahl)."""
    n = graph.n
    step = max(0, min(step, n))
    order = elim.order
    done = set(order[:step])
    current = order[step - 1] if step > 0 else None
    bag = set(elim.bags[current]) if current is not None else set()
    colors = [C.COLOR_CURRENT if v == current else C.COLOR_BAG if v in bag else C.COLOR_DONE if v in done else C.COLOR_WAIT for v in range(n)]
    pos = graph.positions
    fig = go.Figure()
    fig.add_trace(_edge_trace(pos, graph.edges(), C.COLOR_EDGE, 1))
    old = [e for s in elim.added[:max(step - 1, 0)] for e in s]
    if old and len(old) <= MAX_OLD_FILL_DRAWN:
        fig.add_trace(_edge_trace(pos, old, C.COLOR_FILL_OLD, 1, dash="dot"))
    now = list(elim.added[step - 1]) if step > 0 else []
    if now:
        fig.add_trace(_edge_trace(pos, now, C.COLOR_FILL, 2.5, dash="dash"))
    big = n > BIG_GRAPH_N
    labelled = n <= C.STEP_VIEW_MAX_N and not big
    fig.add_trace(go.Scatter(
        x=[p[0] for p in pos], y=[p[1] for p in pos], mode="markers+text" if labelled else "markers", text=[str(i + 1) for i in range(n)] if labelled else None, textposition="middle center",
        textfont=dict(color="white", size=10), marker=dict(color=colors, size=8 if big else 22, line=dict(color="white", width=1)), hovertext=list(graph.labels), hoverinfo="text", showlegend=False))
    for name, color in (("wird jetzt eliminiert", C.COLOR_CURRENT), ("Beutel-Partner", C.COLOR_BAG), ("noch nicht eliminiert", C.COLOR_WAIT), ("eliminiert", C.COLOR_DONE)):
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", marker=dict(color=color, size=12), name=name))
    if now:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", line=dict(color=C.COLOR_FILL, width=2.5, dash="dash"), name="ergänzte Kante (Sehne)"))
    fig.add_trace(go.Scatter(x=[-1.25, 1.25], y=[-1.25, 1.25], mode="markers", marker=dict(opacity=0), hoverinfo="skip", showlegend=False))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False, scaleanchor="x", scaleratio=1)
    return _fix(fig, height, legend=dict(orientation="h", y=-0.02, x=0.5, xanchor="center"), margin=dict(l=10, r=10, t=10, b=40))


def build_width_figure(elim, step=None):
    """Beutelgröße minus 1 je Schritt der Ordnung; die Breite ist das Maximum. `step` markiert den aktuellen Schritt."""
    widths = [s - 1 for s in elim.sizes]
    xs = list(range(1, len(widths) + 1))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=widths, mode="lines+markers", line=dict(color=C.COLOR_BLUE, width=2), marker=dict(size=5), hovertemplate="Schritt %{x}: Beutel mit %{y} Partnern<extra></extra>", name="Partner beim Eliminieren"))
    top = max(widths) if widths else 0
    peak = widths.index(top) + 1 if widths else 0
    if widths:
        fig.add_trace(go.Scatter(x=[peak], y=[top], mode="markers", marker=dict(color=C.COLOR_RED, size=12, symbol="diamond"), hovertemplate="Breite %{y} bei Schritt %{x}<extra></extra>", name="Breite (Maximum)"))
        fig.add_hline(y=top, line_dash="dot", line_color="#888888")
    if step and 1 <= step <= len(widths):
        fig.add_vline(x=step, line_dash="dash", line_color=C.COLOR_CURRENT)
    fig.update_xaxes(title="Schritt der Ordnung")
    fig.update_yaxes(title="Beutelgröße − 1", rangemode="tozero")
    return _fix(fig, 300, legend=dict(orientation="h", y=1.25, x=0.5, xanchor="center"))


def tree_layout(dec, root):
    """Zeichnung des Beutelbaums: y = −Tiefe, x = Blattposition (innere Beutel mittig über ihren Kindern). Gibt (Positionen, Tiefen, Eltern) zurück."""
    k = len(dec.bags)
    nbrs = [[] for _ in range(k)]
    for a, b in dec.edges:
        nbrs[a].append(b)
        nbrs[b].append(a)
    parent, depth, children = {root: None}, {root: 0}, {i: [] for i in range(k)}
    order = [root]
    for x in order:
        for y in sorted(nbrs[x]):
            if y not in parent:
                parent[y] = x
                depth[y] = depth[x] + 1
                children[x].append(y)
                order.append(y)
    xpos, nxt = {}, [0]
    for x in reversed(order):
        if not children[x]:
            xpos[x] = nxt[0]
            nxt[0] += 1
    for x in reversed(order):
        if children[x]:
            xpos[x] = sum(xpos[c] for c in children[x]) / len(children[x])
    return {x: (xpos[x], -depth[x]) for x in order}, depth, parent


def build_bag_tree_figure(dec, root, height=520):
    """Der Beutelbaum: ein Punkt je Beutel (Größe und Farbe nach Beutelgröße, Hover mit den Knoten), Linien für die Baumkanten."""
    pos, _, _ = tree_layout(dec, root)
    fig = go.Figure()
    xs, ys = [], []
    for a, b in dec.edges:
        xs += [pos[a][0], pos[b][0], None]
        ys += [pos[a][1], pos[b][1], None]
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color="rgba(150,150,150,0.6)", width=1.5), hoverinfo="skip", showlegend=False))
    ids = sorted(pos)
    sizes = [len(dec.bags[i]) for i in ids]
    labelled = len(ids) <= 40
    fig.add_trace(go.Scatter(
        x=[pos[i][0] for i in ids], y=[pos[i][1] for i in ids], mode="markers+text" if labelled else "markers", text=[str(s) for s in sizes] if labelled else None, textfont=dict(color="white", size=10),
        marker=dict(size=[14 + 3 * s for s in sizes], color=sizes, colorscale=[[0, "#a9c4de"], [1, "#1f4e79"]], cmin=1, cmax=max(sizes) + 1, line=dict(color="white", width=1), showscale=False),
        hovertext=[f"Beutel von Knoten {i + 1}: {', '.join(str(v + 1) for v in sorted(dec.bags[i]))} ({len(dec.bags[i])} Knoten)" for i in ids], hoverinfo="text", showlegend=False))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return _fix(fig, height, margin=dict(l=10, r=10, t=10, b=10))


def build_family_figure(rows):
    """Je Familie: der bekannte Wert (senkrechter Strich), die Breite von Min-Grad und Min-Fill, die untere Schranke MMD+ und der exakte Wert (wo berechnet)."""
    names = [f"{r['name']} (n = {r['n']})" for r in rows]
    fig = go.Figure()
    series = (("known", "bekannter Wert", "#888888", "line-ns", 16), ("mindeg", "Min-Grad", "#4c78a8", "circle", 11), ("minfill", "Min-Fill", "#2F6B65", "diamond", 11), ("lower", "untere Schranke MMD+", "#e0a030", "triangle-up", 11))
    for key, label, color, symbol, size in series:
        fig.add_trace(go.Scatter(x=[r[key] for r in rows], y=names, mode="markers", name=label, marker=dict(color=color, size=size, symbol=symbol, line=dict(width=2, color=color)),
                                 hovertemplate="%{x}<extra>" + label + "</extra>"))
    ex = [r for r in rows if r["exact"] is not None]
    fig.add_trace(go.Scatter(x=[r["exact"] for r in ex], y=[f"{r['name']} (n = {r['n']})" for r in ex], mode="markers", name="exakt (DP)", marker=dict(color="rgba(0,0,0,0)", size=17, symbol="circle-open", line=dict(width=2, color="#c0504d")),
                             hovertemplate="%{x}<extra>exakt (DP)</extra>"))
    fig.update_xaxes(title="Breite bzw. Baumweite", dtick=1)
    fig.update_yaxes(autorange="reversed")
    return _fix(fig, 460, legend=dict(orientation="h", y=1.14, x=0.5, xanchor="center"), margin=dict(l=210, r=20, t=60, b=50))


def build_grid_figure(rows):
    """Gitter k × k: die Baumweite k (Gerade), Min-Fill, Min-Grad, MMD+ und die zufällige Reihenfolge (Median) über k."""
    ks = [r["k"] for r in rows]
    fig = go.Figure()
    for key, label, color, dash in (("random", "zufällige Reihenfolge (Median)", "#c0504d", None), ("mindeg", "Min-Grad", "#4c78a8", "dash"), ("minfill", "Min-Fill", "#2F6B65", None), ("lower", "untere Schranke MMD+", "#e0a030", "dot")):
        fig.add_trace(go.Scatter(x=ks, y=[r[key] for r in rows], mode="lines+markers", name=label, line=dict(color=color, width=3, dash=dash), marker=dict(size=7), hovertemplate="k = %{x}: %{y}<extra>" + label + "</extra>"))
    fig.add_trace(go.Scatter(x=ks, y=ks, mode="lines", name="Baumweite k", line=dict(color="#888888", width=2), hovertemplate="k = %{x}: Baumweite %{y}<extra></extra>"))
    fig.update_xaxes(title="Seitenlänge k des Gitters", dtick=1)
    fig.update_yaxes(title="Breite", rangemode="tozero")
    return _fix(fig, 400, legend=dict(orientation="h", y=1.22, x=0.5, xanchor="center"))


def build_small_figure(rows):
    """Je Kantenwahrscheinlichkeit: Anteil der Graphen (Prozent), in denen Min-Grad, Min-Fill und MMD+ den exakten Wert treffen, und in denen untere und obere Schranke zusammenfallen."""
    ps = [f"p = {r['p']} %" for r in rows]
    fig = go.Figure()
    for key, label, color in (("mindeg_exact", "Min-Grad exakt", "#4c78a8"), ("minfill_exact", "Min-Fill exakt", "#2F6B65"), ("lower_exact", "MMD+ exakt", "#e0a030"), ("certified", "Schranken fallen zusammen", "#8c6bb1")):
        fig.add_trace(go.Bar(x=ps, y=[100.0 * r[key] / r["samples"] for r in rows], name=label, marker_color=color, hovertemplate="%{y:.0f} %<extra>" + label + "</extra>"))
    fig.update_yaxes(title="Anteil der Graphen (%)", range=[0, 105])
    return _fix(fig, 360, barmode="group", legend=dict(orientation="h", y=1.25, x=0.5, xanchor="center"))


def build_growth_figure(rows, x_key, title):
    """Breite über der Knotenzahl: Min-Fill, Min-Grad und MMD+ (Zufallsnetz: x = Knoten der Riesenkomponente, Toronto: x = Zahl der Kreuzungen)."""
    fig = go.Figure()
    for key, label, color, dash in (("mindeg", "Min-Grad", "#4c78a8", "dash"), ("minfill", "Min-Fill", "#2F6B65", None), ("lower", "untere Schranke MMD+", "#e0a030", "dot")):
        fig.add_trace(go.Scatter(x=[r[x_key] for r in rows], y=[r[key] for r in rows], mode="lines+markers", name=label, line=dict(color=color, width=3, dash=dash), marker=dict(size=7),
                                 hovertemplate="%{x:,.0f} Knoten: %{y}<extra>" + label + "</extra>"))
    fig.update_xaxes(title=title)
    fig.update_yaxes(title="Breite", rangemode="tozero")
    return _fix(fig, 360, legend=dict(orientation="h", y=1.25, x=0.5, xanchor="center"))
