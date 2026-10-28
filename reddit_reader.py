"""Read-only reader for new public posts in a few subreddits.

Runs once a day. It gets an app-only OAuth token (client_credentials, no user
login), reads /r/{subreddit}/new once per subreddit, keeps recent posts above a
small score, and prints them as JSON lines. It never posts, comments, votes or
sends messages.

Credentials come from environment variables only:
    REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
LISTING_URL = "https://oauth.reddit.com/r/{sub}/new"

SUBREDDITS = [
    "SaaS",
    "startups",
    "artificial",
    "LocalLLaMA",
    "devops",
    "smallbusiness",
    "ExperiencedDevs",
]
LIMIT = 100  # listing maximum: one request per subreddit
MIN_SCORE = 5
LOOKBACK = timedelta(hours=26)
TIMEOUT_S = 30.0

# Only these fields are kept. Comments, user profiles and votes are never read.
FIELDS = ("name", "subreddit", "title", "selftext", "author", "score", "num_comments", "permalink")


def get_token(client: httpx.Client, client_id: str, client_secret: str, user_agent: str) -> str:
    response = client.post(
        TOKEN_URL,
        data={"grant_type": "client_credentials"},
        auth=(client_id, client_secret),
        headers={"User-Agent": user_agent},
    )
    response.raise_for_status()
    body = response.json()
    if "access_token" not in body:
        raise RuntimeError(f"token refused: {body.get('error', 'no access_token')}")
    return body["access_token"]


def read_new_posts(
    client: httpx.Client, token: str, user_agent: str, since: datetime
) -> list[dict[str, Any]]:
    headers = {"Authorization": f"bearer {token}", "User-Agent": user_agent}
    posts: dict[str, dict[str, Any]] = {}
    for sub in SUBREDDITS:
        response = client.get(
            LISTING_URL.format(sub=sub),
            params={"limit": LIMIT, "raw_json": 1},
            headers=headers,
        )
        response.raise_for_status()
        for child in response.json().get("data", {}).get("children", []):
            post = child.get("data") or {}
            created = datetime.fromtimestamp(float(post.get("created_utc", 0)), UTC)
            if post.get("over_18") or created < since:
                continue
            if (post.get("score") or 0) < MIN_SCORE:
                continue
            kept = {field: post.get(field) for field in FIELDS}
            kept["created_utc"] = created.isoformat()
            posts.setdefault(post["name"], kept)
    return list(posts.values())


def main() -> int:
    try:
        client_id = os.environ["REDDIT_CLIENT_ID"]
        client_secret = os.environ["REDDIT_CLIENT_SECRET"]
        user_agent = os.environ["REDDIT_USER_AGENT"]
    except KeyError as missing:
        print(f"missing environment variable {missing}", file=sys.stderr)
        return 1
    since = datetime.now(UTC) - LOOKBACK
    with httpx.Client(timeout=TIMEOUT_S) as client:
        token = get_token(client, client_id, client_secret, user_agent)
        for post in read_new_posts(client, token, user_agent, since):
            print(json.dumps(post, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
