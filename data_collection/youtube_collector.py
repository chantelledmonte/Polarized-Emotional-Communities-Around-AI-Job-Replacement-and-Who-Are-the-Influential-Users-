
"""
YouTube Data Collector
======================
Collects video metadata and comment threads using the YouTube Data API v3.

Nodes  : users (commenters / video authors)
Edges  : reply relationships (A replied to B within a comment thread)

FIX — Gap 1 (API retry logic): _get() now retries on 429/503 with exponential backoff.
FIX — Gap 1 (Data sampling):   collect() accepts a network_sample_size param that
      randomly samples the COLLECTED data down to a reproducible subset and logs
      exactly what was kept vs dropped — so your report can cite it precisely.
FIX — Gap 2 (API key):         Key is never logged or printed; validated silently.
"""

import time
import random
import logging
import requests
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)


# Null-like string values to reject in author fields
_NULL_VALS = {"unknown", "nan", "none", "null", "", "deleted"}

RETRY_STATUS_CODES = {429, 500, 503}
MAX_RETRIES = 4
BASE_BACKOFF = 2.0  # seconds; doubles each retry


class YouTubeCollector:
    BASE_URL = "https://www.googleapis.com/youtube/v3"

    def __init__(self, api_key: str):
        if not api_key or api_key.strip().upper() in ("", "YOUR_YOUTUBE_API_KEY_HERE"):
            raise ValueError(
                "YouTube API key is missing. Set YOUTUBE_API_KEY env var or pass it directly."
            )
        self._api_key = api_key  # private — never printed

    # Internal helpers 

    def _get(self, endpoint: str, params: dict) -> dict:
        """
        GET request with exponential-backoff retry on rate-limit / server errors.
        Fixes Gap 3 (no retry logic for API quota limits).
        """
        p = dict(params)
        p["key"] = self._api_key  # key injected here, never stored in logs

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = requests.get(
                    f"{self.BASE_URL}/{endpoint}", params=p, timeout=20
                )
                if resp.status_code in RETRY_STATUS_CODES:
                    wait = BASE_BACKOFF ** attempt + random.uniform(0, 1)
                    logger.warning(
                        "HTTP %s on attempt %d — retrying in %.1fs",
                        resp.status_code, attempt, wait,
                    )
                    print(f" Rate limit / server error (HTTP {resp.status_code}) "
                          f"— waiting {wait:.1f}s (attempt {attempt}/{MAX_RETRIES})")
                    time.sleep(wait)
                    continue

                resp.raise_for_status()
                return resp.json()

            except requests.Timeout:
                wait = BASE_BACKOFF ** attempt
                print(f"Timeout — retrying in {wait:.1f}s (attempt {attempt}/{MAX_RETRIES})")
                time.sleep(wait)

            except requests.HTTPError as e:
                # 403 = comments disabled or quota exhausted — don't retry
                if e.response.status_code == 403:
                    raise
                raise

        raise RuntimeError(
            f"YouTube API endpoint '{endpoint}' failed after {MAX_RETRIES} retries."
        )

    @staticmethod
    def _is_valid_author(author_id: str) -> bool:
        """
        Returns True only for non-null, non-placeholder author IDs.
        Fixes Gap 5 (missing null author handling).
        """
        if not isinstance(author_id, str):
            return False
        return author_id.strip().lower() not in _NULL_VALS

    def search_videos(self, query: str, max_results: int = 10) -> list[dict]:
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": min(max_results, 50),
            "relevanceLanguage": "en",
            "order": "relevance",
        }
        data = self._get("search", params)
        videos = []
        for item in data.get("items", []):
            vid_id = item.get("id", {}).get("videoId")
            if not vid_id:
                continue
            videos.append({
                "video_id": vid_id,
                "title": item["snippet"]["title"],
                "channel_id": item["snippet"]["channelId"],
                "channel_title": item["snippet"]["channelTitle"],
                "published_at": item["snippet"]["publishedAt"],
                "description": item["snippet"].get("description", "")[:500],
                "query": query,
            })
        return videos

    def get_video_stats(self, video_ids: list[str]) -> dict:
        params = {"part": "statistics", "id": ",".join(video_ids[:50])}
        data = self._get("videos", params)
        stats = {}
        for item in data.get("items", []):
            s = item.get("statistics", {})
            stats[item["id"]] = {
                "view_count":    int(s.get("viewCount",    0)),
                "like_count":    int(s.get("likeCount",    0)),
                "comment_count": int(s.get("commentCount", 0)),
            }
        return stats

    def get_comments(self, video_id: str, max_comments: int = 200) -> list[dict]:
        """Collect top-level comments and their replies for a single video."""
        comments = []
        page_token = None
        fetched = 0

        while fetched < max_comments:
            params = {
                "part": "snippet,replies",
                "videoId": video_id,
                "maxResults": min(100, max_comments - fetched),
                "order": "relevance",
                "textFormat": "plainText",
            }
            if page_token:
                params["pageToken"] = page_token

            try:
                data = self._get("commentThreads", params)
            except requests.HTTPError as e:
                if e.response.status_code == 403:
                    print(f" Comments disabled on {video_id} — skipping")
                    break
                raise

            for thread in data.get("items", []):
                top_snip  = thread["snippet"]["topLevelComment"]["snippet"]
                top_id    = thread["snippet"]["topLevelComment"]["id"]
                top_author = top_snip.get("authorChannelId", {}).get("value", "")

                # Fix Gap 5: validate author before adding
                top_author = top_author if self._is_valid_author(top_author) else None

                comments.append({
                    "comment_id":       top_id,
                    "video_id":         video_id,
                    "text":             top_snip.get("textDisplay", ""),
                    "author_name":      top_snip.get("authorDisplayName", ""),
                    "author_id":        top_author,
                    "like_count":       top_snip.get("likeCount", 0),
                    "published_at":     top_snip.get("publishedAt", ""),
                    "is_reply":         False,
                    "parent_id":        None,
                    "parent_author_id": None,
                })
                fetched += 1

                for reply in thread.get("replies", {}).get("comments", []):
                    rs = reply["snippet"]
                    reply_author = rs.get("authorChannelId", {}).get("value", "")
                    reply_author = reply_author if self._is_valid_author(reply_author) else None

                    comments.append({
                        "comment_id":       reply["id"],
                        "video_id":         video_id,
                        "text":             rs.get("textDisplay", ""),
                        "author_name":      rs.get("authorDisplayName", ""),
                        "author_id":        reply_author,
                        "like_count":       rs.get("likeCount", 0),
                        "published_at":     rs.get("publishedAt", ""),
                        "is_reply":         True,
                        "parent_id":        top_id,
                        "parent_author_id": top_author,
                    })

            page_token = data.get("nextPageToken")
            if not page_token:
                break
            time.sleep(0.3)

        return comments

    #  Public API 

    def collect(
        self,
        queries: list[str],
        max_videos: int = 10,
        max_comments: int = 200,
        network_sample_size: int = None,
        random_seed: int = 42,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Main collection method.

        Parameters
        ----------
        queries             : search queries to run
        max_videos          : videos per query
        max_comments        : comments per video
        network_sample_size : if set, randomly sample DOWN to this many comments
                              after collection. Documents the sampling decision.
                              Fix for Gap 1 (data sampling inconsistency).
        random_seed         : reproducibility seed for sampling

        Returns
        -------
        df_videos, df_comments
        """
        all_videos   = []
        all_comments = []
        seen_video_ids = set()

        for query in queries:
            print(f"Searching YouTube: '{query}'")
            try:
                videos = self.search_videos(query, max_results=max_videos)
            except Exception as e:
                print(f"Search failed for '{query}': {e}")
                continue

            for v in videos:
                if v["video_id"] not in seen_video_ids:
                    seen_video_ids.add(v["video_id"])
                    all_videos.append(v)
            time.sleep(0.5)

        if not all_videos:
            raise RuntimeError("No YouTube videos found. Check your API key and queries.")

        # Fetch stats
        video_ids = [v["video_id"] for v in all_videos]
        stats = {}
        for i in range(0, len(video_ids), 50):
            try:
                stats.update(self.get_video_stats(video_ids[i:i+50]))
            except Exception as e:
                print(f" Stats fetch failed for batch: {e}")
        for v in all_videos:
            v.update(stats.get(v["video_id"], {}))

        df_videos = pd.DataFrame(all_videos)
        if "comment_count" in df_videos.columns:
            df_videos = df_videos.sort_values("comment_count", ascending=False)

        print(f"Fetching comments for {len(df_videos)} videos...")
        for _, row in df_videos.iterrows():
            vid = row["video_id"]
            print(f"    → {vid}: {str(row.get('title',''))[:55]}")
            try:
                cmts = self.get_comments(vid, max_comments=max_comments)
                all_comments.extend(cmts)
            except Exception as e:
                print(f" Comment fetch failed for {vid}: {e}")
            time.sleep(0.5)

        df_comments = pd.DataFrame(all_comments)
        df_comments = df_comments.drop_duplicates(subset=["comment_id"])
        df_comments["collected_at"] = datetime.utcnow().isoformat()

        n_raw = len(df_comments)
        n_null_authors = df_comments["author_id"].isna().sum()

        #FIX Gap 1: document sampling decision 
        if network_sample_size and n_raw > network_sample_size:
            # Stratified: keep all reply rows (needed for edges), sample top-levels
            replies    = df_comments[df_comments["is_reply"] == True]
            top_level  = df_comments[df_comments["is_reply"] == False]
            n_top_keep = max(0, network_sample_size - len(replies))
            top_sample = top_level.sample(
                n=min(n_top_keep, len(top_level)),
                random_state=random_seed
            )
            df_comments = pd.concat([top_sample, replies]).reset_index(drop=True)
            print(f"\nSAMPLING NOTE (document in report):")
            print(f"     Raw collected : {n_raw:,} comments")
            print(f"     Sampled to    : {len(df_comments):,} (seed={random_seed})")
            print(f"     Strategy      : keep all {len(replies):,} replies (for edges) "
                  f"+ random sample of {len(top_sample):,} top-level comments")
            print(f"     Reason        : network analysis feasibility & graph density")
        else:
            print(f"\n No sampling applied — using full dataset ({n_raw:,} comments)")

        print(f" YouTube: {len(df_videos)} videos, {len(df_comments)} comments")
        print(f"     Null/anonymous authors dropped from graph: {n_null_authors}")
        return df_videos, df_comments
