import io
import asyncio
from datetime import datetime, timezone, timedelta

from PIL import Image, ImageDraw, ImageFont

CARD = (26, 31, 38)
GREEN = (74, 222, 128)
RED = (248, 71, 85)
WHITE = (236, 240, 244)
GREY = (139, 152, 165)

_FONT_R = "C:/Windows/Fonts/msjh.ttc"
_FONT_B = "C:/Windows/Fonts/msjhbd.ttc"
_fc: dict = {}

W = 980
HEAD_H = 34
ROW_H = 64
MAP_X = 96
SCORE_X, KDA_X, RATIO_X, HS_X, ACS_X, RR_X = 280, 450, 575, 680, 785, 895

TAIPEI = timezone(timedelta(hours=8))


def _font(size, bold=False):
    key = (size, bold)
    if key not in _fc:
        try:
            _fc[key] = ImageFont.truetype(_FONT_B if bold else _FONT_R, size)
        except Exception:
            _fc[key] = ImageFont.load_default()
    return _fc[key]


def _mix(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def _date(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(TAIPEI)
    except Exception:
        return ""
    return f"{dt.year}年 {dt.month}月 {dt.day}日"


def _score(d, x, cy, mine, opp):
    f = _font(21, bold=True)
    sep = " : "
    mc = GREEN if mine > opp else RED if mine < opp else GREY
    oc = GREEN if opp > mine else RED if opp < mine else GREY
    s_mine = str(mine)
    d.text((x, cy), s_mine, font=f, fill=mc, anchor="lm")
    x += d.textlength(s_mine, font=f)
    d.text((x, cy), sep, font=f, fill=GREY, anchor="lm")
    x += d.textlength(sep, font=f)
    d.text((x, cy), str(opp), font=f, fill=oc, anchor="lm")


def _rr_text(rr):
    if rr is None:
        return "—", GREY
    if rr > 0:
        return f"+{rr}", GREEN
    if rr < 0:
        return f"{rr}", RED
    return "0", GREY


def _draw(rows: list[dict], icons: dict) -> bytes:
    h = HEAD_H + len(rows) * ROW_H + 8
    img = Image.new("RGBA", (W, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    hy = HEAD_H // 2
    d.text((MAP_X, hy), "地圖", font=_font(14), fill=GREY, anchor="lm")
    d.text((SCORE_X, hy), "比分", font=_font(14), fill=GREY, anchor="lm")
    for x, label in [(KDA_X, "K / D / A"), (RATIO_X, "KDA"),
                     (HS_X, "HS%"), (ACS_X, "ACS"), (RR_X, "RR")]:
        d.text((x, hy), label, font=_font(14), fill=GREY, anchor="mm")

    y = HEAD_H
    for r in rows:
        win = r["result"] == "win"
        loss = r["result"] == "loss"
        accent = GREEN if win else RED if loss else GREY

        d.rounded_rectangle((10, y + 4, W - 10, y + ROW_H - 4), radius=10,
                            fill=_mix(CARD, accent, 0.10))
        d.rounded_rectangle((16, y + 14, 21, y + ROW_H - 14), radius=3, fill=accent)

        cy = y + ROW_H // 2

        icon = icons.get(r["agent_id"])
        if icon is not None:
            ic = icon.resize((48, 48), Image.LANCZOS)
            img.paste(ic, (36, cy - 24), ic)

        d.text((MAP_X, cy - 11), r["map"], font=_font(20, bold=True), fill=WHITE, anchor="lm")
        d.text((MAP_X, cy + 12), _date(r["started_at"]) or "競技", font=_font(13), fill=GREY, anchor="lm")

        _score(d, SCORE_X, cy, r["mine"], r["opp"])
        d.text((KDA_X, cy), f"{r['k']} / {r['d']} / {r['a']}", font=_font(18, bold=True), fill=WHITE, anchor="mm")
        ratio = (r["k"] + r["a"]) / r["d"] if r["d"] else (r["k"] + r["a"])
        d.text((RATIO_X, cy), f"{ratio:.2f}", font=_font(18, bold=True), fill=WHITE, anchor="mm")
        d.text((HS_X, cy), f"{r['hs']:.0f}%", font=_font(18, bold=True), fill=WHITE, anchor="mm")
        d.text((ACS_X, cy), f"{r['acs']:.0f}", font=_font(18, bold=True), fill=WHITE, anchor="mm")
        rr_str, rr_col = _rr_text(r.get("rr"))
        d.text((RR_X, cy), rr_str, font=_font(18, bold=True), fill=rr_col, anchor="mm")

        y += ROW_H

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


async def render_match_card(rows: list[dict], assets) -> bytes | None:
    if not rows:
        return None

    icons = {}
    if assets is not None:
        for aid in {r["agent_id"] for r in rows if r["agent_id"]}:
            icons[aid] = await assets.get_agent_icon(aid)

    return await asyncio.to_thread(_draw, rows, icons)
