import os
import requests
import feedparser

# FxTwitter RSS feeds were manually confirmed to load for all four ANIVO sources.
FEED_BASE = os.getenv("FXTWITTER_BASE", "https://fxtwitter.com").rstrip("/")
USERS = ["animetherapy", "ahmedm94m", "ascom0", "animerakuar"]


def parse_feed(url, label):
    response = requests.get(
        url,
        timeout=25,
        headers={"User-Agent": "Mozilla/5.0 (compatible; ANIVO/0.3; +https://github.com/Mariam-El-Jarkas/anivo-bot)"},
    )
    response.raise_for_status()

    feed = feedparser.parse(response.content)
    if feed.bozo and not feed.entries:
        raise ValueError(f"Invalid or unreadable RSS feed: {getattr(feed, 'bozo_exception', 'unknown feed error')}")

    items = []
    for entry in feed.entries:
        link = entry.get("link")
        title = (entry.get("title") or "").strip()
        summary = entry.get("summary") or entry.get("description") or ""
        if not link or not (title or summary):
            continue

        image_url = ""

        # FxTwitter RSS commonly exposes post images as RSS enclosures.
        for enclosure in entry.get("enclosures", []):
            if (enclosure.get("type") or "").startswith("image/"):
                image_url = enclosure.get("href") or enclosure.get("url") or ""
                if image_url:
                    break

        # Also support Media RSS fields used by some feed responses.
        if not image_url:
            media = entry.get("media_content") or entry.get("media_thumbnail") or []
            if media:
                image_url = media[0].get("url", "")

        items.append(
            {
                "id": entry.get("id") or link,
                "title": title,
                "summary": summary,
                "link": link,
                "image_url": image_url,
                "source": label,
            }
        )

    return items


def fetch_all():
    results = []

    for user in USERS:
        feed_url = f"{FEED_BASE}/{user}/feed.xml"
        try:
            fetched = parse_feed(feed_url, f"X @{user}")
            results.extend(fetched)
            print(f"[OK] @{user}: {len(fetched)} posts")
        except Exception as exc:
            print(f"[WARN] @{user}: {exc}")

    # Keep support for optional extra RSS feeds.
    extra_feeds = filter(
        None,
        (value.strip() for value in os.getenv("EXTRA_FEEDS", "").split(",")),
    )
    for index, url in enumerate(extra_feeds, 1):
        try:
            fetched = parse_feed(url, f"Extra feed {index}")
            results.extend(fetched)
            print(f"[OK] extra feed {index}: {len(fetched)} posts")
        except Exception as exc:
            print(f"[WARN] extra feed {index}: {exc}")

    return results
