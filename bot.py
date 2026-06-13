import os
import asyncio

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

from services.henrik_api import HenrikAPI
from services.riot_auth import RiotAuth
from utils.assets import AssetManager
from utils.settings import GuildSettings
from utils.database import Database

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
HENRIK_API_KEY = os.getenv("HENRIK_API_KEY")
GUILD_ID = os.getenv("GUILD_ID")

intents = discord.Intents.default()

class ValorantBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.henrik_api = HenrikAPI(HENRIK_API_KEY)
        self.assets = AssetManager()
        self.settings = GuildSettings()
        self.db = Database()
        self.riot_auth = RiotAuth()

    async def setup_hook(self):
        await self.load_extension("cogs.rank")
        await self.load_extension("cogs.stats")
        await self.load_extension("cogs.region")
        await self.load_extension("cogs.binding")
        await self.load_extension("cogs.store")
        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            print(f"已同步 {len(synced)} 個指令到伺服器 {GUILD_ID}（即時生效）")
        else:
            synced = await self.tree.sync()
            print(f"已同步 {len(synced)} 個全域 slash command（最久約 1 小時生效）")

    async def on_ready(self):
        print(f"已登入：{self.user}（id={self.user.id}）")
        await self.change_presence(
            activity=discord.Game(name="顆秒 !! 棒棒棒棒")
        )

    async def close(self):
        await self.henrik_api.close()
        await self.assets.close()
        self.db.close()
        await super().close()

bot = ValorantBot()

@bot.tree.command(name="ping", description="測試 bot 是否在線")
async def ping(interaction: discord.Interaction):
    latency_ms = round(bot.latency * 1000)
    await interaction.response.send_message(f"延遲 {latency_ms} ms", ephemeral=True)

def main():
    if not DISCORD_TOKEN:
        raise SystemExit("缺少 DISCORD_TOKEN，請在 .env 填入。")
    if not HENRIK_API_KEY:
        raise SystemExit("缺少 HENRIK_API_KEY，請在 .env 填入。")
    bot.run(DISCORD_TOKEN)

if __name__ == "__main__":
    main()
