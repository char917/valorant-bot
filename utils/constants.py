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

def get_tier_base(tier_name: str) -> str:
    if not tier_name:
        return "Unrated"
    return tier_name.split(" ")[0]

def get_tier_color(tier_name: str) -> str:
    return TIER_COLORS.get(get_tier_base(tier_name), TIER_COLORS["Unrated"])

def get_tier_color_by_id(tier_id: int) -> str:
    base = TIER_ID_BASE.get(tier_id, "Unrated")
    return TIER_COLORS[base]

def hex_to_int(hex_str: str) -> int:
    return int(hex_str.lstrip("#"), 16)
