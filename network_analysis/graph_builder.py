# """
# Graph Builder
# =============
# Constructs directed, weighted interaction graphs from comment / post data.

# YouTube
# -------
#   Nodes : user IDs (author_id)
#   Edges : directed reply edges A → B (A replied to B)
#   Weight: number of replies from A to B

# Bluesky
# -------
#   Nodes : user handles (author_handle)
#   Edges : directed reply / mention edges A → B
#   Weight: interaction count
# """

# import networkx as nx
# import pandas as pd
# from collections import defaultdict


# def build_youtube_reply_graph(
#     df: pd.DataFrame,
#     author_col: str = "author_id",
#     parent_col: str = "parent_author_id",
#     min_edge_weight: int = 1,
# ) -> nx.DiGraph:
#     """
#     Build a directed weighted graph from YouTube comment threads.

#     An edge A → B exists when user A replied to a comment by user B.
#     Self-loops and edges to 'unknown' users are removed.

#     Parameters
#     ----------
#     df             : comments DataFrame (must include reply rows with parent_author_id)
#     author_col     : column for the replying user's ID
#     parent_col     : column for the parent comment's author ID
#     min_edge_weight: drop edges with fewer interactions than this threshold

#     Returns
#     -------
#     G : nx.DiGraph
#     """
#     G = nx.DiGraph()
#     edge_weights: dict = defaultdict(int)

#     replies = df[df["is_reply"] == True].copy()

#     for _, row in replies.iterrows():
#         src = str(row.get(author_col, "")).strip()
#         tgt = str(row.get(parent_col, "")).strip()

#         if not src or not tgt:
#             continue
#         if src in ("unknown", "nan", "None") or tgt in ("unknown", "nan", "None"):
#             continue
#         if src == tgt:
#             continue  # skip self-loops

#         edge_weights[(src, tgt)] += 1

#     for (src, tgt), w in edge_weights.items():
#         if w >= min_edge_weight:
#             G.add_edge(src, tgt, weight=w)

#     # Add node attribute: total comment count
#     comment_counts = df.groupby(author_col).size().to_dict()
#     for node in G.nodes():
#         G.nodes[node]["comment_count"] = comment_counts.get(node, 0)

#     print(f"  📊 YouTube graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
#     return G


# def build_bluesky_reply_graph(
#     df: pd.DataFrame,
#     author_col: str = "author_handle",
#     reply_to_col: str = "reply_to_handle",
#     mention_col: str = "mentions",
#     min_edge_weight: int = 1,
# ) -> nx.DiGraph:
#     """
#     Build a directed weighted graph from Bluesky posts.

#     Edges come from two sources:
#       1. Direct replies  : A → B when A replied to B's post
#       2. Mentions        : A → B when A mentioned @B in their post

#     Parameters
#     ----------
#     df             : posts DataFrame
#     author_col     : column for the posting user's handle
#     reply_to_col   : column for the handle being replied to (may be NaN)
#     mention_col    : column with comma-separated mentioned DIDs/handles
#     min_edge_weight: drop edges with fewer interactions

#     Returns
#     -------
#     G : nx.DiGraph
#     """
#     G = nx.DiGraph()
#     edge_weights: dict = defaultdict(int)

#     for _, row in df.iterrows():
#         src = str(row.get(author_col, "")).strip()
#         if not src or src in ("nan", "None", ""):
#             continue

#         # Reply edges
#         tgt_reply = str(row.get(reply_to_col, "")).strip()
#         if tgt_reply and tgt_reply not in ("nan", "None", "") and tgt_reply != src:
#             edge_weights[(src, tgt_reply)] += 1

#         # Mention edges
#         mentions_raw = str(row.get(mention_col, "")).strip()
#         if mentions_raw and mentions_raw not in ("nan", "None", ""):
#             for mention in mentions_raw.split(","):
#                 mention = mention.strip()
#                 if mention and mention != src:
#                     edge_weights[(src, mention)] += 1

#     for (src, tgt), w in edge_weights.items():
#         if w >= min_edge_weight:
#             G.add_edge(src, tgt, weight=w)

#     # Node attributes
#     post_counts = df.groupby(author_col).size().to_dict()
#     for node in G.nodes():
#         G.nodes[node]["post_count"] = post_counts.get(node, 0)

#     print(f"  📊 Bluesky graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
#     return G






"""
Graph Builder
=============
Constructs directed, weighted interaction graphs from comment / post data.

FIX — Gap 5 (null author handling): comprehensive validation rejects None,
      NaN, empty string, 'unknown', 'deleted', numeric-only strings, and
      strings shorter than 3 chars. Reports drop counts for documentation.

Network design:
  Nodes : individual users (YouTube channel ID / Bluesky handle)
  Edges : directed reply A → B  (A replied to B's comment)
  Type  : Directed (replies have a clear sender → receiver)
  Weight: number of replies between the same pair of users
"""

import re
import networkx as nx
import pandas as pd
from collections import defaultdict

# Comprehensive null/placeholder set
_NULL_VALS = {
    "unknown", "nan", "none", "null", "", "deleted",
    "anonymous", "n/a", "na", "[deleted]", "[removed]",
}

def _is_valid_id(val) -> bool:
    """
    Returns True only when val is a usable, non-null identifier.
    Fixes Gap 5: goes beyond basic string check to catch numeric-only
    placeholders and very short/meaningless IDs.
    """
    if val is None:
        return False
    s = str(val).strip().lower()
    if s in _NULL_VALS:
        return False
    if len(s) < 3:
        return False
    # Reject purely numeric short strings that look like placeholder IDs
    if re.fullmatch(r'\d{1,4}', s):
        return False
    return True


