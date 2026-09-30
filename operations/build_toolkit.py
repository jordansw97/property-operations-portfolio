#!/usr/bin/env python3
"""Build the Property Operations Toolkit workbook.

Generates operations/property-operations-toolkit.xlsx — a proof-of-concept
property operations management workbook: dashboard, work order tracking,
turnover readiness, retention, and service recovery. All data is fictional
sample data for demonstration.
"""
from datetime import date
from pathlib import Path
from copy import copy

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import CellIsRule, FormulaRule

OUT = Path(__file__).resolve().parent / "property-operations-toolkit.xlsx"

NAVY = "16233F"
GOLD = "C19A3D"
WHITE = "FFFFFF"
DARK = "23272E"
GRAY = "5A6472"
LIGHT = "F4F1E8"
GREEN = "1E7E34"
GREEN_BG = "D4EDDA"
AMBER = "856404"
AMBER_BG = "FFF3CD"
RED = "C0392B"
RED_BG = "F8D7DA"
GRAY_BG = "E9ECEF"

header_font = Font(name="Calibri", bold=True, color=WHITE, size=11)
header_fill = PatternFill("solid", fgColor=NAVY)
title_font = Font(name="Calibri", bold=True, color=NAVY, size=16)
subtitle_font = Font(name="Calibri", color=GRAY, size=11, italic=True)
body_font = Font(name="Calibri", size=11, color=DARK)
thin = Side(style="thin", color="B0B7C3")
border = Border(left=thin, right=thin, top=thin, bottom=thin)
center = Alignment(horizontal="center", vertical="center", wrap_text=True)
left_wrap = Alignment(horizontal="left", vertical="center", wrap_text=True)

SAMPLE_NOTE = ("All data on this sheet is fictional sample data for demonstration "
               "purposes. Replace with live property data to use operationally.")


def style_header(ws, ncols, row=1):
    for col in range(1, ncols + 1):
        c = ws.cell(row=row, column=col)
        c.font = header_font
        c.fill = header_fill
        c.alignment = center
        c.border = border


def finalize_sheet(ws, ncols, widths):
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, max_col=ncols):
        for c in row:
            c.border = border
            if c.font == Font():  # untouched default
                pass
    # body font + alignment defaults
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, max_col=ncols):
        for c in row:
            if not c.font.bold or c.font.color is None:
                pass


def add_validation(ws, col_letter, formula, start_row=2, end_row=200):
    dv = DataValidation(type="list", formula1=formula, allow_blank=True)
    dv.error = "Please choose a value from the dropdown."
    dv.errorTitle = "Invalid entry"
    ws.add_data_validation(dv)
    dv.add(f"{col_letter}{start_row}:{col_letter}{end_row}")


wb = Workbook()

# ---------------------------------------------------------------- README
ws = wb.active
ws.title = "README"
ws["A1"] = "Property Operations Toolkit"
ws["A1"].font = title_font
ws["A2"] = "Proof of concept · Jordan S. Williams · Resident Experience Specialist (Shift Lead)"
ws["A2"].font = subtitle_font
ws["A4"] = SAMPLE_NOTE
ws["A4"].font = Font(name="Calibri", italic=True, color=RED, size=11)
lines = [
    ("Dashboard", "Live KPI summary. Every metric is a formula reading the tracker sheets — no manual tallying."),
    ("Work Orders", "Full work-order lifecycle: intake → assignment → SLA tracking → close. SLA targets set automatically by priority (Emergency 1d, High 3d, Standard 7d, Low 14d); status flags Breached / At Risk / On Track in real time."),
    ("Turnover", "Unit make-ready pipeline for move-in surges: inspection → deficiencies → QC → ready. Built for high-volume turnover like a 2,224-unit surge."),
    ("Retention", "Lease-renewal pipeline: offer sent, outreach touches, resident intent, and at-risk reasons. Retention rate calculated on decided units only."),
    ("Service Recovery", "Resident experience log: issue → owner → action → follow-up → satisfaction score. Closes the loop on service failures."),
    ("", ""),
    ("How to use it:", ""),
    ("1.", "Replace the sample rows with live data (keep the header row and formulas)."),
    ("2.", "Use the dropdowns — they enforce clean categories for reporting."),
    ("3.", "Watch the Dashboard: it updates itself as trackers change."),
    ("4.", "Extend it: add sheets per building, pivot the trackers monthly, or feed the data into a BI tool."),
]
r = 6
for label, desc in lines:
    ws[f"A{r}"] = label
    ws[f"B{r}"] = desc
    ws[f"A{r}"].font = Font(name="Calibri", bold=True, size=11, color=NAVY if desc else DARK)
    ws[f"B{r}"].font = body_font
    ws[f"B{r}"].alignment = left_wrap
    r += 1
