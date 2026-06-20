import io
import asyncio

from PIL import Image

CANVAS_W = 900
RATIO = 2.1
FILL = 1.0


def _normalize_weapon_image(weapon_img: Image.Image) -> bytes:
    canvas_h = int(CANVAS_W / RATIO)
    canvas = Image.new("RGBA", (CANVAS_W, canvas_h), (0, 0, 0, 0))

    scale = min(CANVAS_W / weapon_img.width, canvas_h / weapon_img.height) * FILL
    nw = max(1, int(weapon_img.width * scale))
    nh = max(1, int(weapon_img.height * scale))
    resized = weapon_img.resize((nw, nh), Image.LANCZOS)
    canvas.paste(resized, ((CANVAS_W - nw) // 2, (canvas_h - nh) // 2), resized)

    buf = io.BytesIO()
    canvas.save(buf, format="PNG")
    return buf.getvalue()


async def render_store_weapon_images(offers: list[dict], assets) -> list[bytes | None]:
    result = []
    for offer in offers:
        image_url = offer.get("image")
        if not image_url:
            result.append(None)
            continue

        try:
            weapon_img = await assets._get_image(image_url)
            png = await asyncio.to_thread(_normalize_weapon_image, weapon_img)
        except Exception:
            png = None
        result.append(png)

    return result