def build_youtube_reply_graph(
    df: pd.DataFrame,
    author_col: str = "author_id",
    parent_col: str = "parent_author_id",
    min_edge_weight: int = 1,
) -> nx.DiGraph:
    """
    Build a directed weighted graph from YouTube comment threads.

    Edge A → B = user A replied to user B's comment.
    Self-loops removed. Both endpoints must pass _is_valid_id().

    Parameters
    ----------
    df              : comments DataFrame with reply chain columns
    author_col      : column for the replying user's channel ID
    parent_col      : column for the parent comment's author channel ID
    min_edge_weight : drop edges below this reply-count threshold

    Returns
    -------
    G : nx.DiGraph  (directed, weighted)
    """
    G = nx.DiGraph()
    edge_weights: dict = defaultdict(int)

    # Counters for documentation / report
    n_total_replies  = 0
    n_dropped_null   = 0
    n_dropped_self   = 0

    replies = df[df["is_reply"] == True].copy()

    for _, row in replies.iterrows():
        n_total_replies += 1
        src = row.get(author_col)
        tgt = row.get(parent_col)

        # Fix Gap 5: validate both endpoints thoroughly
        if not _is_valid_id(src) or not _is_valid_id(tgt):
            n_dropped_null += 1
            continue

        src, tgt = str(src).strip(), str(tgt).strip()

        if src == tgt:
            n_dropped_self += 1
            continue

        edge_weights[(src, tgt)] += 1

    for (src, tgt), w in edge_weights.items():
        if w >= min_edge_weight:
            G.add_edge(src, tgt, weight=w)

    # Attach per-user comment count as a node attribute
    comment_counts = (
        df[df[author_col].apply(_is_valid_id)]
        .groupby(author_col).size().to_dict()
    )
    for node in G.nodes():
        G.nodes[node]["comment_count"] = comment_counts.get(node, 0)

    n_dropped_weight = sum(1 for w in edge_weights.values() if w < min_edge_weight)

    print(f"  📊 YouTube graph built:")
    print(f"     Nodes (users)   : {G.number_of_nodes()}")
    print(f"     Edges (replies) : {G.number_of_edges()}")
    print(f"     Dropped — null author  : {n_dropped_null}/{n_total_replies}")
    print(f"     Dropped — self-loop    : {n_dropped_self}/{n_total_replies}")
    print(f"     Dropped — low weight   : {n_dropped_weight} edges (min_weight={min_edge_weight})")
    return G


def build_bluesky_reply_graph(
    df: pd.DataFrame,
    author_col: str = "author_handle",
    reply_to_col: str = "reply_to_handle",
    mention_col: str = "mentions",
    min_edge_weight: int = 1,
) -> nx.DiGraph:
    """
    Build a directed weighted graph from Bluesky posts.

    Edges come from two sources:
      1. Direct replies  : A → B when A replied to B's post
      2. Mentions        : A → B when A @mentioned B

    Parameters
    ----------
    df              : posts DataFrame
    author_col      : posting user's handle
    reply_to_col    : handle being replied to (may be NaN)
    mention_col     : comma-separated mentioned handles/DIDs
    min_edge_weight : drop edges below this threshold

    Returns
    -------
    G : nx.DiGraph  (directed, weighted)
    """
    G = nx.DiGraph()
    edge_weights: dict = defaultdict(int)

    n_reply_edges   = 0
    n_mention_edges = 0
    n_dropped_null  = 0

    for _, row in df.iterrows():
        src = row.get(author_col)
        if not _is_valid_id(src):
            n_dropped_null += 1
            continue
        src = str(src).strip()

        # 1. Reply edges
        tgt_reply = row.get(reply_to_col)
        if _is_valid_id(tgt_reply):
            tgt_reply = str(tgt_reply).strip()
            if tgt_reply != src:
                edge_weights[(src, tgt_reply)] += 1
                n_reply_edges += 1

        # 2. Mention edges
        mentions_raw = row.get(mention_col)
        if _is_valid_id(mentions_raw):
            for mention in str(mentions_raw).split(","):
                mention = mention.strip()
                if _is_valid_id(mention) and mention != src:
                    edge_weights[(src, mention)] += 1
                    n_mention_edges += 1

    for (src, tgt), w in edge_weights.items():
        if w >= min_edge_weight:
            G.add_edge(src, tgt, weight=w)

    post_counts = (
        df[df[author_col].apply(_is_valid_id)]
        .groupby(author_col).size().to_dict()
    )
    for node in G.nodes():
        G.nodes[node]["post_count"] = post_counts.get(node, 0)

    n_dropped_weight = sum(1 for w in edge_weights.values() if w < min_edge_weight)

    print(f"  📊 Bluesky graph built:")
    print(f"     Nodes (users)   : {G.number_of_nodes()}")
    print(f"     Edges (replies+mentions): {G.number_of_edges()}")
    print(f"     Reply edges added  : {n_reply_edges}")
    print(f"     Mention edges added: {n_mention_edges}")
    print(f"     Dropped — null author  : {n_dropped_null} rows")
    print(f"     Dropped — low weight   : {n_dropped_weight} edges (min_weight={min_edge_weight})")
    return G
