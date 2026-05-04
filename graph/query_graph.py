import networkx as nx

from build_graph import enterprise_graph

# =========================
# GRAPH SUMMARY
# =========================

print("\nGRAPH LOADED")

print(
    f"Nodes: {enterprise_graph.number_of_nodes()}"
)

print(
    f"Edges: {enterprise_graph.number_of_edges()}"
)

# =========================
# FIND AVAILABLE DEAL IDS
# =========================

deal_nodes = []

for node, data in enterprise_graph.nodes(data=True):

    if data.get("node_type") == "deal":

        deal_nodes.append(node)

print("\nAVAILABLE DEAL IDS:")

print(deal_nodes[:10])

# =========================
# SELECT DEAL
# =========================

deal_id = deal_nodes[0]

print(f"\nSELECTED DEAL: {deal_id}")

# =========================
# VERIFY DEAL EXISTS
# =========================

if deal_id in enterprise_graph:

    print(f"\nDeal Found: {deal_id}")

else:

    print(f"\nDeal NOT found: {deal_id}")

# =========================
# GET CONNECTED NODES
# =========================

connected_nodes = list(
    enterprise_graph.neighbors(deal_id)
)

print("\nCONNECTED NODES:")

print(connected_nodes)

# =========================
# SHOW ENTITY DETAILS
# =========================

print("\nCONNECTED ENTITY DETAILS:\n")

for node in connected_nodes:

    node_data = enterprise_graph.nodes[node]

    print(f"Node: {node}")

    print(
        f"Type: {node_data.get('node_type')}"
    )

    print("-" * 40)

# =========================
# SHOW CONNECTED RISKS
# =========================

print("\nCONNECTED RISKS:\n")

for node in connected_nodes:

    node_data = enterprise_graph.nodes[node]

    if node_data.get("node_type") == "risk":

        print(f"Risk ID: {node}")

        print(
            f"Category: {node_data.get('risk_category')}"
        )

        print(
            f"Likelihood: {node_data.get('likelihood')}"
        )

        print(
            f"Impact: {node_data.get('impact')}"
        )

        print(
            f"Status: {node_data.get('current_status')}"
        )

        print("-" * 50)

# =========================
# SHOW CONNECTED ESCALATIONS
# =========================

print("\nCONNECTED ESCALATIONS:\n")

for node in connected_nodes:

    node_data = enterprise_graph.nodes[node]

    if node_data.get("node_type") == "escalation":

        print(
            f"Escalation ID: {node}"
        )

        print(
            f"Severity: {node_data.get('severity')}"
        )

        print(
            f"Source: {node_data.get('escalation_source')}"
        )

        print(
            f"Resolution Status: {node_data.get('resolution_status')}"
        )

        print("-" * 50)

# =========================
# SHOW CONNECTED TICKETS
# =========================

print("\nCONNECTED TICKETS:\n")

for node in connected_nodes:

    node_data = enterprise_graph.nodes[node]

    if node_data.get("node_type") == "ticket":

        print(f"Ticket ID: {node}")

        print(
            f"Priority: {node_data.get('priority')}"
        )

        print(
            f"Severity: {node_data.get('severity')}"
        )

        print(
            f"Status: {node_data.get('status')}"
        )

        print(
            f"Issue Category: {node_data.get('issue_category')}"
        )

        print("-" * 50)

# =========================
# SHOW CONNECTED MEETINGS
# =========================

print("\nCONNECTED MEETINGS:\n")

for node in connected_nodes:

    node_data = enterprise_graph.nodes[node]

    if node_data.get("node_type") == "meeting":

        print(f"Meeting ID: {node}")

        print(
            f"Meeting Type: {node_data.get('meeting_type')}"
        )

        print(
            f"Meeting Date: {node_data.get('meeting_date')}"
        )

        print("-" * 50)

# =========================
# SHOW CONNECTED CUSTOMER
# =========================

print("\nCONNECTED CUSTOMER:\n")

for node in connected_nodes:

    node_data = enterprise_graph.nodes[node]

    if node_data.get("node_type") == "customer":

        print(f"Customer ID: {node}")

        print(
            f"Customer Name: {node_data.get('customer_name')}"
        )

        print(
            f"Industry: {node_data.get('industry')}"
        )

        print(
            f"Region: {node_data.get('region')}"
        )

        print(
            f"Account Tier: {node_data.get('account_tier')}"
        )

        print("-" * 50)