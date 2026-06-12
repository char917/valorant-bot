REGIONS = ["ap", "na", "eu", "kr", "latam", "br"]

REGION_LABELS = {
    "ap": "亞太 (AP)",
    "na": "北美 (NA)",
    "eu": "歐洲 (EU)",
    "kr": "韓國 (KR)",
    "latam": "拉美 (LATAM)",
    "br": "巴西 (BR)",
}

TIER_COLORS = {
    "Iron": "#4f514f",
    "Bronze": "#a5855d",
    "Silver": "#bbc2c2",
    "Gold": "#eccf56",
    "Platinum": "#59a9b6",
    "Diamond": "#b489c4",
    "Ascendant": "#6ae2af",
    "Immortal": "#bb3d65",
    "Radiant": "#ffffaa",
    "Unrated": "#5c5c5c",
}

TIER_ID_BASE = {
    **{n: "Iron" for n in (3, 4, 5)},
    **{n: "Bronze" for n in (6, 7, 8)},
    **{n: "Silver" for n in (9, 10, 11)},
    **{n: "Gold" for n in (12, 13, 14)},
    **{n: "Platinum" for n in (15, 16, 17)},
    **{n: "Diamond" for n in (18, 19, 20)},
    **{n: "Ascendant" for n in (21, 22, 23)},
    **{n: "Immortal" for n in (24, 25, 26)},
    27: "Radiant",
}

TIER_NAME_ZH = {
    "Iron": "鐵牌",
    "Bronze": "銅牌",
    "Silver": "銀牌",
    "Gold": "金牌",
    "Platinum": "白金",
    "Diamond": "鑽石",
    "Ascendant": "超凡入聖",
    "Immortal": "神話",
    "Radiant": "輻能戰魂",
}


def get_tier_base(tier_name: str) -> str:
    if not tier_name:
        return "Unrated"
    return tier_name.split(" ")[0]


def localize_tier(tier_name: str) -> str:
    base = get_tier_base(tier_name)
    if base == "Unrated":
        return "未定級"
    zh = TIER_NAME_ZH.get(base)
    if zh is None:
        return tier_name
    parts = tier_name.split(" ", 1)
    div = parts[1] if len(parts) > 1 else ""
    return f"{zh} {div}".strip()

def get_tier_color(tier_name: str) -> str:
    return TIER_COLORS.get(get_tier_base(tier_name), TIER_COLORS["Unrated"])

def get_tier_color_by_id(tier_id: int) -> str:
    base = TIER_ID_BASE.get(tier_id, "Unrated")
    return TIER_COLORS[base]

def hex_to_int(hex_str: str) -> int:
    return int(hex_str.lstrip("#"), 16)
