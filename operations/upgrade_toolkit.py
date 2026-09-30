#!/usr/bin/env python3
"""Upgrade the Property Operations Toolkit to v2: genuine game-changer UX.

Layers on top of build_toolkit.py (which is re-run first for a clean base):
  1. HOME sheet        - app-style launcher with live pulse stats + big nav buttons
  2. ACTION CENTER     - auto-surfaced priority lists (breaches, at-risk, follow-ups,
                         QC fails, renewal outreach) driven by live AGGREGATE formulas
  3. DASHBOARD charts  - real Excel charts (WO by category, SLA donut, turnover, intent)
  4. WEEKLY REPORT     - print-ready leadership one-pager, formula-driven
  5. Tab colors, Home set as the opening sheet.

Usage:  python3 upgrade_toolkit.py
"""
import runpy
from pathlib import Path
from copy import copy

from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, PieChart, Reference

HERE = Path(__file__).resolve().parent
XLSX = HERE / "property-operations-toolkit.xlsx"

# Rebuild the base workbook from scratch so the upgrade is always consistent.
runpy.run_path(str(HERE / "build_toolkit.py"), run_name="__main__")

wb = load_workbook(XLSX)

# ---------------------------------------------------------------- palette
NAVY   = "1F3864"
GOLD   = "D9A441"
RED    = "C00000"
AMBER  = "ED7D31"
GREEN  = "2E7D32"
BLUE   = "2E75B6"
DGRAY  = "404040"
LGRAY  = "F2F2F2"
WHITE  = "FFFFFF"

thin = Side(style="thin", color="BFBFBF")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)

title_font  = Font(name="Calibri", size=22, bold=True, color=NAVY)
sub_font    = Font(name="Calibri", size=11, italic=True, color="808080")
sec_font    = Font(name="Calibri", size=13, bold=True, color=WHITE)
hdr_font    = Font(name="Calibri", size=10, bold=True, color=WHITE)
body_font   = Font(name="Calibri", size=11, color=DGRAY)
big_font    = Font(name="Calibri", size=26, bold=True)
btn_font    = Font(name="Calibri", size=14, bold=True, color=WHITE)
link_font   = Font(name="Calibri", size=10, bold=True, color=BLUE, underline="single")

def style_range(ws, row, col_lo, col_hi, font=None, fill=None, alignment=None,
                border=None, number_format=None):
    for c in range(col_lo, col_hi + 1):
        cell = ws.cell(row=row, column=c)
        if font: cell.font = font
        if fill: cell.fill = fill
        if alignment: cell.alignment = alignment
        if border: cell.border = border
        if number_format: cell.number_format = number_format

# ============================================================ 1. HOME ===
home = wb.create_sheet("Home", 0)
home.sheet_properties.tabColor = GOLD
home.sheet_view.showGridLines = False
for col, w in zip("ABCDEFGHI", [3, 22, 22, 22, 22, 22, 22, 22, 3]):
    home.column_dimensions[col].width = w

home.merge_cells("B1:H1")
c = home["B1"]; c.value = "Property Operations Toolkit"
c.font = title_font; c.alignment = Alignment(horizontal="center", vertical="center")
home.row_dimensions[1].height = 40
home.merge_cells("B2:H2")
c = home["B2"]; c.value = "One command center for work orders, turnover, retention, and service recovery."
c.font = sub_font; c.alignment = Alignment(horizontal="center")

