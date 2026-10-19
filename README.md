# Baumweite: Eliminationsordnung und Baumzerlegung – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-treewidth-demo.streamlit.app/)** -->

Fünftes Stück der **Härte-und-Struktur-Reihe** der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“. Die Reihe fragt, welche Struktur ein auf Graphen schweres Problem leicht macht. Die ersten drei Stücke ([bron-kerbosch-demo](https://github.com/sebastian-hanisch/bron-kerbosch-demo), [max-clique-demo](https://github.com/sebastian-hanisch/max-clique-demo), [vertex-cover-demo](https://github.com/sebastian-hanisch/vertex-cover-demo)) suchen Cliquen und Überdeckungen auf beliebigen Graphen, das vierte ([chordal-graphs-demo](https://github.com/sebastian-hanisch/chordal-graphs-demo)) zeigt, dass eine perfekte Eliminationsordnung alle vier Zahlen ohne Suche liefert, **wenn der Graph chordal ist**. Dieses Stück macht daraus ein Maß für **jeden** Graphen: Man eliminiert die Knoten in einer Reihenfolge und **ergänzt dabei die fehlenden Kanten** (die Sehnen aus Stück 4); die größte Menge „Knoten und seine späteren Partner“ ist die **Breite** der Ordnung, die kleinste Breite über alle Ordnungen die **Baumweite**, und die Beutel der Ordnung bilden eine **Baumzerlegung**, auf der das nächste Stück rechnet. Die Kernfrage: **Wie baumartig ist ein Netz, wie sicher lässt sich das sagen, und wie breit ist ein echtes Straßennetz?** Die Kante `fix` verbindet mit Stück 4 (chordale Ergänzung = Baumzerlegung). Anders als die Fall-Demos zeigt die Demo ein Verfahren an einem wachsenden Beispiel.

```
Bron–Kerbosch: alle maximalen Cliquen (Wurzel)
 ├─ Größte Clique: Färbungsschranke und Kernzahl
 ├─ Knotenüberdeckung: Approximation, Kernbildung, Verzweigen
 ├─ Chordale und perfekte Graphen
 │    └─ Baumweite: Eliminationsordnung und Baumzerlegung                [DIESES STÜCK]
 │         └─ Dynamische Programmierung auf der Baumzerlegung
 ├─ Kantenclique-Überdeckung und Kernbildung
 └─ Unabhängige Menge im großen Maßstab: Reduktionen und Lokalsuche
```

## Warum dieses Problem

Auf einem Baum sind viele schwere Aufgaben leicht, auf einem Kreis kaum schwerer, auf einem dichten Gitter nicht mehr. Die Baumweite sagt, wie weit ein Graph von einem Baum entfernt ist: Baum 1, Kreis 2, das k × k-Gitter k, der vollständige Graph n − 1. Sie ist selbst NP-schwer. Die Demo zeigt, wie man sie von oben **eingrenzt** (Min-Grad und Min-Fill als Eliminationsordnungen), von unten (die Min-Grad-Kontraktion MMD+), **exakt für kleine Netze** (Teilmengen-DP bis n = 16) und an einem **echten Straßennetz** (der OpenStreetMap-Ausschnitt aus der Demo zur Breitensuche, 5 072 Kreuzungen).

Abgrenzung: `cliquenbandbreite-demo` nennt Bodlaenders Programm für beschränkte Baumweite nur als Anregung für eine eigene Färbungs-DP, `bandbreite-demo` kennt die Bandbreite (die Baumweite ist nie größer), `bfs-demo` und `routenresilienz-demo` kennen Straßennetze, aber keine dieser Demos berechnet Baumweite. Als eigenes Thema sind Baumweite, Eliminationsordnung mit Auffüllen und Baumzerlegung neu.

## Modell

Ungerichteter Graph G = (V, E). Netztypen (die Störung bedeutet je Typ etwas anderes, die Hilfe der App nennt es): **Gitter** (Straßenraster mit Seitenlänge ⌊√n⌉, Störung = Anteil zufällig gesperrter Kanten), **Baum plus Zusatzkanten** (zufälliger Baum, Störung = Zahl zusätzlicher Zufallskanten in Prozent von n), **Kreis plus Sehnen**, **Zufallsnetz** (G(n, p) mit mittlerem Grad 1,5 plus Störung durch 20), **Konfliktgraph von Teilstrecken** (Sendungen auf einer Linie, chordal wie in Stück 4) und **Toronto** (die n Kreuzungen, die dem Mittelpunkt des Ausschnitts am nächsten liegen; Daten wie in `bfs-demo`, ODbL, Störung = Sperrungen). Feste Vergleichsgraphen: Baum, Kreise, Gitter, vollständige und vollständig bipartite Graphen, Petersen-Graph (Baumweite 4), Hyperwürfel Q4 (6). Alle Graphen außer Toronto sind synthetisch; der Zufall kommt aus `random.Random(seed)`, die Algorithmen sind vollständig deterministisch (Gleichstand: kleinster Index). Formeln und Literatur stehen im 📐-Expander der App.

**Daten und Lizenz:** Kartendaten © [OpenStreetMap-Mitwirkende](https://www.openstreetmap.org/copyright), Open Database License (ODbL) 1.0. `data/toronto_campus.json` ist derselbe Auszug wie in der Demo zur Breitensuche (5 072 Knoten, aus 14 503 gerichteten Bögen 7 621 ungerichtete Kanten) und steht deshalb ebenfalls unter der ODbL – siehe [data/LICENSE-ODbL.md](data/LICENSE-ODbL.md).

## Methodik

| Verfahren | Idee |
|---|---|
| **Eliminieren mit Auffüllen** | Knoten in einer Reihenfolge entfernen; vor dem Entfernen die noch vorhandenen Nachbarn paarweise verbinden. Der Knoten samt diesen Nachbarn ist sein **Beutel**, die Breite der Ordnung die größte Beutelgröße minus 1. |
| **Min-Grad** | Immer den Knoten mit den wenigsten noch vorhandenen Nachbarn eliminieren (Heap, Gleichstand: kleinster Index). |
| **Min-Fill** | Immer den Knoten eliminieren, dessen Nachbarn die wenigsten fehlenden Kanten haben; betroffen sind nach jedem Schritt die Nachbarn und deren Nachbarn. |
| **Zufällige Reihenfolge** | zum Vergleich: zeigt, wie viel die Heuristik bringt. |
| **MMD+** (untere Schranke) | Den Knoten kleinsten Grades in den Nachbarn mit den wenigsten gemeinsamen Nachbarn kontrahieren und den größten dabei gesehenen kleinsten Grad merken; Kontraktionen senken die Baumweite nie. |
| **Exakt** | Teilmengen-DP: f(S) = min über v ∈ S von max(f(S ∖ {v}), \|Q(S ∖ {v}, v)\|); Q = Knoten außerhalb, die von v über Knoten in S erreichbar sind. Zustände 2^n, deshalb bis n = 16. |
| **Zerlegung** | Beutel(v) = v und seine Beutel-Nachbarn; der Beutel von v hängt am Beutel seines frühesten späteren Nachbarn (bei mehreren Komponenten werden die Wurzeln der Reihe nach verbunden). Die **Prüfung** testet vier Dinge einzeln: jeder Knoten in einem Beutel, jede Kante in einem Beutel, die Beutelkanten bilden einen Baum, die Beutel mit einem Knoten sind zusammenhängend. |
| **Abschluss** | Der aufgefüllte Graph H ist chordal, die Ordnung ist für ihn perfekt, und ω(H) = Breite + 1 (Brücke zu Stück 4; Prüfung mit gekürztem Code aus Stück 4). |

Die App hat zwei Tabs („Eliminieren“ mit Schritt-Regler und Breitenkurve, „Zerlegung“ mit dem Beutelbaum bis n = 60 und der Prüfung der vier Eigenschaften), eine Kernfrage mit Verdikt und vier Experimente.

## Befunde (gemessen, keine Behauptungen)

Jede Zahl steht in `tests/test_claims.py`. Alle Werte sind ganzzahlig und plattformunabhängig exakt. Die Tabellen der Experimente sind feste Instanzen (`SWEEP_SEEDS`, feste Seeds je Zelle). Die Rechenzeiten dagegen sind **nicht** festgeschrieben (Entwicklungsrechner, Python): Der exakte DP braucht bei n = 14 etwa 0,2 s, bei n = 15 0,4 bis 0,6 s und bei n = 16 1,1 bis 1,6 s.

| Frage | Befund |
|---|---|
| Standardfall (Gitter 4×4, Min-Fill)? | 16 Knoten, 24 Kanten. **Baumweite 4, exakt** (DP); Min-Fill und Min-Grad liefern Breite 4 mit je 18 ergänzten Sehnen, MMD+ ist 4. Die Zerlegung hat 16 Beutel, der größte 5 Knoten; der aufgefüllte Graph ist chordal mit ω = 5 = Breite + 1. |
| Treffen die Heuristiken die bekannten Werte (Experiment 1)? | **Ja bei allen 10 Familien**: Baum (20 Knoten) 1, Kreis C12 2, Gitter 3×3 bis 6×6 mit 3 bis 6, K8 7, K_{3,5} 3, Petersen-Graph 4, Hyperwürfel Q4 6. Die untere Schranke MMD+ **beweist** den Wert bei 8 davon (alle außer Gitter 5×5 und 6×6, wo sie 4 liefert); wo n ≤ 16 gilt, bestätigt der DP den bekannten Wert. |
| Und auf größeren Gittern (Experiment 2)? | **Bis 6×6 exakt, ab 7×7 darüber**: 7×7: 8 statt 7, 8×8: **10 statt 8**, 10×10: 13, 12×12: **16 statt 12**, 14×14: **19 (Min-Fill) und 20 (Min-Grad) statt 14**. Eine zufällige Reihenfolge braucht im Median 4, 7, 7, 12, 15, 22, 31, 43, 62 für k = 3, 4, 5, 6, 7, 8, 10, 12, 14. Die untere Schranke MMD+ bleibt bei 3 bis 5 (**5 bei 14×14**). |
| Wie gut sind die Heuristiken auf kleinen Zufallsnetzen (Experiment 3, n = 11, je 100 Graphen)? | **Min-Fill trifft den exakten Wert in 397 von 400 Graphen, Min-Grad in 384**, die Lücke ist nie größer als 1. Bei p = 20 % und 30 % sind alle drei Verfahren in allen 100 Graphen exakt; bei p = 50 % Min-Fill 98, Min-Grad 90, MMD+ 89; bei p = 70 % Min-Fill 99, Min-Grad 94, MMD+ 73. **In 359 von 400 Graphen fallen untere und obere Schranke zusammen** (der Wert ist dann ohne den DP bewiesen); in jedem Graphen gilt untere ≤ exakt ≤ obere Schranke. |
| Wie wächst die Breite bei dünnen Zufallsnetzen (Experiment 4)? | **Etwa linear in der Knotenzahl**: Mittlerer Grad 3, Riesenkomponente 47, 94, 194, 377 Knoten: Min-Fill-Breite 7, 13, 26, 49 (**0,13 bis 0,14 mal die Knotenzahl**), Min-Grad 8, 13, 27, 50, MMD+ 6, 7, 11, 14. Das Preset „Dünner Zufall“ (400 Knoten, 622 Kanten, 14 Komponenten): Breite 55 (Min-Grad 56), untere Schranke 14. |
| **Wie breit ist ein echtes Straßennetz?** | **Zwischen 6 und 50.** Die n Kreuzungen um den Mittelpunkt des Toronto-Ausschnitts, Min-Fill / Min-Grad / MMD+: 200 Kreuzungen 4 / 5 / 4, 400: 6 / 7 / 4, 800: 15 / 15 / 5, 1 600: 21 / 27 / 5, 3 200: 38 / 44 / 6, **5 072: 50 / 57 / 6**. Die obere Schranke wächst mit dem Ausschnitt, die untere bleibt bei 6: **Die Demo behauptet keinen Wert.** Die Zerlegung des ganzen Ausschnitts ist gültig (5 072 Beutel, Breite 50). |
| Preset „Toronto“ (600 Kreuzungen)? | 779 Kanten, 4 Komponenten, Breite 11 mit 769 Sehnen (Min-Grad: ebenfalls 11, aber 814 Sehnen), untere Schranke 5; Zerlegung 600 Beutel, größter 12. |
| Gitter 12×12 („die Lücke wächst“)? | 264 Kanten; Min-Fill Breite 16 (604 Sehnen), Min-Grad 16 (618), untere Schranke 5, bekannte Baumweite 12 (also höchstens 4 darüber). |
| Was bringt die Heuristik gegenüber einer zufälligen Reihenfolge? | Preset „Zufällige Reihenfolge“ (10×10-Gitter, Seed 8): zufällig **Breite 34 mit 1 094 Sehnen**, Min-Fill und Min-Grad je **13 mit 355 bzw. 376 Sehnen**, bekannter Wert 10. |
| Baum und fast ein Baum? | Preset „Baum: fast baumartig“ (30 Knoten, 33 Kanten, also 4 Zusatzkanten): Breite 2 mit 7 Sehnen, **untere Schranke ebenfalls 2: bewiesen**. |
| Wann wird nichts ergänzt? | Preset „Chordal“ (40 Sendungen auf einer Linie, 254 Konflikte): **Min-Fill ergänzt 0 Kanten**, Breite 10 = ω − 1 = Baumweite (exakt, chordal); Min-Grad ergänzt hier **4 Sehnen**, obwohl der Graph chordal ist, mit derselben Breite 10. |
| Gilt „aufgefüllter Graph chordal, ω = Breite + 1“? | **Ja** auf allen 7 Presets und für jeden Netztyp und jede Ordnung in den Tests; die Zerlegung ist in jedem gemessenen Fall gültig. |

## Befunde und Korrekturen gegenüber dem Plan

Der Einzelplan hatte eine Vormessung mit eigenem Wegwerfskript. **Das Bild blieb im Kern, einzelne Zahlen änderten sich:** Die Vormessung sah die erste Überschreitung der Gitterbreite beim 8×8-Gitter (sie hatte die Größe 7 übersprungen); mit der Größe 7 beginnt sie schon dort (8 statt 7). Die Heuristiken sind auf dem kleinen Zufallsnetz (n = 11) besser als in der Vormessung (Min-Fill 397 von 400 statt 147 bis 150 von 150 je Dichte, andere feste Instanzen). Der Toronto-Ausschnitt wird jetzt nicht mehr nach Radius, sondern nach den n nächsten Kreuzungen geschnitten (die Knoten sind nach Abstand nummeriert): für den ganzen Ausschnitt ist die obere Schranke deshalb **50 statt 51** (anderer Gleichstand), und die Größen der Zwischenschritte sind andere. Die Aussage der Vormessung „Min-Grad ist um ein Vielfaches schneller“ ist **keine README-Zahl** (die Demo misst keine Laufzeit). Abweichungen vom Einzelplan: Die **Bandbreite** wird nur bis n = 8 per Brute Force berechnet (statt 9, wegen der Testlaufzeit); der Regler „Knoten“ geht bis 600 (statt unbegrenzt), weil Min-Fill auf dichten Zufallsnetzen mit 1 000 Knoten über 30 Sekunden braucht; das ganze Toronto-Netz (5 072 Kreuzungen) steht deshalb nur in Experiment 4. Die MMD+-Variante ist „least-c“ ohne Verbesserungen. Ein Play-Knopf für die Schritt-Ansicht entfällt zugunsten eines Schritt-Reglers. Kein PDF-Export (Konzepte-Demos haben üblicherweise keinen). Kein scipy und kein networkx zur Laufzeit: beide stehen nur in `requirements-dev.txt` für die Gegenproben.

## Ehrliche Grenzen

- **Heuristiken ohne Garantie.** Min-Grad und Min-Fill liefern nur obere Schranken; auf Gittern ab 7×7 liegen sie über dem Wert, die Lücke wächst (4 beim 12×12-Gitter, 5 beim 14×14-Gitter).
- **Untere Schranke einfach.** MMD+ ist auf Gittern und echten Straßennetzen weit unter dem Wert; stärkere Schranken und exakte Verfahren (der PID-Algorithmus von Tamaki, der Wettbewerb PACE) gibt es, sie sind hier nur Einordnung im Mathematik-Expander. Deshalb ist die Antwort für Toronto ein Intervall (6 bis 50).
- **Exakt nur klein.** Der Teilmengen-DP braucht 2^n Zustände, bei n = 16 etwa ein bis zwei Sekunden.
- **Ungerichtet, ohne Gewichte.** Beim Toronto-Ausschnitt zählen nur Kreuzungen und Straßenstücke; Einbahnstraßen, Längen und Zeiten fehlen. Die Baumweite hängt auch davon ab, wie dicht die Karte digitalisiert wurde.
- **Ausschnitt, nicht die Stadt.** 5 072 Kreuzungen im Umkreis von 1 km; die Breite eines größeren Netzes kann anders wachsen.
- **Baumweite ist ein Strukturmaß.** Eine kleine Breite verspricht kleine Beutel, aber noch keine schnelle Lösung einer Aufgabe; das zeigt erst das nächste Stück.
- **Schritte statt Laufzeit.** Die Experimente messen Breiten, Sehnen und Beutel, keine Laufzeiten.
- **Synthetische Daten.** Außer dem Toronto-Ausschnitt sind alle Netze erzeugt; Hauptansicht bis n = 600.

## Verifikation

- **Kern:** jede Einheit (`eliminate`, `min_degree_order`, `min_fill_order`, `fill_count`, `mmd_plus`, `exact_treewidth`, `tree_decomposition`, `validate_decomposition`, `completion`, `bandwidth_small`) gegen Handrechnung auf den Mini-Instanzen (Pfad, Dreieck mit Pendel, Viereck, Fünfeck, K4, Stern, 3×3-Gitter, Petersen-Graph); Beutel, Baumkanten und Sehnen sind auf Papier nachgerechnet (Dreieck mit Pendel: Ordnung 3, 0, 1, 2, Beutel {0,1,2}, {1,2}, {2}, {2,3}).
- **Orakel (`tests/test_oracle_treewidth.py`):** die exakte Baumweite gleich Brute Force über alle Eliminationsordnungen auf 355 festen Zufallsgraphen (330 mit höchstens 6, 25 mit 7 Knoten) und gleich den bekannten Familienwerten (Bäume, Kreise C3 bis C12, K_n, K_{a,b}, Gitter 2×2 bis 4×4, Petersen, Q3, Q4); untere ≤ exakt ≤ jede Heuristik auf über 300 gemischten Graphen (Zufall, Bäume mit Zusatzkanten, Kreise mit Sehnen, Konfliktgraphen, Gitter mit Sperrungen); die exakte Ordnung erreicht den Wert; `networkx.treewidth_min_*` nie unter dem exakten Wert; **jede Zerlegung aus einer Ordnung (Min-Grad, Min-Fill, zufällig) ist gültig nach der eigenen Prüfung und nach einer davon unabhängigen Prüfung mit networkx** (die Prüfung lehnt kaputte Zerlegungen ab: Kante fehlt, Knoten fehlt, Baum zerfällt, Teilbaum zerfällt); auf chordalen Graphen Auffüllung 0 und Breite = `chordal_graph_treewidth` = ω − 1; der Abschluss ist nach networkx chordal; Teilgraphen-Monotonie (100 Paare); Baumweite ≤ Bandbreite; Baumweite einer disjunkten Vereinigung = Maximum.
- **Zweige (`tests/test_branches.py`):** Min-Fill schlägt Min-Grad auf einem Graphen (Breite 3 gegen 4) und verliert auf einem anderen (6 gegen 5); eine Heuristik liegt über dem exakten Wert; die zufällige Reihenfolge ist auf dem Gitter schlechter; MMD+ trifft auf vollständigen Graphen und verfehlt auf Gittern; die Schranken fallen auf einem Graphen zusammen und bleiben auf einem anderen auseinander; jeder Zweig des Verdikts der Kernfrage.
- **Mutationsprüfung** (`tools/oracle_mutation.py`, 60 von 130 Stellen, mit ganzer Suite): Rate 78 %, vier Überlebende, alle äquivalent: der Sonderfall n = 0 in den beiden Aufzählungsverfahren liefert dasselbe wie die allgemeine Rechnung, und die Sortierrichtung beim Auffüllen ändert nur die Reihenfolge, in der Kanten in Mengen eingefügt werden. Aus der ersten Runde stammen die Tests zu `fill_count`, MMD+, Baumprüfung und Bandbreite.
- **Zahlen:** `tests/test_claims.py` rechnet jede Zahl dieser README über dieselben Auswertungsfunktionen wie die App nach; `tests/test_verdicts.py` prüft jeden Verdikt-Text an handgesetzten Werten.
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler an Minimum und Maximum, jeder Netztyp, jede Ordnung, Extrem-Seeds, Permalink, Schritt-Regler, Beutelbaum-Grenze, Preset-Hervorhebung, fester Kopf) und Footer-Test.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: zwei Tabs, Kernfrage, vier Experimente, Brücken, Grenzen, Mathematik |
| `data/LICENSE-ODbL.md` | Lizenz der OpenStreetMap-Daten |
| `data/toronto_campus.json` | der Toronto-Ausschnitt (5 072 Knoten) aus `bfs-demo` |
| `twd_algorithm.py` | Kern: Eliminieren, Min-Grad, Min-Fill, MMD+, exakter DP, Zerlegung und Prüfung, Abschluss, Brücke zu Stück 4, Bandbreite |
| `twd_constants.py` | Regler-Grenzen, Rechengrenzen, Farben, Presets |
| `twd_evaluation.py` | Einstellungen, Analyse, Experimente und Verdikte |
| `twd_layout.py` | fester Kopf (Gerüst aus `new_demo.py`) |
| `twd_presets.py` | Permalink (Begrenzen), Presets in der Seitenleiste mit Hervorhebung, Zufalls-Seed-Button |
| `twd_scenario.py` | Netze: Gitter, Baum, Kreis, Zufall, Konfliktgraph, Toronto und die festen Vergleichsgraphen |
| `twd_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `requirements-dev.txt` | Laufzeit plus pytest, networkx und scipy (nur für die Gegenproben) |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `tests/` | Algorithmus, Orakel, Zweige, Szenarien, Zahlen, Verdikte, Figuren, Presets, Layout, AppTest, Footer |

## Bewusst nicht umgesetzt

- **Exakte Verfahren für große Graphen** (PID-Algorithmus von Tamaki, Separatoren-Verfahren) und **stärkere untere Schranken**: Einordnung im Mathematik-Expander.
- **Dynamische Programmierung auf der Zerlegung** (das nächste Stück der Reihe).
- **Ein Play-Knopf** für die Schritt-Ansicht und **PDF-Export** (siehe Korrekturen oben).

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

## Literatur

- Bodlaender, H. L. (1993). *A tourist guide through treewidth.* Acta Cybernetica 11(1–2), 1–21.
- Arnborg, S., Corneil, D. G., & Proskurowski, A. (1987). *Complexity of finding embeddings in a k-tree.* SIAM Journal on Algebraic and Discrete Methods 8(2), 277–284.
- Bodlaender, H. L., Fomin, F. V., Koster, A. M. C. A., Kratsch, D., & Thilikos, D. M. (2012). *On exact algorithms for treewidth.* ACM Transactions on Algorithms 9(1), Art. 12.
- Bodlaender, H. L., & Koster, A. M. C. A. (2011). *Treewidth computations II. Lower bounds.* Information and Computation 209(7), 1103–1119.
- Tamaki, H. (2017). *Positive-instance driven dynamic programming for treewidth.* ESA 2017 (LIPIcs 87, 68:1–68:13).

Gebaut mit Streamlit, Plotly und pandas.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
