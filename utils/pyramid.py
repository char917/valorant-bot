import io
import math

from PIL import Image, ImageDraw

_H = math.sin(math.pi / 3)

_ROWS = 7

_SS = 2

_FIT_W = 0.6
_FIT_YOFFSET = -0.066

def extract_win_tiers(season: dict) -> list[tuple[int, str]]:
    for key in ("act_wins", "act_rank_wins"):
        arr = season.get(key)
        if isinstance(arr, list) and arr:
            out = []
            for e in arr:
                if not isinstance(e, dict):
                    continue
                tier_id = e.get("id")
                if tier_id is None:
                    tier_id = e.get("tier", 0)
                name = e.get("name") or e.get("patched_tier") or ""
                out.append((int(tier_id or 0), name))
            return out
    return []

def render_pyramid(win_tiers: list[tuple[int, str]], assets: dict, size: int = 512):
    tris = assets["tris"]
    tiers = sorted([tid for tid, _ in win_tiers if tid in tris], reverse=True)
    if not tiers:
        return None

    px = size * _SS
    canvas = Image.new("RGBA", (px, px), (0, 0, 0, 0))

    width = _FIT_W
    height = width * _H
    left = (1 - width) / 2 * px
    top = ((1 - height) * 2 / 3 + _FIT_YOFFSET) * px
    w_px = width * px
    h_px = height * px
    cell_w = w_px / _ROWS
    cell_h = h_px / _ROWS

    def node_x(k, i):
        return 0.5 - 0.5 * k / _ROWS + i / _ROWS

    def fx(x):
        return left + x * w_px

    def fy(k):
        return top + (k / _ROWS) * h_px

    grid = ImageDraw.Draw(canvas)
    for r in range(_ROWS):
        for j in range(2 * r + 1):
            if j % 2 == 0:
                a = j // 2
                poly = [(node_x(r, a), r), (node_x(r + 1, a), r + 1), (node_x(r + 1, a + 1), r + 1)]
            else:
                a = (j - 1) // 2
                poly = [(node_x(r, a), r), (node_x(r, a + 1), r), (node_x(r + 1, a + 1), r + 1)]
            grid.polygon([(fx(x), fy(k)) for x, k in poly], outline=(255, 255, 255, 38), width=_SS)

    resized: dict = {}

    def gem(tier_id, kind):
        key = (tier_id, kind)
        if key not in resized:
            img = tris[tier_id][0 if kind == "up" else 1]
            w = math.ceil(cell_w) + 2
            h = math.ceil(cell_h) + 2
            resized[key] = img.resize((w, h), Image.LANCZOS)
        return resized[key]

    idx = 0
    for r in range(_ROWS):
        for j in range(2 * r + 1):
            if idx >= len(tiers):
                break
            tier_id = tiers[idx]
            idx += 1
            if j % 2 == 0:
                a = j // 2
                x0, y0 = fx(node_x(r + 1, a)), fy(r)
                canvas.alpha_composite(gem(tier_id, "up"), (round(x0) - 1, round(y0) - 1))
            else:
                a = (j - 1) // 2
                x0, y0 = fx(node_x(r, a)), fy(r)
                canvas.alpha_composite(gem(tier_id, "down"), (round(x0) - 1, round(y0) - 1))
        if idx >= len(tiers):
            break

    canvas.alpha_composite(assets["frame"].resize((px, px), Image.LANCZOS))

    img = canvas.resize((size, size), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()