# ---- pulse stats (live formulas)
home.merge_cells("B4:H4")
c = home["B4"]; c.value = "PULSE — RIGHT NOW"
c.font = Font(name="Calibri", size=11, bold=True, color="808080")
pulse = [
    ("B", "C", RED,   "SLA breaches",      '=COUNTIFS(\'Work Orders\'!L2:L500,"Breached")'),
    ("D", "E", AMBER, "At risk",           '=COUNTIFS(\'Work Orders\'!L2:L500,"At Risk")'),
    ("F", "G", BLUE,  "Follow-ups due",    '=COUNTIFS(\'Service Recovery\'!H2:H500,"No",\'Service Recovery\'!I2:I500,"<>"&"",\'Service Recovery\'!I2:I500,"<="&TODAY()+2)'),
    ("H", "I", GREEN, "Units not ready",   '=COUNTA(Turnover!A2:A500)-COUNTIFS(Turnover!H2:H500,"Ready")-COUNTIFS(Turnover!H2:H500,"Ready for QC")'),
]
for c0, c1, color, label, formula in pulse:
    ci0 = ord(c0) - 64; ci1 = ord(c1) - 64
    home.merge_cells(f"{c0}5:{c1}5")
    cell = home[f"{c0}5"]; cell.value = label.upper()
    cell.font = Font(name="Calibri", size=9, bold=True, color="808080")
    cell.alignment = Alignment(horizontal="center")
    home.merge_cells(f"{c0}6:{c1}6")
    cell = home[f"{c0}6"]; cell.value = formula
    cell.font = Font(name="Calibri", size=26, bold=True, color=color)
    cell.alignment = Alignment(horizontal="center", vertical="center")
    home.merge_cells(f"{c0}7:{c1}7")
    cell = home[f"{c0}7"]; cell.value = "View in Action Center →"
    cell.font = Font(name="Calibri", size=9, color=BLUE, underline="single")
    cell.alignment = Alignment(horizontal="center")
    cell.hyperlink = "#'Action Center'!A1"
    style_range(home, 5, ci0, ci1, border=BORDER)
    style_range(home, 6, ci0, ci1, border=BORDER)
    style_range(home, 7, ci0, ci1, border=BORDER)
home.row_dimensions[6].height = 38

# ---- nav buttons
home.merge_cells("B9:H9")
c = home["B9"]; c.value = "OPEN A TRACKER"
c.font = Font(name="Calibri", size=11, bold=True, color="808080")

def button(ws, rng, label, target, fill=NAVY):
    ws.merge_cells(rng)
    top = rng.split(":")[0]
    cell = ws[top]
    cell.value = label
    cell.font = btn_font
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell.fill = PatternFill("solid", fgColor=fill)
    cell.hyperlink = target
    r0 = int("".join(ch for ch in top if ch.isdigit()))
    r1 = int("".join(ch for ch in rng.split(":")[1] if ch.isdigit()))
    for r in range(r0, r1 + 1):
        ws.row_dimensions[r].height = 30

button(home, "B10:C12", "Dashboard",            "#'Dashboard'!A1")
button(home, "D10:E12", "Work Orders",          "#'Work Orders'!A1")
button(home, "F10:G12", "Turnover",             "#'Turnover'!A1")
button(home, "B14:C16", "Retention",            "#'Retention'!A1")
button(home, "D14:E16", "Service Recovery",     "#'Service Recovery'!A1")
button(home, "F14:G16", "⚡ Action Center",      "#'Action Center'!A1", fill=RED)
button(home, "H14:H16", "Weekly\nReport",       "#'Weekly Report'!A1", fill=GREEN)
home["H14"].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

home.merge_cells("B18:H19")
c = home["B18"]
c.value = ("SAMPLE DATA — every number on this page is live. Add a row to any tracker and the pulse, "
           "charts, Action Center, and Weekly Report update on their own.\nBuilt by Jordan S. Williams · Resident Experience Specialist (Shift Lead)")
c.font = Font(name="Calibri", size=9, italic=True, color="808080")
c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

# =================================================== 2. ACTION CENTER ===
# ---- hidden sequence helpers on the source sheets.
# Portable mechanism (no array formulas): each attention-worthy row gets a
# sequential number via COUNTIF(S); the Action Center then MATCHes 1..n.
# Works in Excel, LibreOffice, and Google Sheets.
def add_seq(ws, col, header, formula):
    hcell = ws.cell(row=1, column=col, value=header)
    hcell.font = hdr_font
    hcell.fill = PatternFill("solid", fgColor=NAVY)
    hcell.alignment = Alignment(horizontal="center", vertical="center")
    for r in range(2, 501):
        ws.cell(row=r, column=col, value=formula.replace("{r}", str(r)))
    ws.column_dimensions[get_column_letter(col)].hidden = True

_wo = wb["Work Orders"]; _sr = wb["Service Recovery"]
_to = wb["Turnover"]; _rt = wb["Retention"]
add_seq(_wo, 13, "_seq_breach",
        '=IF($L{r}="Breached",COUNTIF($L$2:$L{r},"Breached"),"")')
