#!/usr/bin/env python3
"""
jira_daily_analysis.py
Analysiert zwei Jira-JSON-Exporte (heute + gestern) und erstellt einen HTML-Daily-Report.
Aufruf: python jira_daily_analysis.py <heute.json> <gestern.json> [output.html]
"""

import json
import sys
from datetime import datetime

TARGET_ASSIGNEES = [
    "Antje Fischer", "Ingo Niekamp", "Kevin Knuth", "Mario Schneider",
    "René Charlé", "Sami Ben Hamouda", "Steven Kühnl", "Torsten Zimmermann"
]

# ---------------------------------------------------------------------------
# 1. Laden & Indexieren
# ---------------------------------------------------------------------------

def load_export(path):
    with open(path, "r", encoding="utf-8") as f:
        issues = json.load(f)
    lookup = {}
    for issue in issues:
        key = issue["key"]
        if key not in lookup:
            lookup[key] = issue
    return lookup

# ---------------------------------------------------------------------------
# 2. Hilfsfunktionen
# ---------------------------------------------------------------------------

def sec_to_h(s):
    if s is None:
        return None
    return round(s / 3600, 2)

def fmt_h(h):
    if h is None:
        return "keine Daten"
    return f"{h:.2f} h"

def fmt_pct(p):
    if p is None:
        return "keine Daten"
    return f"{p:.1f} %"

def get_assignee(issue):
    a = issue["fields"].get("assignee")
    return a.get("displayName", "") if a else ""

def calc_progress(issue):
    f = issue["fields"]
    prog = f.get("progress")
    if prog and prog.get("total") and prog["total"] > 0:
        return round(prog["progress"] / prog["total"] * 100, 1)
    agg = f.get("aggregateprogress")
    if agg and agg.get("total") and agg["total"] > 0:
        return round(agg["progress"] / agg["total"] * 100, 1)
    ts = f.get("timespent")
    oe = f.get("timeoriginalestimate")
    if ts and oe and oe > 0:
        return round(ts / oe * 100, 1)
    return None

def calc_delta(key, today_map, yesterday_map):
    t_today = today_map[key]["fields"].get("timespent") or 0
    if key in yesterday_map:
        t_yest = yesterday_map[key]["fields"].get("timespent") or 0
        return max(t_today - t_yest, 0)
    return 0  # Neu erschienenes Ticket → kein Delta

def analyze_issue(issue, today_map, yesterday_map):
    key = issue["key"]
    f = issue["fields"]
    timespent   = f.get("timespent")
    original    = f.get("timeoriginalestimate")
    remaining   = f.get("timeestimate")
    status      = f.get("status", {}).get("name", "")
    progress    = calc_progress(issue)
    delta_sec   = calc_delta(key, today_map, yesterday_map)
    new_today   = key not in yesterday_map

    flags = []
    if original and timespent and timespent > original:
        flags.append("OVER_ESTIMATE")
    if not original:
        flags.append("NO_ESTIMATE")
    status_lower = status.lower()
    if ("progress" in status_lower or "arbeit" in status_lower):
        if not timespent or timespent == 0:
            flags.append("IN_PROGRESS_NO_TIME")
    if remaining == 0 or (progress is not None and progress >= 100):
        flags.append("DONE_LIKELY")
    if new_today:
        flags.append("NEW_TODAY")

    return {
        "key":          key,
        "summary":      f.get("summary", ""),
        "status":       status,
        "timespent_h":  sec_to_h(timespent),
        "original_h":   sec_to_h(original),
        "remaining_h":  sec_to_h(remaining),
        "progress_pct": progress,
        "delta_h":      sec_to_h(delta_sec),
        "flags":        flags,
        "new_today":    new_today,
        "updated":      f.get("updated", ""),
    }

# ---------------------------------------------------------------------------
# 3. Haupt-Analyse
# ---------------------------------------------------------------------------