ws.column_dimensions["A"].width = 16
ws.column_dimensions["B"].width = 130

# --------------------------------------------------------------- DASHBOARD
ws = wb.create_sheet("Dashboard")
ws["A1"] = "Operations Dashboard"
ws["A1"].font = title_font
ws["A2"] = "Live KPIs — every value below is a formula. Sample data."
ws["A2"].font = subtitle_font

kpis = [
    ("WORK ORDERS", None),
    ("Open work orders", "=COUNTIFS('Work Orders'!H2:H500,\"Open\")+COUNTIFS('Work Orders'!H2:H500,\"In Progress\")+COUNTIFS('Work Orders'!H2:H500,\"Waiting on Parts\")"),
    ("SLA breaches (open)", "=COUNTIFS('Work Orders'!L2:L500,\"Breached\")"),
    ("At risk of breach", "=COUNTIFS('Work Orders'!L2:L500,\"At Risk\")"),
    ("Emergency orders open", "=COUNTIFS('Work Orders'!E2:E500,\"Emergency\",'Work Orders'!H2:H500,\"<>Closed\")"),
    ("Avg days to close", "=IFERROR(ROUND(AVERAGEIFS('Work Orders'!K2:K500,'Work Orders'!H2:H500,\"Closed\"),1),\"—\")"),
    ("TURNOVER", None),
    ("Units tracked", "=COUNTA(Turnover!A2:A500)"),
    ("Units ready / QC-ready", "=COUNTIFS(Turnover!H2:H500,\"Ready\")+COUNTIFS(Turnover!H2:H500,\"Ready for QC\")"),
    ("% ready", "=IFERROR((COUNTIFS(Turnover!H2:H500,\"Ready\")+COUNTIFS(Turnover!H2:H500,\"Ready for QC\"))/COUNTA(Turnover!A2:A500),0)"),
    ("Avg days move-out → ready", "=IFERROR(ROUND(AVERAGE(Turnover!K2:K500),1),\"—\")"),
    ("RETENTION", None),
    ("Leases tracked", "=COUNTA(Retention!A2:A500)"),
    ("Renewing", "=COUNTIFS(Retention!G2:G500,\"Renewing\")"),
    ("At-risk (undecided + leaving)", "=COUNTIFS(Retention!G2:G500,\"Undecided\")+COUNTIFS(Retention!G2:G500,\"Not Renewing\")"),
    ("Retention rate (decided)", "=IFERROR(COUNTIFS(Retention!G2:G500,\"Renewing\")/COUNTIFS(Retention!G2:G500,\"<>Unknown\",Retention!G2:G500,\"<>\"),0)"),
    ("SERVICE RECOVERY", None),
    ("Open recovery items", "=COUNTIFS('Service Recovery'!H2:H500,\"No\")"),
    ("Avg satisfaction (resolved)", "=IFERROR(ROUND(AVERAGE('Service Recovery'!J2:J500),2),\"—\")"),
]
row = 4
for label, formula in kpis:
    if formula is None:
        ws[f"A{row}"] = label
        ws[f"A{row}"].font = Font(name="Calibri", bold=True, color=WHITE, size=11)
        ws[f"A{row}"].fill = PatternFill("solid", fgColor=NAVY)
        ws.merge_cells(f"A{row}:B{row}")
        row += 1
        continue
    ws[f"A{row}"] = label
    ws[f"A{row}"].font = body_font
    ws[f"B{row}"] = formula
    ws[f"B{row}"].font = Font(name="Calibri", bold=True, size=13, color=NAVY)
    ws[f"B{row}"].alignment = center
    ws[f"B{row}"].border = border
    if "rate" in label or "% ready" in label:
        ws[f"B{row}"].number_format = "0%"
    row += 1
ws[f"A{row+1}"] = "Last updated:"
ws[f"B{row+1}"] = "=TODAY()"
ws[f"B{row+1}"].number_format = "MM/DD/YYYY"
ws.column_dimensions["A"].width = 34
ws.column_dimensions["B"].width = 22

# ------------------------------------------------------------ WORK ORDERS
ws = wb.create_sheet("Work Orders")
headers = ["WO-ID", "Date Opened", "Unit", "Category", "Priority", "Description",
           "Assigned To", "Status", "Date Closed", "SLA Target (days)",
           "Days Open", "SLA Status"]
widths = [10, 13, 10, 18, 11, 44, 14, 16, 13, 14, 11, 12]
for i, h in enumerate(headers, start=1):
    ws.cell(row=1, column=i, value=h)
style_header(ws, len(headers))
ws["A2"] = SAMPLE_NOTE  # placeholder replaced below

