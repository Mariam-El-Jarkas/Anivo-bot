import os, requests
API="https://discord.com/api/v10"
SIGNATURE="🌸 أنيفو || ANIVO 🌸"

def send_news(item, arabic):
    headers={"Authorization":f"Bot {os.environ['DISCORD_BOT_TOKEN']}",
             "Content-Type":"application/json","User-Agent":"ANIVO/0.2"}
    dm=requests.post(f"{API}/users/@me/channels",headers=headers,
                     json={"recipient_id":os.environ["DISCORD_USER_ID"]},timeout=20)
    dm.raise_for_status()
    content=f"{arabic}\n\nالمصدر: {item['link']}\n\n{SIGNATURE}"
    payload={"content":content[:2000]}
    if item.get("image_url"): payload["embeds"]=[{"image":{"url":item["image_url"]}}]
    sent=requests.post(f"{API}/channels/{dm.json()['id']}/messages",
                       headers=headers,json=payload,timeout=25)
    sent.raise_for_status()
