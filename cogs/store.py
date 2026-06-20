import json
import time
import os

import discord
from discord import app_commands
from discord.ext import commands

from services.riot_auth import RiotAuthError
from services.riot_store import get_storefront, RiotStoreError
from utils.store_ui import build_store_embeds
from utils import crypto

TUTORIAL_STEPS = [
    (
        "步驟 1 ・ 登入 Riot 帳號",
        "前往 **playvalorant.com** 登入，記得勾選「**保持登入狀態**」。",
    ),
    (
        "步驟 2 ・ 開啟開發者工具",
        "按 **F12**，點上方「**Application**」→ 左側「**Cookies**」。",
    ),
    (
        "步驟 3 ・ 複製 ssid",
        "點左側 **`https://auth.riotgames.com`**，找到 **`ssid`** 那行，全選複製。\n請勿將 ssid 分享給任何人。",
    ),
    (
        "步驟 4 ・ 輸入 /login",
        "回到 Discord，輸入 **`/login`** 並選擇指令。",
    ),
    (
        "步驟 5 ・ 貼上 ssid",
        "將複製的值貼入表單欄位，按「**提交**」。",
    ),
    (
        "步驟 6 ・ 完成",
        "Bot 回覆「登入成功！」即完成，現在可以使用 **`/store`** 查詢每日商店。\nssid 約一個月過期，到期重複以上步驟。",
    ),
]


class CookieModal(discord.ui.Modal, title="輸入 Riot Cookie 登入"):
    ssid = discord.ui.TextInput(
        label="ssid cookie 的值",
        placeholder="貼上從瀏覽器複製的 ssid 值（很長一串字串）",
        style=discord.TextStyle.paragraph,
        max_length=2000,
    )

    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        await self.cog.handle_cookie_login(interaction, str(self.ssid).strip())


class LoginPromptView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=3600)
        self.cog = cog

    @discord.ui.button(label="登入", style=discord.ButtonStyle.primary)
    async def login(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CookieModal(self.cog))


class Store(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="login", description="用 Riot Cookie 登入以查詢每日商店（不需要輸入帳號密碼）")
    async def login(self, interaction: discord.Interaction):
        await interaction.response.send_modal(CookieModal(self))

    @app_commands.command(name="logout", description="登出並刪除儲存的登入資料")
    async def logout(self, interaction: discord.Interaction):
        removed = self.bot.db.delete_auth(interaction.user.id)
        msg = "登入資料已清除。" if removed else "尚未登入。"
        await interaction.response.send_message(msg, ephemeral=True)

    async def handle_cookie_login(self, interaction: discord.Interaction, ssid: str):
        await interaction.response.defer(ephemeral=True)

        if not ssid:
            await interaction.followup.send("ssid 欄位不得為空。", ephemeral=True)
            return

        session = self.bot.riot_auth.new_session()
        try:
            access_token, id_token = await self.bot.riot_auth.reauth(session, {"ssid": ssid})
        except Exception:
            await session.close()
            await interaction.followup.send("連線失敗，請稍後再試。", ephemeral=True)
            return

        if not access_token:
            await session.close()
            await interaction.followup.send(
                "ssid 無效或已過期，請重新取得並輸入。", ephemeral=True
            )
            return

        try:
            await self.bot.riot_auth.get_entitlements(session, access_token)
        except RiotAuthError as e:
            await session.close()
            await interaction.followup.send(e.message, ephemeral=True)
            return

        region = None
        if id_token:
            region = await self.bot.riot_auth.get_region(session, access_token, id_token)
        if not region:
            region = self.bot.settings.get_region(interaction.guild_id)

        cookies = self.bot.riot_auth.dump_cookies(session)
        await session.close()

        cookies_enc = crypto.encrypt(json.dumps(cookies))
        self.bot.db.set_auth(interaction.user.id, cookies_enc, region, int(time.time()))
        await interaction.followup.send("登入成功，可使用 `/store` 查詢每日商店。", ephemeral=True)

    @app_commands.command(name="store", description="查詢你今日的 Valorant 商店")
    async def store(self, interaction: discord.Interaction):
        auth = self.bot.db.get_auth(interaction.user.id)
        if auth is None:
            await self._prompt_login(interaction, "使用 `/store` 前需要先登入。")
            return

        cookies_enc, region, _ = auth
        cookies_raw = crypto.decrypt(cookies_enc)
        if cookies_raw is None:
            await self._prompt_login(interaction, "登入資料無法解密，請重新登入。")
            return

        await interaction.response.defer()
        session = self.bot.riot_auth.new_session()
        try:
            cookies = json.loads(cookies_raw)
            access_token, id_token = await self.bot.riot_auth.reauth(session, cookies)
            if not access_token:
                await session.close()
                await self._prompt_login(interaction, "登入已過期，請重新登入。", followup=True)
                return

            ent_token = await self.bot.riot_auth.get_entitlements(session, access_token)
            puuid = self.bot.riot_auth.puuid_from_token(access_token)
            store = await get_storefront(session, region, puuid, access_token, ent_token)

            new_cookies = self.bot.riot_auth.dump_cookies(session)
            if new_cookies:
                cookies_enc = crypto.encrypt(json.dumps(new_cookies))
                self.bot.db.set_auth(interaction.user.id, cookies_enc, region, int(time.time()))

        except (RiotAuthError, RiotStoreError) as e:
            await session.close()
            await interaction.followup.send(e.message)
            return
        except Exception:
            await session.close()
            await interaction.followup.send("查詢商店時發生錯誤，請稍後再試。")
            return
        await session.close()

        level_ids = [it["level_id"] for it in store["items"]]
        costs = [it["cost"] for it in store["items"]]
        offers = await self.bot.assets.get_skin_offers(level_ids)

        binding = self.bot.db.get_binding(interaction.user.id)
        name, tag = binding if binding else (interaction.user.display_name, "")
        embeds = build_store_embeds(name, tag, offers, costs, store["remaining"])
        await interaction.followup.send(embeds=embeds)

    async def _prompt_login(self, interaction: discord.Interaction, reason: str, followup: bool = False):
        tutorial_dir = os.path.join("assets", "tutorial")
        files = []
        embeds = []
        for i, (title, desc) in enumerate(TUTORIAL_STEPS):
            filename = f"step{i}.png"
            path = os.path.join(tutorial_dir, filename)
            embed = discord.Embed(title=title, description=desc, color=0xFF4654)
            if os.path.exists(path):
                files.append(discord.File(path, filename=filename))
                embed.set_image(url=f"attachment://{filename}")
            embeds.append(embed)
        embeds[0].set_author(name="Valorant 商店登入教學")

        try:
            await interaction.user.send(embeds=embeds, files=files, view=LoginPromptView(self))
            text = f"{reason} 登入教學已傳送至私訊。"
        except discord.Forbidden:
            text = f"{reason} 請先到隱私設定開啟「允許伺服器成員傳送私訊」後再重試。"

        if followup:
            await interaction.followup.send(text, ephemeral=True)
        else:
            await interaction.response.send_message(text, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Store(bot))
