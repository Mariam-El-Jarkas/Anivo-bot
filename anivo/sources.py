
import os
import requests
import feedparser
import calendar
import re
import json
import html
import time
from datetime import datetime, timezone, timedelta
from xml.etree import ElementTree

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


def fetch_anime_schedule(day=None):
    try:
        witanime_schedule = fetch_witanime_schedule(day)
        if witanime_schedule:
            return witanime_schedule
    except requests.RequestException as exc:
        print(f"[WARN] WitAnime schedule unavailable: {exc}")

    for attempt in range(2):
        try:
            response = requests.get(
                "https://api.jikan.moe/v4/schedules",
                params={"filter": "tv"},
                headers={"User-Agent": "ANIVO/0.4"},
                timeout=25,
            )
            response.raise_for_status()
            data = response.json().get("data", [])
            break
        except (requests.ConnectionError, requests.Timeout) as exc:
            if attempt == 1:
                print(f"[WARN] Jikan schedule unavailable after retry: {exc}")
                return []
            print(f"[WARN] Jikan schedule request failed; retrying once: {exc}")
            time.sleep(2)
        except requests.RequestException as exc:
            print(f"[WARN] Jikan schedule unavailable: {exc}")
            return []
    if day:
        day = day.lower()
        data = [item for item in data if (item.get("broadcast", {}).get("day") or "").lower() == day]

    schedule = []
    for item in data[:50]:
        title = item.get("title")
        broadcast = item.get("broadcast", {}) or {}
        schedule.append({
            "title": title,
            "day": broadcast.get("day"),
            "time": broadcast.get("time"),
            "timezone": broadcast.get("timezone"),
            "url": item.get("url"),
        })
    return schedule


def fetch_witanime_schedule(day=None):
    base = os.getenv("WITANIME_BASE", "https://witanime.site").rstrip("/")
    response = requests.get(
        f"{base}/schedule",
        headers={"User-Agent": "Mozilla/5.0 (compatible; ANIVO/0.4)"},
        timeout=25,
    )
    response.raise_for_status()

    arabic_days = {
        "الاثنين": "Monday",
        "الثلاثاء": "Tuesday",
        "الأربعاء": "Wednesday",
        "الخميس": "Thursday",
        "الجمعة": "Friday",
        "السبت": "Saturday",
        "الأحد": "Sunday",
    }
    wanted = day.title() if day else None
    schedule = []
    markers = list(re.finditer(
        r"الاثنين|الثلاثاء|الأربعاء|الخميس|الجمعة|السبت|الأحد",
        response.text,
    ))

    for index, marker in enumerate(markers):
        english_day = arabic_days[marker.group(0)]
        if wanted and english_day.lower() != wanted.lower():
            continue
        end = markers[index + 1].start() if index + 1 < len(markers) else len(response.text)
        chunk = response.text[marker.end():end]
        anime_links = re.findall(
            r'href=["\'][^"\']*?/anime/([a-z0-9-]+)["\']',
            chunk,
            re.I,
        )
        for slug in dict.fromkeys(anime_links):
            title = slug.replace("-", " ").title()
            if any(
                item["title"] == title and item["day"] == english_day
                for item in schedule
            ):
                continue
            schedule.append({
                "title": title,
                "day": english_day,
                "time": None,
                "timezone": None,
                "url": f"{base}/anime/{slug}",
            })
    return schedule[:100]


def fetch_anime_trending_feed():
    url = os.getenv(
        "ANIME_TRENDING_FEED",
        "https://anitrendz.net/news/feed",
    )
    return parse_feed(url, "Anime Trending")


