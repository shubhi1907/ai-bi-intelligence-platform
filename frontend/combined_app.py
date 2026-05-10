import html
import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")


@st.cache_data
def load_data():
    return {
        "customers": pd.read_csv(os.path.join(DATA_DIR, "customers.csv")),
        "deals": pd.read_csv(os.path.join(DATA_DIR, "deals.csv")),
        "tickets": pd.read_csv(os.path.join(DATA_DIR, "tickets.csv")),
        "risks": pd.read_csv(os.path.join(DATA_DIR, "risks.csv")),
        "escalations": pd.read_csv(os.path.join(DATA_DIR, "escalations.csv")),
        "meetings": pd.read_csv(os.path.join(DATA_DIR, "meeting_notes.csv")),
        "tasks": pd.read_csv(os.path.join(DATA_DIR, "project_tasks.csv")),
        "status_reports": pd.read_csv(os.path.join(DATA_DIR, "status_reports.csv")),
    }


def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        try:
            api_key = st.secrets["OPENAI_API_KEY"]
        except Exception:
            api_key = None
    return OpenAI(api_key=api_key) if api_key else None


def calculate_risk_score(deals_df, tickets_df, escalations_df, risks_df):
    df = deals_df.copy()
    ticket_counts = tickets_df.groupby("deal_id").size().reset_index(name="ticket_count")
    escalation_counts = escalations_df.groupby("deal_id").size().reset_index(name="escalation_count")
    risk_counts = risks_df.groupby("deal_id").size().reset_index(name="risk_count")

    df = df.merge(ticket_counts, on="deal_id", how="left")
    df = df.merge(escalation_counts, on="deal_id", how="left")
    df = df.merge(risk_counts, on="deal_id", how="left")
    df[["ticket_count", "escalation_count", "risk_count"]] = df[
        ["ticket_count", "escalation_count", "risk_count"]
    ].fillna(0)

    raw_score = (
        (df["open_blockers"] * 5) * 0.25
        + (df["estimated_delay_days"] * 2) * 0.20
        + (df["ticket_count"] * 1) * 0.20
        + (df["escalation_count"] * 8) * 0.20
        + (df["risk_count"] * 6) * 0.15
    )
    max_score = raw_score.max() or 1
    df["risk_score"] = (raw_score / max_score * 100).round(1)
    return df.sort_values("risk_score", ascending=False)


def fmt_money(value):
    if value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"${value / 1_000:.0f}K"
    return f"${value:,.0f}"


def safe(value):
    return html.escape(str(value))


def badge(text, tone="neutral"):
    return f'<span class="badge badge-{tone}">{safe(text)}</span>'


def risk_tone(row):
    if row["risk_score"] >= 92 or row["health_profile"] == "Critical":
        return "critical"
    if row["risk_score"] >= 80 or row["health_profile"] == "At-Risk":
        return "warn"
    return "ok"


def deal_bundle(deal_id, data):
    deals = data["deals"]
    customers = data["customers"]
    tickets = data["tickets"]
    risks = data["risks"]
    escalations = data["escalations"]
    meetings = data["meetings"]
    status_reports = data["status_reports"]

    deal = deals[deals["deal_id"] == deal_id].iloc[0]
    customer = customers[customers["customer_id"] == deal["customer_id"]].iloc[0]
    related_tickets = tickets[tickets["deal_id"] == deal_id]
    related_risks = risks[risks["deal_id"] == deal_id]
    related_escalations = escalations[escalations["deal_id"] == deal_id]
    related_meetings = meetings[meetings["deal_id"] == deal_id]
    related_reports = status_reports[status_reports["deal_id"] == deal_id]
    return deal, customer, related_tickets, related_risks, related_escalations, related_meetings, related_reports


