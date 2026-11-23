import os
import requests

API = "https://discord.com/api/v10"
SIGNATURE = "🌸 أنيفو || ANIVO 🌸"


def recipient_ids():
    raw = os.getenv("DISCORD_USER_IDS") or os.getenv("DISCORD_USER_ID", "")
    values = [value.strip() for value in raw.replace(",", " ").split() if value.strip()]
    return [value for value in values if value.isdigit()]


def _headers():
    return {
        "Authorization": f"Bot {os.environ['DISCORD_BOT_TOKEN']}",
        "Content-Type": "application/json",
        "User-Agent": "ANIVO/0.4",
    }


def send_dm(recipient_id, content, image_url=None, image_bytes=None, filename="anivo.png"):
    headers = _headers()
    dm = requests.post(
        f"{API}/users/@me/channels",
        headers=headers,
        json={"recipient_id": recipient_id},
        timeout=20,
    )
    if not dm.ok:
        detail = dm.text[:500]
        raise RuntimeError(
            f"Discord rejected DM-channel creation for recipient {recipient_id}: "
            f"{dm.status_code} {detail}"
        )
    payload = {"content": content[:2000]}
    if image_bytes:
        payload["embeds"] = [{"image": {"url": f"attachment://{filename}"}}]
        multipart_headers = dict(headers)
        multipart_headers.pop("Content-Type", None)
        sent = requests.post(
            f"{API}/channels/{dm.json()['id']}/messages",
            headers=multipart_headers,
            data={"payload_json": __import__("json").dumps(payload)},
            files={"files[0]": (filename, image_bytes, "image/png")},
            timeout=25,
        )
    else:
        if image_url:
            payload["embeds"] = [{"image": {"url": image_url}}]
        sent = requests.post(
            f"{API}/channels/{dm.json()['id']}/messages",
            headers=headers,
            json=payload,
            timeout=25,
        )
    sent.raise_for_status()


def send_message(content, image_url=None, recipient_ids_override=None, image_bytes=None, filename="anivo.png"):
    ids = recipient_ids_override or recipient_ids()
    if not ids:
        raise RuntimeError(
            "No valid Discord recipient IDs configured. "
            "Set DISCORD_USER_IDS to numeric Discord user IDs."
        )
    for recipient_id in ids:
        send_dm(recipient_id, content, image_url, image_bytes, filename)


def bold(text):
    return "\n".join(f"**{line}**" if line else "" for line in text.strip().splitlines())


def send_news(item, arabic):
    content = bold(f"{arabic}\n\nالمصدر: {item['link']}\n\n{SIGNATURE}")
    send_message(content, item.get("image_url"))
