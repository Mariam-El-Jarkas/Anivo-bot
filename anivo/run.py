
import time

from anivo.sources import fetch_all
from anivo.state import load, save
from anivo.rewriter import rewrite
from anivo.discord_client import send_news

MAX_AGE_SECONDS = 24 * 60 * 60
FUTURE_TOLERANCE_SECONDS = 300


def main():
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
