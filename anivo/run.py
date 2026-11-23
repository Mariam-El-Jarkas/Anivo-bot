
import time
import sys

from anivo.sources import fetch_all
from anivo.state import load, save
from anivo.rewriter import rewrite
from anivo.discord_client import send_news
from anivo.discord_client import send_message, bold, SIGNATURE
from anivo.ranking_image import (
    build_character_image,
    build_ranking_image,
    build_schedule_images,
    current_week_data,
)
from anivo.sources import (
    fetch_anitrendz_chart,
    fetch_anime_schedule,
    fetch_recent_witanime_episodes,
)
from anivo.state import get_cache, set_cache

MAX_AGE_SECONDS = 24 * 60 * 60
FUTURE_TOLERANCE_SECONDS = 300


def main():
    if "--weekly" in sys.argv:
        anime_items = fetch_anitrendz_chart("top-anime", 10)
        if anime_items:
            week = {
                "no": anime_items[0].get("week_no"),
                "season": anime_items[0].get("season"),
                "date": anime_items[0].get("chart_date"),
            }
            content = f"**أفضل 10 أنميات أسبوعية من Anime Trending**\n\n{SIGNATURE}"
            image_bytes = build_ranking_image(
                anime_items,
                title="Top 10 Anime This Week",
                source_url="https://www.anitrendz.com/charts/top-anime",
                week=week,
            )
            send_message(content, image_bytes=image_bytes, filename="anivo-top-anime-week.png")

        male = fetch_anitrendz_chart("male-characters", 5)
        female = fetch_anitrendz_chart("female-characters", 5)
        character_items = [
            {
                **item,
                "character_group": group,
                "sub_text": f"{label} · {item.get('sub_text', '')}",
            }
            for entries, group, label in (
                (male, "male", "Male"),
                (female, "female", "Female"),
            )
            for item in entries
        ]
        if character_items:
            content = f"**أفضل 10 شخصيات أسبوعية من Anime Trending**\n\n{SIGNATURE}"
            character_week = {
                "no": character_items[0].get("week_no"),
                "season": character_items[0].get("season"),
                "date": character_items[0].get("chart_date"),
            }
            image_bytes = build_character_image(
                character_items,
                week=character_week,
                source_url="https://www.anitrendz.com/charts/male-characters",
            )
            send_message(content, image_bytes=image_bytes, filename="anivo-top-characters-week.png")
        print("[DONE] Sent weekly Anime Trending report.")
        return

    if "--episodes" in sys.argv:
        items = fetch_recent_witanime_episodes(24)
        if not items:
            print("[SKIPPED] No recent WitAnime episodes could be fetched.")
            return
        sent_count = 0
        for item in items:
            cache_key = f"witanime:{item['url']}"
            if get_cache(cache_key):
                continue
            content = bold(
                f"Anime {item['anime']} ep {item['episode']} is out.\n"
                f"{item['url']}\n\n{SIGNATURE}"
            )
            send_message(content)
            set_cache(cache_key, {"sent": True})
            sent_count += 1
        print(f"[DONE] Sent {sent_count} recent WitAnime episodes.")
        return

    if "--schedule" in sys.argv:
        day = None
        if len(sys.argv) >= 3:
            day = sys.argv[sys.argv.index("--schedule") + 1]
        schedule = fetch_anime_schedule(day)
        if not schedule:
            raise RuntimeError(
                "No anime schedule data was available from WitAnime, Jikan, or AniList; "
                "see the source warnings above."
            )
        heading = f"**جدول صدور الأنمي - {day}**" if day else "**جدول صدور الأنمي أسبوعياً**"
        image_pages = build_schedule_images(
            schedule,
            week=current_week_data(),
            today=time.strftime("%A"),
        )
        if not image_pages:
            raise RuntimeError("The anime schedule could not be rendered into image pages.")
        for page_number, image_bytes in enumerate(image_pages, start=1):
            page_heading = f"{heading} ({page_number}/{len(image_pages)})" if len(image_pages) > 1 else heading
            send_message(
                f"{page_heading}\n\n{SIGNATURE}",
                image_bytes=image_bytes,
                filename=f"anivo-anime-weekly-schedule-{page_number:02}.png",
            )
        print(f"[DONE] Sent anime release schedule ({len(image_pages)} page(s)).")
        return

    state = load()
    items = fetch_all()

    if not items:
        print("No feed items available.")
        return

    now = time.time()
    cutoff = now - MAX_AGE_SECONDS

    seen = set(state["seen"])

    recent = []
    old_count = 0
    undated_count = 0

    for item in items:
        published_at = item.get("published_at")

        if published_at is None:
            undated_count += 1
            continue

        if published_at < cutoff or published_at > now + FUTURE_TOLERANCE_SECONDS:
            old_count += 1
            continue

        recent.append(item)

    print(f"[FILTER] Recent (last 24h): {len(recent)}")
    print(f"[FILTER] Old/out-of-range: {old_count}")
    print(f"[FILTER] Missing publication date: {undated_count}")

    fresh = [
        item for item in recent
        if item["id"] not in seen
    ]

    sent_count = 0

    for item in reversed(fresh[-5:]):
        try:
            news_text = rewrite(item)
            send_news(item, news_text)

            seen.add(item["id"])
            sent_count += 1
            print(f"[SENT] {item['link']}")

        except Exception as exc:
            print(f"[SKIPPED] {item.get('link')}: {exc}")

    save({
        "initialized": True,
        "seen": list(seen)[-2000:]
    })

    print(f"[DONE] Sent {sent_count} recent news posts.")


if __name__ == "__main__":
    main()
