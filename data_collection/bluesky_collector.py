# """
# Bluesky Data Collector
# ======================
# Collects posts and reply threads using the AT Protocol public AppView.

# Authentication: optional (public posts accessible without it), but a
# Bluesky handle + app-password unlocks higher rate limits.

# Nodes  : user handles (DID or handle)
# Edges  : reply relationships (A replied to B) and mentions (@mention)
# """

# import time
# import requests
# import pandas as pd
# from datetime import datetime


# # BSKY_PUBLIC_API = "https://public.api.bsky.app/xrpc"
# BSKY_PUBLIC_API = "https://bsky.social/xrpc"
# BSKY_AUTH_API   = "https://bsky.social/xrpc"


# class BlueskyCollector:
#     def __init__(self, handle: str = "", app_password: str = ""):
#         self.session_token = None
#         self.handle = handle
#         if handle and app_password:
#             self._authenticate(handle, app_password)

#     # ── Auth ───────────────────────────────────────────────────────────────────

#     def _authenticate(self, handle: str, password: str):
#         resp = requests.post(
#             f"{BSKY_AUTH_API}/com.atproto.server.createSession",
#             json={"identifier": handle, "password": password},
#             timeout=15,
#         )
#         if resp.status_code == 200:
#             self.session_token = resp.json().get("accessJwt")
#             print(f"  🔑 Bluesky authenticated as {handle}")
#         else:
#             print(f"  ⚠️  Bluesky auth failed ({resp.status_code}); using public API.")

#     def _headers(self) -> dict:
#         h = {"Accept": "application/json"}
#         if self.session_token:
#             h["Authorization"] = f"Bearer {self.session_token}"
#         return h

#     # ── Internal helpers ───────────────────────────────────────────────────────

#     def _search_posts(self, query: str, limit: int = 100, cursor: str = None) -> dict:
#         params = {"q": query, "limit": min(limit, 100), "lang": "en"}
#         if cursor:
#             params["cursor"] = cursor
#         resp = requests.get(
#             f"{BSKY_PUBLIC_API}/app.bsky.feed.searchPosts",
#             params=params,
#             headers=self._headers(),
#             timeout=15,
#         )
#         resp.raise_for_status()
#         return resp.json()

#     def _get_thread(self, uri: str, depth: int = 3) -> dict:
#         params = {"uri": uri, "depth": depth}
#         resp = requests.get(
#             f"{BSKY_PUBLIC_API}/app.bsky.feed.getPostThread",
#             params=params,
#             headers=self._headers(),
#             timeout=15,
#         )
#         if resp.status_code != 200:
#             return {}
#         return resp.json()

#     @staticmethod
#     def _parse_post(post_view: dict, query: str = "") -> dict:
#         record = post_view.get("record", {})
#         author = post_view.get("author", {})

#         # Extract reply-to info
#         reply_to_uri = None
#         reply_to_handle = None
#         reply_info = record.get("reply", {})
#         if reply_info:
#             parent = reply_info.get("parent", {})
#             reply_to_uri = parent.get("uri", None)

#         # Extract mentions from facets
#         mentions = []
#         for facet in record.get("facets", []):
#             for feature in facet.get("features", []):
#                 if feature.get("$type") == "app.bsky.richtext.facet#mention":
#                     mentions.append(feature.get("did", ""))

#         return {
#             "uri": post_view.get("uri", ""),
#             "cid": post_view.get("cid", ""),
#             "author_handle": author.get("handle", ""),
#             "author_did": author.get("did", ""),
#             "author_display": author.get("displayName", ""),
#             "text": record.get("text", ""),
#             "created_at": record.get("createdAt", ""),
#             "like_count": post_view.get("likeCount", 0),
#             "reply_count": post_view.get("replyCount", 0),
#             "repost_count": post_view.get("repostCount", 0),
#             "reply_to_uri": reply_to_uri,
#             "reply_to_handle": reply_to_handle,  # resolved later
#             "mentions": ",".join(mentions),
#             "is_reply": bool(reply_info),
#             "query": query,
#         }