def run_analysis(today_map, yesterday_map):
    assignee_issues = {name: [] for name in TARGET_ASSIGNEES}
    for key, issue in today_map.items():
        name = get_assignee(issue)
        if name in TARGET_ASSIGNEES:
            assignee_issues[name].append(issue)

    analysis = {}
    for name in TARGET_ASSIGNEES:
        analysis[name] = [analyze_issue(i, today_map, yesterday_map)
                          for i in assignee_issues[name]]

    deltas = {}
    for name in TARGET_ASSIGNEES:
        total = sum((t["delta_h"] or 0) for t in analysis[name])
        deltas[name] = round(total, 2)

    return analysis, deltas, assignee_issues

# ---------------------------------------------------------------------------
# 4. HTML-Report generieren
# ---------------------------------------------------------------------------

def person_block_html(name, tickets):
    if not tickets:
        return f'''<div class="person-block">
  <div class="person-name">{name}</div>
  <ul><li><em>Keine Tickets im Export gefunden.</em></li></ul>
</div>'''

    def score(t):
        s = 0
        if "DONE_LIKELY"          in t["flags"]: s += 3
        if "OVER_ESTIMATE"        in t["flags"]: s += 2
        if "IN_PROGRESS_NO_TIME"  in t["flags"]: s += 2
        if (t["delta_h"] or 0)   >  0:           s += 1
        if (t["progress_pct"] or 0) >= 80:        s += 1
        return s

    shown = sorted(tickets, key=score, reverse=True)[:3]
    lines = []
    for t in shown:
        flags_html = ""
        if "OVER_ESTIMATE"       in t["flags"]: flags_html += ' <span class="flag-over">⚠ Estimate überschritten</span>'
        if "IN_PROGRESS_NO_TIME" in t["flags"]: flags_html += ' <span class="flag-noprog">⚠ In Progress ohne Zeitbuchung</span>'
        if "NO_ESTIMATE"         in t["flags"]: flags_html += ' <span class="flag-noprog">⚠ Kein Estimate</span>'
        if "DONE_LIKELY"         in t["flags"]: flags_html += ' <span style="color:#2d9e2d;">✔ Vermutlich abgeschlossen</span>'
        if t["new_today"]:                      flags_html += ' <span style="color:#0052cc;font-size:11px;">[Neu heute]</span>'

        meta = [t["status"],
                fmt_pct(t["progress_pct"]) + " Fortschritt",
                fmt_h(t["remaining_h"]) + " Rest"]
        if (t["delta_h"] or 0) > 0:
            meta.append(f'+{t["delta_h"]:.2f} h gestern gebucht')

        summary = t["summary"][:90] + ("…" if len(t["summary"]) > 90 else "")
        lines.append(f'''    <li>
      <span class="ticket-key">{t["key"]}</span> &ndash; {summary}
      {flags_html}
      <span class="meta">({" | ".join(meta)})</span>
    </li>''')

    return f'''<div class="person-block">
  <div class="person-name">{name}</div>
  <ul>
{''.join(lines)}
  </ul>
</div>'''