wo_data = [
    ("WO-1001", date(2026, 9, 28), "A-101", "Plumbing", "High", "Kitchen sink draining slowly; possible grease buildup", "M. Torres", "In Progress", None),
    ("WO-1002", date(2026, 9, 28), "B-214", "HVAC", "Emergency", "AC not cooling below 78°F; unit running constantly", "D. Kim", "In Progress", None),
    ("WO-1003", date(2026, 9, 27), "C-309", "Appliance", "Standard", "Garbage disposal jammed; humming but not spinning", "R. Patel", "Open", None),
    ("WO-1004", date(2026, 9, 27), "A-118", "Lock/Key", "High", "Bedroom door lock sticking; resident unable to lock", "J. Williams", "In Progress", None),
    ("WO-1005", date(2026, 9, 26), "D-102", "Electrical", "Standard", "Hallway light flickering in entry", "M. Torres", "Closed", date(2026, 9, 27)),
    ("WO-1006", date(2026, 9, 26), "B-207", "Plumbing", "Emergency", "Water leaking under bathroom sink; shutoff engaged", "D. Kim", "Closed", date(2026, 9, 26)),
    ("WO-1007", date(2026, 9, 25), "C-315", "Appliance", "Standard", "Dishwasher leaking at front seal during cycle", "R. Patel", "Waiting on Parts", None),
    ("WO-1008", date(2026, 9, 25), "A-122", "Electrical", "High", "Thermostat unresponsive; blank display", "M. Torres", "Closed", date(2026, 9, 26)),
    ("WO-1009", date(2026, 9, 24), "D-118", "Interior", "Low", "Window screen torn in living room", "A. Johnson", "Open", None),
    ("WO-1010", date(2026, 9, 24), "B-201", "Appliance", "Standard", "Stove burner not igniting; gas smell ruled out", "R. Patel", "Closed", date(2026, 9, 25)),
    ("WO-1011", date(2026, 9, 23), "C-301", "HVAC", "High", "Weak airflow in bedroom vent; filter replaced, still weak", "D. Kim", "In Progress", None),
    ("WO-1012", date(2026, 9, 23), "A-109", "Plumbing", "Standard", "Toilet running continuously after flush", "M. Torres", "Closed", date(2026, 9, 24)),
    ("WO-1013", date(2026, 9, 22), "D-105", "Pest Control", "Standard", "Ants along kitchen baseboard near patio door", "Vendor: Apex", "Closed", date(2026, 9, 24)),
    ("WO-1014", date(2026, 9, 22), "B-220", "Electrical", "Standard", "Bathroom GFCI outlet tripped; will not reset", "M. Torres", "Open", None),
    ("WO-1015", date(2026, 9, 21), "C-308", "Interior", "Low", "Scuffed paint on living room wall near entry", "A. Johnson", "Closed", date(2026, 9, 26)),
    ("WO-1016", date(2026, 9, 21), "A-115", "Appliance", "High", "Refrigerator not holding temp; food spoilage risk", "R. Patel", "Closed", date(2026, 9, 22)),
    ("WO-1017", date(2026, 9, 20), "D-111", "Plumbing", "Standard", "Shower head low pressure; likely mineral buildup", "M. Torres", "Open", None),
    ("WO-1018", date(2026, 9, 19), "B-212", "Lock/Key", "High", "Mailbox key broken off in lock", "J. Williams", "Closed", date(2026, 9, 20)),
    ("WO-1019", date(2026, 9, 19), "C-322", "HVAC", "Emergency", "No cooling at all; compressor not engaging", "D. Kim", "Closed", date(2026, 9, 19)),
    ("WO-1020", date(2026, 9, 18), "A-104", "Exterior/Common Area", "Standard", "Breezeway light out on 1st floor", "M. Torres", "Closed", date(2026, 9, 19)),
    ("WO-1021", date(2026, 9, 18), "D-120", "Appliance", "Low", "Microwave turntable not rotating", "Unassigned", "Open", None),
    ("WO-1022", date(2026, 9, 17), "B-205", "Plumbing", "High", "Water heater pilot will not stay lit", "D. Kim", "Waiting on Parts", None),
    ("WO-1023", date(2026, 9, 17), "C-305", "Interior", "Standard", "Closet door off track in primary bedroom", "A. Johnson", "Closed", date(2026, 9, 18)),
    ("WO-1024", date(2026, 9, 16), "A-130", "Electrical", "Standard", "Ceiling fan wobbling at high speed", "M. Torres", "Closed", date(2026, 9, 17)),
    ("WO-1025", date(2026, 9, 15), "D-108", "Pest Control", "High", "Wasp nest under stairwell eave near entry", "Vendor: Apex", "Closed", date(2026, 9, 16)),
    ("WO-1026", date(2026, 9, 14), "B-218", "HVAC", "Standard", "Annual filter + coil check (preventive)", "D. Kim", "Closed", date(2026, 9, 14)),
    ("WO-1027", date(2026, 9, 12), "C-318", "Plumbing", "Low", "Slow drip at tub spout when off", "Unassigned", "Open", None),
    ("WO-1028", date(2026, 9, 10), "A-112", "Interior", "Low", "Touch-up paint: hallway scuffs", "A. Johnson", "Open", None),
]
r = 2
for wid, opened, unit, cat, pri, desc, assigned, status, closed in wo_data:
    ws.cell(row=r, column=1, value=wid)
    c = ws.cell(row=r, column=2, value=opened); c.number_format = "MM/DD/YYYY"
    ws.cell(row=r, column=3, value=unit)
    ws.cell(row=r, column=4, value=cat)
    ws.cell(row=r, column=5, value=pri)
    ws.cell(row=r, column=6, value=desc)
    ws.cell(row=r, column=7, value=assigned)
    ws.cell(row=r, column=8, value=status)
    if closed:
        c = ws.cell(row=r, column=9, value=closed); c.number_format = "MM/DD/YYYY"
    # J: SLA target by priority
    ws.cell(row=r, column=10, value=f'=IF(E{r}="Emergency",1,IF(E{r}="High",3,IF(E{r}="Standard",7,14)))')
    # K: days open
    ws.cell(row=r, column=11, value=f'=IF(H{r}="Closed",I{r}-B{r},TODAY()-B{r})')
    ws.cell(row=r, column=11).number_format = "0"
    # L: SLA status
    ws.cell(row=r, column=12, value=f'=IF(H{r}="Closed","Closed",IF(K{r}>J{r},"Breached",IF(K{r}>=J{r}-1,"At Risk","On Track")))')
    r += 1