#     # ── Public API ─────────────────────────────────────────────────────────────

#     def collect(
#         self,
#         queries: list[str],
#         max_posts: int = 500,
#     ) -> pd.DataFrame:
#         """
#         Search Bluesky for posts matching each query and collect reply threads.

#         Returns
#         -------
#         df : DataFrame of posts with reply/mention edges info
#         """
#         all_posts = []
#         seen_uris = set()
#         per_query = max(max_posts // len(queries), 50)

#         for query in queries:
#             print(f"  🔍 Searching Bluesky: '{query}'")
#             fetched = 0
#             cursor = None

#             while fetched < per_query:
#                 try:
#                     data = self._search_posts(query, limit=min(100, per_query - fetched), cursor=cursor)
#                 except requests.HTTPError as e:
#                     print(f"    ⚠️  Bluesky search error: {e}")
#                     break

#                 posts_raw = data.get("posts", [])
#                 if not posts_raw:
#                     break

#                 for pv in posts_raw:
#                     uri = pv.get("uri", "")
#                     if uri in seen_uris:
#                         continue
#                     seen_uris.add(uri)
#                     all_posts.append(self._parse_post(pv, query=query))
#                     fetched += 1

#                 cursor = data.get("cursor")
#                 if not cursor:
#                     break
#                 time.sleep(0.4)

#         if not all_posts:
#             print("  ⚠️  No Bluesky posts collected (API may be unavailable).")
#             return pd.DataFrame(columns=[
#                 "uri","cid","author_handle","author_did","author_display",
#                 "text","created_at","like_count","reply_count","repost_count",
#                 "reply_to_uri","reply_to_handle","mentions","is_reply","query"
#             ])

#         df = pd.DataFrame(all_posts)

#         # Resolve reply_to_handle from URIs we already have
#         uri_to_handle = dict(zip(df["uri"], df["author_handle"]))
#         df["reply_to_handle"] = df["reply_to_uri"].map(uri_to_handle)

#         df["collected_at"] = datetime.utcnow().isoformat()
#         df = df.drop_duplicates(subset=["uri"])

#         print(f"  ✅ Bluesky: {len(df)} posts collected")
#         return df










"""
Bluesky Data Collector
======================
Collects posts and reply threads using the AT Protocol public AppView.

Authentication: optional (public posts accessible without it), but a
Bluesky handle + app-password unlocks higher rate limits.

Nodes  : user handles (DID or handle)
Edges  : reply relationships (A replied to B) and mentions (@mention)
"""

import time
import requests
import pandas as pd
from datetime import datetime


BSKY_PUBLIC_API = "https://bsky.social/xrpc"
BSKY_AUTH_API   = "https://bsky.social/xrpc"

