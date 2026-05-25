"""
Network Visualiser
==================
Draws community-coloured network graphs with node sizes proportional to PageRank.
"""

import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import numpy as np


PALETTE = [
    "#E63946", "#457B9D", "#2A9D8F", "#E9C46A", "#F4A261",
    "#264653", "#6A0572", "#118AB2", "#06D6A0", "#FFB703",
]


def visualise_network(
    G: nx.DiGraph,
    partition: dict,
    df_centrality: pd.DataFrame,
    title: str = "Network",
    save_path: str = None,
    max_nodes: int = 300,
    figsize: tuple = (14, 10),
):
    """
    Draw a spring-layout network with:
      - Node colour  = community
      - Node size    = PageRank × scale
      - Edge width   = edge weight (normalised)
      - Labels       = top-10 nodes by PageRank only

    Parameters
    ----------
    G            : directed graph (with 'community' attribute set)
    partition    : node → community_id dict
    df_centrality: centrality DataFrame (must have 'node', 'pagerank')
    title        : plot title
    save_path    : if set, saves the figure here
    max_nodes    : subsample large graphs for readability
    figsize      : matplotlib figure size
    """
    if G.number_of_nodes() == 0:
        print(f"    {title}: empty graph, skipping visualisation.")
        return

    # Subsample if needed
    if G.number_of_nodes() > max_nodes:
        # Keep top max_nodes by PageRank
        top_nodes = set(
            df_centrality.nlargest(max_nodes, "pagerank")["node"].tolist()
        )
        G = G.subgraph(top_nodes).copy()
        partition = {k: v for k, v in partition.items() if k in top_nodes}

    communities = sorted(set(partition.values()))
    color_map = {cid: PALETTE[i % len(PALETTE)] for i, cid in enumerate(communities)}

    # Node colours & sizes
    pr_map = dict(zip(df_centrality["node"], df_centrality["pagerank"]))
    node_list = list(G.nodes())
    node_colors = [color_map.get(partition.get(n, 0), "#AAAAAA") for n in node_list]

    pr_values = np.array([pr_map.get(n, 1e-6) for n in node_list])
    pr_norm   = (pr_values - pr_values.min()) / (pr_values.max() - pr_values.min() + 1e-9)
    node_sizes = 50 + pr_norm * 800  # range 50–850

    # Edge widths
    edges = list(G.edges(data=True))
    weights = np.array([d.get("weight", 1) for _, _, d in edges], dtype=float)
    if weights.max() > 0:
        edge_widths = 0.3 + (weights / weights.max()) * 2.0
    else:
        edge_widths = [0.5] * len(edges)

    # Layout
    seed = 42
    if G.number_of_nodes() < 50:
        pos = nx.spring_layout(G, seed=seed, k=1.5)
    else:
        pos = nx.spring_layout(G, seed=seed, k=0.8, iterations=30)

    fig, ax = plt.subplots(figsize=figsize)

    # Draw edges
    nx.draw_networkx_edges(
        G, pos, ax=ax,
        width=edge_widths,
        alpha=0.4,
        edge_color="#888888",
        arrows=True,
        arrowsize=8,
        connectionstyle="arc3,rad=0.1",
    )

    # Draw nodes
    nx.draw_networkx_nodes(
        G, pos, ax=ax,
        nodelist=node_list,
        node_color=node_colors,
        node_size=node_sizes,
        alpha=0.85,
        linewidths=0.5,
        edgecolors="white",
    )

    # Label top-10 nodes only
    top10 = set(df_centrality.nlargest(10, "pagerank")["node"].tolist())
    labels = {n: str(n)[:15] for n in node_list if n in top10}
    nx.draw_networkx_labels(
        G, pos, labels=labels, ax=ax,
        font_size=7, font_color="black", font_weight="bold",
    )

    # Legend for communities
    for cid in communities[:10]:
        ax.scatter([], [], c=color_map[cid], s=80, label=f"Community {cid}")
    ax.legend(loc="upper left", fontsize=8, framealpha=0.8,
              title="Communities", title_fontsize=9)

    ax.set_title(title, fontsize=15, fontweight="bold", pad=15)
    ax.axis("off")

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"  💾 Saved: {save_path}")
    plt.show()
    plt.close()