def deal_evidence_text(deal_id, data):
    deal, customer, tickets, risks, escalations, meetings, reports = deal_bundle(deal_id, data)
    return f"""
Customer: {customer['customer_name']} ({customer['industry']}, {customer['region']})
Deal: {deal['deal_id']} - {deal['project_name']}
Project status: {deal['project_status']}
Implementation phase: {deal['implementation_phase']}
Health profile: {deal['health_profile']}
Health score: {deal['health_score']}
Estimated delay days: {deal['estimated_delay_days']}
Open blockers: {deal['open_blockers']}
Budget utilization: {deal['budget_utilization_pct']}%
Contract value: {customer['contract_value']}

Tickets:
{tickets[['ticket_id', 'priority', 'severity', 'status', 'issue_category', 'ticket_summary']].head(8).to_string(index=False)}

Risks:
{risks[['risk_id', 'risk_category', 'likelihood', 'impact', 'current_status']].head(8).to_string(index=False)}

Escalations:
{escalations[['escalation_id', 'severity', 'escalation_reason', 'resolution_status']].head(8).to_string(index=False)}

Recent status:
{reports[['reporting_week', 'overall_status', 'current_risks', 'next_steps']].head(4).to_string(index=False)}

Meeting notes:
{meetings[['meeting_date', 'meeting_type', 'meeting_notes', 'action_items']].head(4).to_string(index=False)}
""".strip()


def ask_ai(question, evidence, role):
    client = get_openai_client()
    if client is None:
        return "OpenAI key is not configured, so this preview can show evidence but cannot generate an AI answer."

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a senior enterprise intelligence advisor. Answer with a clear executive point of view. "
                    "Use the supplied metrics and evidence. Do not invent data. Mention the evidence behind your answer."
                ),
            },
            {
                "role": "user",
                "content": f"Role: {role}\nQuestion: {question}\n\nEvidence:\n{evidence}",
            },
        ],
    )
    return response.choices[0].message.content