def find_witanime_episode(anime_name, episode_number):
    search_url = "https://witanime.net/"
    response = requests.get(
        search_url,
        params={"search_param": "animes", "s": anime_name},
        headers={"User-Agent": "Mozilla/5.0 (compatible; ANIVO/0.4)"},
        timeout=25,
    )
    response.raise_for_status()

    links = re.findall(r'href=["\']([^"\']+)["\'][^>]*>([^<]*' + re.escape(anime_name) + r'[^<]*)<', response.text, re.I)
    for link, _label in links:
        if "witanime" in link or link.startswith("/"):
            base = requests.compat.urljoin(search_url, link)
            episode_params = {"ep": episode_number} if episode_number else None
            episode = requests.get(
                base,
                params=episode_params,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=25,
            )
            episode.raise_for_status()
            direct_links = re.findall(
                r'href=["\']([^"\']+)["\']',
                episode.text,
                re.I,
            )
            for direct in direct_links:
                if "episode-" in direct.lower() or f"-{episode_number}" in direct.lower():
                    return requests.compat.urljoin(base, direct)

    return f"https://witanime.net/?search_param=animes&s={requests.utils.quote(anime_name)}"


def fetch_anitrendz_chart(chart="top-anime", limit=10):
    base = os.getenv("ANITRENDZ_BASE", "https://www.anitrendz.com").rstrip("/")
    response = requests.get(
        f"{base}/charts/{chart}",
        headers={"User-Agent": "Mozilla/5.0 (compatible; ANIVO/0.4)"},
        timeout=25,
    )
    response.raise_for_status()

    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        response.text,
        re.S,
    )
    if not match:
        return []

    data = json.loads(html.unescape(match.group(1)))
    charts = data.get("props", {}).get("pageProps", {}).get("charts", [])
    if not charts:
        return []

    choices = charts[0].get("choices", [])
    ranked = sorted(
        choices,
        key=lambda choice: int(choice.get("position", 10**9)),
    )
    return [
        {
            "name": choice.get("name") or choice.get("nameAlt") or "",
            "position": choice.get("position"),
            "sub_text": choice.get("subText"),
            "image_url": (choice.get("images") or {}).get("full")
            or (choice.get("images") or {}).get("large")
            or (choice.get("images") or {}).get("small"),
            "votes": choice.get("total"),
            "previous_position": choice.get("previously"),
            "weeks": choice.get("weeksAtTopTen"),
            "week_no": charts[0].get("week"),
            "season": charts[0].get("season"),
            "chart_date": charts[0].get("date"),
            "chart_votes": charts[0].get("votes"),
        }
        for choice in ranked[:limit]
        if choice.get("name") or choice.get("nameAlt")
    ]


def fetch_recent_witanime_episodes(hours=24):
    base = os.getenv("WITANIME_BASE", "https://witanime.site").rstrip("/")
    try:
        response = requests.get(
            f"{base}/sitemap.xml",
            headers={"User-Agent": "Mozilla/5.0 (compatible; ANIVO/0.4)"},
            timeout=25,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"[WARN] WitAnime episode sitemap unavailable: {exc}")
        return []
    root = ElementTree.fromstring(response.content)
    namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    episode_sitemaps = [
        loc.text
        for loc in root.findall(".//s:loc", namespace)
        if "/sitemap-episodes-" in (loc.text or "")
    ]

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    recent = []
    for sitemap_url in episode_sitemaps:
        sitemap = requests.get(sitemap_url, timeout=25)
        sitemap.raise_for_status()
        sitemap_root = ElementTree.fromstring(sitemap.content)
        for url in sitemap_root.findall(".//s:url", namespace):
            loc = url.find("s:loc", namespace)
            lastmod = url.find("s:lastmod", namespace)
            if loc is None or lastmod is None:
                continue
            try:
                updated = datetime.fromisoformat(lastmod.text.replace("Z", "+00:00"))
            except (AttributeError, ValueError):
                continue
            if updated < cutoff:
                continue

            path = loc.text.rstrip("/").split("/watch/", 1)[-1]
            parts = path.rsplit("/", 1)
            if len(parts) != 2:
                continue
            slug, episode = parts
            recent.append({
                "anime": slug.replace("-", " ").title(),
                "episode": episode,
                "url": loc.text,
                "updated_at": updated.isoformat(),
            })
    return sorted(recent, key=lambda item: item["updated_at"], reverse=True)
