
import os
import requests
import feedparser
import calendar

FEED_BASE = os.getenv("FXTWITTER_BASE", "https://fxtwitter.com").rstrip("/")
USERS = ["animetherapy", "ahmedm94m", "ascom0", "animerakuar"]


def parse_feed(url, label):
    response = requests.get(
        url,
        timeout=25,
        headers={"User-Agent": "Mozilla/5.0 (compatible; ANIVO/0.3)"},
    )
    response.raise_for_status()
    feed = feedparser.parse(response.content)

    if feed.bozo and not feed.entries:
        raise ValueError("Invalid or unreadable RSS feed")

    items = []

    for entry in feed.entries:
        link = entry.get("link")
        title = (entry.get("title") or "").strip()
        summary = entry.get("summary") or entry.get("description") or ""

        if not link or not (title or summary):
            continue

        published = (
            entry.get("published_parsed")
            or entry.get("updated_parsed")
        )

        published_at = (
            calendar.timegm(published)
            if published else None
        )

        image_url = ""

        for enclosure in entry.get("enclosures", []):
            if (enclosure.get("type") or "").startswith("image/"):
                image_url = enclosure.get("href") or enclosure.get("url") or ""
                if image_url:
                    break

        if not image_url:
            media = entry.get("media_content") or entry.get("media_thumbnail") or []
            if media:
                image_url = media[0].get("url", "")

        items.append({
            "id": entry.get("id") or link,
            "title": title,
            "summary": summary,
            "link": link,
            "image_url": image_url,
            "source": label,
            "published_at": published_at,
        })

    return items


def fetch_all():
    results = []

    for user in USERS:
        try:
            url = f"{FEED_BASE}/{user}/feed.xml"
            fetched = parse_feed(url, f"X @{user}")
            results.extend(fetched)
            print(f"[OK] @{user}: {len(fetched)} posts")
        except Exception as exc:
            print(f"[WARN] @{user}: {exc}")

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