add_seq(_wo, 14, "_seq_risk",
        '=IF($L{r}="At Risk",COUNTIF($L$2:$L{r},"At Risk"),"")')
add_seq(_sr, 11, "_seq_followup",
        '=IF(AND($H{r}="No",$I{r}<>"",$I{r}<=TODAY()+2),'
        'COUNTIFS($H$2:$H{r},"No",$I$2:$I{r},"<>"&"",$I$2:$I{r},"<="&TODAY()+2),"")')
add_seq(_to, 11, "_seq_qcfail",
        '=IF($I{r}="No",COUNTIF($I$2:$I{r},"No"),"")')
add_seq(_rt, 10, "_seq_outreach",
        '=IF(OR($G{r}="Unknown",$G{r}="Undecided"),'
        'COUNTIFS($G$2:$G{r},"Unknown")+COUNTIFS($G$2:$G{r},"Undecided"),"")')

ac = wb.create_sheet("Action Center", 1)
ac.sheet_properties.tabColor = RED
ac.column_dimensions["A"].hidden = True   # helper column (row numbers)
for col, w in [("B", 13), ("C", 10), ("D", 13), ("E", 15), ("F", 13), ("G", 13)]:
    ac.column_dimensions[col].width = w

ac.merge_cells("B1:G1")
c = ac["B1"]; c.value = "⚡ Action Center"
c.font = Font(name="Calibri", size=20, bold=True, color=RED)
ac.merge_cells("B2:G2")
c = ac["B2"]; c.value = "Everything that needs you, surfaced automatically. Fix it in the source tracker — this page updates itself."
c.font = sub_font

def section(ws, row, title, fill, headers, n, helper_formula, col_formulas):
    """Write one attention section. helper_formula has {k} = 1-based item index.
    col_formulas: list of (header, formula_template) with {r} = row, {a} = $A{r}."""
    ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=2 + len(headers) - 1)
    cell = ws.cell(row=row, column=2); cell.value = title
    cell.font = sec_font; cell.fill = PatternFill("solid", fgColor=fill)
    cell.alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[row].height = 26
    for i, (h, _) in enumerate(headers):
        cell = ws.cell(row=row + 1, column=2 + i); cell.value = h
        cell.font = hdr_font; cell.fill = PatternFill("solid", fgColor="404040")
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BORDER
    ws.row_dimensions[row + 1].height = 30
    for j in range(n):
        r = row + 2 + j
        k = j + 1
        ws.cell(row=r, column=1).value = helper_formula.format(k=k)
        for i, (_, tmpl) in enumerate(headers):
            cell = ws.cell(row=r, column=2 + i)
            cell.value = col_formulas[i].format(r=r, a=f"$A{r}")
            cell.font = body_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = BORDER
            if "Open →" in col_formulas[i]:
                cell.font = link_font
        ws.row_dimensions[r].height = 20
    return row + 2 + n

def idx(src, col, a):
    return f"=IF({a}=\"\",\"\",INDEX('{src}'!{col}:{col},{a}))"

def golink(src, a):
    return f"=IF({a}=\"\",\"\",HYPERLINK(\"#'{src}'!A\"&{a},\"Open →\"))"

