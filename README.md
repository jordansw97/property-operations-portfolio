# Property Operations Portfolio

**Jordan S. Williams** — Resident Experience Specialist (Shift Lead), American Campus Communities

A working portfolio of property operations management: not just what I've done, but *how I run the operation*. The narratives in `/portfolio` tell the story; the toolkit in `/operations` proves the method.

## What's here

| Folder | Contents |
|---|---|
| `/portfolio` | Four one-page leadership narratives: the promotion case, crisis response team funding, 20% shrink reduction, and a 2,224-unit turnover surge |
| `/operations` | **Property Operations Toolkit** (`property-operations-toolkit.xlsx`) — a proof-of-concept workbook for running a residential community, plus its build script and data dictionary |

## The Operations Toolkit

A ten-sheet workbook that runs the core loops of property operations — built with
[`operations/build_toolkit.py`](operations/build_toolkit.py) and upgraded by
[`operations/upgrade_toolkit.py`](operations/upgrade_toolkit.py) (run the upgrade
script to regenerate everything from scratch):

- **Home** — app-style launcher: live pulse stats (breaches, at-risk, follow-ups due, units not ready) and one-click navigation buttons to every tracker
- **Action Center** — the daily priority queue. SLA breaches, at-risk items, due follow-ups, QC failures, and renewal outreach surface automatically through hidden `_seq_` helper columns (plain `COUNTIF`/`MATCH` sequencing — no array formulas, so it works in Excel, Sheets, and LibreOffice). Fix the source row and this page updates itself; every item links straight back to its tracker row
- **Dashboard** — live KPIs plus four auto-updating charts (work orders by category, SLA status, turnover pipeline, renewal intent), 100% formula-driven
- **Weekly Report** — print-ready one-pager for standup or 1:1s: this week's numbers and the top 3 breaches, every value a live formula
- **Work Orders** — full lifecycle tracking with automatic SLA targets by priority (Emergency 1d · High 3d · Standard 7d · Low 14d) and real-time Breached / At Risk / On Track flagging
- **Turnover** — unit make-ready pipeline: inspection → deficiencies → QC → ready, built for high-volume turnover surges
- **Retention** — lease-renewal pipeline with outreach tracking and retention rate on decided units
- **Service Recovery** — resident experience log that closes the loop: issue → owner → action → follow-up → satisfaction score

Dropdowns enforce clean categories, conditional formatting surfaces risk at a glance, and every metric on the Dashboard updates itself as the trackers change. See [`operations/DATA_DICTIONARY.md`](operations/DATA_DICTIONARY.md) for column definitions and formula logic — the workbook is built in code, so it's version-controlled and reproducible.

> **Sample data:** every row in the toolkit is fictional sample data for demonstration. Replace with live property data to use operationally.

## Philosophy

Scale doesn't excuse inconsistency. The systems that hold a 10,000+ resident community to standard are the same ones in this repo: track everything, flag risk early, close every loop, and let the data — not memory — run the morning huddle.
