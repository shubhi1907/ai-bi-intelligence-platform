import html
import os
import re

import anthropic
import pandas as pd
import streamlit as st
from dotenv import load_dotenv


load_dotenv()

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")

REGION_MAP = {
    "North America": "AMER",
    "LATAM":         "AMER",
    "Europe":        "EMEA",
    "APAC":          "APAC",
}

ROLE_META = {
    "Head of Enterprise Intelligence":            {"initials": "HE", "display": "Executive",      "title": "Head of Enterprise Intelligence"},
    "Implementations Lead": {"initials": "IL", "display": "Implementations Lead", "title": "Implementations Lead"},
    "Revenue Leader":               {"initials": "RL", "display": "Revenue Lead",  "title": "Revenue & Growth"},
}


# ── Data loading ──────────────────────────────────────────────────────────────

@st.cache_data
def load_data():
    return {
        "customers":     pd.read_csv(os.path.join(DATA_DIR, "customers.csv")),
        "deals":         pd.read_csv(os.path.join(DATA_DIR, "deals.csv")),
        "tickets":       pd.read_csv(os.path.join(DATA_DIR, "tickets.csv")),
        "risks":         pd.read_csv(os.path.join(DATA_DIR, "risks.csv")),
        "escalations":   pd.read_csv(os.path.join(DATA_DIR, "escalations.csv")),
        "meetings":      pd.read_csv(os.path.join(DATA_DIR, "meeting_notes.csv")),
        "tasks":         pd.read_csv(os.path.join(DATA_DIR, "project_tasks.csv")),
        "status_reports":pd.read_csv(os.path.join(DATA_DIR, "status_reports.csv")),
    }


def get_claude_client():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        try:
            api_key = st.secrets["ANTHROPIC_API_KEY"]
        except Exception:
            api_key = None
    return anthropic.Anthropic(api_key=api_key) if api_key else None


# ── Tool schemas ──────────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "lookup_deal",
        "description": "Get full details for a specific deal including tickets, risks, escalations, meetings, status reports, and relationship context.",
        "input_schema": {"type": "object", "properties": {"deal_id": {"type": "string"}}, "required": ["deal_id"]},
    },
    {
        "name": "get_top_risks",
        "description": "Return the top N riskiest deals, optionally filtered by region (AMER/EMEA/APAC) or health (Healthy/At-Risk/Critical).",
        "input_schema": {
            "type": "object",
            "properties": {
                "n":      {"type": "integer"},
                "region": {"type": "string"},
                "health": {"type": "string"},
            },
            "required": [],
        },
    },
    {
        "name": "compare_deals",
        "description": "Compare two deals side-by-side on risk, delay, blockers, health, and contract value.",
        "input_schema": {
            "type": "object",
            "properties": {"deal_id_1": {"type": "string"}, "deal_id_2": {"type": "string"}},
            "required": ["deal_id_1", "deal_id_2"],
        },
    },
    {
        "name": "get_tickets_by_category",
        "description": "Find open tickets by issue category across the portfolio.",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {"type": "string"},
                "priority": {"type": "string"},
            },
            "required": ["category"],
        },
    },
    {
        "name": "get_related_deals",
        "description": "Find deals related to a given deal via same customer, same PM, or same issue pattern.",
        "input_schema": {
            "type": "object",
            "properties": {
                "deal_id":      {"type": "string"},
                "relationship": {"type": "string", "enum": ["same_customer", "same_pm", "same_issue_pattern"]},
            },
            "required": ["deal_id", "relationship"],
        },
    },
]


def execute_tool(name, inputs, data, enriched_deals):
    if name == "lookup_deal":
        did = inputs["deal_id"]
        try:
            return deal_evidence_text(did, data) + deal_relationship_context(did, data, enriched_deals)
        except Exception as e:
            return f"Deal {did} not found: {e}"

    if name == "get_top_risks":
        df = enriched_deals.copy()
        if inputs.get("region"): df = df[df["region"] == inputs["region"]]
        if inputs.get("health"): df = df[df["health_profile"] == inputs["health"]]
        cols = ["deal_id", "customer_name", "health_profile", "risk_score", "estimated_delay_days", "open_blockers", "contract_value"]
        return df.head(inputs.get("n", 5))[cols].to_string(index=False)

    if name == "compare_deals":
        lines = []
        for did in [inputs["deal_id_1"], inputs["deal_id_2"]]:
            try:
                r = enriched_deals[enriched_deals["deal_id"] == did].iloc[0]
                lines.append(f"{did}: risk={r['risk_score']}, delay={r['estimated_delay_days']}d, blockers={r['open_blockers']}, health={r['health_profile']}, value={fmt_money(r['contract_value'])}")
            except Exception:
                lines.append(f"{did}: not found")
        return "\n".join(lines)

    if name == "get_tickets_by_category":
        df = data["tickets"][data["tickets"]["issue_category"] == inputs["category"]]
        if inputs.get("priority"): df = df[df["priority"] == inputs["priority"]]
        df = df[df["status"].isin(["Open", "In Progress", "Pending"])]
        return df[["ticket_id", "deal_id", "priority", "severity", "sla_breach", "ticket_summary"]].head(10).to_string(index=False)

    if name == "get_related_deals":
        did, rel = inputs["deal_id"], inputs["relationship"]
        try:
            deal = data["deals"][data["deals"]["deal_id"] == did].iloc[0]
            if rel == "same_customer":
                df = enriched_deals[(enriched_deals["customer_id"] == deal["customer_id"]) & (enriched_deals["deal_id"] != did)][["deal_id", "project_name", "health_profile", "risk_score"]]
                return f"Other deals for same customer:\n{df.to_string(index=False)}"
            if rel == "same_pm":
                pm = deal["project_manager"]
                df = data["deals"][(data["deals"]["project_manager"] == pm) & (data["deals"]["deal_id"] != did)].merge(enriched_deals[["deal_id", "risk_score"]], on="deal_id", how="left")[["deal_id", "project_name", "health_profile", "risk_score"]]
                return f"Other deals managed by {pm}:\n{df.to_string(index=False)}"
            if rel == "same_issue_pattern":
                tix = data["tickets"][data["tickets"]["deal_id"] == did]
                if not len(tix): return "No tickets for this deal."
                top_cat = tix["issue_category"].value_counts().index[0]
                similar = data["tickets"][data["tickets"]["issue_category"] == top_cat]["deal_id"].unique()
                df = enriched_deals[(enriched_deals["deal_id"].isin(similar)) & (enriched_deals["deal_id"] != did)][["deal_id", "customer_name", "health_profile", "risk_score"]].head(8)
                return f"Deals sharing top issue '{top_cat}':\n{df.to_string(index=False)}"
        except Exception as e:
            return f"Error: {e}"
    return f"Unknown tool: {name}"


