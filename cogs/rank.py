import discord
from discord import app_commands
from discord.ext import commands

from services.henrik_api import HenrikAPIError
from utils.rank_ui import parse_riot_id, build_overview_embed, SeasonView

class Rank(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="rank", description="查詢 Valorant 段位（目前 + 歷史最高 + 各賽季）")
    @app_commands.describe(riot_id="RiotID，格式：名稱#Tag，例如 Charlie#1234")
    async def rank(self, interaction: discord.Interaction, riot_id: str):
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
            data = await self.bot.henrik_api.get_mmr(region, name, tag)
        except HenrikAPIError as e:
            await interaction.followup.send(f"⚠️ {e.message}")
            return

        view = SeasonView(interaction.user.id, name, tag, data, self.bot.assets)
        embed = build_overview_embed(name, tag, data)
        await interaction.followup.send(embed=embed, view=view, wait=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Rank(bot))