class BlueskyCollector:
    def __init__(self, handle: str = "", app_password: str = ""):
        self.session_token = None
        self.handle = handle
        if handle and app_password:
            self._authenticate(handle, app_password)

    # ── Auth ───────────────────────────────────────────────────────────────────

    def _authenticate(self, handle: str, password: str):
        resp = requests.post(
            f"{BSKY_AUTH_API}/com.atproto.server.createSession",
            json={"identifier": handle, "password": password},
            timeout=15,
        )
        if resp.status_code == 200:
            self.session_token = resp.json().get("accessJwt")
            print(f"  🔑 Bluesky authenticated as {handle}")
        else:
            print(f"  ⚠️  Bluesky auth failed ({resp.status_code}); using public API.")

    def _headers(self) -> dict:
        h = {"Accept": "application/json"}
        if self.session_token:
            h["Authorization"] = f"Bearer {self.session_token}"
        return h

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _search_posts(self, query: str, limit: int = 100, cursor: str = None) -> dict:
        params = {"q": query, "limit": min(limit, 100), "lang": "en"}
        if cursor:
            params["cursor"] = cursor
        resp = requests.get(
            f"{BSKY_PUBLIC_API}/app.bsky.feed.searchPosts",
            params=params,
            headers=self._headers(),
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    def _get_thread(self, uri: str, depth: int = 3) -> dict:
        params = {"uri": uri, "depth": depth}
        resp = requests.get(
            f"{BSKY_PUBLIC_API}/app.bsky.feed.getPostThread",
            params=params,
            headers=self._headers(),
            timeout=15,
        )
        if resp.status_code != 200:
            return {}
        return resp.json()

    @staticmethod
    def _parse_post(post_view: dict, query: str = "") -> dict:
        record = post_view.get("record", {})
        author = post_view.get("author", {})

        # Extract reply-to info
        reply_to_uri = None
        reply_to_handle = None
        reply_info = record.get("reply", {})
        if reply_info:
            parent = reply_info.get("parent", {})
            reply_to_uri = parent.get("uri", None)

        # Extract mentions from facets
        mentions = []
        for facet in record.get("facets", []):
            for feature in facet.get("features", []):
                if feature.get("$type") == "app.bsky.richtext.facet#mention":
                    mentions.append(feature.get("did", ""))

        return {
            "uri": post_view.get("uri", ""),
            "cid": post_view.get("cid", ""),
            "author_handle": author.get("handle", ""),
            "author_did": author.get("did", ""),
            "author_display": author.get("displayName", ""),
            "text": record.get("text", ""),
            "created_at": record.get("createdAt", ""),
            "like_count": post_view.get("likeCount", 0),
            "reply_count": post_view.get("replyCount", 0),
            "repost_count": post_view.get("repostCount", 0),
            "reply_to_uri": reply_to_uri,
            "reply_to_handle": reply_to_handle,  # resolved later
            "mentions": ",".join(mentions),
            "is_reply": bool(reply_info),
            "query": query,
        }

    # ── Public API ─────────────────────────────────────────────────────────────

    def collect(
        self,
        queries: list[str],
        max_posts: int = 500,
    ) -> pd.DataFrame:
        """
        Search Bluesky for posts matching each query and collect reply threads.

        Returns
        -------
        df : DataFrame of posts with reply/mention edges info
        """
        all_posts = []
        seen_uris = set()
        per_query = max(max_posts // len(queries), 50)

        for query in queries:
            print(f"  🔍 Searching Bluesky: '{query}'")
            fetched = 0
            cursor = None

            while fetched < per_query:
                try:
                    data = self._search_posts(query, limit=min(100, per_query - fetched), cursor=cursor)
                except requests.HTTPError as e:
                    print(f"    ⚠️  Bluesky search error: {e}")
                    break

                posts_raw = data.get("posts", [])
                if not posts_raw:
                    break

                for pv in posts_raw:
                    uri = pv.get("uri", "")
                    if uri in seen_uris:
                        continue
                    seen_uris.add(uri)
                    all_posts.append(self._parse_post(pv, query=query))
                    fetched += 1

                cursor = data.get("cursor")
                if not cursor:
                    break
                time.sleep(0.4)

        if not all_posts:
            print("  ⚠️  No Bluesky posts collected (API may be unavailable).")
            return pd.DataFrame(columns=[
                "uri","cid","author_handle","author_did","author_display",
                "text","created_at","like_count","reply_count","repost_count",
                "reply_to_uri","reply_to_handle","mentions","is_reply","query"
            ])

        df = pd.DataFrame(all_posts)

        # Resolve reply_to_handle from URIs we already have
        uri_to_handle = dict(zip(df["uri"], df["author_handle"]))
        df["reply_to_handle"] = df["reply_to_uri"].map(uri_to_handle)

        df["collected_at"] = datetime.utcnow().isoformat()
        df = df.drop_duplicates(subset=["uri"])

        print(f"  ✅ Bluesky: {len(df)} posts collected")
        return df