# ── Data helpers ──────────────────────────────────────────────────────────────

def calculate_risk_score(deals_df, tickets_df, escalations_df, risks_df):
    df = deals_df.copy()
    for col, src, name in [
        (tickets_df,    "deal_id", "ticket_count"),
        (escalations_df,"deal_id", "escalation_count"),
        (risks_df,      "deal_id", "risk_count"),
    ]:
        counts = col.groupby("deal_id").size().reset_index(name=name)
        df = df.merge(counts, on="deal_id", how="left")
    df[["ticket_count", "escalation_count", "risk_count"]] = df[["ticket_count", "escalation_count", "risk_count"]].fillna(0)
    raw = (
        (df["open_blockers"] * 5) * 0.25
        + (df["estimated_delay_days"] * 2) * 0.20
        + (df["ticket_count"] * 1) * 0.20
        + (df["escalation_count"] * 8) * 0.20
        + (df["risk_count"] * 6) * 0.15
    )
    df["risk_score"] = (raw / (raw.max() or 1) * 100).round(1)
    return df.sort_values("risk_score", ascending=False)


def fmt_money(v):
    if v >= 1_000_000: return f"${v/1_000_000:.1f}M"
    if v >= 1_000:     return f"${v/1_000:.0f}K"
    return f"${v:,.0f}"

def safe(v):    return html.escape(str(v))
def risk_tone(row):
    if row["risk_score"] >= 92 or row["health_profile"] == "Critical": return "critical"
    if row["risk_score"] >= 80 or row["health_profile"] == "At-Risk":  return "at-risk"
    return "on-track"

def delay_color(row):
    d = row["estimated_delay_days"]
    if d >= 20: return "red"
    if d >= 7:  return "amber"
    return "green"

def deal_bundle(deal_id, data):
    deal     = data["deals"][data["deals"]["deal_id"] == deal_id].iloc[0]
    customer = data["customers"][data["customers"]["customer_id"] == deal["customer_id"]].iloc[0]
    return (
        deal, customer,
        data["tickets"][data["tickets"]["deal_id"] == deal_id],
        data["risks"][data["risks"]["deal_id"] == deal_id],
        data["escalations"][data["escalations"]["deal_id"] == deal_id],
        data["meetings"][data["meetings"]["deal_id"] == deal_id],
        data["status_reports"][data["status_reports"]["deal_id"] == deal_id],
    )

def deal_evidence_text(deal_id, data):
    deal, customer, tickets, risks, escalations, meetings, reports = deal_bundle(deal_id, data)
    return f"""
Customer: {customer['customer_name']} ({customer['industry']}, {customer['region']})
Deal: {deal['deal_id']} - {deal['project_name']}
Status: {deal['project_status']} | Phase: {deal['implementation_phase']}
Health: {deal['health_profile']} | Score: {deal['health_score']}
Delay: {deal['estimated_delay_days']} days | Blockers: {deal['open_blockers']}
Budget utilization: {deal['budget_utilization_pct']}% | Contract: {customer['contract_value']}

Tickets:
{tickets[['ticket_id','priority','severity','status','issue_category','ticket_summary']].head(8).to_string(index=False)}

Risks:
{risks[['risk_id','risk_category','likelihood','impact','current_status']].head(8).to_string(index=False)}

Escalations:
{escalations[['escalation_id','severity','escalation_reason','resolution_status']].head(8).to_string(index=False)}

Status reports:
{reports[['reporting_week','overall_status','current_risks','next_steps']].head(4).to_string(index=False)}

Meeting notes:
{meetings[['meeting_date','meeting_type','meeting_notes','action_items']].head(4).to_string(index=False)}
""".strip()

def deal_relationship_context(deal_id, data, enriched_deals):
    try: deal = data["deals"][data["deals"]["deal_id"] == deal_id].iloc[0]
    except IndexError: return ""
    lines = ["\nRelationship Context:"]
    same = enriched_deals[(enriched_deals["customer_id"] == deal["customer_id"]) & (enriched_deals["deal_id"] != deal_id)][["deal_id","health_profile","risk_score","estimated_delay_days"]]
    if len(same):
        at_risk = same[same["health_profile"].isin(["At-Risk","Critical"])]
        lines.append(f"Same customer has {len(same)} other deal(s), {len(at_risk)} at-risk/critical:")
        lines.append(same.to_string(index=False))
    pm = deal.get("project_manager", "")
    if pm:
        pm_deals = enriched_deals[(enriched_deals["project_manager"] == pm) & (enriched_deals["deal_id"] != deal_id)]
        lines.append(f"PM '{pm}' manages {len(pm_deals)} other deal(s), {pm_deals[pm_deals['health_profile'].isin(['At-Risk','Critical'])].shape[0]} at-risk.")
    tix = data["tickets"][data["tickets"]["deal_id"] == deal_id]
    if len(tix):
        top_cat = tix["issue_category"].value_counts().index[0]
        spread = data["tickets"][data["tickets"]["issue_category"] == top_cat]["deal_id"].nunique()
        lines.append(f"Top issue '{top_cat}' affects {spread} deal(s) portfolio-wide.")
    return "\n".join(lines)


