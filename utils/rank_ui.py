import io
import asyncio
import re

import discord

from services.henrik_api import HenrikAPI, HenrikAPIError
from utils.constants import (
    REGIONS,
    REGION_LABELS,
    get_tier_color,
    hex_to_int,
)
from utils.pyramid import render_pyramid, extract_win_tiers


def parse_riot_id(text: str):
    text = text.strip()
    if "#" not in text:
        return None
    name, tag = text.rsplit("#", 1)
    name, tag = name.strip(), tag.strip()
    if not name or not tag:
        return None
    return name, tag


def dig(data, *keys, default=None):
    cur = data
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
        if cur is None:
            return default
    return cur


def calc_winrate(wins: int, games: int):
    if not games:
        return None
    return round(wins / games * 100, 1)


def _season_sort_key(short: str) -> tuple:
    m = re.match(r'e(\d+)a(\d+)', short)
    return (int(m.group(1)), int(m.group(2))) if m else (0, 0)


def format_season_label(short: str) -> str:
    m = re.match(r'e(\d+)a(\d+)', short)
    if m:
        ep, act = int(m.group(1)), int(m.group(2))
        if ep >= 10:
            return f"V{ep + 15} - 第{act}章"
        return f"EP{ep} - 第{act}章"
    return short


def seasons_from_data(data: dict) -> list[tuple[str, dict]]:
    by_season = data.get("by_season") or {}
    result = [
        (short, s)
        for short, s in by_season.items()
        if isinstance(s, dict) and "error" not in s
    ]
    return sorted(result, key=lambda x: _season_sort_key(x[0]), reverse=True)


def build_overview_embed(name: str, tag: str, data: dict) -> discord.Embed:
    current_tier = dig(data, "current_data", "currenttierpatched", default="未定級")
    rr = dig(data, "current_data", "ranking_in_tier", default=0)
    peak_tier = dig(data, "highest_rank", "patched_tier", default="無紀錄")
    peak_season = dig(data, "highest_rank", "season", default="—")

    embed = discord.Embed(
        title=f"{name}#{tag} 的段位",
        color=hex_to_int(get_tier_color(current_tier)),
    )
    embed.add_field(name="目前段位", value=f"**{current_tier}** ・ {rr} RR", inline=False)
    embed.add_field(name="歷史最高", value=f"**{peak_tier}**（{peak_season}）", inline=False)

    badge = dig(data, "current_data", "images", "small") or dig(data, "current_data", "images", "large")
    if badge:
        embed.set_thumbnail(url=badge)

    seasons = seasons_from_data(data)
    if seasons:
        embed.set_footer(text=f"共 {len(seasons)} 個賽季紀錄 ・ 用下方選單切換")
    else:
        embed.set_footer(text="查無賽季紀錄")
    return embed


def build_season_embed(name: str, tag: str, short: str, season: dict, index: int, total: int) -> discord.Embed:
    end_tier = season.get("final_rank_patched") or "未定級"
    wins = season.get("wins") or 0
    games = season.get("number_of_games") or 0
    losses = max(games - wins, 0)
    winrate = calc_winrate(wins, games)
    winrate_text = f"{winrate}%" if winrate is not None else "—"

    embed = discord.Embed(
        title=f"{name}#{tag} ・ {format_season_label(short)}",
        color=hex_to_int(get_tier_color(end_tier)),
    )
    embed.add_field(name="結算段位", value=f"**{end_tier}**", inline=False)
    embed.add_field(name="場數", value=f"{games} 場", inline=True)
    embed.add_field(name="勝 / 敗", value=f"{wins} / {losses}", inline=True)
    embed.add_field(name="勝率", value=winrate_text, inline=True)
    embed.set_footer(text=f"賽季 {index + 1} / {total}")
    return embed


async def build_season_page(name: str, tag: str, short: str, season: dict, index: int, total: int, assets):
    embed = build_season_embed(name, tag, short, season, index, total)
    win_tiers = extract_win_tiers(season)
    if not win_tiers or assets is None:
        return embed, None

    wins = season.get("wins") or len(win_tiers)
    resolved = await assets.resolve_pyramid("", [t for t, _ in win_tiers], wins)
    if not resolved:
        return embed, None

    png = await asyncio.to_thread(render_pyramid, win_tiers, resolved)
    if not png:
        return embed, None

    embed.set_image(url="attachment://pyramid.png")
    return embed, discord.File(io.BytesIO(png), filename="pyramid.png")


class SeasonView(discord.ui.View):
    def __init__(self, author_id: int, name: str, tag: str, data: dict, assets=None):
        super().__init__(timeout=180)
        self.author_id = author_id
        self.name = name
        self.tag = tag
        self.data = data
        self.assets = assets
        self.seasons = seasons_from_data(data)
        self.index = None
        self._rebuild()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("這不是你發起的查詢喔。", ephemeral=True)
            return False
        return True

    def _rebuild(self):
        self.clear_items()

        if self.seasons:
            options = [
                discord.SelectOption(
                    label=format_season_label(short),
                    value=str(i),
                    default=(self.index == i),
                )
                for i, (short, _) in enumerate(self.seasons[:25])
            ]
            placeholder = "選擇賽季…" if self.index is None else format_season_label(self.seasons[self.index][0])
            select = discord.ui.Select(
                placeholder=placeholder,
                options=options,
                min_values=1,
                max_values=1,
            )
            select.callback = self._on_season_select
            self.add_item(select)

        home = discord.ui.Button(
            label="總覽",
            emoji="🏠",
            style=discord.ButtonStyle.primary,
            disabled=(self.index is None),
        )
        home.callback = self._on_home
        self.add_item(home)

    async def _on_season_select(self, interaction: discord.Interaction):
        self.index = int(interaction.data["values"][0])
        await self._update(interaction)

    async def _on_home(self, interaction: discord.Interaction):
        self.index = None
        await self._update(interaction)

    async def _current_page(self):
        if self.index is None:
            return build_overview_embed(self.name, self.tag, self.data), None
        short, season = self.seasons[self.index]
        return await build_season_page(
            self.name, self.tag, short, season, self.index, len(self.seasons), self.assets
        )

    async def _update(self, interaction: discord.Interaction):
        self._rebuild()
        await interaction.response.defer()
        embed, file = await self._current_page()
        attachments = [file] if file else []
        await interaction.edit_original_response(embed=embed, view=self, attachments=attachments)


class RegionSelect(discord.ui.Select):
    def __init__(self, api: HenrikAPI, author_id: int, name: str, tag: str, assets=None):
        self.api = api
        self.author_id = author_id
        self.name = name
        self.tag = tag
        self.assets = assets
        options = [
            discord.SelectOption(label=REGION_LABELS[r], value=r) for r in REGIONS
        ]
        super().__init__(placeholder="選擇你的區域…", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        region = self.values[0]
        await interaction.response.defer()
        try:
            data = await self.api.get_mmr(region, self.name, self.tag)
        except HenrikAPIError as e:
            await interaction.edit_original_response(content=f"⚠️ {e.message}", view=None)
            return

        view = SeasonView(self.author_id, self.name, self.tag, data, self.assets)
        embed = build_overview_embed(self.name, self.tag, data)
        await interaction.edit_original_response(content=None, embed=embed, view=view)


class RegionSelectView(discord.ui.View):
    def __init__(self, api: HenrikAPI, author_id: int, name: str, tag: str, assets=None):
        super().__init__(timeout=120)
        self.author_id = author_id
        self.add_item(RegionSelect(api, author_id, name, tag, assets))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("這不是你發起的查詢喔。", ephemeral=True)
            return False
        return True
