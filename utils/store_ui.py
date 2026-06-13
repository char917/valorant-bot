import os
import discord

_vp_id = os.getenv("VP_EMOJI_ID")
VP_EMOJI = f"<:vp:{_vp_id}>" if _vp_id else "VP"


def _color(hex6: str | None) -> discord.Color:
    if not hex6:
        return discord.Color.dark_theme()
    try:
        return discord.Color(int(hex6, 16))
    except ValueError:
        return discord.Color.dark_theme()


def format_remaining(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    return f"{h} 小時 {m} 分"


def build_store_embeds(name: str, tag: str, offers: list[dict], costs: list, remaining: int) -> list[discord.Embed]:
    tag_str = f"#{tag}" if tag else ""
    header = discord.Embed(description=f"**{name}{tag_str} 的每日商店**  |  {format_remaining(remaining)}後刷新")

    embeds = [header]
    for offer, cost in zip(offers, costs):
        price = f"{VP_EMOJI} {cost} VP" if cost is not None else "—"
        embed = discord.Embed(
            title=offer["name"],
            description=price,
            color=_color(offer.get("color")),
        )
        if offer.get("image"):
            embed.set_image(url=offer["image"])
        embeds.append(embed)

    return embeds
