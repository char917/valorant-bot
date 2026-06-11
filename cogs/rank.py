import discord
from discord import app_commands
from discord.ext import commands

from utils.rank_ui import parse_riot_id, RegionSelectView

class Rank(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="rank", description="查詢 Valorant 段位（目前 + 歷史最高 + 各賽季）")
    @app_commands.describe(riot_id="你的 RiotID，格式：名稱#Tag，例如 Charlie#1234")
    async def rank(self, interaction: discord.Interaction, riot_id: str):
        parsed = parse_riot_id(riot_id)
        if parsed is None:
            await interaction.response.send_message(
                "RiotID 格式不對喔，要像這樣：`名稱#Tag`，例如 `Charlie#1234`。",
                ephemeral=True,
            )
            return

        name, tag = parsed
        view = RegionSelectView(
            self.bot.henrik_api, interaction.user.id, name, tag, self.bot.assets
        )
        await interaction.response.send_message(
            f"要查 **{name}#{tag}** 的段位，先選個區域：",
            view=view,
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(Rank(bot))
