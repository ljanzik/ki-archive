Aufgabe

Analysiere eine vollständige Jira-Exportdatei (JSON) und erstelle eine kompakte Daily-Zusammenfassung, die in etwa 60 Sekunden vorgelesen werden kann.

Die Zusammenfassung soll den aktuellen Arbeitsstand der wichtigsten Tickets pro Mitarbeiter sowie Teamrisiken darstellen.

Zu betrachtende Mitarbeiter

Analysiere nur Tickets, deren Assignee einer der folgenden Mitarbeiter ist:

Antje Fischer

Ingo Niekamp

Kevin Knuth

Mario Schneider

René Charlé

Sami Ben Hamouda

Steven David Kühnl

Torsten Zimmermann

Wenn ein Mitarbeiter keine Tickets hat, schreibe:

keine Tickets im Export gefunden

Schritt 1 – Tickets identifizieren

Iteriere über alle Issues im Export.

Prüfe das Feld:

fields.assignee.displayName

Wenn der Assignee zu einem der genannten Mitarbeiter gehört:

füge das Ticket diesem Mitarbeiter zu.

Regeln:

Der Ticket-Key ist eindeutig.

Wenn ein Ticket mehrfach vorkommt, darf es nur einmal gezählt werden.

Der gesamte Export muss analysiert werden, keine Stichproben.

Schritt 2 – Relevante Felder extrahieren

Lies pro Ticket mindestens folgende Felder aus:

Identifikation

key

fields.summary

Status

fields.status.name

Zeit

fields.timespent

fields.aggregatetimespent

Schätzungen

fields.timeoriginalestimate

fields.aggregatetimeoriginalestimate

fields.timeestimate

fields.aggregatetimeestimate

Fortschritt

fields.progress.progress

fields.progress.total

fields.aggregateprogress.progress

fields.aggregateprogress.total

Zeitstempel

fields.created

fields.updated

Schritt 3 – Zeiten korrekt behandeln

Wichtig:

Die gebuchte Zeit ist eine Gesamtsumme des Tickets und bezieht sich nicht zwingend auf den aktuellen Zeitraum.

Daher:

Zeiten nur zur Fortschrittsberechnung nutzen

keine Summen über Mitarbeiter oder Team bilden

Konvertierung:

Stunden = Sekunden / 3600

Runde auf zwei Nachkommastellen.

Schritt 4 – Fortschritt berechnen

Wenn vorhanden:

Fortschritt % = progress.progress / progress.total

oder

aggregateprogress.progress / aggregateprogress.total

Wenn diese Daten fehlen:

Fortschritt % = timespent / originalestimate

Wenn keine Daten vorhanden:

Fortschritt: keine Daten vorhanden
Schritt 5 – Ticketbewertung

Pro Ticket erkenne automatisch:

Markierungen:

Estimate überschritten

Ticket ohne Estimate

In Arbeit ohne Zeitbuchung

vermutlich abgeschlossen

kürzlich aktualisiert

Definitionen:

vermutlich abgeschlossen

Restaufwand = 0
oder Fortschritt ≥ 100 %

kürzlich aktualisiert

updated innerhalb der letzten 24 Stunden
Schritt 6 – Mitarbeiter-Zusammenfassung

Für jeden Mitarbeiter:

Nenne maximal 2–3 relevante Tickets:

wichtigste Fortschritte

Tickets kurz vor Abschluss

große Tickets mit viel Restaufwand

auffällige Tickets

Formatiere in 2–3 kurzen Sätzen.

Beispielstruktur:

Name

Ticket A ist fast fertig (~80 %).
Ticket B läuft weiter mit größerem Restaufwand.
Ticket C wurde kürzlich abgeschlossen / über Estimate beendet.

Wenn keine Tickets existieren:

Name
keine Tickets im Export gefunden
Schritt 7 – Teamweite Punkte

Erstelle abschließend drei kurze Abschnitte.

Mögliche Risiken

Liste:

Tickets deutlich über Estimate

große Tickets mit viel Restaufwand

Tickets In Arbeit ohne Zeitbuchung

Neue oder unklare Tickets

Liste Tickets:

ohne Estimate

neu erstellt

Vermutlich abgeschlossene Tickets

Liste Tickets mit:

Fortschritt ≥ 100 %

Restaufwand = 0

Ausgabeformat

Die Ausgabe muss sehr kompakt sein.

Struktur:

60-Sekunden-Daily

Name
2–3 kurze Sätze

Name
2–3 kurze Sätze

...

Teamweite Punkte
Risiken
Neue Tickets
Abgeschlossene Tickets
Qualitätsregeln

Analysiere die gesamte Datei.

Kein Ticket übersehen.

Keine Zeiten summieren.

Keine Annahmen treffen, die nicht aus den Daten ableitbar sind.

Wenn Daten fehlen:

keine Daten vorhanden

Schreibe präzise und knapp.

Die Ausgabe soll sich direkt im Scrum Daily vorlesen lassen und als HTML formatiert sein.