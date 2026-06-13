import discord
from discord import app_commands
from discord.ext import commands

from utils.rank_ui import parse_riot_id

class Binding(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="bind", description="綁定你的 Riot ID，之後 /rank 和 /stats 可以不用輸入")
    @app_commands.describe(riot_id="你的 RiotID，格式：名稱#Tag，例如 Charlie#1234")
    async def bind(self, interaction: discord.Interaction, riot_id: str):
        parsed = parse_riot_id(riot_id)
        if parsed is None:
            await interaction.response.send_message(
                "RiotID 格式不正確，請使用 `名稱#Tag` 格式。",
                ephemeral=True,
            )
            return
        name, tag = parsed
        self.bot.db.set_binding(interaction.user.id, name, tag)
        await interaction.response.send_message(f"綁定成功：**{name}#{tag}**", ephemeral=True)

    @app_commands.command(name="unbind", description="解除綁定的 Riot ID")
    async def unbind(self, interaction: discord.Interaction):
        removed = self.bot.db.delete_binding(interaction.user.id)
        if removed:
            await interaction.response.send_message("綁定已解除。", ephemeral=True)
        else:
            await interaction.response.send_message("尚未綁定 Riot ID。", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Binding(bot))