def role_config(role, filtered_deals, filtered_tickets, filtered_tasks, total_value, avg_delay):
    highest = filtered_deals.iloc[0]
    top_issue = filtered_tickets["issue_category"].mode().iloc[0] if len(filtered_tickets) else "No tickets"
    blocked_tasks = filtered_tasks[filtered_tasks["dependency_flag"].astype(str).str.lower() == "yes"].shape[0]
    high_priority = filtered_tickets[filtered_tickets["priority"].isin(["Critical", "High"])].shape[0]

    configs = {
        "BK - Head of EIS": {
            "name": "BK",
            "subtitle": "3 executive decisions need your attention today",
            "brief": "Morning Brief",
            "default_question": "What should I tell the executive team about portfolio risk, capacity, and the next decision?",
            "why": (
                f"The portfolio has {len(filtered_deals):,} active deals worth {fmt_money(total_value)}. "
                f"The highest risk item is {highest['deal_id']} with {highest['estimated_delay_days']} delay days and "
                f"{highest['open_blockers']} blockers. Avg delay is {avg_delay:.1f} days, so the management question is capacity and escalation priority."
            ),
            "decisions": [
                {
                    "title": f"Escalate {highest['deal_id']}",
                    "reason": f"Critical risk, {highest['estimated_delay_days']} day delay, {highest['open_blockers']} blockers",
                    "primary": "Show Evidence",
                    "secondary": "Ask AI",
                },
                {
                    "title": "Review SLA Breaches",
                    "reason": f"{filtered_tickets[filtered_tickets['sla_breach'].astype(str).str.lower() == 'yes'].shape[0]:,} breached tickets across portfolio",
                    "primary": "Open Trend",
                    "secondary": "Assign Owner",
                },
                {
                    "title": "Protect Revenue Exposure",
                    "reason": f"{fmt_money(total_value)} in scoped contract value with Europe leading value at risk",
                    "primary": "Prepare Brief",
                    "secondary": "Export PDF",
                },
            ],
            "table_title": "Top Executive Risks",
        },
        "Scott - Implementations Lead": {
            "name": "Scott",
            "subtitle": "3 delivery interventions are ready for your team",
            "brief": "Delivery Standup",
            "default_question": "Which delivery blockers should my implementation team tackle first this week?",
            "why": (
                f"Your team should focus on {top_issue}, high-priority tickets, and dependency blockers. "
                f"There are {high_priority:,} critical or high priority tickets and {blocked_tasks:,} blocked tasks in scope."
            ),
            "decisions": [
                {
                    "title": "Clear Dependency Blockers",
                    "reason": f"{blocked_tasks:,} tasks have dependency flags and may delay delivery",
                    "primary": "Open Queue",
                    "secondary": "Notify PMs",
                },
                {
                    "title": f"Attack {top_issue}",
                    "reason": "This is the most common ticket issue category in the selected portfolio",
                    "primary": "View Tickets",
                    "secondary": "Ask AI",
                },
                {
                    "title": f"Prepare BK Update on {highest['deal_id']}",
                    "reason": f"{highest['open_blockers']} blockers and {highest['estimated_delay_days']} delay days need a crisp status",
                    "primary": "Draft Update",
                    "secondary": "Show Evidence",
                },
            ],
            "table_title": "Delivery Work Queue",
        },
        "Revenue Leader": {
            "name": "Revenue Leader",
            "subtitle": "3 revenue protection calls are ready",
            "brief": "Revenue Brief",
            "default_question": "Where is revenue most exposed, and what should leadership do next?",
            "why": (
                f"Scoped contract value is {fmt_money(total_value)}. The revenue story is not only which deals are large, "
                "but which large deals are delayed, blocked, or escalated."
            ),
            "decisions": [
                {
                    "title": "Protect Largest Risk Deal",
                    "reason": f"{highest['deal_id']} combines high risk with executive visibility",
                    "primary": "Open Account",
                    "secondary": "Prepare Brief",
                },
                {
                    "title": "Review Critical Accounts",
                    "reason": f"{filtered_deals[filtered_deals['health_profile'] == 'Critical'].shape[0]:,} critical deals in scope",
                    "primary": "Rank Accounts",
                    "secondary": "Ask AI",
                },
                {
                    "title": "Explain Revenue Risk",
                    "reason": f"{fmt_money(total_value)} needs evidence-backed narrative, not only dashboard numbers",
                    "primary": "Generate Narrative",
                    "secondary": "Export PDF",
                },
            ],
            "table_title": "Revenue Exposure",
        },
    }
    return configs[role]


def decision_cards(decisions):
    cards = []
    for index, item in enumerate(decisions, start=1):
        cards.append(
            f"<div class='decision-card'>"
            f"<div class='decision-index'>Decision {index}</div>"
            f"<div class='decision-title'>{safe(item['title'])}</div>"
            f"<div class='decision-reason'>{safe(item['reason'])}</div>"
            f"<div class='button-row'>"
            f"<span class='mock-button primary'>{safe(item['primary'])}</span>"
            f"<span class='mock-button'>{safe(item['secondary'])}</span>"
            f"</div></div>"
        )
    return '<div class="decision-grid">' + "".join(cards) + "</div>"


def metric_grid(metrics):
    cards = []
    for label, value in metrics:
        cards.append(
            f'<div class="metric-card"><div class="metric-label">{safe(label)}</div><div class="metric-value">{safe(value)}</div></div>'
        )
    return '<div class="metric-grid">' + "".join(cards) + "</div>"


