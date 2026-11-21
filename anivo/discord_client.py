import os
import requests

DISCORD_API = "https://discord.com/api/v10"


def send_dm(message: str) -> None:
    token = os.environ["DISCORD_BOT_TOKEN"]
    user_id = os.environ["DISCORD_USER_ID"]
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json",
        "User-Agent": "ANIVO (https://github.com/, 0.1.0)",
    }

    # Create (or retrieve) a DM channel with the configured user.
    response = requests.post(
        f"{DISCORD_API}/users/@me/channels",
        headers=headers,
        json={"recipient_id": user_id},
        timeout=20,
    )
    response.raise_for_status()
    channel_id = response.json()["id"]

    sent = requests.post(
        f"{DISCORD_API}/channels/{channel_id}/messages",
        headers=headers,
        json={"content": message},
        timeout=20,
    )
    sent.raise_for_status()
