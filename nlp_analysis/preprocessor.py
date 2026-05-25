"""
Text Preprocessor
=================
Cleans and normalises social media text for NLP tasks.
"""

import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

nltk.download("stopwords", quiet=True)
nltk.download("punkt", quiet=True)
nltk.download("wordnet", quiet=True)
nltk.download("punkt_tab", quiet=True)

# AI/jobs domain stopwords to add to standard set
DOMAIN_STOPWORDS = {
    "ai", "artificial", "intelligence", "job", "jobs", "work", "worker",
    "people", "think", "know", "just", "going", "get", "like", "make",
    "one", "also", "well", "really", "already", "still", "even", "would",
    "could", "will", "say", "said", "http", "https", "www", "com",
}


class TextPreprocessor:
    def __init__(self, extra_stopwords: set = None):
        self._stop = set(stopwords.words("english")) | DOMAIN_STOPWORDS
        if extra_stopwords:
            self._stop |= extra_stopwords
        self._lemmatizer = WordNetLemmatizer()

    def clean(self, text: str) -> str:
        """Full cleaning pipeline for LDA input."""
        if not isinstance(text, str) or not text.strip():
            return ""
        # Lower-case
        text = text.lower()
        # Remove URLs
        text = re.sub(r"https?://\S+|www\.\S+", " ", text)
        # Remove @mentions and #hashtags symbols (keep word)
        text = re.sub(r"@\w+", " ", text)
        text = re.sub(r"#(\w+)", r"\1", text)
        # Remove HTML entities
        text = re.sub(r"&\w+;", " ", text)
        # Remove non-alpha characters
        text = re.sub(r"[^a-z\s]", " ", text)
        # Tokenise
        tokens = word_tokenize(text)
        # Remove stopwords and short tokens, then lemmatise
        tokens = [
            self._lemmatizer.lemmatize(t)
            for t in tokens
            if t not in self._stop and len(t) > 2
        ]
        return " ".join(tokens)

    def raw_clean(self, text: str) -> str:
        """Light cleaning for sentiment analysis (preserves negations etc.)."""
        if not isinstance(text, str):
            return ""
        text = re.sub(r"https?://\S+|www\.\S+", " ", text)
        text = re.sub(r"&\w+;", " ", text)
        return text.strip()