finalize_sheet(ws, len(headers), widths)
# date columns centered
for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
    row[1].alignment = center
    if row[8].value:
        row[8].alignment = center
    row[9].alignment = center
    row[10].alignment = center
    row[11].alignment = center
    row[5].alignment = left_wrap
    for c in row:
        c.font = body_font

add_validation(ws, "D", '"Plumbing,Electrical,HVAC,Appliance,Lock/Key,Pest Control,Interior,Exterior/Common Area"')
add_validation(ws, "E", '"Emergency,High,Standard,Low"')
add_validation(ws, "H", '"Open,In Progress,Waiting on Parts,Closed"')

# conditional formatting on SLA status (col L)
ws.conditional_formatting.add("L2:L500", CellIsRule(operator="equal", formula=['"Breached"'],
    fill=PatternFill("solid", fgColor=RED_BG), font=Font(color=RED, bold=True)))
ws.conditional_formatting.add("L2:L500", CellIsRule(operator="equal", formula=['"At Risk"'],
    fill=PatternFill("solid", fgColor=AMBER_BG), font=Font(color=AMBER, bold=True)))
ws.conditional_formatting.add("L2:L500", CellIsRule(operator="equal", formula=['"On Track"'],
    fill=PatternFill("solid", fgColor=GREEN_BG), font=Font(color=GREEN)))
ws.conditional_formatting.add("L2:L500", CellIsRule(operator="equal", formula=['"Closed"'],
    fill=PatternFill("solid", fgColor=GRAY_BG), font=Font(color=GRAY)))
ws.conditional_formatting.add("E2:E500", CellIsRule(operator="equal", formula=['"Emergency"'],
    font=Font(color=RED, bold=True)))

# --------------------------------------------------------------- TURNOVER
ws = wb.create_sheet("Turnover")
headers = ["Unit", "Building", "Move-Out Date", "Inspection Date", "Inspector",
           "Deficiencies Found", "Top Deficiency", "Make-Ready Status",
           "QC Pass", "Ready Date", "Days: Move-Out → Ready"]
widths = [10, 10, 14, 14, 13, 14, 16, 16, 10, 13, 16]
for i, h in enumerate(headers, start=1):
    ws.cell(row=1, column=i, value=h)
style_header(ws, len(headers))

