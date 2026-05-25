"""
Network Statistics
==================
Computes summary statistics for a network.
"""

import networkx as nx
import numpy as np


def network_summary(G: nx.DiGraph, label: str = "") -> dict:
    """
    Compute high-level network statistics.

    Parameters
    ----------
    G     : directed graph
    label : platform label (for the 'platform' column)

    Returns
    -------
    dict of statistics
    """
    if G.number_of_nodes() == 0:
        return {"platform": label, "nodes": 0, "edges": 0}

    G_und = G.to_undirected()
    n = G.number_of_nodes()
    m = G.number_of_edges()

    # Density
    density = nx.density(G)

    # Average clustering (undirected)
    try:
        avg_clustering = nx.average_clustering(G_und)
    except Exception:
        avg_clustering = float("nan")

    # Average shortest path (largest connected component only)
    try:
        largest_cc = max(nx.connected_components(G_und), key=len)
        G_lcc = G_und.subgraph(largest_cc)
        if len(largest_cc) > 1:
            avg_path = nx.average_shortest_path_length(G_lcc)
            diameter  = nx.diameter(G_lcc)
        else:
            avg_path = 0.0
            diameter  = 0
    except Exception:
        avg_path = float("nan")
        diameter  = float("nan")

    # Degree stats
    in_degrees  = [d for _, d in G.in_degree()]
    out_degrees = [d for _, d in G.out_degree()]

    # Reciprocity
    try:
        reciprocity = nx.reciprocity(G)
    except Exception:
        reciprocity = float("nan")

    return {
        "platform":           label,
        "nodes":              n,
        "edges":              m,
        "density":            round(density, 6),
        "avg_clustering":     round(avg_clustering, 4),
        "avg_shortest_path":  round(avg_path, 4) if not np.isnan(avg_path) else "N/A",
        "diameter":           diameter,
        "reciprocity":        round(reciprocity, 4) if not np.isnan(reciprocity) else "N/A",
        "avg_in_degree":      round(np.mean(in_degrees), 3),
        "max_in_degree":      int(np.max(in_degrees)),
        "avg_out_degree":     round(np.mean(out_degrees), 3),
        "n_weakly_connected_components": nx.number_weakly_connected_components(G),
    }
