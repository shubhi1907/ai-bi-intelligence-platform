import streamlit as st
import pandas as pd
import chromadb

from sentence_transformers import SentenceTransformer
from streamlit_option_menu import option_menu
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# =========================================================
# OPENAI CLIENT SETUP
# =========================================================

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    api_key = st.secrets["OPENAI_API_KEY"]

client = OpenAI(api_key=api_key)

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="AI Executive Deal Intelligence",
    page_icon="📊",
    layout="wide"
)

# =========================================================
# LOAD DATA
# =========================================================

deals_df = pd.read_csv("data/deals.csv")
tickets_df = pd.read_csv("data/tickets.csv")
risks_df = pd.read_csv("data/risks.csv")
escalations_df = pd.read_csv("data/escalations.csv")
meetings_df = pd.read_csv("data/meeting_notes.csv")
customers_df = pd.read_csv("data/customers.csv")

# =========================================================
# RISK SCORING FUNCTION
# =========================================================

def calculate_risk_score():

    df = deals_df.copy()

    # Count related entities
    ticket_counts = tickets_df.groupby("deal_id").size().reset_index(name="ticket_count")
    escalation_counts = escalations_df.groupby("deal_id").size().reset_index(name="escalation_count")
    risk_counts = risks_df.groupby("deal_id").size().reset_index(name="risk_count")

    df = df.merge(ticket_counts, on="deal_id", how="left")
    df = df.merge(escalation_counts, on="deal_id", how="left")
    df = df.merge(risk_counts, on="deal_id", how="left")

    # Fill nulls
    df[["ticket_count", "escalation_count", "risk_count"]] = df[
        ["ticket_count", "escalation_count", "risk_count"]
    ].fillna(0)

    # Normalize values (simple scaling)
    df["blocker_score"] = df["open_blockers"] * 5
    df["delay_score"] = df["estimated_delay_days"] * 2
    df["ticket_score"] = df["ticket_count"] * 1
    df["escalation_score"] = df["escalation_count"] * 8
    df["risk_score_component"] = df["risk_count"] * 6

    # Final weighted score
    df["risk_score"] = (
        df["blocker_score"] * 0.25 +
        df["delay_score"] * 0.20 +
        df["ticket_score"] * 0.20 +
        df["escalation_score"] * 0.20 +
        df["risk_score_component"] * 0.15
    )

    # Normalize to 0–100
    df["risk_score"] = (df["risk_score"] / df["risk_score"].max()) * 100

    return df.sort_values(by="risk_score", ascending=False)

# =========================================================
# ROOT CAUSE ANALYSIS
# =========================================================

def generate_root_cause_analysis():

    # Top ticket issue categories
    ticket_issues = tickets_df["issue_category"].value_counts().head(5)

    # Top risk categories
    risk_categories = risks_df["risk_category"].value_counts().head(5)

    # Top escalation reasons
    escalation_reasons = escalations_df["escalation_reason"].value_counts().head(5)

    context = f"""
    Ticket Issues:
    {ticket_issues.to_dict()}

    Risk Categories:
    {risk_categories.to_dict()}

    Escalation Reasons:
    {escalation_reasons.to_dict()}
    """

    prompt = f"""
    You are an enterprise operations analyst.

    Analyze the following aggregated data and provide:

    1. Top root causes of delivery risk
    2. Key patterns across tickets, risks, and escalations
    3. Strategic insights for leadership

    Data:
    {context}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content

# =========================================================
# EXECUTIVE BRIEFING FUNCTION
# =========================================================

@st.cache_data
def generate_executive_briefing():

    scored_deals = calculate_risk_score()

    risky_deals = scored_deals.head(5)

    context = ""

    for _, deal in risky_deals.iterrows():

        deal_id = deal["deal_id"]

        related_risks = risks_df[
            risks_df["deal_id"] == deal_id
        ]

        related_escalations = escalations_df[
            escalations_df["deal_id"] == deal_id
        ]

        context += f"""
        Deal: {deal_id}
        Project: {deal['project_name']}
        Health: {deal['health_profile']}
        Blockers: {deal['open_blockers']}
        Delay: {deal['estimated_delay_days']}

        Risks:
        {' '.join(related_risks['risk_category'].astype(str).tolist())}

        Escalations:
        {' '.join(related_escalations['escalation_reason'].astype(str).tolist())}
        """

    prompt = f"""
    You are an enterprise operations executive assistant.

    Analyze the portfolio below and provide:

    1. Executive summary
    2. Key risks
    3. Escalation patterns
    4. Recommended actions

    Data:
    {context}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content

# =========================================================
# LOAD EMBEDDING MODEL
# =========================================================

@st.cache_resource
def load_embedding_model():

    model = SentenceTransformer(
        "all-MiniLM-L6-v2"
    )

    return model

# =========================================================
# BUILD EXECUTIVE DEAL PROFILES
# =========================================================