def deal_table_html(df, title):
    rows = []
    for _, row in df.head(8).iterrows():
        tone = risk_tone(row)
        rows.append(
            f"<tr>"
            f"<td><strong>{safe(row['deal_id'])}</strong><br><span>{safe(row['customer_name'])}</span></td>"
            f"<td>{safe(row['project_name'])}</td>"
            f"<td>{badge(row['health_profile'], tone)}</td>"
            f"<td>{safe(row['implementation_phase'])}</td>"
            f"<td class='number'>{row['risk_score']:.1f}</td>"
            f"<td class='number'>{int(row['estimated_delay_days'])}d</td>"
            f"<td class='number'>{int(row['open_blockers'])}</td>"
            f"<td class='number'>{fmt_money(row['contract_value'])}</td>"
            f"</tr>"
        )
    return (
        f"<div class='panel'>"
        f"<div class='panel-head'><div><div class='eyebrow'>Portfolio</div><h3>{safe(title)}</h3></div>"
        f"<span class='panel-action'>Export CSV</span></div>"
        f"<table class='deal-table'><thead><tr>"
        f"<th>Deal</th><th>Project</th><th>Health</th><th>Phase</th>"
        f"<th>Risk</th><th>Delay</th><th>Blockers</th><th>Value</th>"
        f"</tr></thead><tbody>{''.join(rows)}</tbody></table></div>"
    )


def evidence_drawer_html(deal_id, data):
    deal, customer, tickets, risks, escalations, meetings, reports = deal_bundle(deal_id, data)
    top_ticket = tickets.iloc[0] if len(tickets) else None
    top_risk = risks.iloc[0] if len(risks) else None
    top_escalation = escalations.iloc[0] if len(escalations) else None
    latest_meeting = meetings.sort_values("meeting_date", ascending=False).iloc[0] if len(meetings) else None
    latest_report = reports.sort_values("reporting_week", ascending=False).iloc[0] if len(reports) else None

    snippets = [
        ("Customer", f"{customer['customer_name']} - {customer['industry']} - {customer['region']}"),
        ("Project", f"{deal['project_name']} is {deal['project_status']} in {deal['implementation_phase']}"),
        ("Ticket", f"{top_ticket['issue_category']}: {top_ticket['ticket_summary']}" if top_ticket is not None else "No tickets"),
        ("Risk", f"{top_risk['risk_category']} with {top_risk['impact']} impact" if top_risk is not None else "No risks"),
        (
            "Escalation",
            f"{top_escalation['severity']} - {top_escalation['escalation_reason']}"
            if top_escalation is not None
            else "No escalations",
        ),
        (
            "Latest Meeting",
            f"{latest_meeting['meeting_date']}: {latest_meeting['action_items']}"
            if latest_meeting is not None
            else "No meetings",
        ),
        (
            "Status Report",
            f"{latest_report['overall_status']}: {latest_report['next_steps']}"
            if latest_report is not None
            else "No status reports",
        ),
    ]

    snippet_html = "".join(
        f"<div class='source-row'>"
        f"<div class='source-label'>{safe(label)}</div>"
        f"<div class='source-text'>{safe(text)}</div>"
        f"</div>"
        for label, text in snippets
    )

    return (
        f"<div class='evidence-drawer'>"
        f"<div class='drawer-top'><div class='eyebrow'>Evidence Drawer</div>"
        f"<h3>Evidence for {safe(deal_id)}</h3></div>"
        f"<div class='drawer-summary'><strong>{safe(customer['customer_name'])}</strong>"
        f"<span>{safe(deal['health_profile'])} health - {safe(deal['estimated_delay_days'])} delay days - "
        f"{safe(deal['open_blockers'])} blockers</span></div>"
        f"{snippet_html}"
        f"<div class='button-row drawer-actions'>"
        f"<span class='mock-button primary'>Copy Brief</span>"
        f"<span class='mock-button'>Export PDF</span>"
        f"<span class='mock-button'>Send to Scott</span>"
        f"</div></div>"
    )


def source_chips():
    return (
        "<div class='source-chips'>"
        "<span>Tickets</span><span>Risks</span><span>Escalations</span>"
        "<span>Meetings</span><span>Status Reports</span>"
        "</div>"
    )


st.set_page_config(
    page_title="AI BI Intelligence Platform",
    page_icon=":bar_chart:",
    layout="wide",
)

