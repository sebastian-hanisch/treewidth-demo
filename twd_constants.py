"""Konstanten: Regler-Grenzen, Rechengrenzen, feste Annahmen, Farben und Presets."""

N_MIN, N_MAX, DEFAULT_N = 6, 600, 16
PCT_MIN, PCT_MAX, DEFAULT_PCT = 0, 60, 0                 # Störung in Prozent (Bedeutung je Netztyp, siehe NET_HELP)
SEED_MAX, DEFAULT_SEED = 999999, 5
SWEEP_SEEDS = tuple(range(100000, 100005))               # feste Instanzen für alle Sweeps: nie ein einzelner Seed als Befund

# Netztypen
NET_TYPES = {
    "grid": "Gitter (Straßenraster)",
    "tree": "Baum plus Zusatzkanten",
    "cycle": "Kreis plus Sehnen",
    "random": "Zufallsnetz (dünn)",
    "chordal": "Konfliktgraph von Teilstrecken",
    "toronto": "Toronto (echte Straßen)",
}
DEFAULT_NET = "grid"
NET_HELP = (
    "Gitter: ein Straßenraster mit ungefähr n Kreuzungen (Seitenlänge ⌊√n⌉); die Störung ist der Anteil zufällig gesperrter Kanten. "
    "Baum plus Zusatzkanten: ein zufälliger Baum; die Störung ist die Zahl zusätzlicher Zufallskanten in Prozent von n. "
    "Kreis plus Sehnen: ein Ring; die Störung ist die Zahl zusätzlicher Zufallssehnen in Prozent von n. "
    "Zufallsnetz: jedes Paar unabhängig, mittlerer Grad 1,5 plus Störung durch 20 (bei 60 % also 4,5). "
    "Konfliktgraph von Teilstrecken: Sendungen auf einer Linie, die Störung ist die mittlere Streckenlänge in Prozent der Linie; er ist chordal. "
    "Toronto: die n Kreuzungen, die dem Mittelpunkt am nächsten liegen (OpenStreetMap, ODbL); die Störung ist der Anteil zufällig gesperrter Kanten."
)
PCT_LABEL = "Störung (%)"

# Ordnung, mit der eliminiert wird
ORDERS = {"minfill": "Min-Fill (wenigste ergänzte Kanten)", "mindegree": "Min-Grad (wenigste Nachbarn)", "random": "zufällige Reihenfolge"}
DEFAULT_ORDER = "minfill"

# Rechengrenzen
EXACT_MAX_N = 16             # größte Knotenzahl des exakten Verfahrens (Teilmengen-DP, 2^n): bei n = 16 etwa 1 bis 2 Sekunden
BANDWIDTH_MAX_N = 8          # größte Knotenzahl der Bandbreite per Brute Force
DRAW_MAX_N = 60              # größte Knotenzahl, bis zu der der Beutelbaum gezeichnet wird
STEP_VIEW_MAX_N = 400        # größte Knotenzahl, bis zu der die Schritt-Ansicht Knoten beschriftet

# Experimente
FAMILY_GRIDS = (3, 4, 5, 6)
GRID_SIDES = (3, 4, 5, 6, 7, 8, 10, 12, 14)
GRID_RANDOM_ORDERS = 5
SMALL_N = 11
SMALL_PS = (20, 30, 50, 70)
SMALL_SAMPLES = 100
GROWTH_NS = (50, 100, 200, 400)
TORONTO_NS = (200, 400, 800, 1600, 3200, 5072)

# Farben
COLOR_DONE = "#d0d0d0"       # bereits eliminiert
COLOR_CURRENT = "#c0504d"    # der Knoten, der gerade eliminiert wird
COLOR_BAG = "#e0a030"        # seine Beutel-Partner
COLOR_WAIT = "#9fb3c8"       # noch nicht eliminiert
COLOR_EDGE = "rgba(150,150,150,0.35)"
COLOR_FILL = "#e0a030"       # ergänzte Kante
COLOR_FILL_OLD = "rgba(224,160,48,0.35)"
COLOR_GOOD = "#2F6B65"
COLOR_BLUE = "#4c78a8"
COLOR_RED = "#c0504d"

PRESETS = {
    "Lehrbeispiel (Gitter 4×4)": {"net": "grid", "n": 16, "pct": 0, "seed": 5, "order": "minfill"},
    "Gitter: die Lücke wächst": {"net": "grid", "n": 144, "pct": 0, "seed": 5, "order": "minfill"},
    "Baum: fast baumartig": {"net": "tree", "n": 30, "pct": 15, "seed": 5, "order": "minfill"},
    "Dünner Zufall: lineare Breite": {"net": "random", "n": 400, "pct": 30, "seed": 5, "order": "minfill"},
    "Toronto: wie breit ist ein echtes Netz?": {"net": "toronto", "n": 600, "pct": 0, "seed": 5, "order": "minfill"},
    "Chordal: nichts ergänzen": {"net": "chordal", "n": 40, "pct": 20, "seed": 5, "order": "minfill"},
    "Zufällige Reihenfolge: viel breiter": {"net": "grid", "n": 100, "pct": 0, "seed": 8, "order": "random"},
}
PRESET_HELP = {
    "Lehrbeispiel (Gitter 4×4)": "Ein Straßenraster mit 16 Kreuzungen: Die Baumweite ist 4, Min-Fill findet sie, der exakte Wert bestätigt es. Gut zum Durchklicken der Schritte.",
    "Gitter: die Lücke wächst": "Ein 12×12-Gitter hat die Baumweite 12; die Heuristik liegt darüber, die untere Schranke weit darunter.",
    "Baum: fast baumartig": "Ein Baum mit 30 Knoten und ein paar Zusatzkanten: Jede Zusatzkante schließt einen Kreis, die Breite steigt nur langsam.",
    "Dünner Zufall: lineare Breite": "400 Knoten, mittlerer Grad 3: Die Breite wächst bei solchen Zufallsnetzen mit der Knotenzahl, nicht mit ihrer Wurzel.",
    "Toronto: wie breit ist ein echtes Netz?": "Die 600 Kreuzungen um den Mittelpunkt des Toronto-Ausschnitts: Zwischen der unteren und der oberen Schranke bleibt eine große Lücke, die Antwort ist ein Intervall.",
    "Chordal: nichts ergänzen": "Teilstrecken auf einer Linie: Der Konfliktgraph ist chordal, es müssen keine Kanten ergänzt werden, und die Breite ist die größte Clique minus 1.",
    "Zufällige Reihenfolge: viel breiter": "Ein 10×10-Gitter (Baumweite 10), in zufälliger Reihenfolge eliminiert: Die Breite ist mehr als doppelt so groß wie die von Min-Fill.",
}
