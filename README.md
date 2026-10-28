# reddit-reader

A small, read-only script for a personal, non-commercial research project. Once a day it reads new public posts in a few technology and developer communities, so I can follow which tools, problems and topics people are discussing.

## What it does

1. Gets an app-only OAuth token (`client_credentials`; no user login, no user scopes).
2. Makes one request per subreddit to `/r/{subreddit}/new?limit=100` for:
   r/SaaS, r/startups, r/artificial, r/LocalLLaMA, r/devops, r/smallbusiness, r/ExperiencedDevs.
3. Keeps posts from the last 26 hours with a score of 5 or more, skipping NSFW posts.
4. Prints each post as one JSON line.

About 8 requests per day in total, far below Reddit's 100 queries per minute.

## What it never does

- Post, comment, vote or send messages
- Read comments, user profiles, votes, or private, quarantined or NSFW content
- Act as a user account

## Data kept

Post id, subreddit, title, self-text, author name, score, comment count, permalink and created time. Posts are kept in a private database that only I can access. Nothing is published, shared with third parties, sold or used to train AI models. Raw post text is deleted after 90 days, and I will delete any data on request.

## Running

```bash
export REDDIT_CLIENT_ID=...
export REDDIT_CLIENT_SECRET=...
export REDDIT_USER_AGENT="linux:reddit-reader:v0.1 (by /u/<username>)"
uv run reddit_reader.py
```

Credentials come only from environment variables and are never stored in this repository.