def teamwide_html(analysis):
    risks_items, new_items, done_items = [], [], []
    seen_risk, seen_new, seen_done = set(), set(), set()

    for name in TARGET_ASSIGNEES:
        for t in analysis[name]:
            # Risiken
            is_risk = (
                "OVER_ESTIMATE"       in t["flags"] or
                "IN_PROGRESS_NO_TIME" in t["flags"] or
                ((t["remaining_h"] or 0) > 10 and (t["progress_pct"] or 0) < 50)
            )
            if is_risk and t["key"] not in seen_risk:
                reason = []
                if "OVER_ESTIMATE"       in t["flags"]:
                    reason.append(f'Estimate überschritten ({fmt_h(t["timespent_h"])} vs. {fmt_h(t["original_h"])})')
                if "IN_PROGRESS_NO_TIME" in t["flags"]:
                    reason.append("In Progress ohne Zeitbuchung")
                if (t["remaining_h"] or 0) > 10 and (t["progress_pct"] or 0) < 50:
                    reason.append(f'{fmt_h(t["remaining_h"])} Restaufwand bei {fmt_pct(t["progress_pct"])} Fortschritt')
                s = t["summary"][:80] + ("…" if len(t["summary"]) > 80 else "")
                risks_items.append(f'<div class="risk"><b>{t["key"]}</b> ({name}) &ndash; {s}. <span class="meta">{" | ".join(reason)}</span></div>')
                seen_risk.add(t["key"])

            # Neue / unklare
            if ("NO_ESTIMATE" in t["flags"] or t["new_today"]) and t["key"] not in seen_new:
                reasons = []
                if t["new_today"]:             reasons.append("Neu heute")
                if "NO_ESTIMATE" in t["flags"]: reasons.append("kein Estimate")
                if not t["timespent_h"]:        reasons.append("kein Aufwand gebucht")
                s = t["summary"][:80] + ("…" if len(t["summary"]) > 80 else "")
                new_items.append(f'<div class="new-ticket"><b>{t["key"]}</b> ({name}) &ndash; {s}. <span class="meta">{" | ".join(reasons)}</span></div>')
                seen_new.add(t["key"])

            # Abgeschlossen
            if "DONE_LIKELY" in t["flags"] and t["key"] not in seen_done:
                s = t["summary"][:80] + ("…" if len(t["summary"]) > 80 else "")
                done_items.append(f'<div class="done-ticket"><b>{t["key"]}</b> ({name}) &ndash; {s}. <span class="meta">{t["status"]} | {fmt_pct(t["progress_pct"])} | {fmt_h(t["remaining_h"])} Rest</span></div>')
                seen_done.add(t["key"])

    return "\n".join(risks_items), "\n".join(new_items), "\n".join(done_items)

def table_html(deltas, assignee_issues):
    rows = sorted(
        [(name, deltas[name], len(assignee_issues[name])) for name in TARGET_ASSIGNEES],
        key=lambda x: x[1], reverse=True
    )
    delta_sum  = sum(deltas.values())
    ticket_sum = sum(len(assignee_issues[n]) for n in TARGET_ASSIGNEES)

    rows_html = ""
    for i, (name, dh, count) in enumerate(rows):
        bg    = "#f4f7fc" if i % 2 == 0 else "#ffffff"
        ds    = f"+{dh:.2f} h" if dh > 0 else "—"
        dc    = "#2d9e2d" if dh > 0 else "#999"
        rows_html += f'''    <tr style="background:{bg};">
      <td style="padding:8px 12px;font-weight:bold;">{name}</td>
      <td style="padding:8px 12px;text-align:right;color:{dc};font-weight:bold;">{ds}</td>
      <td style="padding:8px 12px;text-align:right;">{count}</td>
    </tr>\n'''

    rows_html += f'''    <tr style="background:#e8edf5;font-weight:bold;border-top:2px solid #1a3c6e;">
      <td style="padding:9px 12px;">Gesamt</td>
      <td style="padding:9px 12px;text-align:right;color:#2d9e2d;">+{delta_sum:.2f} h</td>
      <td style="padding:9px 12px;text-align:right;">{ticket_sum}</td>
    </tr>'''
    return rows_html

