"""
Community Detector
==================
Detects communities using the Louvain method (modularity optimisation).

For directed graphs, we project to undirected before community detection,
then annotate each node with its community membership and the mean sentiment
of its members.
"""

import networkx as nx

try:
    import community as community_louvain
except ImportError:
    try:
        from community import community_louvain
    except ImportError:
        community_louvain = None


def detect_communities(
    G: nx.DiGraph,
    label: str = "",
    resolution: float = 1.0,
) -> tuple[nx.DiGraph, dict]:
    """
    Detect communities in a directed graph using Louvain on the undirected projection.

    Parameters
    ----------
    G          : directed graph
    label      : name for logging
    resolution : Louvain resolution parameter (higher → more, smaller communities)

    Returns
    -------
    G_annotated : same graph with 'community' node attribute added
    partition   : dict mapping node → community_id
    """
    if G.number_of_nodes() == 0:
        print(f"    {label} graph empty; no communities.")
        return G, {}

    G_und = G.to_undirected()

    if community_louvain is None:
        # Fallback: greedy modularity
        print(f"    python-louvain not installed; using greedy modularity for {label}.")
        communities = nx.community.greedy_modularity_communities(G_und)
        partition = {}
        for cid, comm in enumerate(communities):
            for node in comm:
                partition[node] = cid
    else:
        partition = community_louvain.best_partition(
            G_und, resolution=resolution, random_state=42
        )

    n_communities = len(set(partition.values()))
    modularity = _compute_modularity(G_und, partition)

    print(f"   {label}: {n_communities} communities detected  "
          f"(modularity Q = {modularity:.4f})")

    nx.set_node_attributes(G, partition, "community")
    return G, partition


def _compute_modularity(G_und: nx.Graph, partition: dict) -> float:
    """Compute modularity of a partition."""
    try:
        if community_louvain:
            return community_louvain.modularity(partition, G_und)
        # Manual computation
        m = G_und.number_of_edges()
        if m == 0:
            return 0.0
        communities = {}
        for node, cid in partition.items():
            communities.setdefault(cid, set()).add(node)
        Q = 0.0
        for cid, members in communities.items():
            subgraph = G_und.subgraph(members)
            lc = subgraph.number_of_edges()
            dc = sum(dict(G_und.degree(members)).values())
            Q += (lc / m) - (dc / (2 * m)) ** 2
        return Q
    except Exception:
        return float("nan")