# ── AI functions ──────────────────────────────────────────────────────────────

def _blocks_to_dicts(blocks):
    out = []
    for b in blocks:
        if b.type == "text":    out.append({"type": "text", "text": b.text})
        elif b.type == "tool_use": out.append({"type": "tool_use", "id": b.id, "name": b.name, "input": b.input})
    return out

def ask_ai(question, portfolio_ctx, deal_evidence, role, data, enriched_deals):
    client = get_claude_client()
    if not client:
        return (
            "**API key not configured.** "
            "Locally: add `ANTHROPIC_API_KEY` to your `.env` file. "
            "On Streamlit Cloud: open the app's **Settings → Secrets** and add "
            "`ANTHROPIC_API_KEY = \"sk-ant-...\"`."
        )
    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": f"Portfolio snapshot:\n{portfolio_ctx}\n\nFocus deal:\n{deal_evidence}", "cache_control": {"type": "ephemeral"}},
            {"type": "text", "text": f"Role: {role}\nQuestion: {question}"},
        ],
    }]
    for _ in range(6):
        resp = client.messages.create(
            model="claude-sonnet-4-6", max_tokens=2048,
            system=[{"type": "text", "text": (
                "You are a senior enterprise intelligence advisor with tool access to live deal data. "
                "Answer concisely with an executive point of view. Use tools when you need to drill into specific deals. "
                "Always cite the data behind your answer."
            ), "cache_control": {"type": "ephemeral"}}],
            tools=TOOLS, messages=messages,
        )
        if resp.stop_reason == "end_turn":
            for b in resp.content:
                if b.type == "text": return b.text
            return ""
        if resp.stop_reason == "tool_use":
            results = [{"type": "tool_result", "tool_use_id": b.id, "content": execute_tool(b.name, b.input, data, enriched_deals)}
                       for b in resp.content if b.type == "tool_use"]
            messages.append({"role": "assistant", "content": _blocks_to_dicts(resp.content)})
            messages.append({"role": "user", "content": results})
        else:
            break
    for b in resp.content:
        if hasattr(b, "text"): return b.text
    return "Unable to generate a response."

def generate_brief(deal_id, data, enriched_deals, role):
    client = get_claude_client()
    if not client: return "**API key not configured.**"
    ev  = deal_evidence_text(deal_id, data)
    rel = deal_relationship_context(deal_id, data, enriched_deals)
    resp = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=1024,
        system=[{"type": "text", "text": "You are an enterprise intelligence advisor writing concise executive briefs. Three tight paragraphs: Situation, Risk, Action (with owners). Direct and specific — no filler.", "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": f"Executive brief for {deal_id}. Role: {role}.\nPara 1 — Situation. Para 2 — Risk. Para 3 — Action with owners.\n\nEvidence:\n{ev}\n{rel}"}],
    )
    return resp.content[0].text


# ── UI helpers ────────────────────────────────────────────────────────────────

def fmt_chat(text):
    """Escape then apply minimal markdown for chat bubble display."""
    t = html.escape(text)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'\n{2,}', '<br><br>', t)
    t = t.replace('\n', '<br>')
    return t

def chat_panel_html(history, user_initials):
    if not history:
        empty = "<div class='chat-empty'>Ask me anything about your portfolio, deals, or risk trends.</div>"
        return f"<div class='ai-messages'>{empty}</div>"
    msgs = []
    for msg in history[-8:]:
        if msg["role"] == "user":
            msgs.append(
                f"<div class='msg'>"
                f"<div class='msg-meta'><div class='msg-avatar user-av'>{safe(user_initials)}</div>"
                f"<div class='msg-name'>{safe(msg.get('name','You'))}</div></div>"
                f"<div class='msg-bubble user-bubble'>{safe(msg['text'])}</div>"
                f"</div>"
            )
        else:
            msgs.append(
                f"<div class='msg'>"
                f"<div class='msg-meta'><div class='msg-avatar ai-av'>AI</div>"
                f"<div class='msg-name'>AI BI Intelligence</div></div>"
                f"<div class='msg-bubble ai-bubble'>{fmt_chat(msg['text'])}</div>"
                f"</div>"
            )
    return f"<div class='ai-messages'>{''.join(msgs)}</div>"


def deal_table_html(df, title):
    rows = []
    for _, row in df.head(8).iterrows():
        tone  = risk_tone(row)
        dcol  = delay_color(row)
        delay = int(row["estimated_delay_days"])
        delay_str = f"+{delay}d" if delay > 0 else f"{delay}d"
        rows.append(
            f"<tr>"
            f"<td><div class='td-company'>{safe(row['customer_name'])}</div>"
            f"<div class='td-sub'>{safe(row['project_name'])}</div></td>"
            f"<td><span class='status-pill {tone}'>{safe(row['health_profile'])}</span></td>"
            f"<td class='num'><span class='delay-val {dcol}'>{delay_str}</span></td>"
            f"<td class='num contract'>{fmt_money(row['contract_value'])}</td>"
            f"</tr>"
        )
    return (
        f"<div class='panel'>"
        f"<div class='panel-hd'><div class='panel-title'>{safe(title)}</div>"
        f"<div class='panel-sub'>Sorted by risk · {len(df)} deals in scope</div></div>"
        f"<table><thead><tr>"
        f"<th>Customer</th><th>Status</th><th class='num'>Delay</th><th class='num'>Value</th>"
        f"</tr></thead><tbody>{''.join(rows)}</tbody></table></div>"
    )


def metrics_strip_html(metrics):
    cells = []
    for label, value, color, delta, delta_type, pct in metrics:
        bar_color = {"blue": "#1f5eff", "green": "#16a34a", "red": "#dc2626", "amber": "#d97706"}.get(color, "#94a3b8")
        delta_cls = {"pos": "pos", "neg": "neg"}.get(delta_type, "neu")
        arrow = "▲ " if delta_type == "pos" else ("▼ " if delta_type == "neg" else "— ")
        cells.append(
            f"<div class='m-cell'>"
            f"<div class='m-label'>{safe(label)}</div>"
            f"<div class='m-value' style='color:{bar_color}'>{safe(value)}</div>"
            f"<div class='m-bar'><div class='m-fill' style='width:{pct}%;background:{bar_color}'></div></div>"
            f"<div class='m-delta {delta_cls}'>{arrow}{safe(delta)}</div>"
            f"</div>"
        )
    return f"<div class='metrics-strip'>{''.join(cells)}</div>"


# ── Role configuration ────────────────────────────────────────────────────────

def role_config(role, filtered_deals, filtered_tickets, filtered_tasks, total_value, avg_delay):
    highest   = filtered_deals.iloc[0]
    top_issue = filtered_tickets["issue_category"].mode().iloc[0] if len(filtered_tickets) else "tickets"
    blocked   = filtered_tasks[filtered_tasks["dependency_flag"].astype(str).str.lower() == "yes"].shape[0]
    hi_pri    = filtered_tickets[filtered_tickets["priority"].isin(["Critical","High"])].shape[0]
    sla_cnt   = filtered_tickets[filtered_tickets["sla_breach"].astype(str).str.lower() == "yes"].shape[0]
    crit_cnt  = filtered_deals[filtered_deals["health_profile"] == "Critical"].shape[0]

    configs = {
        "Head of Enterprise Intelligence": {
            "subtitle": "3 decisions need your attention today",
            "default_q": "What should I tell the executive team about portfolio risk and the next decision?",
            "decisions": [
                {"title": f"Escalate {highest['customer_name']}", "color": "red",
                 "reason": f"Highest risk — {highest['estimated_delay_days']}d delay, {highest['open_blockers']} blockers",
                 "q": f"Should I escalate {highest['deal_id']} ({highest['customer_name']})? What are the key risks and what should I tell the exec team?"},
                {"title": "Review SLA Breaches", "color": "amber",
                 "reason": f"{sla_cnt:,} tickets have breached SLA across the portfolio",
                 "q": "Which SLA breaches are most critical right now and what is the fastest path to resolving them?"},
                {"title": "Protect Revenue Exposure", "color": "blue",
                 "reason": f"{fmt_money(total_value)} in contract value — largest deals carry the most risk",
                 "q": "Where is revenue most exposed? Identify deals combining high risk with large contract values."},
            ],
            "table_title": "Portfolio — Priority Order",
        },
        "Implementations Lead": {
            "subtitle": "3 delivery actions are ready for your team",
            "default_q": "Which delivery blockers should my team tackle first this week?",
            "decisions": [
                {"title": "Clear Dependency Blockers", "color": "red",
                 "reason": f"{blocked:,} tasks are blocked and may delay delivery",
                 "q": f"Which of the {blocked} dependency-blocked tasks should my team clear first? Prioritise by delivery impact."},
                {"title": f"Resolve {top_issue}", "color": "amber",
                 "reason": "Most common issue category in the portfolio right now",
                 "q": f"What is causing the spike in '{top_issue}' tickets? Which deals are most affected?"},
                {"title": f"Update Leadership on {highest['customer_name']}", "color": "blue",
                 "reason": f"{highest['open_blockers']} blockers and {highest['estimated_delay_days']}d delay need a clear status",
                 "q": f"Draft a clear status update for {highest['deal_id']} ({highest['customer_name']}) to share with leadership."},
            ],
            "table_title": "Delivery Work Queue",
        },
        "Revenue Leader": {
            "subtitle": "3 revenue protection actions are ready",
            "default_q": "Where is revenue most exposed, and what should leadership do next?",
            "decisions": [
                {"title": f"Protect {highest['customer_name']}", "color": "red",
                 "reason": f"Highest risk — {fmt_money(highest['contract_value'])} contract at stake",
                 "q": f"What is the revenue risk for {highest['deal_id']} ({highest['customer_name']}) and what actions should leadership take now?"},
                {"title": "Review Critical Accounts", "color": "amber",
                 "reason": f"{crit_cnt:,} accounts in critical status across the portfolio",
                 "q": "Rank the critical accounts by combined revenue risk with recommended mitigation for each."},
                {"title": "Build Board Narrative", "color": "blue",
                 "reason": f"{fmt_money(total_value)} needs an evidence-backed story for the board",
                 "q": f"Write an evidence-backed revenue risk narrative for the board. {fmt_money(total_value)} in scope across {len(filtered_deals)} deals."},
            ],
            "table_title": "Revenue Exposure — Priority Order",
        },
    }
    return configs[role]


# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(page_title="AI BI Intelligence", page_icon=":bar_chart:", layout="wide")

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/icon?family=Material+Icons');
  @import url('https://fonts.googleapis.com/icon?family=Material+Icons+Round');
  /* ── Reset Streamlit chrome ───────────────────────── */
  #MainMenu, footer { visibility: hidden; }
  [data-testid="stHeader"] { background: transparent; }
  .block-container { padding: 12px 20px 40px !important; max-width: 1600px; }

  /* ── Color palette ────────────────────────────────── */
  :root {
    --bg:       #f4f6fb;
    --card:     #ffffff;
    --sidebar:  #f0f3f9;
    --border:   #e1e7f0;
    --blue:     #1f5eff;
    --green:    #16a34a;
    --red:      #dc2626;
    --amber:    #d97706;
    --txt1:     #0f172a;
    --txt2:     #475569;
    --txt3:     #94a3b8;
  }

  body, [data-testid="stAppViewContainer"] { background: var(--bg) !important; }

  /* ── Sidebar ──────────────────────────────────────── */
  [data-testid="stSidebar"] { background: var(--sidebar) !important; border-right: 1px solid var(--border); }
  [data-testid="stSidebar"] section.main { background: var(--sidebar) !important; }
  [data-testid="stSidebar"] .stSelectbox label,
  [data-testid="stSidebar"] .stRadio label,
  [data-testid="stSidebar"] .stMultiSelect label { color: var(--txt3) !important; font-size: 10px !important; text-transform: uppercase; letter-spacing: 0.7px; font-weight: 700 !important; }

  /* ── Profile card ─────────────────────────────────── */
  .profile-card { padding: 16px; border-bottom: 1px solid var(--border); text-align: center; }
  .avatar { width: 48px; height: 48px; border-radius: 50%; background: linear-gradient(135deg,#dbeafe,#bfdbfe); border: 2px solid var(--blue); display: flex; align-items: center; justify-content: center; font-size: 16px; font-weight: 800; color: var(--blue); margin: 0 auto 8px; }
  .profile-name { font-size: 13px; font-weight: 700; color: var(--txt1); }
  .profile-role { font-size: 11px; color: var(--txt3); margin-top: 2px; }
  .profile-dot  { display: inline-flex; align-items: center; gap: 4px; font-size: 10px; color: var(--green); font-weight: 600; margin-top: 6px; }
  .profile-dot::before { content:''; width:6px; height:6px; border-radius:50%; background:var(--green); display:inline-block; }

  .sidebar-footer { padding: 12px 16px; border-top: 1px solid var(--border); }
  .sf-label { font-size: 10px; color: var(--txt3); margin-bottom: 2px; }
  .sf-val   { font-size: 11px; color: var(--txt2); font-weight: 500; }

  /* ── Page header ──────────────────────────────────── */
  .page-hd { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; padding-bottom:14px; border-bottom:1px solid var(--border); }
  .page-hd h1 { font-size:28px; font-weight:800; color:var(--txt1); margin:0 0 3px; }
  .page-hd p  { font-size:13px; color:var(--txt2); margin:0; }
  .kpi-row { display:flex; gap:8px; align-items:center; }
  .kpi-badge { display:inline-flex; align-items:center; gap:5px; border-radius:20px; padding:5px 12px; font-size:11.5px; font-weight:600; white-space:nowrap; }
  .kpi-badge::before { content:''; width:6px; height:6px; border-radius:50%; flex-shrink:0; }
  .kpi-blue  { background:rgba(31,94,255,.07);  color:var(--blue);  border:1px solid rgba(31,94,255,.18); }
  .kpi-blue::before  { background:var(--blue); }
  .kpi-green { background:rgba(22,163,74,.07);  color:var(--green); border:1px solid rgba(22,163,74,.18); }
  .kpi-green::before { background:var(--green); }
  .kpi-amber { background:rgba(217,119,6,.07);  color:var(--amber); border:1px solid rgba(217,119,6,.18); }
  .kpi-amber::before { background:var(--amber); }

  /* ── Priority cards ───────────────────────────────── */
  .p-card { background:var(--card); border:1px solid var(--border); border-radius:8px; box-shadow:0 1px 3px rgba(0,0,0,.05); padding:16px 18px; position:relative; overflow:hidden; margin-bottom:8px; min-height:140px; }
  .p-card::before { content:''; position:absolute; left:0; top:0; bottom:0; width:4px; }
  .p-card.red::before   { background:var(--red); }
  .p-card.amber::before { background:var(--amber); }
  .p-card.blue::before  { background:var(--blue); }
  .p-num   { font-size:10px; font-weight:800; text-transform:uppercase; letter-spacing:.6px; margin-bottom:6px; }
  .p-card.red .p-num   { color:var(--red); }
  .p-card.amber .p-num { color:var(--amber); }
  .p-card.blue .p-num  { color:var(--blue); }
  .p-company { font-size:17px; font-weight:800; color:var(--txt1); margin-bottom:6px; line-height:1.2; }
  .p-reason  { font-size:12px; color:var(--txt2); line-height:1.5; }
  .p-tag { display:inline-flex; align-items:center; font-size:11px; font-weight:600; padding:2px 8px; border-radius:4px; margin-top:8px; }
  .p-tag.red   { background:rgba(220,38,38,.08);  color:var(--red); }
  .p-tag.amber { background:rgba(217,119,6,.08);  color:var(--amber); }
  .p-tag.blue  { background:rgba(31,94,255,.08);  color:var(--blue); }

  /* ── Card AI answer ───────────────────────────────── */
  .card-ans { background:#f0f5ff; border:1px solid #c5d9ff; border-radius:8px; padding:14px 16px; margin:4px 0 16px; }
  .card-ans-label { font-size:10px; font-weight:800; text-transform:uppercase; letter-spacing:.06em; color:var(--blue); margin-bottom:4px; }
  .card-ans-title { font-size:15px; font-weight:700; color:var(--txt1); margin-bottom:10px; }

  /* ── Panel (table) ────────────────────────────────── */
  .panel { background:var(--card); border:1px solid var(--border); border-radius:8px; box-shadow:0 1px 3px rgba(0,0,0,.05); overflow:hidden; }
  .panel-hd { padding:13px 16px 11px; border-bottom:1px solid var(--border); }
  .panel-title { font-size:13px; font-weight:700; color:var(--txt1); }
  .panel-sub   { font-size:11px; color:var(--txt3); margin-top:1px; }
  table { width:100%; border-collapse:collapse; font-size:13px; }
  thead th { padding:8px 14px; text-align:left; font-size:10.5px; font-weight:700; text-transform:uppercase; letter-spacing:.6px; color:var(--txt3); border-bottom:1px solid var(--border); }
  thead th.num { text-align:right; }
  tbody tr { border-bottom:1px solid var(--border); transition:background .1s; }
  tbody tr:nth-child(even) { background:rgba(244,246,251,.8); }
  tbody tr:hover { background:rgba(31,94,255,.04); }
  tbody td { padding:10px 14px; color:var(--txt1); vertical-align:middle; }
  tbody td.num { text-align:right; }
  .td-company { font-weight:600; font-size:13px; }
  .td-sub     { font-size:11px; color:var(--txt3); margin-top:1px; }
  .status-pill { display:inline-flex; align-items:center; gap:4px; font-size:10.5px; font-weight:700; padding:3px 9px; border-radius:20px; white-space:nowrap; }
  .status-pill::before { content:''; width:5px; height:5px; border-radius:50%; flex-shrink:0; }
  .status-pill.critical  { background:rgba(220,38,38,.08);  color:var(--red); }
  .status-pill.critical::before  { background:var(--red); }
  .status-pill.at-risk   { background:rgba(217,119,6,.08);  color:var(--amber); }
  .status-pill.at-risk::before   { background:var(--amber); }
  .status-pill.on-track  { background:rgba(22,163,74,.08);  color:var(--green); }
  .status-pill.on-track::before  { background:var(--green); }
  .status-pill.Healthy   { background:rgba(22,163,74,.08);  color:var(--green); }
  .status-pill.Healthy::before   { background:var(--green); }
  .delay-val { font-weight:700; }
  .delay-val.red   { color:var(--red); }
  .delay-val.amber { color:var(--amber); }
  .delay-val.green { color:var(--green); }
  .contract { font-weight:700; font-variant-numeric:tabular-nums; }

  /* ── AI chat panel ────────────────────────────────── */
  .ai-panel-hd { background:var(--card); border:1px solid var(--border); border-radius:8px 8px 0 0; padding:13px 16px 12px; border-bottom:1px solid var(--border); display:flex; justify-content:space-between; align-items:center; }
  .ai-panel-title { font-size:13px; font-weight:700; color:var(--txt1); }
  .ai-panel-sub   { font-size:11px; color:var(--txt3); margin-top:1px; }
  .ai-dot { display:inline-flex; align-items:center; gap:5px; font-size:10.5px; color:var(--green); font-weight:600; }
  .ai-dot::before { content:''; width:7px; height:7px; border-radius:50%; background:var(--green); box-shadow:0 0 5px rgba(22,163,74,.5); animation:pulse 2s infinite; flex-shrink:0; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }

  .ai-messages { background:var(--card); border-left:1px solid var(--border); border-right:1px solid var(--border); padding:14px 14px 8px; min-height:340px; max-height:340px; overflow-y:auto; display:flex; flex-direction:column; gap:12px; }
  .chat-empty { color:var(--txt3); font-size:13px; padding:20px 0; text-align:center; }
  .msg { display:flex; flex-direction:column; gap:5px; }
  .msg-meta { display:flex; align-items:center; gap:7px; }
  .msg-avatar { width:22px; height:22px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:9px; font-weight:800; flex-shrink:0; }
  .user-av { background:linear-gradient(135deg,#dbeafe,#bfdbfe); color:var(--blue); }
  .ai-av   { background:linear-gradient(135deg,#dcfce7,#bbf7d0); color:var(--green); }
  .msg-name { font-size:10.5px; font-weight:700; color:var(--txt3); }
  .msg-bubble { font-size:12.5px; line-height:1.6; padding:10px 13px; border-radius:6px; }
  .user-bubble { background:rgba(31,94,255,.06); border:1px solid rgba(31,94,255,.12); color:var(--txt1); }
  .ai-bubble   { background:#f8fafc; border:1px solid var(--border); color:var(--txt2); }
  .ai-bubble strong { color:var(--txt1); }

  /* ── Metrics strip ────────────────────────────────── */
  .metrics-strip { display:grid; grid-template-columns:repeat(6,1fr); background:var(--card); border:1px solid var(--border); border-radius:8px; box-shadow:0 1px 3px rgba(0,0,0,.05); overflow:hidden; margin-top:16px; }
  .m-cell { padding:14px 16px; border-right:1px solid var(--border); display:flex; flex-direction:column; gap:4px; }
  .m-cell:last-child { border-right:none; }
  .m-label { font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:.7px; color:var(--txt3); }
  .m-value { font-size:20px; font-weight:800; letter-spacing:-.5px; font-variant-numeric:tabular-nums; line-height:1; }
  .m-bar  { height:3px; background:#e2e8f0; border-radius:2px; overflow:hidden; }
  .m-fill { height:100%; border-radius:2px; }
  .m-delta { font-size:10.5px; font-weight:600; }
  .m-delta.pos { color:var(--green); }
  .m-delta.neg { color:var(--red); }
  .m-delta.neu { color:var(--txt3); }

  /* ── Form input styling ───────────────────────────── */
  [data-testid="stForm"] { border:none !important; padding:0 !important; }
  .ai-input-wrap { background:var(--card); border:1px solid var(--border); border-top:none; border-radius:0 0 8px 8px; padding:10px 12px; }
</style>
""", unsafe_allow_html=True)


# ── Data ──────────────────────────────────────────────────────────────────────

data = load_data()
data = {**data, "customers": data["customers"].assign(region=data["customers"]["region"].map(REGION_MAP).fillna(data["customers"]["region"]))}

scored_deals   = calculate_risk_score(data["deals"], data["tickets"], data["escalations"], data["risks"])
enriched_deals = scored_deals.merge(
    data["customers"][["customer_id","customer_name","region","account_tier","contract_value"]],
    on="customer_id", how="left"
)


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    # Will be updated after role selection below — placeholder first
    role = st.selectbox("Role", list(ROLE_META.keys()), label_visibility="collapsed")
    meta = ROLE_META[role]

    st.markdown(
        f"<div class='profile-card'>"
        f"<div class='avatar'>{meta['initials']}</div>"
        f"<div class='profile-name'>{meta['display']}</div>"
        f"<div class='profile-role'>{meta['title']}</div>"
        f"<div class='profile-dot'>Active Session</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    st.divider()

    with st.expander("Advanced Filters", expanded=False):
        health_filter = st.multiselect(
            "Health Status",
            sorted(data["deals"]["health_profile"].dropna().unique()),
            default=sorted(data["deals"]["health_profile"].dropna().unique()),
        )
        region_filter = st.multiselect(
            "Region",
            sorted(data["customers"]["region"].dropna().unique()),
            default=sorted(data["customers"]["region"].dropna().unique()),
        )

    st.divider()
    focus_deal = st.selectbox(
        "Deal Details",
        enriched_deals["deal_id"].tolist(),
        index=0,
        help="Select a deal to view details and generate briefs",
    )

    st.markdown(
        "<div class='sidebar-footer'>"
        "<div class='sf-label'>Last sync</div>"
        f"<div class='sf-val'>Today, {pd.Timestamp.now().strftime('%H:%M')}</div>"
        "</div>",
        unsafe_allow_html=True,
    )


# ── Filter & aggregate ────────────────────────────────────────────────────────

filtered_deals = enriched_deals[
    enriched_deals["health_profile"].isin(health_filter) &
    enriched_deals["region"].isin(region_filter)
].copy()

if filtered_deals.empty:
    st.warning("No deals match the selected filters.")
    st.stop()

filtered_ids     = set(filtered_deals["deal_id"])
filtered_tickets = data["tickets"][data["tickets"]["deal_id"].isin(filtered_ids)]
filtered_tasks   = data["tasks"][data["tasks"]["deal_id"].isin(filtered_ids)]
filtered_risks   = data["risks"][data["risks"]["deal_id"].isin(filtered_ids)]
filtered_escs    = data["escalations"][data["escalations"]["deal_id"].isin(filtered_ids)]

total_value   = filtered_deals["contract_value"].sum()
avg_delay     = filtered_deals["estimated_delay_days"].mean()
open_tickets  = filtered_tickets[filtered_tickets["status"].isin(["Open","In Progress","Pending"])].shape[0]
sla_breaches  = filtered_tickets[filtered_tickets["sla_breach"].astype(str).str.lower() == "yes"].shape[0]
blocked_count = filtered_tasks[filtered_tasks["dependency_flag"].astype(str).str.lower() == "yes"].shape[0]
at_risk_value = filtered_deals[filtered_deals["health_profile"].isin(["At-Risk","Critical"])]["contract_value"].sum()

config = role_config(role, filtered_deals, filtered_tickets, filtered_tasks, total_value, avg_delay)

portfolio_ctx = (
    f"Deals: {len(filtered_deals)} | Value: {fmt_money(total_value)} | Avg delay: {avg_delay:.1f}d\n"
    f"Open tickets: {open_tickets} | SLA breaches: {sla_breaches} | Blocked tasks: {blocked_count}\n"
    f"Top issues: {filtered_tickets['issue_category'].value_counts().head(5).to_dict()}\n"
    f"Top risky: {filtered_deals[['deal_id','customer_name','risk_score','estimated_delay_days','open_blockers']].head(5).to_dict(orient='records')}"
)
focus_evidence = deal_evidence_text(focus_deal, data) + "\n" + deal_relationship_context(focus_deal, data, enriched_deals)


# ── Session state ─────────────────────────────────────────────────────────────

for k, v in [("active_card", None), ("card_answer_1", None), ("card_answer_2", None),
             ("card_answer_3", None), ("deal_brief", None), ("chat_history", []),
             ("_prev_deal", None), ("_prev_role", None)]:
    if k not in st.session_state: st.session_state[k] = v

if st.session_state["_prev_role"] != role:
    st.session_state.update({"active_card": None, "card_answer_1": None, "card_answer_2": None,
                              "card_answer_3": None, "deal_brief": None, "_prev_role": role})

if st.session_state["_prev_deal"] != focus_deal:
    st.session_state.update({"deal_brief": None, "_prev_deal": focus_deal})


# ── Page header ───────────────────────────────────────────────────────────────

crit_count = filtered_deals[filtered_deals["health_profile"] == "Critical"].shape[0]
st.markdown(
    f"<div class='page-hd'>"
    f"<div><h1>Good morning, {safe(meta['display'])}</h1><p>{safe(config['subtitle'])}</p></div>"
    f"<div class='kpi-row'>"
    f"<div class='kpi-badge kpi-blue'>{len(filtered_deals):,} Deals</div>"
    f"<div class='kpi-badge kpi-green'>{fmt_money(total_value)} Pipeline</div>"
    f"<div class='kpi-badge kpi-amber'>{avg_delay:.1f}d Avg Delay</div>"
    f"</div></div>",
    unsafe_allow_html=True,
)


# ── Priority cards ────────────────────────────────────────────────────────────

st.markdown(
    "<div style='font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.8px;color:#94a3b8;margin-bottom:10px'>Priority Actions — Today</div>",
    unsafe_allow_html=True,
)

triggered_card = None
cols = st.columns(3)
for i, (col, dec) in enumerate(zip(cols, config["decisions"]), start=1):
    with col:
        st.markdown(
            f"<div class='p-card {dec['color']}'>"
            f"<div class='p-num'>Priority {i}</div>"
            f"<div class='p-company'>{safe(dec['title'])}</div>"
            f"<div class='p-reason'>{safe(dec['reason'])}</div>"
            f"<div class='p-tag {dec['color']}'>{safe(dec['reason'].split('—')[0].strip())}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        b1, b2 = st.columns(2)
        with b1:
            if st.button("Show Analysis", key=f"p_{i}_{role}", type="primary", use_container_width=True):
                triggered_card = i
        with b2:
            if st.button("Ask AI", key=f"s_{i}_{role}", use_container_width=True):
                triggered_card = i

if triggered_card is not None:
    st.session_state.active_card = triggered_card
    dec = config["decisions"][triggered_card - 1]
    with st.spinner(f"Analysing — {dec['title']}…"):
        st.session_state[f"card_answer_{triggered_card}"] = ask_ai(
            dec["q"], portfolio_ctx, focus_evidence, role, data, enriched_deals
        )

active = st.session_state.get("active_card")
if active and st.session_state.get(f"card_answer_{active}"):
    dec = config["decisions"][active - 1]
    st.markdown(
        f"<div class='card-ans'>"
        f"<div class='card-ans-label'>AI Analysis — Priority {active}</div>"
        f"<div class='card-ans-title'>{safe(dec['title'])}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )
    st.markdown(st.session_state[f"card_answer_{active}"])


# ── Middle: table + AI chat ───────────────────────────────────────────────────

st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)
left, right = st.columns([3, 2], gap="medium")

with left:
    st.markdown(deal_table_html(filtered_deals, config["table_title"]), unsafe_allow_html=True)

with right:
    # Chat panel header
    st.markdown(
        "<div class='ai-panel-hd'>"
        "<div><div class='ai-panel-title'>AI Assistant</div>"
        "<div class='ai-panel-sub'>Powered by Claude · live deal data</div></div>"
        "<div class='ai-dot'>Ready</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    # Chat history
    st.markdown(
        chat_panel_html(st.session_state.chat_history, meta["initials"]),
        unsafe_allow_html=True,
    )

    # Input
    st.markdown("<div class='ai-input-wrap'>", unsafe_allow_html=True)
    with st.form("chat_form", clear_on_submit=True):
        ic, bc = st.columns([5, 1])
        with ic:
            user_q = st.text_input("", placeholder="Ask about any deal, region, or trend…", label_visibility="collapsed")
        with bc:
            submitted = st.form_submit_button("Ask", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if submitted and user_q.strip():
        st.session_state.chat_history.append({"role": "user", "text": user_q, "name": meta["display"]})
        with st.spinner(""):
            answer = ask_ai(user_q, portfolio_ctx, focus_evidence, role, data, enriched_deals)
        st.session_state.chat_history.append({"role": "ai", "text": answer})
        st.rerun()

    # Generate brief
    st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)
    if st.button("Generate Executive Brief", key="gen_brief", type="primary", use_container_width=True):
        with st.spinner(f"Writing brief for {focus_deal}…"):
            st.session_state.deal_brief = generate_brief(focus_deal, data, enriched_deals, role)
    if st.session_state.deal_brief:
        with st.expander(f"Executive Brief — {focus_deal}", expanded=True):
            st.markdown(st.session_state.deal_brief)


# ── Metrics strip ─────────────────────────────────────────────────────────────

st.markdown(
    metrics_strip_html([
        ("Active Deals",     f"{len(filtered_deals):,}",  "blue",  f"{len(filtered_deals)} in scope",     "neu", min(len(filtered_deals), 100)),
        ("Pipeline Value",   fmt_money(total_value),       "blue",  f"Total contract value",               "neu", 68),
        ("Avg Delay",        f"{avg_delay:.1f}d",          "amber", f"vs 14d target",                      "neg", 55),
        ("At-Risk Value",    fmt_money(at_risk_value),     "red",   f"{crit_count} critical deals",        "neg", int(at_risk_value/total_value*100) if total_value else 0),
        ("SLA Breaches",     f"{sla_breaches:,}",          "red",   f"across {len(filtered_deals)} deals", "neg", min(sla_breaches * 2, 100)),
        ("Blocked Tasks",    f"{blocked_count:,}",         "amber", f"dependency flags",                   "neu", min(blocked_count * 3, 100)),
    ]),
    unsafe_allow_html=True,
)
