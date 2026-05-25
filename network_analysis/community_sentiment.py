"""
Community Sentiment Analyser
============================
Merges user-level sentiment from comments/posts with community membership
to produce community-level sentiment profiles.
"""

import pandas as pd
import numpy as np


def analyse_community_sentiment(
    df: pd.DataFrame,
    df_centrality: pd.DataFrame,
    partition: dict,
    user_col: str = "author_id",
    sentiment_col: str = "compound",
    min_users: int = 5
) -> pd.DataFrame:
    """
    Compute per-community sentiment statistics.

    Parameters
    ----------
    df           : raw comments/posts DataFrame (with sentiment columns)
    df_centrality: centrality DataFrame (with 'node' column)
    partition    : node → community_id dict
    user_col     : column in df that holds the user identifier
    sentiment_col: VADER compound score column
    min_users    : minimum community size to report

    Returns
    -------
    DataFrame with columns:
        community, n_users, n_posts, mean_sentiment, std_sentiment,
        pct_positive, pct_negative, pct_neutral, sentiment_label
    """
    if not partition:
        return pd.DataFrame()

    # Add community membership to comments
    df = df.copy()
    df["community"] = df[user_col].map(partition)
    df = df.dropna(subset=["community"])
    df["community"] = df["community"].astype(int)

    rows = []
    for cid, group in df.groupby("community"):
        n_posts   = len(group)
        n_users   = group[user_col].nunique()
        if n_users < min_users:
            continue

        compounds = group[sentiment_col].dropna()
        mean_sent = compounds.mean()
        std_sent  = compounds.std()

        pct_pos = (compounds >= 0.05).mean()
        pct_neg = (compounds <= -0.05).mean()
        pct_neu = 1 - pct_pos - pct_neg

        # Community-level label
        if mean_sent >= 0.05:
            comm_label = "Positive"
        elif mean_sent <= -0.05:
            comm_label = "Negative"
        else:
            comm_label = "Neutral"

        rows.append({
            "community":      cid,
            "n_users":        n_users,
            "n_posts":        n_posts,
            "mean_sentiment": round(mean_sent, 4),
            "std_sentiment":  round(std_sent,  4),
            "pct_positive":   round(pct_pos,   3),
            "pct_negative":   round(pct_neg,   3),
            "pct_neutral":    round(pct_neu,   3),
            "sentiment_label": comm_label,
        })

    # result = pd.DataFrame(rows).sort_values("community")
    
    result = pd.DataFrame(rows)

    # Handle empty result safely
    if result.empty:
        print("WARNING: No valid communities found for sentiment analysis.")
        return pd.DataFrame(columns=[
            "community",
            "n_users",
            "n_posts",
            "mean_sentiment",
            "std_sentiment",
            "pct_positive",
            "pct_negative",
            "pct_neutral",
            "sentiment_label"
        ])

    result = result.sort_values("community")
    
    
    
    
    
    
    

    # Polarisation metric: std across community means
    if len(result) > 1:
        pol_index = result["mean_sentiment"].std()
        print(f"   Cross-community polarisation index (σ of means): {pol_index:.4f}")
    return result




# added this 

def detect_polarized_communities(
    df_community_sentiment: pd.DataFrame,
    threshold: float = 0.25,
) -> pd.DataFrame:
    """
    Flags emotionally polarized communities.

    A community is considered polarized if:
    |mean_sentiment| >= threshold
    """

    df = df_community_sentiment.copy()

    df["polarized"] = (
        df["mean_sentiment"].abs() >= threshold
    )

    return df
