import io
import os
import json

import aiohttp
from PIL import Image

META_TIERS_URL = "https://valorant-api.com/v1/competitivetiers"
META_SEASONS_URL = "https://valorant-api.com/v1/seasons/competitive"
MAPS_URL = "https://valorant-api.com/v1/maps?language=zh-TW"
SKINS_URL = "https://valorant-api.com/v1/weapons/skins?language=zh-TW"
CONTENT_TIERS_URL = "https://valorant-api.com/v1/contenttiers"

CACHE_DIR = ".asset_cache"

class AssetManager:
    def __init__(self):
        self._session: aiohttp.ClientSession | None = None
        self._img_cache: dict[str, Image.Image] = {}
        self._meta = None
        self._map_names = None
        self._skins = None
        self._tier_colors = None
        os.makedirs(CACHE_DIR, exist_ok=True)

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def _get_json(self, url: str, cache_name: str) -> dict:
        path = os.path.join(CACHE_DIR, cache_name)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        session = await self._get_session()
        async with session.get(url) as resp:
            resp.raise_for_status()
            data = await resp.json()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return data

    async def _get_image(self, url: str) -> Image.Image:
        if url in self._img_cache:
            return self._img_cache[url]
        fname = "_".join(url.split("/")[-2:])
        path = os.path.join(CACHE_DIR, fname)
        if os.path.exists(path):
            img = Image.open(path).convert("RGBA")
        else:
            session = await self._get_session()
            async with session.get(url) as resp:
                resp.raise_for_status()
                raw = await resp.read()
            with open(path, "wb") as f:
                f.write(raw)
            img = Image.open(io.BytesIO(raw)).convert("RGBA")
        self._img_cache[url] = img
        return img

    async def get_map_names(self) -> dict:
        if self._map_names is not None:
            return self._map_names
        try:
            data = await self._get_json(MAPS_URL, "maps_zhtw.json")
            self._map_names = {
                m["uuid"]: m.get("displayName", "")
                for m in data.get("data", []) if m.get("uuid")
            }
        except Exception:
            self._map_names = {}
        return self._map_names

    async def get_skin_offers(self, level_ids: list[str]) -> list[dict]:
        skins = await self._load_skins()
        colors = await self._load_tier_colors()
        result = []
        for lid in level_ids:
            skin = skins.get(lid)
            if not skin:
                result.append({"name": "未知皮膚", "image": None, "color": None})
                continue
            result.append({
                "name": skin["name"],
                "image": skin["image"],
                "color": colors.get(skin["tier"]),
            })
        return result

    async def _load_skins(self) -> dict:
        if self._skins is not None:
            return self._skins
        try:
            data = await self._get_json(SKINS_URL, "skins_zhtw.json")
            mapping = {}
            for s in data.get("data", []):
                name = s.get("displayName", "")
                image = s.get("displayIcon")
                tier = s.get("contentTierUuid")
                for lvl in s.get("levels") or []:
                    uuid = lvl.get("uuid")
                    if uuid:
                        mapping[uuid] = {
                            "name": name,
                            "image": image or lvl.get("displayIcon"),
                            "tier": tier,
                        }
            self._skins = mapping
        except Exception:
            self._skins = {}
        return self._skins

    async def _load_tier_colors(self) -> dict:
        if self._tier_colors is not None:
            return self._tier_colors
        try:
            data = await self._get_json(CONTENT_TIERS_URL, "content_tiers.json")
            self._tier_colors = {
                t["uuid"]: t.get("highlightColor", "")[:6]
                for t in data.get("data", []) if t.get("uuid")
            }
        except Exception:
            self._tier_colors = {}
        return self._tier_colors

    async def get_agent_icon(self, agent_id: str):
        if not agent_id:
            return None
        url = f"https://media.valorant-api.com/agents/{agent_id}/displayicon.png"
        try:
            return await self._get_image(url)
        except Exception:
            return None

    async def _load_meta(self) -> dict:
        if self._meta is not None:
            return self._meta

        tiers_data = await self._get_json(META_TIERS_URL, "meta_tiers.json")
        seasons_data = await self._get_json(META_SEASONS_URL, "meta_seasons.json")

        collections = {}
        for coll in tiers_data["data"]:
            tris = {}
            for t in coll["tiers"]:
                up = t.get("rankTriangleUpIcon")
                down = t.get("rankTriangleDownIcon")
                if up and down:
                    tris[t["tier"]] = (up, down)
            collections[coll["uuid"]] = tris

        seasons = {}
        latest = None
        for s in seasons_data["data"]:
            borders = s.get("borders")
            if not borders:
                continue
            entry = {
                "collection": s["competitiveTiersUuid"],
                "borders": sorted(borders, key=lambda b: b["winsRequired"]),
            }
            seasons[s["seasonUuid"]] = entry
            latest = entry

        self._meta = {"collections": collections, "seasons": seasons, "latest": latest}
        return self._meta

    @staticmethod
    def _pick_border(borders: list, wins: int) -> dict:
        chosen = borders[0]
        for b in borders:
            if wins >= b["winsRequired"]:
                chosen = b
        return chosen

    async def resolve_pyramid(self, season_uuid: str, win_tiers: list[int], wins: int):
        try:
            meta = await self._load_meta()
            entry = meta["seasons"].get(season_uuid) or meta["latest"]
            if entry is None:
                return None

            tris_map = meta["collections"].get(entry["collection"], {})
            border = self._pick_border(entry["borders"], wins)

            frame = await self._get_image(border["displayIcon"])

            tris = {}
            for tier in set(win_tiers):
                urls = tris_map.get(tier)
                if not urls:
                    continue
                up = await self._get_image(urls[0])
                down = await self._get_image(urls[1])
                tris[tier] = (up, down)

            if not tris:
                return None
            return {"frame": frame, "tris": tris}
        except Exception:
            return None