st.markdown(
    """
    <style>
      [data-testid="stAppViewContainer"] { background: #f6f8fb; }
      [data-testid="stSidebar"] { background: #edf1f6; border-right: 1px solid #dfe5ee; }
      .block-container { padding-top: 32px; max-width: 1440px; }
      h1, h2, h3, p { letter-spacing: 0; }
      .hero {
        display: flex;
        justify-content: space-between;
        gap: 24px;
        align-items: flex-end;
        margin-bottom: 18px;
      }
      .hero h1 {
        color: #1f2430;
        font-size: 42px;
        line-height: 1.05;
        margin: 0 0 8px;
      }
      .hero p { color: #657083; font-size: 16px; margin: 0; }
      .brief-pill {
        border: 1px solid #cdd6e2;
        background: #fff;
        color: #1f2430;
        border-radius: 999px;
        padding: 10px 16px;
        font-weight: 700;
        white-space: nowrap;
      }
      .decision-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 14px;
        margin: 14px 0 18px;
      }
      .decision-card, .metric-card, .panel, .evidence-drawer, .ai-panel {
        background: #fff;
        border: 1px solid #e1e7f0;
        border-radius: 8px;
        box-shadow: 0 10px 28px rgba(35, 48, 73, 0.05);
      }
      .decision-card { padding: 18px; min-height: 178px; }
      .decision-index {
        color: #d64545;
        font-size: 12px;
        font-weight: 800;
        text-transform: uppercase;
        margin-bottom: 8px;
      }
      .decision-title { color: #1f2430; font-size: 20px; font-weight: 800; margin-bottom: 8px; }
      .decision-reason { color: #657083; font-size: 14px; line-height: 1.4; min-height: 42px; }
      .button-row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 16px; }
      .mock-button {
        border: 1px solid #d7dfeb;
        border-radius: 6px;
        color: #2e3747;
        font-size: 13px;
        font-weight: 700;
        padding: 8px 11px;
        background: #fff;
      }
      .mock-button.primary { background: #1f5eff; border-color: #1f5eff; color: #fff; }
      .metric-grid {
        display: grid;
        grid-template-columns: repeat(6, minmax(120px, 1fr));
        gap: 12px;
        margin: 10px 0 18px;
      }
      .metric-card { padding: 14px 16px; min-height: 88px; }
      .metric-label { color: #657083; font-size: 12px; margin-bottom: 8px; }
      .metric-value {
        color: #1f2430;
        font-size: 27px;
        line-height: 1.05;
        font-weight: 800;
        white-space: nowrap;
      }
      .workspace {
        display: grid;
        grid-template-columns: minmax(0, 1.55fr) minmax(360px, 0.75fr);
        gap: 16px;
        align-items: start;
      }
      .panel { padding: 16px; }
      .panel-head {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 12px;
      }
      .eyebrow {
        color: #d64545;
        font-size: 11px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: .04em;
      }
      .panel h3, .evidence-drawer h3 { color: #1f2430; font-size: 21px; margin: 3px 0 0; }
      .panel-action {
        color: #1f5eff;
        font-size: 12px;
        font-weight: 800;
        border: 1px solid #d7dfeb;
        border-radius: 6px;
        padding: 7px 10px;
      }
      .deal-table { border-collapse: collapse; width: 100%; font-size: 13px; }
      .deal-table th {
        color: #657083;
        font-size: 11px;
        text-align: left;
        padding: 9px 8px;
        border-bottom: 1px solid #e1e7f0;
        text-transform: uppercase;
      }
      .deal-table td { color: #263043; padding: 11px 8px; border-bottom: 1px solid #eef2f7; vertical-align: top; }
      .deal-table td span { color: #687286; font-size: 12px; }
      .number { text-align: right; font-variant-numeric: tabular-nums; }
      .badge {
        border-radius: 999px;
        padding: 4px 8px;
        font-size: 12px;
        font-weight: 800;
        white-space: nowrap;
      }
      .badge-critical { background: #ffe7e7; color: #b42318; }
      .badge-warn { background: #fff4d7; color: #9a5b00; }
      .badge-ok { background: #ddfbea; color: #0f7a45; }
      .badge-neutral { background: #eef2f7; color: #4c5668; }
      .evidence-drawer { padding: 18px; position: sticky; top: 18px; }
      .drawer-summary {
        background: #f5f7fb;
        border-radius: 8px;
        padding: 12px;
        margin: 12px 0;
        display: grid;
        gap: 4px;
      }
      .drawer-summary strong { color: #1f2430; }
      .drawer-summary span { color: #657083; font-size: 13px; }
      .source-row { border-top: 1px solid #eef2f7; padding: 11px 0; }
      .source-label { color: #1f5eff; font-size: 12px; font-weight: 800; margin-bottom: 3px; }
      .source-text { color: #2b3446; font-size: 13px; line-height: 1.38; }
      .drawer-actions .mock-button { flex: 1; text-align: center; }
      .insight-grid {
        display: grid;
        grid-template-columns: minmax(0, .9fr) minmax(0, 1fr);
        gap: 16px;
        margin-top: 16px;
      }
      .ai-panel { padding: 16px; }
      .ai-panel h3 { color: #1f2430; margin: 0 0 8px; font-size: 20px; }
      .ai-panel p { color: #4f5a6b; line-height: 1.5; margin: 0 0 12px; }
      .source-chips { display: flex; gap: 8px; flex-wrap: wrap; }
      .source-chips span {
        background: #eef4ff;
        border: 1px solid #cfe0ff;
        color: #1f5eff;
        border-radius: 999px;
        padding: 5px 9px;
        font-size: 12px;
        font-weight: 800;
      }
      @media (max-width: 1200px) {
        .decision-grid, .metric-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        .workspace, .insight-grid { grid-template-columns: 1fr; }
        .evidence-drawer { position: static; }
      }
    </style>
    """,
    unsafe_allow_html=True,
)

