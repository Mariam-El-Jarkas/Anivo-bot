from io import BytesIO

import requests
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
    width, row_height = 1080, 118
    height = 190 + row_height * len(items) + 90
    image = Image.new("RGB", (width, height), "#101820")
    draw = ImageDraw.Draw(image)

    draw.rectangle((0, 0, width, 190), fill="#ff9f1c")
    draw.rectangle((0, 0, 155, 190), fill="#f15a24")
    logo = _font(27, True)
    draw.text((20, 64), "ANIME\nTRENDING", fill="white", font=logo, align="center")
    draw.text((178, 58), title, fill="white", font=_font(48, True))
    draw.text((178, 125), "ANIVO WEEKLY CHART", fill="#fff4d6", font=_font(24, True))

    for index, item in enumerate(items):
        y = 190 + index * row_height
        draw.rectangle((0, y, width, y + row_height - 4), fill="#1b2838")
        draw.rectangle((0, y, 100, y + row_height - 4), fill="#f15a24")
        rank = str(item["position"] if item.get("position") else index + 1)
        draw.text((50, y + 31), rank, fill="white", font=_font(52, True), anchor="mm")

        x = 116
        image_url = item.get("image_url")
        if image_url:
            try:
                response = requests.get(image_url, timeout=15)
                response.raise_for_status()
                cover = Image.open(BytesIO(response.content)).convert("RGB")
                cover.thumbnail((150, row_height - 18))
                canvas = Image.new("RGB", (150, row_height - 18), "#26384d")
                canvas.paste(
                    cover,
                    ((canvas.width - cover.width) // 2, (canvas.height - cover.height) // 2),
                )
                image.paste(canvas, (x, y + 9))
            except Exception:
                pass
        text_x = 282
        name = item["name"]
        draw.text((text_x, y + 27), name[:38], fill="white", font=_font(26, True))
        sub_text = item.get("sub_text")
        if sub_text:
            draw.text((text_x, y + 67), sub_text[:55], fill="#cfd7df", font=_font(18))

    footer_y = height - 70
    draw.rectangle((0, footer_y, width, height), fill="#ff9f1c")
    draw.text((width // 2, footer_y + 35), "ANIVO || ANIVO", fill="white", font=_font(28, True), anchor="mm")

    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()