turnover_data = [
    ("A-101", "A", date(2026, 7, 28), date(2026, 7, 29), "J. Williams", 4, "Paint", "Ready", "Yes", date(2026, 8, 4)),
    ("A-115", "A", date(2026, 7, 28), date(2026, 7, 29), "J. Williams", 7, "Flooring", "Ready", "Yes", date(2026, 8, 7)),
    ("A-122", "A", date(2026, 7, 29), date(2026, 7, 30), "M. Torres", 2, "Cleaning", "Ready", "Yes", date(2026, 8, 3)),
    ("B-201", "B", date(2026, 7, 29), date(2026, 7, 30), "M. Torres", 5, "Appliance", "Ready", "Yes", date(2026, 8, 6)),
    ("B-207", "B", date(2026, 7, 30), date(2026, 7, 31), "D. Kim", 9, "Plumbing", "Ready for QC", "Pending", None),
    ("B-214", "B", date(2026, 7, 30), date(2026, 7, 31), "D. Kim", 3, "Paint", "Ready", "Yes", date(2026, 8, 5)),
    ("C-301", "C", date(2026, 7, 31), date(2026, 8, 1), "R. Patel", 6, "Damaged Fixture", "In Progress", "Pending", None),
    ("C-308", "C", date(2026, 7, 31), date(2026, 8, 1), "R. Patel", 1, "Cleaning", "Ready", "Yes", date(2026, 8, 3)),
    ("C-315", "C", date(2026, 8, 1), date(2026, 8, 2), "A. Johnson", 8, "Flooring", "In Progress", "Pending", None),
    ("D-102", "D", date(2026, 8, 1), date(2026, 8, 2), "A. Johnson", 2, "Paint", "Ready", "Yes", date(2026, 8, 5)),
    ("D-108", "D", date(2026, 8, 2), date(2026, 8, 3), "J. Williams", 4, "Appliance", "Ready for QC", "Pending", None),
    ("D-111", "D", date(2026, 8, 2), date(2026, 8, 3), "J. Williams", 0, "None", "Ready", "Yes", date(2026, 8, 4)),
    ("A-104", "A", date(2026, 8, 3), date(2026, 8, 4), "M. Torres", 5, "Plumbing", "In Progress", "Pending", None),
    ("A-109", "A", date(2026, 8, 3), date(2026, 8, 4), "M. Torres", 3, "Electrical", "Ready for QC", "No", None),
    ("B-205", "B", date(2026, 8, 4), date(2026, 8, 5), "D. Kim", 6, "Paint", "In Progress", "Pending", None),
    ("B-212", "B", date(2026, 8, 4), date(2026, 8, 5), "D. Kim", 2, "Cleaning", "Not Started", "Pending", None),
    ("C-305", "C", date(2026, 8, 5), date(2026, 8, 6), "R. Patel", 4, "Damaged Fixture", "In Progress", "Pending", None),
    ("C-318", "C", date(2026, 8, 5), date(2026, 8, 6), "R. Patel", 7, "Flooring", "Not Started", "Pending", None),
    ("D-105", "D", date(2026, 8, 6), date(2026, 8, 7), "A. Johnson", 1, "Cleaning", "Ready", "Yes", date(2026, 8, 8)),
    ("D-118", "D", date(2026, 8, 6), date(2026, 8, 7), "A. Johnson", 3, "Paint", "In Progress", "Pending", None),
    ("A-118", "A", date(2026, 8, 7), date(2026, 8, 8), "J. Williams", 5, "Appliance", "Not Started", "Pending", None),
    ("B-220", "B", date(2026, 8, 7), date(2026, 8, 8), "M. Torres", 2, "Electrical", "In Progress", "Pending", None),
]
r = 2
for unit, bldg, out, insp, inspector, defs, topdef, status, qc, ready in turnover_data:
    ws.cell(row=r, column=1, value=unit)
    ws.cell(row=r, column=2, value=bldg)
    for col, d in ((3, out), (4, insp)):
        c = ws.cell(row=r, column=col, value=d); c.number_format = "MM/DD/YYYY"; c.alignment = center
    ws.cell(row=r, column=5, value=inspector)
    c = ws.cell(row=r, column=6, value=defs); c.alignment = center
    ws.cell(row=r, column=7, value=topdef)
    ws.cell(row=r, column=8, value=status)
    c = ws.cell(row=r, column=9, value=qc); c.alignment = center
    if ready:
        c = ws.cell(row=r, column=10, value=ready); c.number_format = "MM/DD/YYYY"; c.alignment = center
    ws.cell(row=r, column=11, value=f'=IF(J{r}="","",J{r}-C{r})')
    ws.cell(row=r, column=11).number_format = "0"
    ws.cell(row=r, column=11).alignment = center
    r += 1

finalize_sheet(ws, len(headers), widths)
for row in ws.iter_rows(min_row=2, max_row=ws.max_row, max_col=len(headers)):
    for c in row:
        c.font = body_font
    row[0].alignment = center
    row[1].alignment = center

add_validation(ws, "G", '"Paint,Flooring,Appliance,Plumbing,Electrical,Cleaning,Damaged Fixture,None"')
add_validation(ws, "H", '"Not Started,In Progress,Ready for QC,Ready"')
add_validation(ws, "I", '"Yes,No,Pending"')
ws.conditional_formatting.add("H2:H500", CellIsRule(operator="equal", formula=['"Ready"'],
    fill=PatternFill("solid", fgColor=GREEN_BG), font=Font(color=GREEN, bold=True)))
