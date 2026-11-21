import json
from pathlib import Path
PATH=Path("data/seen_posts.json")
def load():
    if not PATH.exists(): return {"initialized":False,"seen":[]}
    try:
        d=json.loads(PATH.read_text(encoding="utf-8"))
        return {"initialized":bool(d.get("initialized")),"seen":d.get("seen",[])}
    except Exception: return {"initialized":False,"seen":[]}
def save(state):
    PATH.parent.mkdir(exist_ok=True)
    PATH.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding="utf-8")
