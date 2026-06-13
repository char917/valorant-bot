import ssl
import json
import base64
import re

import aiohttp
from yarl import URL

AUTH_URL = "https://auth.riotgames.com/api/v1/authorization"
ENTITLEMENTS_URL = "https://entitlements.auth.riotgames.com/api/token/v1"
GEO_URL = "https://riot-geo.pas.si.riotgames.com/pas/v1/product/valorant"
REAUTH_URL = (
    "https://auth.riotgames.com/authorize"
    "?redirect_uri=https%3A%2F%2Fplayvalorant.com%2Fopt_in"
    "&client_id=play-valorant-web-prod"
    "&response_type=token%20id_token"
    "&nonce=1&scope=account%20openid"
)

AUTH_BODY = {
    "client_id": "play-valorant-web-prod",
    "nonce": "1",
    "redirect_uri": "https://playvalorant.com/opt_in",
    "response_type": "token id_token",
    "scope": "account openid",
}

USER_AGENT = "RiotClient/63.0.9.4909983.4789131 rso-auth (Windows;10;;Professional, x64)"

# Cloudflare 會擋掉預設 TLS 指紋，固定一組 cipher 順序繞過
FORCED_CIPHERS = ":".join([
    "ECDHE-ECDSA-CHACHA20-POLY1305", "ECDHE-RSA-CHACHA20-POLY1305",
    "ECDHE-ECDSA-AES128-GCM-SHA256", "ECDHE-RSA-AES128-GCM-SHA256",
    "ECDHE-ECDSA-AES256-GCM-SHA384", "ECDHE-RSA-AES256-GCM-SHA384",
    "ECDHE-ECDSA-AES128-SHA", "ECDHE-RSA-AES128-SHA",
    "ECDHE-ECDSA-AES256-SHA", "ECDHE-RSA-AES256-SHA",
    "AES128-GCM-SHA256", "AES256-GCM-SHA384",
    "AES128-SHA", "AES256-SHA", "DES-CBC3-SHA",
])


class RiotAuthError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def _build_ssl_ctx() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.minimum_version = ssl.TLSVersion.TLSv1_3
    ctx.set_ciphers(FORCED_CIPHERS)
    return ctx


def _token_from_uri(uri: str) -> str | None:
    m = re.search(r"access_token=([^&]+)", uri)
    return m.group(1) if m else None


def _tokens_from_uri(uri: str) -> tuple[str | None, str | None]:
    at = re.search(r"access_token=([^&]+)", uri)
    it = re.search(r"id_token=([^&]+)", uri)
    return (at.group(1) if at else None, it.group(1) if it else None)


def _puuid_from_token(access_token: str) -> str | None:
    try:
        payload = access_token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        data = json.loads(base64.urlsafe_b64decode(payload))
        return data.get("sub")
    except Exception:
        return None


class RiotAuth:
    def __init__(self):
        self._ssl_ctx = _build_ssl_ctx()

    def new_session(self) -> aiohttp.ClientSession:
        connector = aiohttp.TCPConnector(ssl=self._ssl_ctx)
        return aiohttp.ClientSession(
            connector=connector,
            headers={"User-Agent": USER_AGENT},
            cookie_jar=aiohttp.CookieJar(),
        )

    async def authorize(self, session: aiohttp.ClientSession, username: str, password: str) -> dict:
        async with session.post(AUTH_URL, json=AUTH_BODY) as resp:
            if resp.status != 200:
                raise RiotAuthError("無法連上 Riot 登入伺服器，請稍後再試。")

        body = {"type": "auth", "username": username, "password": password, "remember": True}
        async with session.put(AUTH_URL, json=body) as resp:
            data = await resp.json()

        if data.get("type") == "response":
            uri = data["response"]["parameters"]["uri"]
            access_token, id_token = _tokens_from_uri(uri)
            return {"status": "ok", "access_token": access_token, "id_token": id_token}

        if data.get("type") == "multifactor":
            email = data.get("multifactor", {}).get("email", "")
            return {"status": "2fa", "email": email}

        if data.get("error") == "auth_failure":
            raise RiotAuthError("帳號或密碼錯誤。")
        if data.get("error") == "rate_limited":
            raise RiotAuthError("嘗試太頻繁，請過幾分鐘再試。")
        raise RiotAuthError("登入失敗，請確認帳密後再試。")

    async def submit_2fa(self, session: aiohttp.ClientSession, code: str) -> dict:
        body = {"type": "multifactor", "code": code, "rememberDevice": True}
        async with session.put(AUTH_URL, json=body) as resp:
            data = await resp.json()

        if data.get("type") == "response":
            uri = data["response"]["parameters"]["uri"]
            access_token, id_token = _tokens_from_uri(uri)
            return {"status": "ok", "access_token": access_token, "id_token": id_token}
        raise RiotAuthError("驗證碼錯誤或已過期，請重新登入。")

    async def reauth(self, session: aiohttp.ClientSession, cookies: dict) -> tuple[str | None, str | None]:
        session.cookie_jar.update_cookies(cookies, URL("https://auth.riotgames.com"))
        async with session.get(REAUTH_URL, allow_redirects=False) as resp:
            location = resp.headers.get("Location", "")
        return _tokens_from_uri(location)

    async def get_entitlements(self, session: aiohttp.ClientSession, access_token: str) -> str:
        headers = {"Authorization": f"Bearer {access_token}"}
        async with session.post(ENTITLEMENTS_URL, json={}, headers=headers) as resp:
            data = await resp.json()
        token = data.get("entitlements_token")
        if not token:
            raise RiotAuthError("無法取得 entitlements，請重新登入。")
        return token

    async def get_region(self, session: aiohttp.ClientSession, access_token: str, id_token: str) -> str | None:
        headers = {"Authorization": f"Bearer {access_token}"}
        try:
            async with session.put(GEO_URL, json={"id_token": id_token}, headers=headers) as resp:
                data = await resp.json()
            return data.get("affinities", {}).get("live")
        except Exception:
            return None

    @staticmethod
    def dump_cookies(session: aiohttp.ClientSession) -> dict:
        return {c.key: c.value for c in session.cookie_jar}

    @staticmethod
    def puuid_from_token(access_token: str) -> str | None:
        return _puuid_from_token(access_token)
