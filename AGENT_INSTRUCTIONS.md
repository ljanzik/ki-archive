# Jira Daily Report Agent – Anweisungen & Dokumentation

## Zweck
Dieser Agent analysiert täglich zwei Jira-JSON-Exportdateien (heute + gestern) und erstellt daraus einen kompakten HTML-Report für das Scrum Daily (~60 Sekunden Vorlesezeit).

---

## Dateien in diesem Paket

| Datei | Beschreibung |
|---|---|
| `jira_daily_analysis.py` | Vollständiges Python-Analyseskript (eigenständig ausführbar) |
| `daily_summary_YYYY-MM-DD.html` | Beispiel-Output des Reports |

---

## Voraussetzungen

- Python 3.8+
- Keine externen Bibliotheken erforderlich (nur Python-Standardbibliothek)
- Jira-Exporte als JSON-Dateien (Jira REST API v2, Array von Issues)

---

## Verwendung (Kommandozeile)

```bash
python jira_daily_analysis.py heute.json gestern.json [output.html]
```

**Beispiel:**
```bash
python jira_daily_analysis.py 2026-03-12.json 2026-03-11.json daily_2026-03-12.html
```

Wenn kein Output-Pfad angegeben wird, wird die Datei automatisch nach dem heutigen Datum benannt:
`daily_YYYY-MM-DD.html`

---

## Verwendung als Langdock-Agent

### Prompt für den Agenten:

```
Du bist ein Jira Daily Report Agent.

Der Nutzer liefert dir zwei JSON-Dateien:
- Eine Datei vom heutigen Tag (heute.json)
- Eine Datei vom gestrigen Tag (gestern.json)

Führe das beigefügte Python-Skript `jira_daily_analysis.py` mit diesen beiden Dateien aus und liefere den fertigen HTML-Report zurück.

Wenn die Dateien noch nicht vorhanden sind, fordere den Nutzer auf, sie hochzuladen.
```

### Zu betrachtende Mitarbeiter (konfigurierbar in `TARGET_ASSIGNEES`):
- Antje Fischer
- Ingo Niekamp
- Kevin Knuth
- Mario Schneider
- René Charlé
- Sami Ben Hamouda
- Steven Kühnl
- Torsten Zimmermann

> **Anpassen:** Die Liste `TARGET_ASSIGNEES` am Anfang des Skripts kann jederzeit erweitert oder geändert werden.

---

## Analysemethodik (Schritt für Schritt)

### Schritt 1 – Tickets identifizieren
- Iteration über alle Issues im heutigen Export
- Zuordnung nach `fields.assignee.displayName`
- Jedes Ticket wird nur einmal gezählt (Deduplizierung per `key`)

### Schritt 2 – Felder extrahieren
Pro Ticket werden ausgewertet:
- `key`, `fields.summary`, `fields.status.name`
- `fields.timespent`, `fields.timeoriginalestimate`, `fields.timeestimate`
- `fields.progress`, `fields.aggregateprogress` (nur für Fortschrittsberechnung)
- `fields.updated`

> ⚠ **Nicht verwendet für Zeitberechnung:** `aggregatetimespent`, `aggregatetimeoriginalestimate`, `aggregatetimeestimate` (enthalten Subtask-Summen → Doppelzählung)

### Schritt 3 – Zeitdifferenz (Delta)
```
delta_seconds = timespent_heute - timespent_gestern
```
- Delta wird **nur** berechnet, wenn das Ticket in **beiden** Exporten vorhanden ist
- Negative Deltas werden auf 0 gesetzt (Zeitkorrektur)
- Neue Tickets (nur in heute) erhalten Delta = 0

### Schritt 4 – Fortschritt
Priorität:
1. `progress.progress / progress.total`
2. `aggregateprogress.progress / aggregateprogress.total`
3. `timespent / timeoriginalestimate`
4. „keine Daten"

### Schritt 5 – Ticket-Flags
| Flag | Bedingung |
|---|---|
| `OVER_ESTIMATE` | `timespent > timeoriginalestimate` |
| `NO_ESTIMATE` | `timeoriginalestimate` fehlt |
| `IN_PROGRESS_NO_TIME` | Status enthält „progress" oder „arbeit" UND `timespent = 0` |
| `DONE_LIKELY` | `timeestimate = 0` ODER Fortschritt ≥ 100 % |
| `NEW_TODAY` | Ticket nicht im gestrigen Export vorhanden |

### Schritt 6 – Mitarbeiter-Zusammenfassung
- Max. 3 Tickets pro Person
- Auswahl nach Relevanz-Score (abgeschlossen > Risiko > aktiv mit Delta > hoher Fortschritt)

### Schritt 7 – Teamweite Punkte
- **Risiken:** Estimate überschritten | In Progress ohne Buchung | Restaufwand > 10 h bei < 50 % Fortschritt
- **Neu/unklar:** kein Estimate | neu im heutigen Export | kein Aufwand
- **Abgeschlossen:** Fortschritt ≥ 100 % oder Restaufwand = 0

---

## Output-Format

Der Report ist ein selbstenthaltendes HTML-Dokument mit:
1. **60-Sekunden-Daily** – Mitarbeiter-Zusammenfassung (2–3 Sätze/Person)
2. **Teamweite Punkte** – Risiken | Neue Tickets | Abgeschlossene Tickets
3. **Aufwandstabelle** – Gestern gebuchte Stunden je Mitarbeiter

---

## Konfiguration anpassen

Im Skript `jira_daily_analysis.py` können folgende Werte angepasst werden:

```python
# Zeile ~10: Mitarbeiter-Liste
TARGET_ASSIGNEES = [
    "Antje Fischer",
    ...
]

# Zeile ~200: Risiko-Schwellwert Restaufwand (Standard: 10 h)
(t["remaining_h"] or 0) > 10

# Zeile ~200: Risiko-Schwellwert Fortschritt (Standard: < 50 %)
(t["progress_pct"] or 0) < 50
```

---

## Qualitätssicherung

- ✅ Gesamter Export wird analysiert – keine Stichproben
- ✅ Kein Ticket wird doppelt gezählt
- ✅ Keine aggregierten Zeitfelder für Buchungsberechnungen
- ✅ Delta nur wenn Ticket in beiden Exporten vorhanden
- ✅ Negative Deltas = 0
- ✅ Fehlende Daten werden als „keine Daten" ausgewiesen, keine Annahmen

---

## Beispiel-Tagesablauf

```
1. Jira-Export von heute herunterladen  → 2026-03-12.json
2. Jira-Export von gestern bereithalten → 2026-03-11.json
3. Skript ausführen:
   python jira_daily_analysis.py 2026-03-12.json 2026-03-11.json
4. HTML-Report öffnen und im Daily vorlesen
```

---

*Erstellt: 12. März 2026 | Version 1.0*