data = load_data()
customers_df = data["customers"]
deals_df = data["deals"]
tickets_df = data["tickets"]
risks_df = data["risks"]
escalations_df = data["escalations"]
meetings_df = data["meetings"]
tasks_df = data["tasks"]

scored_deals = calculate_risk_score(deals_df, tickets_df, escalations_df, risks_df)
enriched_deals = scored_deals.merge(
    customers_df[["customer_id", "customer_name", "region", "account_tier", "contract_value"]],
    on="customer_id",
    how="left",
)

with st.sidebar:
    st.header("Control Center")
    role = st.selectbox("Role", ["BK - Head of EIS", "Scott - Implementations Lead", "Revenue Leader"])
    health_filter = st.multiselect(
        "Health",
        sorted(deals_df["health_profile"].dropna().unique()),
        default=sorted(deals_df["health_profile"].dropna().unique()),
    )
    region_filter = st.multiselect(
        "Region",
        sorted(customers_df["region"].dropna().unique()),
        default=sorted(customers_df["region"].dropna().unique()),
    )
    st.divider()
    focus_mode = st.radio("Focus", ["Today", "This week", "This quarter"], horizontal=False)

filtered_deals = enriched_deals[
    enriched_deals["health_profile"].isin(health_filter)
    & enriched_deals["region"].isin(region_filter)
].copy()

if filtered_deals.empty:
    st.warning("No deals match the selected filters.")
    st.stop()

filtered_ids = set(filtered_deals["deal_id"])
filtered_tickets = tickets_df[tickets_df["deal_id"].isin(filtered_ids)]
filtered_risks = risks_df[risks_df["deal_id"].isin(filtered_ids)]
filtered_escalations = escalations_df[escalations_df["deal_id"].isin(filtered_ids)]
filtered_tasks = tasks_df[tasks_df["deal_id"].isin(filtered_ids)]