ws.conditional_formatting.add("H2:H500", CellIsRule(operator="equal", formula=['"Ready for QC"'],
    fill=PatternFill("solid", fgColor="D1ECF1"), font=Font(color="0C5460", bold=True)))
ws.conditional_formatting.add("H2:H500", CellIsRule(operator="equal", formula=['"In Progress"'],
    fill=PatternFill("solid", fgColor=AMBER_BG), font=Font(color=AMBER)))
ws.conditional_formatting.add("H2:H500", CellIsRule(operator="equal", formula=['"Not Started"'],
    fill=PatternFill("solid", fgColor=RED_BG), font=Font(color=RED)))
ws.conditional_formatting.add("I2:I500", CellIsRule(operator="equal", formula=['"No"'],
    fill=PatternFill("solid", fgColor=RED_BG), font=Font(color=RED, bold=True)))

# --------------------------------------------------------------- RETENTION
ws = wb.create_sheet("Retention")
headers = ["Unit", "Resident ID", "Lease End", "Monthly Rent", "Renewal Offer Sent",
           "Outreach Touches", "Intent", "Reason (if leaving)", "Notes"]
widths = [10, 13, 13, 14, 16, 14, 14, 20, 40]
for i, h in enumerate(headers, start=1):
    ws.cell(row=1, column=i, value=h)
style_header(ws, len(headers))

retention_data = [
    ("A-101", "R-001", date(2026, 10, 31), 1249, "Yes", 3, "Renewing", "N/A", "Signed 12-mo renewal; roommate staying"),
    ("A-104", "R-002", date(2026, 10, 31), 1199, "Yes", 2, "Undecided", "N/A", "Comparing nearby property; follow up 10/7"),
    ("A-109", "R-003", date(2026, 11, 30), 1299, "Yes", 4, "Renewing", "N/A", "Renewed after service recovery on AC issue"),
    ("A-112", "R-004", date(2026, 10, 31), 1149, "No", 1, "Unknown", "N/A", "No contact yet; priority outreach"),
    ("A-115", "R-005", date(2026, 11, 30), 1349, "Yes", 2, "Not Renewing", "Relocating", "Job transfer out of state"),
    ("A-118", "R-006", date(2026, 12, 31), 1249, "No", 0, "Unknown", "N/A", ""),
    ("A-122", "R-007", date(2026, 10, 31), 1199, "Yes", 5, "Renewing", "N/A", "Long-term resident; requested same unit"),
    ("A-130", "R-008", date(2026, 11, 30), 1099, "Yes", 3, "Undecided", "N/A", "Price-sensitive; reviewing concession options"),
    ("B-201", "R-009", date(2026, 10, 31), 1299, "Yes", 2, "Renewing", "N/A", ""),
    ("B-205", "R-010", date(2026, 11, 30), 1249, "Yes", 4, "Not Renewing", "Roommate Change", "Roommate graduating; can't cover solo"),
    ("B-207", "R-011", date(2026, 10, 31), 1349, "Yes", 3, "Renewing", "N/A", ""),
    ("B-212", "R-012", date(2026, 12, 31), 1199, "No", 1, "Unknown", "N/A", ""),
    ("B-214", "R-013", date(2026, 10, 31), 1299, "Yes", 6, "Renewing", "N/A", "Recovered after repeated HVAC issues; personal follow-ups"),
    ("B-218", "R-014", date(2026, 11, 30), 1149, "Yes", 2, "Undecided", "N/A", "Noise concerns; offered unit transfer info"),
    ("B-220", "R-015", date(2026, 10, 31), 1249, "Yes", 3, "Not Renewing", "Price", "Found cheaper option nearby"),
    ("C-301", "R-016", date(2026, 11, 30), 1399, "Yes", 2, "Renewing", "N/A", ""),
    ("C-305", "R-017", date(2026, 10, 31), 1299, "Yes", 4, "Undecided", "N/A", "Service experience concerns; manager follow-up scheduled"),
    ("C-308", "R-018", date(2026, 12, 31), 1249, "No", 0, "Unknown", "N/A", ""),
    ("C-309", "R-019", date(2026, 10, 31), 1199, "Yes", 3, "Renewing", "N/A", ""),
    ("C-315", "R-020", date(2026, 11, 30), 1349, "Yes", 2, "Not Renewing", "Service Experience", "Multiple maintenance delays; exit interview offered"),
    ("C-318", "R-021", date(2026, 10, 31), 1299, "Yes", 5, "Renewing", "N/A", ""),
    ("C-322", "R-022", date(2026, 11, 30), 1449, "Yes", 1, "Unknown", "N/A", "New outreach started"),
    ("D-102", "R-023", date(2026, 10, 31), 1149, "Yes", 3, "Renewing", "N/A", ""),
    ("D-105", "R-024", date(2026, 12, 31), 1199, "No", 0, "Unknown", "N/A", ""),
]
r = 2
for unit, rid, lease_end, rent, offer, touches, intent, reason, notes in retention_data:
    ws.cell(row=r, column=1, value=unit)
    ws.cell(row=r, column=2, value=rid)
    c = ws.cell(row=r, column=3, value=lease_end); c.number_format = "MM/DD/YYYY"; c.alignment = center
    c = ws.cell(row=r, column=4, value=rent); c.number_format = '"$"#,##0'; c.alignment = center
    c = ws.cell(row=r, column=5, value=offer); c.alignment = center
    c = ws.cell(row=r, column=6, value=touches); c.alignment = center
    ws.cell(row=r, column=7, value=intent)
    ws.cell(row=r, column=8, value=reason)
    ws.cell(row=r, column=9, value=notes)
    r += 1

