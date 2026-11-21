from anivo.sources import fetch_all
from anivo.state import load,save
from anivo.rewriter import rewrite
from anivo.discord_client import send_news

def main():
    state=load(); items=fetch_all()
    if not items:
        print("No feed items available."); return
    seen=set(state["seen"])
    if not state["initialized"]:
        seen.update(x["id"] for x in items)
        save({"initialized":True,"seen":list(seen)[-2000:]})
        print("Initialized from existing posts; no old posts sent.")
        return
    fresh=[x for x in items if x["id"] not in seen]
    for item in reversed(fresh[-5:]):
        try:
            text=rewrite(item); send_news(item,text)
            seen.add(item["id"]); print(f"[SENT] {item['link']}")
        except Exception as exc: print(f"[SKIPPED] {item.get('link')}: {exc}")
    save({"initialized":True,"seen":list(seen)[-2000:]})

if __name__=="__main__": main()