WO = "'Work Orders'!$L$2:$L$500"
# ---- 1. SLA breaches
r = section(
    ac, 3, "🔴  SLA BREACHES — past target, act now", RED,
    [("WO-ID", 0), ("Unit", 0), ("Priority", 0), ("Days overdue", 0), ("", 0)],
    8,
    "=IFERROR(MATCH({k},'Work Orders'!$M$2:$M$500,0)+1,\"\")",
    [idx("Work Orders", "A", "{a}"), idx("Work Orders", "C", "{a}"),
     idx("Work Orders", "E", "{a}"),
     "=IF({a}=\"\",\"\",INDEX('Work Orders'!K:K,{a})-INDEX('Work Orders'!J:J,{a}))",
     golink("Work Orders", "{a}")],
)
# ---- 2. At risk
r = section(
    ac, r + 1, "🟡  AT RISK — due within 2 days", AMBER,
    [("WO-ID", 0), ("Unit", 0), ("Priority", 0), ("Days left", 0), ("", 0)],
    6,
    "=IFERROR(MATCH({k},'Work Orders'!$N$2:$N$500,0)+1,\"\")",
    [idx("Work Orders", "A", "{a}"), idx("Work Orders", "C", "{a}"),
     idx("Work Orders", "E", "{a}"),
     "=IF({a}=\"\",\"\",INDEX('Work Orders'!J:J,{a})-INDEX('Work Orders'!K:K,{a}))",
     golink("Work Orders", "{a}")],
)
# ---- 3. Follow-ups due
SR_H = "'Service Recovery'!$H$2:$H$500"
SR_I = "'Service Recovery'!$I$2:$I$500"
r = section(
    ac, r + 1, "📦  FOLLOW-UPS DUE — within 2 days, still open", BLUE,
    [("Follow-up", 0), ("Unit", 0), ("Category", 0), ("Severity", 0), ("", 0)],
    6,
    "=IFERROR(MATCH({k},'Service Recovery'!$K$2:$K$500,0)+1,\"\")",
    [idx("Service Recovery", "I", "{a}"), idx("Service Recovery", "B", "{a}"),
     idx("Service Recovery", "C", "{a}"), idx("Service Recovery", "E", "{a}"),
     golink("Service Recovery", "{a}")],
)
for rr in range(r - 6, r):
    ac.cell(row=rr, column=2).number_format = "mm/dd/yyyy"
# ---- 4. Turnover QC failed
r = section(
    ac, r + 1, "🏠  TURNOVER — QC failed, needs rework", "7030A0",
    [("Unit", 0), ("Building", 0), ("Top deficiency", 0), ("Deficiencies", 0), ("", 0)],
    5,
    "=IFERROR(MATCH({k},Turnover!$K$2:$K$500,0)+1,\"\")",
    [idx("Turnover", "A", "{a}"), idx("Turnover", "B", "{a}"),
     idx("Turnover", "G", "{a}"), idx("Turnover", "F", "{a}"),
     golink("Turnover", "{a}")],
)
# ---- 5. Renewal outreach
r = section(
    ac, r + 1, "🔑  RENEWAL OUTREACH — intent unknown or undecided", GREEN,
    [("Unit", 0), ("Lease end", 0), ("Intent", 0), ("Touches", 0), ("", 0)],
    8,
    "=IFERROR(MATCH({k},Retention!$J$2:$J$500,0)+1,\"\")",
    [idx("Retention", "A", "{a}"), idx("Retention", "C", "{a}"),
     idx("Retention", "G", "{a}"), idx("Retention", "F", "{a}"),
     golink("Retention", "{a}")],
)
for rr in range(r - 8, r):
    ac.cell(row=rr, column=3).number_format = "mm/dd/yyyy"

# ================================================= 3. CHART DATA (hidden)
cd = wb.create_sheet("ChartData")
cd.sheet_state = "hidden"
cd["A1"] = "Category"; cd["B1"] = "Count"
cats = ["Plumbing", "Electrical", "HVAC", "Appliance", "Lock/Key", "Pest",
        "Common Area", "Noise"]
for i, cat in enumerate(cats, start=2):
    cd.cell(row=i, column=1, value=cat)
    cd.cell(row=i, column=2,
            value=f"=COUNTIFS('Work Orders'!D2:D500,A{i})")
cd["D1"] = "SLA Status"; cd["E1"] = "Count"
for i, s in enumerate(["Breached", "At Risk", "On Track", "Closed"], start=2):
    cd.cell(row=i, column=4, value=s)
    cd.cell(row=i, column=5,
            value=f"=COUNTIFS('Work Orders'!L2:L500,D{i})")
cd["G1"] = "Make-Ready"; cd["H1"] = "Count"
for i, s in enumerate(["Ready for QC", "In Progress", "Not Started", "Ready"], start=2):
    cd.cell(row=i, column=7, value=s)
    cd.cell(row=i, column=8, value=f"=COUNTIFS(Turnover!H2:H500,G{i})")
cd["J1"] = "Intent"; cd["K1"] = "Count"
for i, s in enumerate(["Renewing", "Undecided", "Unknown", "Not Renewing"], start=2):
    cd.cell(row=i, column=10, value=s)
    cd.cell(row=i, column=11, value=f"=COUNTIFS(Retention!G2:G500,J{i})")