finalize_sheet(ws, len(headers), widths)
for row in ws.iter_rows(min_row=2, max_row=ws.max_row, max_col=len(headers)):
    for c in row:
        c.font = body_font
    row[0].alignment = center
    row[1].alignment = center
    row[8].alignment = left_wrap

add_validation(ws, "E", '"Yes,No"')
add_validation(ws, "G", '"Renewing,Undecided,Not Renewing,Unknown"')
add_validation(ws, "H", '"N/A,Price,Relocating,Roommate Change,Service Experience,Unit Condition,Other"')
ws.conditional_formatting.add("G2:G500", CellIsRule(operator="equal", formula=['"Renewing"'],
    fill=PatternFill("solid", fgColor=GREEN_BG), font=Font(color=GREEN, bold=True)))
ws.conditional_formatting.add("G2:G500", CellIsRule(operator="equal", formula=['"Not Renewing"'],
    fill=PatternFill("solid", fgColor=RED_BG), font=Font(color=RED, bold=True)))
ws.conditional_formatting.add("G2:G500", CellIsRule(operator="equal", formula=['"Undecided"'],
    fill=PatternFill("solid", fgColor=AMBER_BG), font=Font(color=AMBER, bold=True)))

# ------------------------------------------------------ SERVICE RECOVERY
ws = wb.create_sheet("Service Recovery")
headers = ["Date", "Unit", "Issue Category", "Description", "Severity",
           "Owner", "Action Taken", "Resolved", "Follow-Up Date", "Satisfaction (1-5)"]
widths = [12, 10, 18, 42, 11, 13, 42, 10, 14, 14]
for i, h in enumerate(headers, start=1):
    ws.cell(row=1, column=i, value=h)
style_header(ws, len(headers))

