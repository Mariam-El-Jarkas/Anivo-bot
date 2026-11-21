SIGNATURE = "🌸 أنيفو || ANIVO 🌸"


def format_news(arabic_text: str, trailer_url: str | None = None) -> str:
    """Format already-reviewed Arabic text; this function does not translate."""
    parts = []
    if trailer_url:
        parts.append(f"مشاهدة العرض: {trailer_url}")
    parts.append(arabic_text.strip())
    parts.append(SIGNATURE)
    return "\n\n".join(parts)
