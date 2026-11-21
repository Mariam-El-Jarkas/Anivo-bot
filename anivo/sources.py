import os
import requests
import feedparser

BASE=os.getenv("RSSHUB_BASE","https://rsshub.app").rstrip("/")
USERS=["animetherapy","ahmedm94m","ascom0","animerakuar"]

def parse_feed(url, label):
    r=requests.get(url,timeout=25,headers={"User-Agent":"ANIVO/0.2"})
    r.raise_for_status()
    feed=feedparser.parse(r.content)
    out=[]
    for e in feed.entries:
        link=e.get("link")
        title=(e.get("title") or "").strip()
        summary=e.get("summary") or e.get("description") or ""
        if not link or not (title or summary): continue
        image=""
        media=e.get("media_content") or e.get("media_thumbnail") or []
        if media: image=media[0].get("url","")
        if not image:
            for enc in e.get("enclosures",[]):
                if (enc.get("type") or "").startswith("image/"):
                    image=enc.get("href",""); break
        out.append({"id":e.get("id") or link,"title":title,"summary":summary,
                    "link":link,"image_url":image,"source":label})
    return out

def fetch_all():
    results=[]
    for user in USERS:
        try:
            got=parse_feed(f"{BASE}/twitter/user/{user}",f"X @{user}")
            results.extend(got); print(f"[OK] @{user}: {len(got)}")
        except Exception as exc: print(f"[WARN] @{user}: {exc}")
    for i,url in enumerate(filter(None,(x.strip() for x in os.getenv("EXTRA_FEEDS","").split(","))),1):
        try:
            got=parse_feed(url,f"Extra feed {i}")
            results.extend(got); print(f"[OK] extra feed {i}: {len(got)}")
        except Exception as exc: print(f"[WARN] extra feed {i}: {exc}")
    return results