@st.cache_data
def build_deal_profiles():

    deal_profiles = []

    for _, deal in deals_df.iterrows():

        deal_id = deal["deal_id"]

        related_tickets = tickets_df[
            tickets_df["deal_id"] == deal_id
        ]

        related_risks = risks_df[
            risks_df["deal_id"] == deal_id
        ]

        related_escalations = escalations_df[
            escalations_df["deal_id"] == deal_id
        ]

        customer = customers_df[
            customers_df["customer_id"]
            == deal["customer_id"]
        ]

        customer_name = customer.iloc[0]["customer_name"]

        profile_text = f"""
        Deal ID: {deal_id}

        Customer: {customer_name}

        Project Name:
        {deal['project_name']}

        Project Type:
        {deal['project_type']}

        Project Status:
        {deal['project_status']}

        Health Profile:
        {deal['health_profile']}

        Implementation Phase:
        {deal['implementation_phase']}

        Open Blockers:
        {deal['open_blockers']}

        Budget Utilization:
        {deal['budget_utilization_pct']}

        Estimated Delay:
        {deal['estimated_delay_days']}

        Executive Visibility:
        {deal['executive_visibility']}

        Total Tickets:
        {len(related_tickets)}

        Total Risks:
        {len(related_risks)}

        Total Escalations:
        {len(related_escalations)}

        Ticket Issues:
        {' '.join(
            related_tickets['ticket_summary']
            .astype(str)
            .head(10)
            .tolist()
        )}

        Risk Categories:
        {' '.join(
            related_risks['risk_category']
            .astype(str)
            .tolist()
        )}

        Escalation Reasons:
        {' '.join(
            related_escalations['escalation_reason']
            .astype(str)
            .tolist()
        )}
        """

        deal_profiles.append({
            "deal_id": deal_id,
            "profile_text": profile_text
        })

    return pd.DataFrame(deal_profiles)

# =========================================================
# LOAD VECTOR DATABASE
# =========================================================

@st.cache_resource
def load_deal_vector_database():

    deal_profiles_df = build_deal_profiles()

    model = load_embedding_model()

    embeddings = model.encode(
        deal_profiles_df["profile_text"].tolist()
    )

    client = chromadb.Client()

    try:

        client.delete_collection(
            "deal_intelligence"
        )

    except:
        pass

    collection = client.create_collection(
        "deal_intelligence"
    )

    collection.add(
        embeddings=embeddings.tolist(),
        documents=deal_profiles_df[
            "profile_text"
        ].tolist(),
        ids=deal_profiles_df[
            "deal_id"
        ].tolist()
    )

    return collection

# =========================================================
# TITLE
# =========================================================

st.title(
    "AI Executive Deal Intelligence Platform"
)

st.markdown(
    """
    Enterprise AI platform for:
    - Implementation Risk Analysis
    - Escalation Monitoring
    - GraphRAG Operational Intelligence
    - Executive Delivery Insights
    """
)

# =========================================================
# SIDEBAR NAVIGATION
# =========================================================

with st.sidebar:

    #st.markdown("## AI Control Center")

    selected_page = option_menu(
        menu_title="AI Control Center",
        options=[
            "Executive Summary",
            "Semantic Search",
            "Deal Intelligence",
            "Graph Analytics"
        ],
        icons=[
            "bar-chart",
            "search",
            "briefcase",
            "diagram-3"
        ],
        menu_icon="cast",
        default_index=0,
        orientation="vertical",
        styles={
            "container": {
                "padding": "0!important",
                #"background-color": "#0E1117"
            },
            "icon": {
                "color": "#000000",
                "font-size": "16px"
            },
            "nav-link": {
                "font-size": "14px",
                "text-align": "left",
                "margin": "2px",
                "--hover-color": "#8DCCF8",
            },
            "nav-link-selected": {
                "background-color": "#8DCCF8",
            },
        }
    )

# =========================================================
# EXECUTIVE SUMMARY PAGE
# =========================================================

