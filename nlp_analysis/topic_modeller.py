"""
Topic Modeller
==============
Fits Latent Dirichlet Allocation (LDA) on cleaned text and assigns
each document a dominant topic.
"""

import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation


class TopicModeller:
    def __init__(
        self,
        n_topics: int = 5,
        n_top_words: int = 10,
        max_features: int = 5000,
        random_state: int = 42,
    ):
        self.n_topics = n_topics
        self.n_top_words = n_top_words
        self.random_state = random_state

        self._vectorizer = CountVectorizer(
            max_df=0.95,
            min_df=3,
            max_features=max_features,
            ngram_range=(1, 2),
        )
        self._lda = LatentDirichletAllocation(
            n_components=n_topics,
            max_iter=15,
            learning_method="online",
            random_state=random_state,
            n_jobs=-1,
        )
        self.topic_words: dict[int, str] = {}

    def fit_transform(
        self,
        df: pd.DataFrame,
        text_col: str = "clean_text",
        prefix: str = "",
    ) -> tuple[pd.DataFrame, dict[int, str]]:
        """
        Fit LDA and add dominant-topic columns to df.

        Parameters
        ----------
        df       : DataFrame with a cleaned text column
        text_col : name of the cleaned text column
        prefix   : prefix for output columns (e.g. 'yt' or 'bsky')

        Returns
        -------
        df               : modified in place with new columns
        topic_words dict : {topic_id: "word1 word2 ..."}
        """
        texts = df[text_col].fillna("").tolist()
        # Filter out empty texts
        valid_mask = [bool(t.strip()) for t in texts]
        valid_texts = [t for t, m in zip(texts, valid_mask) if m]

        if len(valid_texts) < self.n_topics * 2:
            print(f"    Too few documents for LDA ({len(valid_texts)}). Skipping.")
            dom_col = f"{prefix}_dominant_topic" if prefix else "dominant_topic"
            df[dom_col] = -1
            return df, {}

        dtm = self._vectorizer.fit_transform(valid_texts)
        doc_topics = self._lda.fit_transform(dtm)

        # Extract top words per topic
        feature_names = self._vectorizer.get_feature_names_out()
        topic_words = {}
        for tid, comp in enumerate(self._lda.components_):
            top_idx = comp.argsort()[:-self.n_top_words - 1:-1]
            topic_words[tid] = " | ".join(feature_names[top_idx])
        self.topic_words = topic_words

        # Map dominant topic back to all rows
        dom_col   = f"{prefix}_dominant_topic" if prefix else "dominant_topic"
        topic_col = f"{prefix}_topic_dist"     if prefix else "topic_dist"

        dominant = [int(doc.argmax()) for doc in doc_topics]

        # Build full-length arrays (invalid rows get -1)
        dom_full   = []
        valid_iter = iter(dominant)
        for m in valid_mask:
            dom_full.append(next(valid_iter) if m else -1)

        df[dom_col] = dom_full
        return df, topic_words

    def get_topic_label(self, topic_id: int) -> str:
        return self.topic_words.get(topic_id, f"Topic {topic_id}")
