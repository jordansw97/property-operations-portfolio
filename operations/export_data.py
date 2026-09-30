#!/usr/bin/env python3
"""Export the toolkit's sample data to app/data.js (seed for the web app)."""
import json
from datetime import datetime, date
from pathlib import Path
from openpyxl import load_workbook

HERE = Path(__file__).resolve().parent
wb = load_workbook(HERE / "property-operations-toolkit.xlsx", data_only=False)

def iso(v):
    if isinstance(v, (datetime, date)):
        return v.strftime("%Y-%m-%d")
    return v

def rows(ws, cols, skip_hidden=True):
    out = []
    for r in range(2, ws.max_row + 1):
        if ws.row_dimensions[r].hidden:
            continue
        vals = [ws.cell(row=r, column=c).value for c in cols]
        if all(v in (None, "") for v in vals):
            continue
        out.append([iso(v) for v in vals])
    return out

# Work Orders: A WO-ID, B Date Opened, C Unit, D Category, E Priority,
# F Description, G Assigned To, H Status, I Date Closed
wo = rows(wb["Work Orders"], [1, 2, 3, 4, 5, 6, 7, 8, 9])
# Turnover: A Unit, B Building, C Move-Out, D Inspection, E Inspector,
# F Deficiencies, G Top Deficiency, H Status, I QC, J Ready Date
to = rows(wb["Turnover"], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
# Retention: A Unit, B Resident ID, C Lease End, D Rent, E Offer Sent,
# F Touches, G Intent, H Reason, I Notes
rt = rows(wb["Retention"], [1, 2, 3, 4, 5, 6, 7, 8, 9])
# Service Recovery: A Date, B Unit, C Category, D Description, E Severity,
# F Owner, G Action, H Resolved, I Follow-Up, J Satisfaction
sr = rows(wb["Service Recovery"], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

data = {
    "workOrders": [
        dict(zip(["id", "opened", "unit", "category", "priority",
                  "description", "assignee", "status", "closed"], r)) for r in wo
    ],
    "turnover": [
        dict(zip(["unit", "building", "moveOut", "inspected", "inspector",
                  "deficiencies", "topDeficiency", "status", "qc", "readyDate"], r)) for r in to
    ],
    "retention": [
        dict(zip(["unit", "resident", "leaseEnd", "rent", "offerSent",
                  "touches", "intent", "reason", "notes"], r)) for r in rt
    ],
    "recovery": [
        dict(zip(["date", "unit", "category", "description", "severity",
                  "owner", "action", "resolved", "followUp", "satisfaction"], r)) for r in sr
    ],
}

out = HERE / "app" / "data.js"
out.parent.mkdir(exist_ok=True)
out.write_text(
    "// Sample data exported from property-operations-toolkit.xlsx — fictional, for demo.\n"
    "window.SEED = " + json.dumps(data, indent=1) + ";\n"
)
print(f"Wrote {out}  (WO:{len(wo)} TO:{len(to)} RT:{len(rt)} SR:{len(sr)})")
