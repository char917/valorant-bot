import urllib.request, json, io
from PIL import Image, ImageDraw, ImageFont

# 抓真實武器圖，示範貼到固定比例畫布、置中後的 Discord embed 外觀
RATIO = 2.1   # 圖片框寬高比，越小框越扁、武器看起來越大
FILL = 1.0    # 武器佔框比例，1.0 = 貼齊框邊

want = [("蝴蝶刀", (242, 154, 64)), ("幻象", (210, 90, 200)),
        ("判官", (242, 154, 64)), ("制式手槍", (242, 154, 64))]
prices = ["3550", "1775", "2175", "2175"]

data = json.load(urllib.request.urlopen(
    "https://valorant-api.com/v1/weapons/skins?language=zh-TW", timeout=30))["data"]

picks = []
for kw, color in want:
    for s in data:
        if kw in s["displayName"] and s.get("displayIcon"):
            raw = urllib.request.urlopen(s["displayIcon"], timeout=30).read()
            picks.append((s["displayName"], Image.open(io.BytesIO(raw)).convert("RGBA"), color))
            break

EMBED_W = 520
PAD = 16
BAR = 4
BG = (49, 51, 56)
EMBED_BG = (43, 45, 49)
TEXT = (242, 243, 245)
SUB = (181, 186, 193)
GAP = 8
OUT = 20

FONT_BD = "C:/Windows/Fonts/msjhbd.ttc"
FONT_RG = "C:/Windows/Fonts/msjh.ttc"
f_name = ImageFont.truetype(FONT_BD, 22)
f_vp = ImageFont.truetype(FONT_RG, 19)
f_hd = ImageFont.truetype(FONT_BD, 20)

box_w = EMBED_W - BAR - PAD * 2
box_h = int(box_w / RATIO)
name_h = 30
vp_h = 28
embed_h = PAD + name_h + vp_h + box_h + PAD
header_h = 56

W = EMBED_W + OUT * 2
H = OUT + header_h + GAP + len(picks) * (embed_h + GAP) + OUT
img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

x = OUT
y = OUT
d.rounded_rectangle((x, y, x + EMBED_W, y + header_h), radius=8, fill=EMBED_BG)
d.text((x + PAD, y + 18), "Charlie#0917 的每日商店   |   8 小時 35 分後刷新", font=f_hd, fill=TEXT)
y += header_h + GAP

for (name, wimg, color), price in zip(picks, prices):
    d.rounded_rectangle((x, y, x + EMBED_W, y + embed_h), radius=8, fill=EMBED_BG)
    d.rounded_rectangle((x, y, x + BAR + 2, y + embed_h), radius=2, fill=color)

    tx = x + BAR + PAD
    d.text((tx, y + PAD), name, font=f_name, fill=TEXT)
    d.text((tx, y + PAD + name_h), f"◆ {price} VP", font=f_vp, fill=SUB)

    by = y + PAD + name_h + vp_h
    canvas = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
    scale = min(box_w / wimg.width, box_h / wimg.height) * FILL
    nw, nh = int(wimg.width * scale), int(wimg.height * scale)
    rs = wimg.resize((nw, nh), Image.LANCZOS)
    canvas.paste(rs, ((box_w - nw) // 2, (box_h - nh) // 2), rs)
    img.paste(canvas, (tx, by), canvas)

    y += embed_h + GAP

img.save("store_mockup.png")
print("saved", img.size, "ratio", RATIO, "fill", FILL)
