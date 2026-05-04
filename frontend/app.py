import streamlit as st
import pandas as pd
import chromadb

from sentence_transformers import SentenceTransformer
from streamlit_option_menu import option_menu

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
        "AI-generated implementation intelligence summaries."
    )

    # =====================================================
    # KPI CARDS
    # =====================================================

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            label="Active Deals",
            value=len(deals_df),
            delta="+12"
        )

    with col2:

        st.metric(
            label="Open Risks",
            value=len(risks_df),
            delta="+35"
        )

    with col3:

        st.metric(
            label="Executive Escalations",
            value=len(escalations_df),
            delta="-8"
        )

    with col4:

        st.metric(
            label="Delivery Health",
            value="82%",
            delta="+3%"
        )

    st.divider()

    # =====================================================
    # DELIVERY HEALTH OVERVIEW
    # =====================================================

    st.subheader("Delivery Health Overview")

    health_counts = deals_df[
        "health_profile"
    ].value_counts()

    st.bar_chart(health_counts)

    # =====================================================
    # RISK DISTRIBUTION
    # =====================================================

    st.subheader("Risk Distribution")

    risk_counts = risks_df[
        "impact"
    ].value_counts()

    st.bar_chart(risk_counts)

    # =====================================================
    # ESCALATION DISTRIBUTION
    # =====================================================

    st.subheader("Escalation Severity")

    escalation_counts = escalations_df[
        "severity"
    ].value_counts()

    st.bar_chart(escalation_counts)

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