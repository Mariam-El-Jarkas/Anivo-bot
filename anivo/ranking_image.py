from io import BytesIO
import textwrap

import requests
import arabic_reshaper
from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageFont


def _font(size, bold=False):
    paths = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    )
    for path in paths:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def build_ranking_image(items, title="TOP 10 ANIME OF THE WEEK", source_url=None):
    width, row_height = 1080, 112
    header_height = 150
    footer_height = 48
    height = header_height + row_height * len(items) + footer_height
    image = Image.new("RGB", (width, height), "#101820")
    draw = ImageDraw.Draw(image)

    draw.rectangle((0, 0, width, header_height), fill="#ff9f1c")
    draw.rectangle((0, 0, 14, header_height), fill="#f15a24")
    draw.text((42, 30), "ANIVO", fill="white", font=_font(22, True))

    title_box = (42, 62, width - 36, header_height - 18)
    title_font = _font(48, True)
    while title_font.size > 24:
        bounds = draw.textbbox((0, 0), title, font=title_font)
        if bounds[2] - bounds[0] <= title_box[2] - title_box[0]:
            break
        title_font = _font(title_font.size - 2, True)
    draw.text((title_box[0], title_box[1]), title, fill="white", font=title_font)

    for index, item in enumerate(items):
        y = header_height + index * row_height
        draw.rectangle((0, y, width, y + row_height - 4), fill="#1b2838")
        draw.rectangle((0, y, 92, y + row_height - 4), fill="#f15a24")
        rank = str(item["position"] if item.get("position") else index + 1)
        draw.text((46, y + row_height // 2), rank, fill="white", font=_font(46, True), anchor="mm")

        x = 108
        image_url = item.get("image_url")
        if image_url:
            try:
                response = requests.get(image_url, timeout=15)
                response.raise_for_status()
                cover = Image.open(BytesIO(response.content)).convert("RGB")
                cover.thumbnail((132, row_height - 16))
                canvas = Image.new("RGB", (132, row_height - 16), "#26384d")
                canvas.paste(
                    cover,
                    ((canvas.width - cover.width) // 2, (canvas.height - cover.height) // 2),
                )
                image.paste(canvas, (x, y + 8))
            except Exception:
                pass
        text_x = 260
        name_font = _font(25, True)
        name = item["name"]
        while name_font.size > 17 and draw.textbbox((0, 0), name, font=name_font)[2] > width - text_x - 28:
            name_font = _font(name_font.size - 1, True)
        draw.text((text_x, y + 22), name, fill="white", font=name_font)
        sub_text = item.get("sub_text")
        if sub_text:
            draw.text((text_x, y + 62), sub_text[:65], fill="#cfd7df", font=_font(17))

    footer_y = height - footer_height
    draw.rectangle((0, footer_y, width, height), fill="#101820")
    attribution = "Source: Anime Trending"
    if source_url:
        attribution += "  |  Official chart"
    draw.text((width - 28, footer_y + 14), attribution, fill="#cfd7df", font=_font(15), anchor="ra")

    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()


ARABIC_DAYS = {
    "Monday": "الاثنين",
    "Tuesday": "الثلاثاء",
    "Wednesday": "الأربعاء",
    "Thursday": "الخميس",
    "Friday": "الجمعة",
    "Saturday": "السبت",
    "Sunday": "الأحد",
}


def _rtl(text):
    return get_display(arabic_reshaper.reshape(text))


def build_schedule_image(schedule):
    day_order = list(ARABIC_DAYS)
    grouped = {day: [] for day in day_order}
    for item in schedule:
        day = item.get("day")
        if day in grouped:
            grouped[day].append(item["title"])

    width = 1080
    margin = 28
    gap = 20
    card_width = (width - 2 * margin - gap) // 2
    font = _font(19)
    heading_font = _font(27, True)
    line_height = 30
    cards = []
    for day in day_order:
        titles = grouped[day]
        wrapped = []
        for title in titles:
            wrapped.extend(textwrap.wrap(title, width=32) or [""])
        card_height = 70 + max(1, len(wrapped)) * line_height
        cards.append((day, wrapped, card_height))

    rows = []
    for index in range(0, len(cards), 2):
        row_cards = cards[index:index + 2]
        rows.append((row_cards, max(card[2] for card in row_cards)))
    header_height = 118
    height = header_height + sum(row_height + gap for _, row_height in rows) + margin
    image = Image.new("RGB", (width, height), "#101820")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, width, header_height), fill="#ff9f1c")
    draw.rectangle((0, 0, 14, header_height), fill="#f15a24")
    draw.text((margin, 20), "ANIVO", fill="white", font=_font(20, True))
    draw.text((width - margin, 52), _rtl("جدول صدور الأنمي أسبوعياً"), fill="white", font=_font(37, True), anchor="ra")

    y = header_height
    for row_cards, row_height in rows:
        for column, (day, titles, _) in enumerate(row_cards):
            x = margin + column * (card_width + gap)
            draw.rounded_rectangle(
                (x, y, x + card_width, y + row_height - 8),
                radius=12,
                fill="#1b2838",
            )
            draw.rounded_rectangle(
                (x, y, x + card_width, y + 52),
                radius=12,
                fill="#f15a24",
            )
            draw.text(
                (x + card_width - 18, y + 10),
                _rtl(ARABIC_DAYS[day]),
                fill="white",
                font=heading_font,
                anchor="ra",
            )
            text_y = y + 66
            for line in titles:
                draw.text((x + 16, text_y), line, fill="white", font=font)
                text_y += line_height
        y += row_height + gap

    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()