recovery_data = [
    (date(2026, 9, 27), "B-214", "Maintenance Delay", "Third HVAC visit for same issue; resident frustrated", "High", "J. Williams", "Escalated to vendor supervisor; loaned portable AC unit", "Yes", date(2026, 9, 30), 5),
    (date(2026, 9, 26), "C-305", "Service Experience", "Front desk gave wrong package locker code twice", "Medium", "J. Williams", "Apologized in person; walked resident through Parcel Pending app", "Yes", date(2026, 9, 29), 4),
    (date(2026, 9, 25), "D-118", "Noise Complaint", "Ongoing late-night noise from unit above", "Medium", "M. Torres", "Contacted upstairs resident; issued courtesy notice; scheduled follow-up", "No", date(2026, 10, 2), None),
    (date(2026, 9, 24), "A-115", "Move-In Condition", "Unit not fully cleaned at move-in; dust on surfaces", "High", "J. Williams", "Dispatched cleaning crew same day; $50 account credit", "Yes", date(2026, 9, 27), 5),
    (date(2026, 9, 23), "C-315", "Maintenance Delay", "Flooring repair rescheduled twice without notice", "High", "R. Patel", "Called resident directly; committed date met; supervisor QC walk", "Yes", date(2026, 9, 28), 4),
    (date(2026, 9, 22), "B-201", "Parking Dispute", "Assigned spot repeatedly taken by guest vehicle", "Low", "M. Torres", "Posted reminder notice; towing policy explained to both parties", "Yes", date(2026, 9, 25), 4),
    (date(2026, 9, 21), "D-102", "Package Issue", "Package marked delivered but not in locker", "Medium", "J. Williams", "Reviewed Parcel Pending logs + CCTV; located in wrong locker; delivered", "Yes", date(2026, 9, 24), 5),
    (date(2026, 9, 20), "A-122", "Access Issue", "Fob stopped working overnight; resident locked out at 1 AM", "Critical", "J. Williams", "Immediate re-encode via Salto; escorted resident; incident documented", "Yes", date(2026, 9, 23), 5),
    (date(2026, 9, 19), "C-308", "Common Area", "Pool gate latch broken; safety concern raised", "High", "D. Kim", "Temporary lock + signage same night; work order WO-1019 linked", "Yes", date(2026, 9, 22), 4),
    (date(2026, 9, 18), "B-207", "Billing Question", "Utility overage charge disputed", "Low", "M. Torres", "Pulled meter history; walked through bill line by line", "Yes", date(2026, 9, 21), 3),
    (date(2026, 9, 17), "D-105", "Pest Control", "Ants returned one week after treatment", "Medium", "Vendor: Apex", "Re-treatment scheduled; sealed entry point found during inspection", "No", date(2026, 10, 1), None),
    (date(2026, 9, 16), "A-109", "Maintenance Delay", "Toilet repair took 4 days; resident escalated", "Medium", "J. Williams", "Apology + timeline explanation; prioritized completion; credit offered", "Yes", date(2026, 9, 19), 4),
    (date(2026, 9, 15), "C-322", "Move-In Condition", "Missing smoke detector in bedroom at move-in", "Critical", "J. Williams", "Installed within 2 hours; full unit safety re-check completed", "Yes", date(2026, 9, 18), 5),
    (date(2026, 9, 14), "B-218", "Noise Complaint", "Bass noise during quiet hours; second report", "Medium", "M. Torres", "Second notice issued; documented for lease enforcement file", "No", date(2026, 10, 3), None),
    (date(2026, 9, 12), "D-111", "Amenity Access", "Gym fob access denied erroneously", "Low", "A. Johnson", "Re-synced access group in Salto; confirmed working", "Yes", date(2026, 9, 15), 5),
]
r = 2
for d, unit, cat, desc, sev, owner, action, resolved, followup, sat in recovery_data:
    c = ws.cell(row=r, column=1, value=d); c.number_format = "MM/DD/YYYY"; c.alignment = center
    ws.cell(row=r, column=2, value=unit)
    ws.cell(row=r, column=3, value=cat)
    ws.cell(row=r, column=4, value=desc)
    ws.cell(row=r, column=5, value=sev)
    ws.cell(row=r, column=6, value=owner)
    ws.cell(row=r, column=7, value=action)
    c = ws.cell(row=r, column=8, value=resolved); c.alignment = center
    if followup:
        c = ws.cell(row=r, column=9, value=followup); c.number_format = "MM/DD/YYYY"; c.alignment = center
    if sat:
        c = ws.cell(row=r, column=10, value=sat); c.alignment = center
    r += 1

finalize_sheet(ws, len(headers), widths)
for row in ws.iter_rows(min_row=2, max_row=ws.max_row, max_col=len(headers)):
    for c in row:
        c.font = body_font
    row[1].alignment = center
    row[3].alignment = left_wrap
    row[6].alignment = left_wrap

add_validation(ws, "C", '"Maintenance Delay,Service Experience,Noise Complaint,Move-In Condition,Package Issue,Access Issue,Parking Dispute,Billing Question,Pest Control,Common Area,Amenity Access,Other"')
add_validation(ws, "E", '"Low,Medium,High,Critical"')
add_validation(ws, "H", '"Yes,No"')
add_validation(ws, "J", '"1,2,3,4,5"')
ws.conditional_formatting.add("E2:E500", CellIsRule(operator="equal", formula=['"Critical"'],
    fill=PatternFill("solid", fgColor=RED_BG), font=Font(color=RED, bold=True)))
ws.conditional_formatting.add("E2:E500", CellIsRule(operator="equal", formula=['"High"'],
    fill=PatternFill("solid", fgColor=AMBER_BG), font=Font(color=AMBER, bold=True)))
ws.conditional_formatting.add("H2:H500", CellIsRule(operator="equal", formula=['"No"'],
    fill=PatternFill("solid", fgColor=RED_BG), font=Font(color=RED, bold=True)))

# ------------------------------------------------------------------ SAVE
# README sheet: put sample note cleanly (remove placeholder misuse on WO sheet)
ws_readme = wb["README"]

# Print setup for all sheets
for s in wb.worksheets:
    s.sheet_properties.pageSetUpPr.fitToPage = True
    s.page_setup.orientation = "landscape"
    s.page_setup.fitToWidth = 1
    s.page_setup.fitToHeight = 0

wb.save(OUT)
print(f"Saved {OUT} ({OUT.stat().st_size // 1024} KB)")
print("Sheets:", wb.sheetnames)
