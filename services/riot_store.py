import json
import base64

import aiohttp

SHARD_MAP = {
    "ap": "ap", "na": "na", "eu": "eu", "kr": "kr",
    "latam": "na", "br": "na",
}

VERSION_URL = "https://valorant-api.com/v1/version"

CLIENT_PLATFORM = base64.b64encode(json.dumps({
    "platformType": "PC",
    "platformOS": "Windows",
    "platformOSVersion": "10.0.19042.1.256.64bit",
    "platformChipset": "Unknown",
}).encode()).decode()


class RiotStoreError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


async def _client_version(session: aiohttp.ClientSession) -> str:
    async with session.get(VERSION_URL) as resp:
        data = await resp.json()
    return data["data"]["riotClientVersion"]


async def get_storefront(session: aiohttp.ClientSession, region: str, puuid: str,
                         access_token: str, ent_token: str) -> dict:
    shard = SHARD_MAP.get(region, "ap")
    version = await _client_version(session)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Riot-Entitlements-JWT": ent_token,
        "X-Riot-ClientPlatform": CLIENT_PLATFORM,
        "X-Riot-ClientVersion": version,
        "Content-Type": "application/json",
    }

    url_v3 = f"https://pd.{shard}.a.pvp.net/store/v3/storefront/{puuid}"
    async with session.post(url_v3, json={}, headers=headers) as resp:
        if resp.status == 200:
            data = await resp.json()
        elif resp.status in (400, 404):
            data = None
        else:
            raise RiotStoreError(f"商店查詢失敗（{resp.status}）。")

    # v3 失敗就退回舊版 v2 GET
    if data is None:
        url_v2 = f"https://pd.{shard}.a.pvp.net/store/v2/storefront/{puuid}"
        async with session.get(url_v2, headers=headers) as resp:
            if resp.status != 200:
                raise RiotStoreError("找不到商店資料，可能是區域設定錯誤。")
            data = await resp.json()

    panel = data.get("SkinsPanelLayout")
    if not panel:
        raise RiotStoreError("商店資料格式異常，請稍後再試。")

    offers = panel.get("SingleItemStoreOffers") or []
    costs = {}
    for o in offers:
        cost = o.get("Cost") or {}
        vp = next(iter(cost.values()), None)
        costs[o.get("OfferID")] = vp

    level_ids = panel.get("SingleItemOffers") or [o.get("OfferID") for o in offers]
    remaining = panel.get("SingleItemOffersRemainingDurationInSeconds", 0)

    items = [{"level_id": lid, "cost": costs.get(lid)} for lid in level_ids]
    return {"items": items, "remaining": remaining}
