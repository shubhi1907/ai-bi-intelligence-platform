import pandas as pd
import networkx as nx

# =========================
# LOAD DATA
# =========================

deals_df = pd.read_csv("data/deals.csv")
tickets_df = pd.read_csv("data/tickets.csv")
risks_df = pd.read_csv("data/risks.csv")
escalations_df = pd.read_csv("data/escalations.csv")
meeting_notes_df = pd.read_csv("data/meeting_notes.csv")
customers_df = pd.read_csv("data/customers.csv")

# =========================
# CREATE GRAPH
# =========================

enterprise_graph = nx.Graph()

# =========================
# CUSTOMER NODES
# =========================

for _, row in customers_df.iterrows():

    enterprise_graph.add_node(
        row["customer_id"],
        node_type="customer",
        customer_name=row["customer_name"],
        industry=row["industry"],
        region=row["region"],
        account_tier=row["account_tier"]
    )

# =========================
# DEAL NODES
# =========================

for _, row in deals_df.iterrows():

    enterprise_graph.add_node(
        row["deal_id"],
        node_type="deal",
        project_name=row["project_name"],
        project_status=row["project_status"],
        implementation_phase=row["implementation_phase"],
        health_score=row["health_score"],
        executive_visibility=row["executive_visibility"]
    )

    # CUSTOMER -> DEAL RELATIONSHIP
    enterprise_graph.add_edge(
        row["customer_id"],
        row["deal_id"],
        relationship="HAS_DEAL"
    )

# =========================
# TICKET NODES
# =========================

for _, row in tickets_df.iterrows():

    enterprise_graph.add_node(
        row["ticket_id"],
        node_type="ticket",
        priority=row["priority"],
        severity=row["severity"],
        status=row["status"],
        issue_category=row["issue_category"],
        assigned_team=row["assigned_team"],
        blocker_flag=row["blocker_flag"]
    )

    # DEAL -> TICKET RELATIONSHIP
    enterprise_graph.add_edge(
        row["deal_id"],
        row["ticket_id"],
        relationship="HAS_TICKET"
    )

# =========================
# RISK NODES
# =========================

for _, row in risks_df.iterrows():

    enterprise_graph.add_node(
        row["risk_id"],
        node_type="risk",
        risk_category=row["risk_category"],
        likelihood=row["likelihood"],
        impact=row["impact"],
        current_status=row["current_status"]
    )

    # DEAL -> RISK RELATIONSHIP
    enterprise_graph.add_edge(
        row["deal_id"],
        row["risk_id"],
        relationship="HAS_RISK"
    )

# =========================
# ESCALATION NODES
# =========================

for _, row in escalations_df.iterrows():

    enterprise_graph.add_node(
        row["escalation_id"],
        node_type="escalation",
        severity=row["severity"],
        escalation_source=row["escalation_source"],
        resolution_status=row["resolution_status"]
    )

    # DEAL -> ESCALATION RELATIONSHIP
    enterprise_graph.add_edge(
        row["deal_id"],
        row["escalation_id"],
        relationship="HAS_ESCALATION"
    )

# =========================
# MEETING NODES
# =========================

for _, row in meeting_notes_df.iterrows():

    enterprise_graph.add_node(
        row["meeting_id"],
        node_type="meeting",
        meeting_type=row["meeting_type"],
        meeting_date=row["meeting_date"]
    )

    # DEAL -> MEETING RELATIONSHIP
    enterprise_graph.add_edge(
        row["deal_id"],
        row["meeting_id"],
        relationship="HAS_MEETING"
    )

# =========================
# GRAPH SUMMARY
# =========================

print("\nGRAPH SUCCESSFULLY BUILT")

print("\nTotal Nodes:")
print(enterprise_graph.number_of_nodes())

print("\nTotal Edges:")
print(enterprise_graph.number_of_edges())

# =========================
# NODE TYPE COUNTS
# =========================

node_types = {}

for _, data in enterprise_graph.nodes(data=True):

    node_type = data.get("node_type", "unknown")

    node_types[node_type] = (
        node_types.get(node_type, 0) + 1
    )

print("\nNODE TYPE BREAKDOWN:")

for node_type, count in node_types.items():

    print(f"{node_type}: {count}")