import os, requests
from anivo.youtube import find_official_trailer

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"

def rewrite(item):
    title = item.get("title", "")
    summary = item.get("summary", "")
    combined = f"{title}\n{summary}"
    official_link = None
    if any(marker in combined.lower() for marker in ("trailer", "عرض دعائي", "اعلان", "إعلان", "teaser")):
        try:
            official_link = find_official_trailer(title or summary)
        except Exception:
            official_link = None

    prompt = (
        "أنت محرر أخبار أنمي لقناة ANIVO. أعد صياغة الخبر باللغة العربية الفصحى بأسلوب صحفي طبيعي، لا ترجمة حرفية.\n"
        "أبقِ أسماء الأنمي والشخصيات والأعمال والعناوين الرسمية باللغة الإنجليزية. "
        "لا تخترع معلومات أو تواريخ أو مواسم أو جهات إنتاج. "
        "لا تعرض الإشاعات أو التسريبات كأخبار رسمية؛ وضّح طبيعتها. "
        "إذا لم تكفِ المعلومات لصياغة خبر موثوق، أعد فقط NEEDS_REVIEW. "
        "أعد نص الخبر فقط دون توقيع.\n\n"
        f"العنوان: {item.get('title', '')}\n"
        f"النص: {item.get('summary', '')}\n"
        f"الرابط: {item.get('link', '')}"
    )
    response = requests.post(
        URL,
        params={"key": os.environ["GEMINI_API_KEY"]},
        json={"contents": [{"parts": [{"text": prompt}]}],
              "generationConfig": {"temperature": 0.2, "maxOutputTokens": 450}},
        timeout=45,
    )
    response.raise_for_status()
    data = response.json()
    text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
    if not text or "NEEDS_REVIEW" in text:
        raise ValueError("Insufficient source information; skipped.")
    if official_link:
        return f"News link ANIVO\n\n{text}\n\n{official_link}"
    return text
