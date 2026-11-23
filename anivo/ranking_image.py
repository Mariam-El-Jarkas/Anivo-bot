from datetime import date, timedelta
from io import BytesIO

import arabic_reshaper
import requests
from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageFont, ImageOps


COLORS = {
    "pink": "#F7A8DC",
    "lilac": "#E3B5E8",
    "mid": "#C16FBE",
    "purple": "#A24FA8",
    "deep": "#6E3585",
    "ink": "#4A2358",
    "paper": "#FDF8F8",
    "white": "#FFFFFF",
}
ENGLISH_MONTHS = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December",
}
ENGLISH_SEASONS = {
    "winter": "Winter",
    "spring": "Spring",
    "summer": "Summer",
    "fall": "Fall",
    "autumn": "Fall",
}


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


def _rtl(text):
    return get_display(arabic_reshaper.reshape(str(text)), base_dir="R")


def _english_number(value):
    return str(value).translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))


def _date_en(value):
    parsed = date.fromisoformat(value) if isinstance(value, str) else value
    return f"{ENGLISH_MONTHS[parsed.month]} {parsed.day}, {parsed.year}"


def _date_range(start, end):
    if start.year == end.year and start.month == end.month:
        return (
            f"{ENGLISH_MONTHS[end.month]} {start.day}–{end.day}, {end.year}"
        )
    if start.year == end.year:
        return (
            f"{ENGLISH_MONTHS[start.month]} {start.day} – "
            f"{ENGLISH_MONTHS[end.month]} {end.day}, {end.year}"
        )
    return f"{_date_en(start)} – {_date_en(end)}"


def _week_data(week=None):
    week = week or {}
    chart_date = week.get("date")
    if chart_date:
        end = date.fromisoformat(chart_date)
        start = end - timedelta(days=6)
        season = week.get("season", "")
        year = end.year
        season_name = ENGLISH_SEASONS.get(str(season).lower(), str(season))
        if season_name and str(year) not in season_name:
            season_name = f"{season_name} {year}"
        return {
            "no": week.get("no") or end.isocalendar().week,
            "range": _date_range(start, end),
            "season": season_name,
        }

    today = date.today()
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=6)
    season = week.get("season")
    if not season:
        season = (
            "winter" if today.month in (12, 1, 2) else
            "spring" if today.month in (3, 4, 5) else
            "summer" if today.month in (6, 7, 8) else
            "fall"
        )
    season_name = ENGLISH_SEASONS.get(str(season).lower(), str(season))
    if str(today.year) not in season_name:
        season_name = f"{season_name} {today.year}"
    return {
        "no": week.get("no") or today.isocalendar().week,
        "range": _date_range(start, end),
        "season": season_name,
    }


def _gradient(size, start, end, horizontal=True):
    image = Image.new("RGB", size)
    draw = ImageDraw.Draw(image)
    start_rgb = tuple(int(start[index:index + 2], 16) for index in (1, 3, 5))
    end_rgb = tuple(int(end[index:index + 2], 16) for index in (1, 3, 5))
    length = size[0] if horizontal else size[1]
    for position in range(length):
        ratio = position / max(1, length - 1)
        color = tuple(
            round(start_rgb[channel] + (end_rgb[channel] - start_rgb[channel]) * ratio)
            for channel in range(3)
        )
        if horizontal:
            draw.line((position, 0, position, size[1]), fill=color)
        else:
            draw.line((0, position, size[0], position), fill=color)
    return image


def _rounded_gradient(size, start, end, radius):
    gradient = _gradient(size, start, end)
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius, fill=255)
    return gradient, mask


def _paste_cover(canvas, url, box):
    if not url:
        return
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        cover = Image.open(BytesIO(response.content)).convert("RGB")
        cover = ImageOps.fit(cover, box[2:], method=Image.Resampling.LANCZOS)
        canvas.paste(cover, box[:2])
    except (requests.RequestException, OSError, ValueError):
        return


def _header(image, draw, title, week):
    x, y, width, height = 40, 40, 1000, 200
    gradient, mask = _rounded_gradient(
        (width, height), COLORS["deep"], COLORS["pink"], 36
    )
    image.paste(gradient, (x, y), mask)
    draw.ellipse((x + width - 248, y + 4, x + width - 4, y + 198), fill="#86509B")
    badge = (x + width - 210, y + 34, x + width - 42, y + 166)
    draw.rounded_rectangle(badge, radius=26, fill=COLORS["paper"])
    center_x = (badge[0] + badge[2]) // 2
    draw.text((center_x, y + 48), "WEEK", font=_font(22, True), fill=COLORS["deep"], anchor="mt")
    draw.text((center_x, y + 75), _english_number(week["no"]), font=_font(58, True), fill=COLORS["deep"], anchor="mt")
    draw.text((center_x, y + 137), _rtl(week.get("season", "")), font=_font(17, True), fill=COLORS["purple"], anchor="mt")

    left = x + 42
    draw.text((left, y + 28), "ANIVO", font=_font(24, True), fill="white", anchor="la")
    title_font = _font(48, True)
    while title_font.size > 30 and draw.textbbox((0, 0), _rtl(title), font=title_font)[2] > 690:
        title_font = _font(title_font.size - 2, True)
    draw.text((left, y + 69), _rtl(title), font=title_font, fill="white", anchor="la")
    draw.text(
        (left, y + 137),
        f"Period: {week['range']}",
        font=_font(23),
        fill="#FFF6FB",
        anchor="la",
    )


