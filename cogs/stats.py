import io

import discord
from discord import app_commands
from discord.ext import commands

from services.henrik_api import HenrikAPIError
from utils.rank_ui import parse_riot_id
from utils.stats_ui import compute_match, aggregate, build_stats_embed
from utils.stats_card import render_match_card

class Stats(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="stats", description="近 15 場競技統計（KDA / 暴頭率 / ACS / RR）")
    @app_commands.describe(riot_id="RiotID，格式：名稱#Tag，例如 Charlie#1234")
    async def stats(self, interaction: discord.Interaction, riot_id: str):
        parsed = parse_riot_id(riot_id)
        if parsed is None:
            await interaction.response.send_message(
                "RiotID 格式錯誤，正確格式為：`名稱#Tag`，例如 `Charlie#1234`。",
                ephemeral=True,
            )
            return

        name, tag = parsed
        region = self.bot.settings.get_region(interaction.guild_id)
        await interaction.response.defer()
        try:
            matches = await self.bot.henrik_api.get_lifetime_matches(region, name, tag, size=15)
            history = await self.bot.henrik_api.get_mmr_history(region, name, tag)
        except HenrikAPIError as e:
            await interaction.followup.send(f"⚠️ {e.message}")
            return

        if not matches:
            await interaction.followup.send("查無競技對戰紀錄。")
            return

        rr_map = {
            h.get("match_id"): h.get("mmr_change_to_last_game")
            for h in history if h.get("match_id")
        }
        map_names = await self.bot.assets.get_map_names()
        rows = [compute_match(m) for m in matches]
        for r in rows:
            r["rr"] = rr_map.get(r["match_id"])
            r["map"] = map_names.get(r["map_id"]) or r["map"]

        embed = build_stats_embed(name, tag, aggregate(rows))
        png = await render_match_card(rows, self.bot.assets)
        file = discord.File(io.BytesIO(png), filename="stats.png")
        await interaction.followup.send(embed=embed, file=file)

async def setup(bot: commands.Bot):
    await bot.add_cog(Stats(bot))
