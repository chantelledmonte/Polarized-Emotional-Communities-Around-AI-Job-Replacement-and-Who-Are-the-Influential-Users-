"""
Sentiment Analyser
==================
Uses VADER (Valence Aware Dictionary and sEntiment Reasoner), which is
well-suited to social media text (handles emojis, caps, slang).

Adds columns: compound, pos, neg, neu, sentiment_label
"""

import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


class SentimentAnalyser:
    def __init__(self):
        self._vader = SentimentIntensityAnalyzer()

    def score(self, text: str) -> dict:
        if not isinstance(text, str) or not text.strip():
            return {"compound": 0.0, "pos": 0.0, "neg": 0.0, "neu": 1.0}
        return self._vader.polarity_scores(text)

    @staticmethod
    def label(compound: float) -> str:
        if compound >= 0.05:
            return "Positive"
        if compound <= -0.05:
            return "Negative"
        return "Neutral"

    def analyse(self, df: pd.DataFrame, text_col: str = "text") -> pd.DataFrame:
        """
        Adds sentiment columns to a DataFrame in-place (returns it too).

        Parameters
        ----------
        df       : input DataFrame
        text_col : column containing raw text

        Returns
        -------
        df with added columns: compound, pos, neg, neu, sentiment_label
        """
        scores = df[text_col].fillna("").apply(self.score)
        df["compound"] = scores.apply(lambda s: s["compound"])
        df["pos"]      = scores.apply(lambda s: s["pos"])
        df["neg"]      = scores.apply(lambda s: s["neg"])
        df["neu"]      = scores.apply(lambda s: s["neu"])
        df["sentiment_label"] = df["compound"].apply(self.label)
        return df
