import discord
from discord import app_commands
from discord.ext import commands

from utils.constants import REGIONS, REGION_LABELS

REGION_CHOICES = [app_commands.Choice(name=REGION_LABELS[r], value=r) for r in REGIONS]

class Region(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="setregion", description="設定本伺服器預設查詢的 Valorant 伺服器（限管理員）")
    @app_commands.describe(region="要設定的 Valorant 伺服器")
    @app_commands.choices(region=REGION_CHOICES)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setregion(self, interaction: discord.Interaction, region: app_commands.Choice[str]):
        if interaction.guild_id is None:
            await interaction.response.send_message("此指令僅限在伺服器中使用。", ephemeral=True)
            return
        self.bot.settings.set_region(interaction.guild_id, region.value)
        await interaction.response.send_message(
            f"預設查詢區域已設為 **{region.name}**。"
        )

    @setregion.error
    async def setregion_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            msg = "此指令僅限伺服器管理員使用。"
        else:
            msg = "設定失敗，請稍後再試。"
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Region(bot))