total_contract_value = filtered_deals["contract_value"].sum()
avg_delay = filtered_deals["estimated_delay_days"].mean()
open_ticket_count = filtered_tickets[filtered_tickets["status"].isin(["Open", "In Progress", "Pending"])].shape[0]
sla_breaches = filtered_tickets[filtered_tickets["sla_breach"].astype(str).str.lower() == "yes"].shape[0]
blocked_tasks = filtered_tasks[filtered_tasks["dependency_flag"].astype(str).str.lower() == "yes"].shape[0]
role = role
config = role_config(role, filtered_deals, filtered_tickets, filtered_tasks, total_contract_value, avg_delay)

default_deal = filtered_deals.iloc[0]["deal_id"]
focus_deal = st.sidebar.selectbox("Evidence deal", filtered_deals["deal_id"].tolist(), index=0)

st.markdown(
    f"""
    <div class="hero">
      <div>
        <h1>Good morning, {safe(config['name'])}</h1>
        <p>{safe(config['subtitle'])} - {safe(focus_mode)}</p>
      </div>
      <div class="brief-pill">{safe(config['brief'])}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(decision_cards(config["decisions"]), unsafe_allow_html=True)

metrics = [
    ("Deals", f"{len(filtered_deals):,}"),
    ("Contract Value", fmt_money(total_contract_value)),
    ("Avg Delay", f"{avg_delay:.1f} days"),
    ("Open Tickets", f"{open_ticket_count:,}"),
    ("SLA Breaches", f"{sla_breaches:,}"),
    ("Blocked Tasks", f"{blocked_tasks:,}"),
]
st.markdown(metric_grid(metrics), unsafe_allow_html=True)

left_col, right_col = st.columns([1.55, 0.75], gap="large")

with left_col:
    st.markdown(deal_table_html(filtered_deals, config["table_title"]), unsafe_allow_html=True)

    insight_left, insight_right = st.columns([0.9, 1], gap="medium")
    with insight_left:
        st.markdown('<div class="panel"><div class="eyebrow">Trend</div><h3>Risk Distribution</h3></div>', unsafe_allow_html=True)
        st.bar_chart(filtered_deals.set_index("deal_id")["risk_score"].head(18), height=210)
    with insight_right:
        st.markdown(
            f"<div class='ai-panel'><div class='eyebrow'>AI Brief</div>"
            f"<h3>Why this matters</h3><p>{safe(config['why'])}</p>{source_chips()}</div>",
            unsafe_allow_html=True,
        )
        st.bar_chart(filtered_tickets["issue_category"].value_counts().head(7), height=190)

with right_col:
    st.markdown(evidence_drawer_html(focus_deal or default_deal, data), unsafe_allow_html=True)

st.markdown("### Ask AI with dashboard and evidence context")
question = st.text_input(
    "Question",
    value=config["default_question"],
    placeholder="Ask about revenue, delivery risk, or a specific deal...",
)

portfolio_context = f"""
Portfolio metrics:
Deals in scope: {len(filtered_deals)}
Contract value in scope: {total_contract_value}
Average delay: {avg_delay}
Open tickets: {open_ticket_count}
SLA breaches: {sla_breaches}
Blocked tasks: {blocked_tasks}
Top issue categories: {filtered_tickets['issue_category'].value_counts().head(5).to_dict()}
Top risky deals: {filtered_deals[['deal_id', 'customer_name', 'risk_score', 'estimated_delay_days', 'open_blockers']].head(5).to_dict(orient='records')}
"""

if st.button("Generate AI answer", type="primary"):
    evidence = deal_evidence_text(focus_deal, data)
    with st.spinner("Combining dashboard metrics with retrieved deal evidence..."):
        answer = ask_ai(question, f"{portfolio_context}\n\nSelected deal evidence:\n{evidence}", role)
    st.markdown(answer)

with st.expander("Show full retrieved evidence"):
    st.text_area("Retrieved evidence", deal_evidence_text(focus_deal, data), height=420)