def _background(width, height):
    image = Image.new("RGB", (width, height), COLORS["paper"])
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.ellipse((width - 360, -150, width + 140, 350), fill=(247, 168, 220, 48))
    draw.ellipse((-200, height - 460, 250, height + 80), fill=(193, 111, 190, 25))
    return Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")


def current_week_data():
    today = date.today()
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=6)
    season = (
        "winter" if today.month in (12, 1, 2) else
        "spring" if today.month in (3, 4, 5) else
        "summer" if today.month in (6, 7, 8) else
        "fall"
    )
    return {
        "no": today.isocalendar().week,
        "date": end.isoformat(),
        "season": season,
    }


def _fit_text(draw, text, font, max_width):
    text = str(text)
    if draw.textlength(_rtl(text), font=font) <= max_width:
        return text
    while text and draw.textlength(_rtl(text + "…"), font=font) > max_width:
        text = text[:-1]
    return text.rstrip() + "…"


def build_ranking_image(items, title="Top 10 Anime This Week", source_url=None, week=None):
    items = items[:10]
    width, margin, header_height = 1080, 40, 200
    row_height, row_gap = 118, 14
    footer_height = 22 if source_url else 0
    height = margin * 2 + header_height + row_gap + len(items) * row_height + max(0, len(items) - 1) * row_gap + footer_height
    image = _background(width, height)
    draw = ImageDraw.Draw(image)
    _header(image, draw, title, _week_data(week))

    y = margin + header_height + row_gap
    row_width = width - 2 * margin
    for index, item in enumerate(items):
        row_y = y + index * (row_height + row_gap)
        draw.rounded_rectangle(
            (margin, row_y, margin + row_width, row_y + row_height),
            radius=26,
            fill=COLORS["white"],
        )
        draw.rounded_rectangle(
            (margin, row_y, margin + 112, row_y + row_height),
            radius=26,
            fill=COLORS["deep"],
        )
        draw.rectangle(
            (margin + 98, row_y, margin + 124, row_y + row_height),
            fill=COLORS["deep"],
        )
        draw.text(
            (margin + 56, row_y + row_height // 2),
            _english_number(index + 1),
            font=_font(54, True),
            fill="white",
            anchor="mm",
        )
        thumb_box = (margin + 112, row_y, 210, row_height)
        draw.rectangle(
            (thumb_box[0], row_y, thumb_box[0] + thumb_box[2], row_y + row_height),
            fill=COLORS["lilac"],
        )
        _paste_cover(image, item.get("image_url"), thumb_box)

        text_left = thumb_box[0] + thumb_box[2] + 22
        name_font = _font(31, True)
        info_width = margin + row_width - text_left - 22
        name = _fit_text(draw, item.get("name", ""), name_font, info_width)
        while name_font.size > 20 and draw.textlength(_rtl(name), font=name_font) > info_width:
            name_font = _font(name_font.size - 1, True)
        draw.text((text_left, row_y + 25), _rtl(name), font=name_font, fill=COLORS["ink"], anchor="la")
        detail = item.get("sub_text")
        if detail:
            detail_font = _font(22, True)
            detail = _fit_text(draw, detail, detail_font, info_width)
            draw.text((text_left, row_y + 68), _rtl(detail), font=detail_font, fill=COLORS["purple"], anchor="la")

    if source_url:
        source_y = height - 32
        draw.text((margin, source_y), "Source: Anime Trending", font=_font(17), fill=COLORS["purple"], anchor="la")

    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()


def build_character_image(items, week=None, source_url=None):
    items = items[:10]
    width, margin, header_height = 1080, 40, 200
    gap, card_width, picture_height = 20, 490, 300
    card_height = picture_height + 100
    rows = (len(items) + 1) // 2
    height = margin * 2 + header_height + 20 + rows * card_height + max(0, rows - 1) * gap + 20
    image = _background(width, height)
    draw = ImageDraw.Draw(image)
    _header(image, draw, "Top Characters This Week", _week_data(week))

    start_y = margin + header_height + 20
    for index, item in enumerate(items):
        row, column = divmod(index, 2)
        x = margin + column * (card_width + gap)
        y = start_y + row * (card_height + gap)
        draw.rounded_rectangle(
            (x, y, x + card_width, y + card_height),
            radius=30,
            fill="white",
        )
        image_box = (x, y, card_width, picture_height)
        _paste_cover(image, item.get("image_url"), image_box)
        draw.rounded_rectangle((x + 14, y + 14, x + 78, y + 78), radius=32, fill=COLORS["deep"])
        draw.text(
            (x + 46, y + 46),
            _english_number(item.get("position", index + 1)),
            font=_font(35, True),
            fill="white",
            anchor="mm",
        )
        text_left = x + 20
        name_font = _font(29, True)
        name = _fit_text(draw, item.get("name", ""), name_font, card_width - 40)
        draw.text((text_left, y + picture_height + 14), _rtl(name), font=name_font, fill=COLORS["ink"], anchor="la")
        sub_font = _font(20, True)
        subtitle = _fit_text(draw, item.get("sub_text", ""), sub_font, card_width - 40)
        draw.text((text_left, y + picture_height + 58), _rtl(subtitle), font=sub_font, fill=COLORS["purple"], anchor="la")

    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()


def build_schedule_image(schedule, week=None, today=None, source_url=None):
    day_order = ("Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday")
    grouped = {day: [] for day in day_order}
    for item in schedule:
        day = item.get("day")
        if day in grouped and item.get("title"):
            grouped[day].append(item)

    active_days = [day for day in day_order if grouped[day]]
    width, margin, header_height = 1080, 40, 200
    content_width, row_gap = width - 2 * margin, 16
    day_header_height, item_height = 52, 42
    column_gap, inner_padding = 12, 12

    def day_height(day):
        columns = (len(grouped[day]) + 1) // 2
        return day_header_height + 2 * inner_padding + max(1, columns) * item_height

    height = margin * 2 + header_height + 20
    height += sum(day_height(day) for day in active_days)
    height += max(0, len(active_days) - 1) * row_gap + 20
    image = _background(width, height)
    draw = ImageDraw.Draw(image)
    _header(image, draw, "Weekly Anime Schedule", _week_data(week))

    y = margin + header_height + 20
    title_font = _font(22, True)
    column_width = (content_width - 2 * inner_padding - column_gap) // 2
    for day in active_days:
        row_height = day_height(day)
        draw.rounded_rectangle(
            (margin, y, margin + content_width, y + row_height),
            radius=24,
            fill=COLORS["white"],
        )
        day_color = COLORS["purple"] if day == today else COLORS["deep"]
        gradient, mask = _rounded_gradient(
            (content_width, day_header_height), day_color, COLORS["mid"], 22
        )
        image.paste(gradient, (margin, y), mask)
        draw.rectangle(
            (margin, y + day_header_height - 22, margin + content_width, y + day_header_height),
            fill=COLORS["mid"],
        )
        draw.text(
            (margin + 18, y + day_header_height // 2),
            day,
            font=_font(26, True),
            fill="white",
            anchor="lm",
        )
        items = grouped[day]
        count_text = f"{_english_number(len(items))} anime"
        draw.text(
            (margin + content_width - 18, y + day_header_height // 2),
            count_text,
            font=_font(20, True),
            fill="white",
            anchor="rm",
        )

        right_x = margin + inner_padding + column_width + column_gap
        left_x = margin + inner_padding
        for item_index, item in enumerate(items):
            left_column = item_index < (len(items) + 1) // 2
            column_x = left_x if left_column else right_x
            column_index = item_index if left_column else item_index - (len(items) + 1) // 2
            item_y = y + day_header_height + inner_padding + column_index * item_height
            box = (column_x, item_y, column_x + column_width, item_y + item_height - 4)
            draw.rounded_rectangle(box, radius=12, fill="#FBEAF6")

            title_left = box[0] + 12
            time = item.get("time")
            time_width = 0
            if time:
                time_text = _english_number(time)
                time_font = _font(17, True)
                time_width = min(column_width // 2, int(draw.textlength(time_text, font=time_font)) + 20)
                time_box = (box[2] - 8 - time_width, item_y + 6, box[2] - 8, item_y + item_height - 10)
                draw.rounded_rectangle(time_box, radius=10, fill=COLORS["mid"])
                draw.text(
                    ((time_box[0] + time_box[2]) // 2, (time_box[1] + time_box[3]) // 2),
                    time_text,
                    font=time_font,
                    fill="white",
                    anchor="mm",
                )
            title_width = column_width - 24 - time_width - (8 if time else 0)
            title = _fit_text(draw, item["title"], title_font, title_width)
            draw.text(
                (title_left, item_y + (item_height - 4) // 2),
                _rtl(title),
                font=title_font,
                fill=COLORS["ink"],
                anchor="lm",
            )
        y += row_height + row_gap

    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()