# ================================================= 4. DASHBOARD CHARTS ===
dash = wb["Dashboard"]
dash.sheet_properties.tabColor = NAVY
for col in "CDEFGHIJKL":
    if dash.column_dimensions[col].width < 10:
        dash.column_dimensions[col].width = 10
dash.column_dimensions["C"].width = 3

def add_bar(ws, title, anchor, lab_col, val_col, n):
    ch = BarChart(); ch.type = "col"; ch.style = 10; ch.title = title
    ch.height = 7; ch.width = 13
    ch.add_data(Reference(cd, min_col=val_col, min_row=1, max_row=n), titles_from_data=True)
    ch.set_categories(Reference(cd, min_col=lab_col, min_row=2, max_row=n))
    ch.legend = None
    ws.add_chart(ch, anchor)

def add_pie(ws, title, anchor, lab_col, val_col, n):
    from openpyxl.chart.label import DataLabelList
    ch = PieChart(); ch.title = title; ch.style = 10
    ch.height = 7; ch.width = 13
    ch.add_data(Reference(cd, min_col=val_col, min_row=1, max_row=n), titles_from_data=True)
    ch.set_categories(Reference(cd, min_col=lab_col, min_row=2, max_row=n))
    ch.dataLabels = DataLabelList(); ch.dataLabels.showPercent = True
    ws.add_chart(ch, anchor)

add_bar(dash, "Work Orders by Category", "D4", 1, 2, 9)
add_pie(dash, "SLA Status", "L4", 4, 5, 5)
add_bar(dash, "Turnover Pipeline", "D21", 7, 8, 5)
add_pie(dash, "Renewal Intent", "L21", 10, 11, 5)

dash.merge_cells("D2:L2")
c = dash["D2"]
c.value = "Charts update live from the trackers — see the Action Center for what needs you today →"
c.font = Font(name="Calibri", size=10, italic=True, color=BLUE, underline="single")
c.hyperlink = "#'Action Center'!A1"

# ================================================= 5. WEEKLY REPORT ====
wr = wb.create_sheet("Weekly Report")
wr.sheet_properties.tabColor = GREEN
wr.sheet_view.showGridLines = False
for col, w in [("A", 3), ("B", 30), ("C", 20), ("D", 16)]:
    wr.column_dimensions[col].width = w
wr.merge_cells("B1:C1")
c = wr["B1"]; c.value = "Weekly Operations Report"; c.font = title_font
wr.merge_cells("B2:C2")
c = wr["B2"]
c.value = '="Week of "&TEXT(TODAY()-6,"mm/dd")&" – "&TEXT(TODAY(),"mm/dd/yyyy")'
c.font = Font(name="Calibri", size=12, bold=True, color=DGRAY)

wr.merge_cells("B4:C4")
c = wr["B4"]; c.value = "THIS WEEK'S NUMBERS"; c.font = sec_font
c.fill = PatternFill("solid", fgColor=NAVY)
wr.row_dimensions[4].height = 26
kpis = [
    ("Work orders closed this week",
     '=COUNTIFS(\'Work Orders\'!H2:H500,"Closed",\'Work Orders\'!I2:I500,">="&TODAY()-7)'),
    ("Average days to close",
     '=IFERROR(ROUND(AVERAGEIFS(\'Work Orders\'!K2:K500,\'Work Orders\'!H2:H500,"Closed"),1),"—")'),
    ("SLA breaches right now", '=COUNTIFS(\'Work Orders\'!L2:L500,"Breached")'),
    ("Units made ready this week", '=COUNTIFS(Turnover!J2:J500,">="&TODAY()-7)'),
    ("Renewals secured", '=COUNTIFS(Retention!G2:G500,"Renewing")'),
    ("Avg. service-recovery satisfaction",
     '=IFERROR(ROUND(AVERAGE(\'Service Recovery\'!J2:J500),2),"—")'),
]
for i, (label, formula) in enumerate(kpis):
    r = 5 + i
    wr.cell(row=r, column=2, value=label).font = body_font
    cell = wr.cell(row=r, column=3, value=formula)
    cell.font = Font(name="Calibri", size=13, bold=True, color=NAVY)
    cell.alignment = Alignment(horizontal="center")
    style_range(wr, r, 2, 3, border=BORDER)
    wr.row_dimensions[r].height = 22

