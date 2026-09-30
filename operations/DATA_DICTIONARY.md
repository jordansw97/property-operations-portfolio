# Data Dictionary — Property Operations Toolkit

## Conventions

- All dates: `MM/DD/YYYY`. All dropdowns are data-validated lists — extend them in **Data → Data Validation**.
- Ranges in formulas run to row 500 so the trackers grow without formula edits.
- `TODAY()`-based columns recalculate on every open — "Days Open" is always current.

## Work Orders

| Column | Definition |
|---|---|
| WO-ID | Unique work order identifier (`WO-####`) |
| Date Opened | Intake date |
| Unit | Unit number |
| Category | Plumbing, Electrical, HVAC, Appliance, Lock/Key, Pest Control, Interior, Exterior/Common Area |
| Priority | Emergency, High, Standard, Low |
| Description | Resident-reported issue + findings |
| Assigned To | Technician, vendor, or Unassigned |
| Status | Open, In Progress, Waiting on Parts, Closed |
| Date Closed | Set when Status → Closed |
| SLA Target (days) | Auto: `=IF(Priority="Emergency",1,IF(Priority="High",3,IF(Priority="Standard",7,14)))` |
| Days Open | Auto: `=IF(Status="Closed", DateClosed − DateOpened, TODAY() − DateOpened)` |
| SLA Status | Auto: Closed · Breached (days > target) · At Risk (within 1 day of target) · On Track |

## Turnover

| Column | Definition |
|---|---|
| Unit / Building | Location identifiers |
| Move-Out Date | Prior resident's move-out |
| Inspection Date | Unit inspection completed |
| Inspector | Who inspected |
| Deficiencies Found | Count from inspection |
| Top Deficiency | Paint, Flooring, Appliance, Plumbing, Electrical, Cleaning, Damaged Fixture, None |
| Make-Ready Status | Not Started → In Progress → Ready for QC → Ready |
| QC Pass | Yes / No / Pending (No sends the unit back — the rework loop) |
| Ready Date | Date the unit passed QC |
| Days: Move-Out → Ready | Auto: `=IF(ReadyDate="","",ReadyDate − MoveOutDate)` |

## Retention

| Column | Definition |
|---|---|
| Unit / Resident ID | Location + anonymized resident key |
| Lease End | Current lease expiration |
| Monthly Rent | Current rent |
| Renewal Offer Sent | Yes / No |
| Outreach Touches | Count of renewal conversations |
| Intent | Renewing, Undecided, Not Renewing, Unknown |
| Reason (if leaving) | N/A, Price, Relocating, Roommate Change, Service Experience, Unit Condition, Other |
| Notes | Context for the next touch |

**Retention rate** = Renewing ÷ (all tracked − Unknown). Unknowns are excluded because they represent outreach not yet done, not decisions made.

## Service Recovery

| Column | Definition |
|---|---|
| Date / Unit | When and where |
| Issue Category | Maintenance Delay, Service Experience, Noise Complaint, Move-In Condition, Package Issue, Access Issue, Parking Dispute, Billing Question, Pest Control, Common Area, Amenity Access, Other |
| Description | What happened, from the resident's perspective |
| Severity | Low, Medium, High, Critical |
| Owner | Who owns the resolution |
| Action Taken | What was actually done (not what was promised) |
| Resolved | Yes / No |
| Follow-Up Date | The date you go back to confirm — the loop isn't closed at "action taken" |
| Satisfaction (1-5) | Post-resolution score; blank until the follow-up happens |

## Dashboard KPIs

Every KPI is a formula over the tracker sheets — no manual tallying. Open counts use `COUNTIFS` on status; rates use `IFERROR` guards so empty trackers show `0%`/`—` instead of errors.

## New in v2 — UX upgrade

**Home** — launcher sheet (opens first). Live pulse stats count breaches, at-risk items,
follow-ups due within 2 days, and units not ready; navy nav buttons hyperlink to every sheet.

**Action Center** — the daily priority queue, five auto-surfaced lists:
1. 🔴 SLA Breaches — work orders past their SLA target
2. 🟡 At Risk — due within 2 days
3. 📦 Follow-Ups Due — unresolved service-recovery items with a follow-up date within 2 days
4. 🏠 Turnover QC Failed — units sent back for rework
5. 🔑 Renewal Outreach — intent Unknown or Undecided

Mechanism (portable, no array formulas): each tracker has a hidden `_seq_*` helper column
that assigns a sequential number to attention-worthy rows, e.g. on Work Orders col M:

```
_seq_breach:  =IF($L2="Breached",COUNTIF($L$2:$L2,"Breached"),"")
```

The Action Center then pulls item *k* with `=IFERROR(MATCH(k,'Work Orders'!$M$2:$M$500,0)+1,"")`
and `INDEX`es the display columns off that row number, plus a `HYPERLINK` back to the
source row. `IF`/`COUNTIF`/`COUNTIFS`/`MATCH`/`INDEX`/`HYPERLINK` all evaluate identically
in Excel, Google Sheets, and LibreOffice — deliberately chosen over `AGGREGATE`/`SMALL+IF`
array patterns, which behave inconsistently outside Excel.

**Dashboard charts** — four live charts (work orders by category, SLA status donut, turnover
pipeline, renewal intent donut) fed by `COUNTIFS` summary tables on the hidden `ChartData` sheet.

**Weekly Report** — print-ready one-pager: this week's closed work orders, avg days to close
(`AVERAGEIFS` on closed rows only), current breaches, units made ready, renewals secured,
avg satisfaction, and the top 3 breaches. Fit-to-page portrait setup included.