CSS = """
  body{font-family:Arial,sans-serif;font-size:14px;color:#222;max-width:900px;margin:20px auto;padding:0 20px}
  h1{background:#1a3c6e;color:white;padding:12px 16px;border-radius:6px;font-size:20px;margin-bottom:6px}
  .subtitle{font-size:12px;color:#666;margin-bottom:20px}
  h2{font-size:16px;color:#1a3c6e;border-bottom:2px solid #1a3c6e;margin-top:28px;padding-bottom:4px}
  .person-block{background:#f4f7fc;border-left:4px solid #1a3c6e;padding:10px 14px;margin:10px 0;border-radius:4px}
  .person-name{font-weight:bold;font-size:15px;color:#1a3c6e;margin-bottom:6px}
  .ticket-key{font-weight:bold;color:#0052cc}
  .risk{background:#fff3cd;border-left:4px solid #e6a817;padding:8px 14px;margin:6px 0;border-radius:4px}
  .new-ticket{background:#e8f4e8;border-left:4px solid #2d9e2d;padding:8px 14px;margin:6px 0;border-radius:4px}
  .done-ticket{background:#e8f0ff;border-left:4px solid #5c85d6;padding:8px 14px;margin:6px 0;border-radius:4px}
  .flag-over{color:#c0392b;font-weight:bold}
  .flag-noprog{color:#e67e22;font-weight:bold}
  .section-title{font-size:15px;font-weight:bold;margin:14px 0 6px 0;color:#444}
  .meta{font-size:12px;color:#666}
  ul{margin:4px 0 4px 18px;padding:0}
  li{margin:4px 0}
  table{width:100%;border-collapse:collapse;font-size:14px;margin-top:10px}
  thead tr{background:#1a3c6e;color:white}
  th{padding:9px 12px;text-align:left}
  td{padding:8px 12px}
"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<style>
{css}
</style>
</head>
<body>

<h1>&#128340; 60-Sekunden-Daily &mdash; {date}</h1>
<div class="subtitle">Basis: {count_today} Issues heute | {count_yesterday} Issues gestern &mdash; alle Issues vollständig analysiert, keine Stichproben.</div>

<h2>&#128100; Mitarbeiter-Zusammenfassung</h2>
{persons}

<h2>&#9888;&#65039; Teamweite Punkte</h2>

<div class="section-title">&#128308; Risiken</div>
{risks}

<div class="section-title">&#128994; Neue / unklare Tickets</div>
{new_unclear}

<div class="section-title">&#9989; Vermutlich abgeschlossene Tickets</div>
{done}

<h2>&#128200; Gebuchte Aufwände je Mitarbeiter</h2>
<p style="font-size:12px;color:#555;margin-bottom:8px;">Gestern gebuchte Stunden auf den im Export enthaltenen Tickets
(Delta <code>fields.timespent</code> heute vs. gestern).</p>
<table>
  <thead>
    <tr>
      <th>Mitarbeiter</th>
      <th style="text-align:right;">Gestern gebucht</th>
      <th style="text-align:right;">Anzahl Tickets</th>
    </tr>
  </thead>
  <tbody>
{table_rows}
  </tbody>
</table>
<p style="font-size:11px;color:#888;margin-top:8px;">
* Keine aggregierten Felder. Delta nur bei Tickets in beiden Exporten. Negative Deltas = 0.</p>

</body>
</html>"""

def generate_html(today_map, yesterday_map, analysis, deltas, assignee_issues, report_date):
    persons   = "\n".join(person_block_html(n, analysis[n]) for n in TARGET_ASSIGNEES)
    risks, new_unclear, done = teamwide_html(analysis)
    t_rows    = table_html(deltas, assignee_issues)

    return HTML_TEMPLATE.format(
        css            = CSS,
        date           = report_date,
        count_today    = len(today_map),
        count_yesterday= len(yesterday_map),
        persons        = persons,
        risks          = risks,
        new_unclear    = new_unclear,
        done           = done,
        table_rows     = t_rows,
    )

# ---------------------------------------------------------------------------
# 5. Entry-Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Nutzung: python jira_daily_analysis.py <heute.json> <gestern.json> [output.html]")
        sys.exit(1)

    path_today     = sys.argv[1]
    path_yesterday = sys.argv[2]
    path_out       = sys.argv[3] if len(sys.argv) > 3 else f"daily_{datetime.today().strftime('%Y-%m-%d')}.html"
    report_date    = datetime.today().strftime("%d. %B %Y")

    today_map     = load_export(path_today)
    yesterday_map = load_export(path_yesterday)

    analysis, deltas, assignee_issues = run_analysis(today_map, yesterday_map)
    html = generate_html(today_map, yesterday_map, analysis, deltas, assignee_issues, report_date)

    with open(path_out, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Report gespeichert: {path_out}")
    print(f"  Issues heute:    {len(today_map)}")
    print(f"  Issues gestern:  {len(yesterday_map)}")
    for name in TARGET_ASSIGNEES:
        print(f"  {name}: {len(assignee_issues[name])} Tickets | gestern +{deltas[name]:.2f} h")