wr.merge_cells("B12:D12")
c = wr["B12"]; c.value = "TOP 3 BREACHES"; c.font = sec_font
c.fill = PatternFill("solid", fgColor=RED)
wr.row_dimensions[12].height = 26
for i, h in enumerate(["WO-ID", "Unit", "Days overdue"]):
    cell = wr.cell(row=13, column=2 + i, value=h)
    cell.font = hdr_font; cell.fill = PatternFill("solid", fgColor="404040")
    cell.alignment = Alignment(horizontal="center"); cell.border = BORDER
for j in range(3):
    r = 14 + j; k = j + 1
    a = f"=IFERROR(MATCH({k},'Work Orders'!$M$2:$M$500,0)+1,\"\")"
    wr.cell(row=r, column=1, value=a)
    wr.cell(row=r, column=2,
            value=f"=IF($A{r}=\"\",\"\",INDEX('Work Orders'!A:A,$A{r}))").font = body_font
    wr.cell(row=r, column=3,
            value=f"=IF($A{r}=\"\",\"\",INDEX('Work Orders'!C:C,$A{r}))").font = body_font
    d = wr.cell(row=r, column=4,
                value=f"=IF($A{r}=\"\",\"\",INDEX('Work Orders'!K:K,$A{r})-INDEX('Work Orders'!J:J,$A{r}))")
    d.font = Font(name="Calibri", size=11, bold=True, color=RED)
    for cc in (2, 3, 4):
        wr.cell(row=r, column=cc).border = BORDER
        wr.cell(row=r, column=cc).alignment = Alignment(horizontal="center")
wr.column_dimensions["A"].hidden = True

wr.merge_cells("B18:D20")
c = wr["B18"]
c.value = ("How to use this page: print it (or save as PDF) for standup or your 1:1. "
           "Every number is live — no manual rollup. Full detail lives in the Action Center.")
c.font = Font(name="Calibri", size=9, italic=True, color="808080")
c.alignment = Alignment(wrap_text=True, vertical="top")
wr.sheet_properties.pageSetUpPr.fitToPage = True
wr.page_setup.fitToWidth = 1
wr.page_setup.fitToHeight = 1
wr.page_setup.orientation = "portrait"

# ------------------------------------------------------- tab colors, go
# README: document the new sheets
_readme = wb["README"]
_readme.insert_rows(11, 4)
new_lines = [
    ("Home", "App-style launcher: live pulse stats and one-click navigation buttons to every tracker."),
    ("Action Center", "Your daily priority queue — SLA breaches, at-risk items, due follow-ups, QC failures, and renewal outreach surface automatically via hidden _seq_ helpers. Fix the source row; this page updates itself."),
    ("Weekly Report", "Print-ready one-pager for standup or 1:1s: this week's numbers plus the top 3 breaches. Every value is a live formula."),
    ("", ""),
]
for i, (a, b) in enumerate(new_lines):
    _readme.cell(row=11 + i, column=1, value=a).font = Font(name="Calibri", size=11, bold=True, color="1F3864")
    _readme.cell(row=11 + i, column=2, value=b).font = Font(name="Calibri", size=11, color="404040")
    _readme.cell(row=11 + i, column=2).alignment = Alignment(wrap_text=True, vertical="top")
    _readme.row_dimensions[11 + i].height = 30

for _s in (wb["Home"], ac):
    _s.sheet_properties.pageSetUpPr.fitToPage = True
    _s.page_setup.orientation = "landscape"
    _s.page_setup.fitToWidth = 1
    _s.page_setup.fitToHeight = 1
for name, color in [("Work Orders", BLUE), ("Turnover", AMBER),
                    ("Retention", GREEN), ("Service Recovery", "7030A0"),
                    ("README", "808080")]:
    if name in wb.sheetnames:
        wb[name].sheet_properties.tabColor = color
wb.active = 0  # open on Home

wb.save(XLSX)
print("Saved:", XLSX)
print("Sheets:", wb.sheetnames)
