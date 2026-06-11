import aiohttp
from urllib.parse import quote

BASE_URL = "https://api.henrikdev.xyz"

class HenrikAPIError(Exception):
    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.message = message
        self.status = status

class HenrikAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={"Authorization": self.api_key}
            )
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_mmr(self, region: str, name: str, tag: str) -> dict:
        url = f"{BASE_URL}/valorant/v2/mmr/{region}/{quote(name)}/{quote(tag)}"
        session = await self._get_session()

        try:
            async with session.get(url) as resp:
                try:
                    payload = await resp.json()
                except Exception:
                    raise HenrikAPIError("API 回傳格式異常，請稍後再試。", resp.status)

                if resp.status == 200:
                    return payload.get("data", {})

                if resp.status == 404:
                    raise HenrikAPIError("找不到這位玩家，請確認 RiotID 和區域是否正確。", 404)
                if resp.status == 401 or resp.status == 403:
                    raise HenrikAPIError("API Key 無效或權限不足，請檢查 HENRIK_API_KEY。", resp.status)
                if resp.status == 429:
                    raise HenrikAPIError("查詢太頻繁，請過幾秒再試。", 429)

                msg = self._extract_error(payload)
                raise HenrikAPIError(f"查詢失敗（{resp.status}）：{msg}", resp.status)

        except aiohttp.ClientError:
            raise HenrikAPIError("連不上 Henrik API，請檢查網路後再試。")

    @staticmethod
    def _extract_error(payload: dict) -> str:
        errors = payload.get("errors")
        if isinstance(errors, list) and errors:
            return errors[0].get("message", "未知錯誤")
        return "未知錯誤"
