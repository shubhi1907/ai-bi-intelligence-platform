import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "frontend" / "decision_desk_data.json"


def yes(series):
    return series.astype(str).str.lower().eq("yes")


def money(value):
    value = float(value)
    if value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:,.0f}"


customers = pd.read_csv(DATA / "customers.csv")
deals = pd.read_csv(DATA / "deals.csv")
tickets = pd.read_csv(DATA / "tickets.csv")
risks = pd.read_csv(DATA / "risks.csv")
escalations = pd.read_csv(DATA / "escalations.csv")
meetings = pd.read_csv(DATA / "meeting_notes.csv")
tasks = pd.read_csv(DATA / "project_tasks.csv")
reports = pd.read_csv(DATA / "status_reports.csv")

ticket_counts = tickets.groupby("deal_id").size().reset_index(name="ticket_count")
open_ticket_counts = (
    tickets[tickets["status"].isin(["Open", "In Progress", "Pending"])]
    .groupby("deal_id")
    .size()
    .reset_index(name="open_ticket_count")
)
sla_counts = tickets[yes(tickets["sla_breach"])].groupby("deal_id").size().reset_index(name="sla_breach_count")
risk_counts = risks.groupby("deal_id").size().reset_index(name="risk_count")
escalation_counts = escalations.groupby("deal_id").size().reset_index(name="escalation_count")
blocked_task_counts = tasks[yes(tasks["dependency_flag"])].groupby("deal_id").size().reset_index(name="blocked_task_count")

enriched = deals.merge(customers, on="customer_id", how="left")
for frame in [ticket_counts, open_ticket_counts, sla_counts, risk_counts, escalation_counts, blocked_task_counts]:
    enriched = enriched.merge(frame, on="deal_id", how="left")

for col in [
    "ticket_count",
    "open_ticket_count",
    "sla_breach_count",
    "risk_count",
    "escalation_count",
    "blocked_task_count",
]:
    enriched[col] = enriched[col].fillna(0).astype(int)

raw_score = (
    (enriched["open_blockers"] * 5) * 0.25
    + (enriched["estimated_delay_days"] * 2) * 0.20
    + (enriched["ticket_count"] * 1) * 0.20
    + (enriched["escalation_count"] * 8) * 0.20
    + (enriched["risk_count"] * 6) * 0.15
)
enriched["risk_score"] = (raw_score / (raw_score.max() or 1) * 100).round(0).astype(int)
enriched = enriched.sort_values("risk_score", ascending=False)

top_deal = enriched.iloc[0]
top_region = enriched.groupby("region")["contract_value"].sum().sort_values(ascending=False)
top_issue = tickets["issue_category"].mode().iloc[0]
top_issue_count = int(tickets[tickets["issue_category"].eq(top_issue) & tickets["status"].isin(["Open", "In Progress", "Pending"])].shape[0])
top_risk = risks["risk_category"].mode().iloc[0]

def latest_or_empty(frame, date_col):
    if frame.empty:
        return {}
    return frame.sort_values(date_col, ascending=False).iloc[0].to_dict()


def evidence_for(deal_id):
    deal = enriched[enriched["deal_id"].eq(deal_id)].iloc[0]
    deal_tickets = tickets[tickets["deal_id"].eq(deal_id)]
    deal_risks = risks[risks["deal_id"].eq(deal_id)]
    deal_escalations = escalations[escalations["deal_id"].eq(deal_id)]
    deal_meetings = meetings[meetings["deal_id"].eq(deal_id)]
    deal_reports = reports[reports["deal_id"].eq(deal_id)]

    top_ticket = deal_tickets.sort_values(["priority", "severity"], ascending=True).iloc[0].to_dict() if not deal_tickets.empty else {}
    risk = deal_risks.iloc[0].to_dict() if not deal_risks.empty else {}
    escalation = deal_escalations.iloc[0].to_dict() if not deal_escalations.empty else {}
    meeting = latest_or_empty(deal_meetings, "meeting_date")
    report = latest_or_empty(deal_reports, "reporting_week")

    return {
        "deal_id": deal_id,
        "customer": deal["customer_name"],
        "industry": deal["industry"],
        "region": deal["region"],
        "project": deal["project_name"],
        "phase": deal["implementation_phase"],
        "status": deal["project_status"],
        "health": deal["health_profile"],
        "completion": int(max(10, min(92, 100 - deal["estimated_delay_days"]))),
        "delay_days": int(deal["estimated_delay_days"]),
        "blockers": int(deal["open_blockers"]),
        "contract_value": float(deal["contract_value"]),
        "ticket_issue": top_ticket.get("issue_category", "No ticket issue"),
        "ticket_summary": top_ticket.get("ticket_summary", "No ticket summary available"),
        "open_tickets": int(deal["open_ticket_count"]),
        "risk": risk.get("risk_category", "No risk recorded"),
        "risk_detail": f"{risk.get('impact', 'Unknown')} impact, {deal['estimated_delay_days']} day delay",
        "escalation_owner": escalation.get("executive_owner", "Unassigned"),
        "escalation_reason": escalation.get("escalation_reason", "No escalation recorded"),
        "meeting_date": meeting.get("meeting_date", "No meeting date"),
        "meeting_note": meeting.get("meeting_notes", "No meeting notes available"),
        "action_items": meeting.get("action_items", "No action items available"),
        "status_summary": report.get("executive_summary", "No status report available"),
    }


table_rows = []
for _, row in enriched.head(8).iterrows():
    health = row["health_profile"]
    display_health = "Off Track" if health == "Critical" else ("At Risk" if health == "At-Risk" else "On Track")
    table_rows.append(
        {
            "deal_id": row["deal_id"],
            "customer": row["customer_name"],
            "health": display_health,
            "delay": f"{int(row['estimated_delay_days'])} days",
            "risk_score": int(row["risk_score"]),
            "contract_value": money(row["contract_value"]),
            "region": row["region"],
            "phase": row["implementation_phase"],
        }
    )

region_chart = [
    {"region": region, "value": round(value / 1_000_000, 1)}
    for region, value in top_region.items()
]

payload = {
    "as_of": "May 9, 2026",
    "data_refreshed": "8:15 AM",
    "portfolio": {
        "deals": int(len(enriched)),
        "contract_value": money(enriched["contract_value"].sum()),
        "contract_value_raw": float(enriched["contract_value"].sum()),
        "avg_delay": f"{enriched['estimated_delay_days'].mean():.1f} days",
        "open_tickets": int(tickets[tickets["status"].isin(["Open", "In Progress", "Pending"])].shape[0]),
        "sla_breaches": int(yes(tickets["sla_breach"]).sum()),
        "blocked_tasks": int(yes(tasks["dependency_flag"]).sum()),
        "top_region": top_region.index[0],
        "top_issue": top_issue,
        "top_issue_open": top_issue_count,
        "top_risk": top_risk,
    },
    "top_deal": top_deal["deal_id"],
    "table_rows": table_rows,
    "region_chart": region_chart,
    "evidence": {
        row["deal_id"]: evidence_for(row["deal_id"])
        for _, row in enriched.head(25).iterrows()
    },
}

OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(f"Wrote {OUT}")
