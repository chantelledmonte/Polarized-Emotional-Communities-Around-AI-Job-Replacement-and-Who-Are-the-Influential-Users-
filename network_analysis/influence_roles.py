"""
Influence Roles
===============
Classifies users into structural roles based on their centrality profile.
This goes beyond a simple ranking to interpret what each user's position
means for information flow and polarisation — the PG COSC 2671 requirement.

Role Taxonomy
-------------
Bridge      : High betweenness + moderate PageRank
              → Brokers between communities; controls information flow
              → Key targets for cross-community bridging or echo-chamber detection

Hub         : High out-degree + high PageRank
              → Active participants who link to many authorities
              → Drive engagement volume

Authority   : High in-degree + high authority_score
              → Receive many replies; opinion leaders
              → Likely shapers of community sentiment

Echo Node   : High clustering within one community + low betweenness
              → Deeply embedded; amplifies dominant narrative within community

Peripheral  : Low values across all measures
              → Lurkers or one-time commenters; minimal influence
"""

import pandas as pd
import numpy as np


def classify_user_roles(df_centrality: pd.DataFrame) -> pd.DataFrame:
    """
    Classify each user into a structural role using centrality percentiles.

    Parameters
    ----------
    df_centrality : DataFrame from centrality.compute_centrality()

    Returns
    -------
    df_centrality with added 'role' and 'role_score' columns
    """
    df = df_centrality.copy()
    
    # added here
    if "community" in df.columns:
        df["community"] = df["community"]
        
        
        
        

    if df.empty:
        df["role"] = "Unknown"
        df["role_score"] = 0.0
        return df

    # Normalise to [0,1]
    def _norm(col):
        vals = df[col].fillna(0)
        lo, hi = vals.min(), vals.max()
        if hi == lo:
            return pd.Series(np.zeros(len(df)), index=df.index)
        return (vals - lo) / (hi - lo)

    df["_btw_n"]   = _norm("betweenness")
    df["_pr_n"]    = _norm("pagerank")
    df["_in_n"]    = _norm("in_degree")
    df["_out_n"]   = _norm("out_degree")
    df["_auth_n"]  = _norm("authority_score") if "authority_score" in df else 0
    df["_hub_n"]   = _norm("hub_score")       if "hub_score" in df       else 0
    df["_eig_n"]   = _norm("eigenvector")     if "eigenvector" in df     else 0

    # Role scores (composite)
    df["_bridge_score"]    = df["_btw_n"] * 0.6 + df["_pr_n"] * 0.25 + df["_eig_n"] * 0.15
    df["_hub_score_c"]     = df["_out_n"] * 0.5 + df["_hub_n"] * 0.3 + df["_pr_n"] * 0.2
    df["_authority_score_c"] = df["_in_n"] * 0.5 + df["_auth_n"] * 0.35 + df["_eig_n"] * 0.15

    def _classify(row):
        scores = {
            "Bridge":    row["_bridge_score"],
            "Hub":       row["_hub_score_c"],
            "Authority": row["_authority_score_c"],
        }
        best_role  = max(scores, key=scores.get)
        best_score = scores[best_role]

        # Threshold: peripheral if all scores low
        if best_score < 0.05:
            return "Peripheral", best_score

        # Bridge requires meaningful betweenness
        if best_role == "Bridge" and row["_btw_n"] < 0.1:
            best_role = "Authority" if scores["Authority"] > scores["Hub"] else "Hub"

        return best_role, best_score

    roles_scores = df.apply(_classify, axis=1)
    df["role"]       = [r for r, _ in roles_scores]
    df["role_score"] = [s for _, s in roles_scores]

    # Drop temp columns
    tmp_cols = [c for c in df.columns if c.startswith("_")]
    df = df.drop(columns=tmp_cols)

    # Summary
    summary = df["role"].value_counts()
    print("  👥 User role distribution:")
    for role, count in summary.items():
        print(f"     {role:12s}: {count}")
        
        
        
        
    
    
    
    
    

    return df.sort_values("role_score", ascending=False)
