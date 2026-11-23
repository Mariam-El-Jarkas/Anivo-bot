import os
import requests

API = "https://discord.com/api/v10"
SIGNATURE = "🌸 أنيفو || ANIVO 🌸"


def recipient_ids():
    raw = os.getenv("DISCORD_USER_IDS") or os.getenv("DISCORD_USER_ID", "")
    return [value.strip() for value in raw.replace(",", " ").split() if value.strip()]


def _headers():
    return {
        "Authorization": f"Bot {os.environ['DISCORD_BOT_TOKEN']}",
        "Content-Type": "application/json",
        "User-Agent": "ANIVO/0.4",
    }


def send_dm(recipient_id, content, image_url=None):
    headers = _headers()
    dm = requests.post(
        f"{API}/users/@me/channels",
        headers=headers,
        json={"recipient_id": recipient_id},
        timeout=20,
    )
    dm.raise_for_status()
    payload = {"content": content[:2000]}
    if image_url:
        payload["embeds"] = [{"image": {"url": image_url}}]
    sent = requests.post(
        f"{API}/channels/{dm.json()['id']}/messages",
        headers=headers,
        json=payload,
        timeout=25,
    )
    sent.raise_for_status()


def send_message(content, image_url=None, recipient_ids_override=None):
    ids = recipient_ids_override or recipient_ids()
    for recipient_id in ids:
        send_dm(recipient_id, content, image_url)


def bold(text):
    return "\n".join(f"**{line}**" if line else "" for line in text.strip().splitlines())


def send_news(item, arabic):
    content = bold(f"{arabic}\n\nالمصدر: {item['link']}\n\n{SIGNATURE}")
    send_message(content, item.get("image_url"))
