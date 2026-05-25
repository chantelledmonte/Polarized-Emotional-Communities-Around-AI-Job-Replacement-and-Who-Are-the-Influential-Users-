"""
Centrality Module
=================
Computes multiple centrality measures for directed networks.

Measures included
-----------------
in_degree     : how many users reply TO this user (popularity / authority signal)
out_degree    : how many users this person replies to (activity)
betweenness   : bridge role — how often a node lies on shortest paths
closeness     : how quickly a node can reach all others
pagerank      : recursive influence (like Google PageRank)
eigenvector   : connected to other influential nodes (HITS-style authority)
hub_score     : HITS hub score (points to good authorities)
authority_score: HITS authority score (pointed to by good hubs)

For COSC 2671 PG requirement: all measures are computed and interpreted.
"""

import networkx as nx
import pandas as pd
import numpy as np


def compute_centrality(G: nx.DiGraph, label: str = "") -> pd.DataFrame:
    """
    Compute all centrality measures for a directed graph.

    Parameters
    ----------
    G     : directed NetworkX graph
    label : optional label for print output

    Returns
    -------
    df : DataFrame with one row per node, all centrality scores
    """
    if G.number_of_nodes() == 0:
        print(f"   {label} graph is empty; skipping centrality.")
        return pd.DataFrame(columns=[
            "node","in_degree","out_degree","betweenness",
            "closeness","pagerank","eigenvector","hub_score","authority_score"
        ])

    print(f"   Computing centrality for {label} ({G.number_of_nodes()} nodes)...")

    # In/out degree (normalised)
    n = G.number_of_nodes()
    in_deg  = dict(G.in_degree(weight="weight"))
    out_deg = dict(G.out_degree(weight="weight"))

    # Normalise degree by max value (avoid div-by-zero)
    max_in  = max(in_deg.values())  if in_deg  else 1
    max_out = max(out_deg.values()) if out_deg else 1
    in_deg_norm  = {k: v / max_in  for k, v in in_deg.items()}
    out_deg_norm = {k: v / max_out for k, v in out_deg.items()}

    # Betweenness (use sample for large graphs)
    if n > 500:
        betw = nx.betweenness_centrality(G, k=min(200, n), weight="weight", normalized=True)
    else:
        betw = nx.betweenness_centrality(G, weight="weight", normalized=True)

    # Closeness — use undirected projection for disconnected graphs
    G_und = G.to_undirected()
    try:
        clos = nx.closeness_centrality(G_und)
    except Exception:
        clos = {node: 0.0 for node in G.nodes()}

    # PageRank
    try:
        pr = nx.pagerank(G, alpha=0.85, weight="weight", max_iter=200)
    except nx.PowerIterationFailedConvergence:
        pr = nx.pagerank(G, alpha=0.85, weight="weight", max_iter=1000, tol=1e-4)

    # Eigenvector centrality (may not converge on all graphs)
    try:
        eig = nx.eigenvector_centrality_numpy(G.to_undirected(), weight="weight")
    except Exception:
        eig = {node: 0.0 for node in G.nodes()}

    # HITS hub + authority scores
    try:
        hubs, authorities = nx.hits(G, max_iter=200, normalized=True)
    except Exception:
        hubs       = {node: 0.0 for node in G.nodes()}
        authorities = {node: 0.0 for node in G.nodes()}

    rows = []
    for node in G.nodes():
        rows.append({
            "node":           node,
            "in_degree":      in_deg_norm.get(node, 0.0),
            "out_degree":     out_deg_norm.get(node, 0.0),
            "betweenness":    betw.get(node, 0.0),
            "closeness":      clos.get(node, 0.0),
            "pagerank":       pr.get(node, 0.0),
            "eigenvector":    eig.get(node, 0.0),
            "hub_score":      hubs.get(node, 0.0),
            "authority_score": authorities.get(node, 0.0),
            # Raw degree for annotation
            "in_degree_raw":  in_deg.get(node, 0),
            "out_degree_raw": out_deg.get(node, 0),
            "comment_count":  G.nodes[node].get("comment_count",
                              G.nodes[node].get("post_count", 0)),
        })

    df = pd.DataFrame(rows)
    print(f"   Centrality done for {label}.")
    return df






# added 
def get_top_influential_users(
    df_centrality: pd.DataFrame,
    top_n: int = 10,
    metric: str = "pagerank",
) -> pd.DataFrame:
    """
    Return top influential users.
    """

    return (
        df_centrality
        .sort_values(metric, ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )
