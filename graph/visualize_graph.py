import pandas as pd
import networkx as nx
from pyvis.network import Network

from build_graph import enterprise_graph

print("Graph Loaded")

print(
    "Nodes:",
    enterprise_graph.number_of_nodes()
)

print(
    "Edges:",
    enterprise_graph.number_of_edges()
)

sample_nodes = list(
    enterprise_graph.nodes()
)[:150]

subgraph = enterprise_graph.subgraph(
    sample_nodes
)

net = Network(
    height="900px",
    width="100%",
    bgcolor="#111111",
    font_color="white"
)

color_map = {
    "customer": "#00bfff",
    "deal": "#32cd32",
    "ticket": "#ffcc00",
    "risk": "#ff4d4d",
    "escalation": "#ff00ff",
    "meeting": "#ffa500"
}

for node, data in subgraph.nodes(data=True):

    node_type = data.get(
        "node_type",
        "unknown"
    )

    color = color_map.get(
        node_type,
        "#cccccc"
    )

    net.add_node(
        node,
        label=str(node),
        color=color,
        title=str(data),
        size=20
    )

for source, target, data in subgraph.edges(data=True):

    relationship = data.get(
        "relationship",
        ""
    )

    net.add_edge(
        source,
        target,
        title=relationship
    )

net.barnes_hut()


net.save_graph("enterprise_graph.html")
print(
    "Graph visualization saved as enterprise_graph.html"
)