if selected_page == "Executive Summary":
    st.header("Executive AI Summary")

    st.write(
        "AI-generated implementation intelligence and risk insights."
    )

    # =====================================================
    # KPI CARDS
    # =====================================================

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Active Deals", len(deals_df))

    with col2:
        st.metric("Open Risks", len(risks_df))

    with col3:
        st.metric("Escalations", len(escalations_df))

    with col4:
        st.metric("Avg Delay (Days)", int(deals_df["estimated_delay_days"].mean()))

    st.divider()

    # =====================================================
    # TOP RISKY DEALS
    # =====================================================

    st.subheader("Top Risky Deals")

    scored_deals = calculate_risk_score()

    risky_deals = scored_deals.head(5)

    st.dataframe(
        risky_deals[
            [
                "deal_id",
                "project_name",
                "health_profile",
                "risk_score",
                "open_blockers",
                "estimated_delay_days"
            ]
        ],
        use_container_width=True
    )
    st.divider()

    st.subheader("Risk Score Distribution")

    st.bar_chart(
        scored_deals.set_index("deal_id")["risk_score"].head(20)
    )
    st.divider()
    # =====================================================
    # ROOT CAUSE ANALYSIS
    # =====================================================

    st.subheader("Enterprise Root Cause Analysis")

    if "root_cause" not in st.session_state:
        st.session_state["root_cause"] = None

    if st.button("Analyze Root Causes"):

        with st.spinner("Analyzing enterprise patterns..."):
            st.session_state["root_cause"] = generate_root_cause_analysis()

    if st.session_state["root_cause"]:
        st.info(st.session_state["root_cause"])

    st.divider()

    # =====================================================
    # AI RISK EXPLANATION
    # =====================================================

    st.subheader("Explain Deal Risk")

    selected_deal_for_ai = st.selectbox(
        "Select Deal",
        scored_deals["deal_id"]
    )

    if st.button("Explain Risk"):

        deal_data = deals_df[
            deals_df["deal_id"] == selected_deal_for_ai
        ].iloc[0]

        related_tickets = tickets_df[
            tickets_df["deal_id"] == selected_deal_for_ai
        ]
        

        related_risks = risks_df[
            risks_df["deal_id"] == selected_deal_for_ai
        ]
    

        related_escalations = escalations_df[
            escalations_df["deal_id"] == selected_deal_for_ai
        ]
    

        prompt = f"""
        You are an enterprise delivery expert.
        Explain why this deal is at risk.
        Deal: {selected_deal_for_ai}

        Project: {deal_data['project_name']}
        Health: {deal_data['health_profile']}
        Blockers: {deal_data['open_blockers']}
        Delay: {deal_data['estimated_delay_days']}

        Risks:
        {related_risks[['risk_category','impact','likelihood']].to_dict()}

        Escalations:
        {related_escalations[['severity','escalation_reason']].to_dict()}

        Tickets:
        {related_tickets[['ticket_summary','priority','status']].head(10).to_dict()}

        Provide:
        - concise explanation
        - main drivers of risk
        - recommended action
        """

        with st.spinner("Analyzing deal risk..."):

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

        st.info(response.choices[0].message.content)

    st.divider()

# =====================================================
# EXECUTIVE BRIEFING UI
# =====================================================

st.subheader("AI Executive Portfolio Briefing")

if "briefing" not in st.session_state:
    st.session_state["briefing"] = None

if st.button("Generate Executive Briefing"):

    with st.spinner("Analyzing enterprise portfolio..."):
        st.session_state["briefing"] = generate_executive_briefing()

if st.session_state["briefing"]:
    st.success(st.session_state["briefing"])

# =========================================================
# SEMANTIC SEARCH PAGE
# =========================================================

elif selected_page == "Semantic Search":

    st.header("Enterprise AI Search")

    st.write(
        """
        AI-powered executive intelligence search
        across deals, risks, escalations,
        delivery health, and operational issues.
        """
    )

    model = load_embedding_model()

    enterprise_collection = (
        load_deal_vector_database()
    )

    query = st.text_input(
        "Ask Enterprise AI"
    )

    if query:

        query_embedding = model.encode(
            [query]
        )

        results = enterprise_collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=5
        )

        st.subheader("AI Intelligence Results")

        for result in results["documents"][0]:

            st.info(result)

# =========================================================
# DEAL INTELLIGENCE PAGE
# =========================================================

elif selected_page == "Deal Intelligence":

    st.header("Deal Intelligence")

    st.write(
        "Analyze operational delivery health and escalation patterns."
    )

    selected_deal = st.selectbox(
        "Select Deal",
        deals_df["deal_id"].unique()
    )

    selected_deal_data = deals_df[
        deals_df["deal_id"] == selected_deal
    ]

    selected_tickets = tickets_df[
        tickets_df["deal_id"] == selected_deal
    ]

    selected_risks = risks_df[
        risks_df["deal_id"] == selected_deal
    ]

    selected_escalations = escalations_df[
        escalations_df["deal_id"] == selected_deal
    ]

    st.subheader("Deal Overview")

    st.dataframe(selected_deal_data)

    st.subheader("Related Tickets")

    st.dataframe(
        selected_tickets.head(20)
    )

    st.subheader("Related Risks")

    st.dataframe(
        selected_risks.head(20)
    )

    st.subheader("Related Escalations")

    st.dataframe(
        selected_escalations.head(20)
    )

# =========================================================
# GRAPH ANALYTICS PAGE
# =========================================================

elif selected_page == "Graph Analytics":

    st.header("Enterprise Knowledge Graph")

    st.write(
        "Interactive enterprise relationship intelligence."
    )

    st.info(
        "Open enterprise_graph.html from the graph folder to interact with the knowledge graph visualization."
    )

    graph_col1, graph_col2, graph_col3 = st.columns(3)

    with graph_col1:

        st.metric(
            "Customers",
            len(customers_df)
        )

    with graph_col2:

        st.metric(
            "Deals",
            len(deals_df)
        )

    with graph_col3:

        st.metric(
            "Tickets",
            len(tickets_df)
        )

    st.subheader("Graph Entity Distribution")

    graph_distribution = pd.DataFrame({
        "Entity": [
            "Customers",
            "Deals",
            "Tickets",
            "Risks",
            "Escalations",
            "Meetings"
        ],
        "Count": [
            len(customers_df),
            len(deals_df),
            len(tickets_df),
            len(risks_df),
            len(escalations_df),
            len(meetings_df)
        ]
    })

    st.bar_chart(
        graph_distribution.set_index("Entity")
    )