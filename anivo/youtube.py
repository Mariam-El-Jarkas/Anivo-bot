import html
import json
import re

import requests


def find_official_trailer(search_text):
    response = requests.get(
        "https://www.youtube.com/results",
        params={"search_query": f"{search_text} official trailer"},
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=20,
    )
    response.raise_for_status()
    match = re.search(r"var ytInitialData = (\{.*?\});", response.text)
    if not match:
        return None

    data = json.loads(html.unescape(match.group(1)))
    sections = data.get("contents", {}).get("twoColumnSearchResultsRenderer", {}).get(
        "content", {}
    ).get("sectionListRenderer", {}).get("contents", [])

    for section in sections:
        for item in section.get("itemSectionRenderer", {}).get("contents", []):
            video = item.get("videoRenderer")
            if not video:
                continue
            video_id = video.get("videoId")
            owner = video.get("ownerText", {}).get("runs", [{}])[0].get("text", "")
            title = "".join(
                run.get("text", "")
                for run in video.get("title", {}).get("runs", [])
            )
            if video_id and (
                "official" in owner.lower()
                or "official" in title.lower()
                or "trailer" in title.lower()
            ):
                return f"https://youtu.be/{video_id}"
    return None
