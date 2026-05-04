from openai import OpenAI
import networkx as nx
from build_graph import enterprise_graph
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)

deal_nodes = []

for node, data in enterprise_graph.nodes(data=True):

    if data.get("node_type") == "deal":

        deal_nodes.append(node)

deal_id = deal_nodes[0]

print(f"\nAnalyzing Deal: {deal_id}")

connected_nodes = list(
    enterprise_graph.neighbors(deal_id)
)

tickets = []

risks = []

escalations = []

meetings = []

customer = None

for node in connected_nodes:

    node_data = enterprise_graph.nodes[node]

    node_type = node_data.get("node_type")

    if node_type == "ticket":

        tickets.append(node_data)

    elif node_type == "risk":

        risks.append(node_data)

    elif node_type == "escalation":

        escalations.append(node_data)

    elif node_type == "meeting":

        meetings.append(node_data)

    elif node_type == "customer":

        customer = node_data

prompt = f"""

You are an enterprise implementation intelligence AI.

Analyze the following implementation project.

Customer:
{customer}

Risks:
{risks}

Escalations:
{escalations}

Tickets:
{tickets[:10]}

Meetings:
{meetings[:5]}

Provide:

1. Executive summary
2. Key operational risks
3. Escalation concerns
4. Delivery health assessment
5. Recommended next actions

"""

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {
            "role": "system",
            "content": "You are an enterprise operations intelligence AI."
        },
        {
            "role": "user",
            "content": prompt
        }
    ]
)

print("\nEXECUTIVE AI SUMMARY:\n")

print(
    response.choices[0].message.content
)
