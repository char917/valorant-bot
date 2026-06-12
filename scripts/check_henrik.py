import os
import sys
import json
import asyncio
from urllib.parse import quote

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
import aiohttp

from utils.pyramid import extract_win_tiers

load_dotenv()

USAGE = "用法：python scripts/check_henrik.py 名稱#Tag [伺服器]\n例如：python scripts/check_henrik.py Charlie#0917 ap"
REGIONS = ["ap", "na", "eu", "kr", "latam", "br"]
BASE = "https://api.henrikdev.xyz"


def parse_args():
    args = sys.argv[1:]
    if not args or "#" not in args[0]:
        print(USAGE)
        sys.exit(1)
    name, tag = args[0].rsplit("#", 1)
    region = args[1] if len(args) > 1 else "ap"
    if region not in REGIONS:
        print(f"伺服器要是這些之一：{', '.join(REGIONS)}")
        sys.exit(1)
    return name.strip(), tag.strip(), region


def section(title):
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)


async def fetch(session, url):
    async with session.get(url) as resp:
        text = await resp.text()
        return resp.status, text


async def main():
    name, tag, region = parse_args()

    key = os.getenv("HENRIK_API_KEY")
    if not key:
        print("找不到 HENRIK_API_KEY，請先在 .env 填入後再跑。")
        sys.exit(1)

    headers = {"Authorization": key}
    async with aiohttp.ClientSession(headers=headers) as session:

        # v2 MMR
        url_v2 = f"{BASE}/valorant/v2/mmr/{region}/{quote(name)}/{quote(tag)}"
        section(f"v2 MMR  →  {url_v2}")
        status, body = await fetch(session, url_v2)
        print(f"HTTP {status}")
        try:
            parsed = json.loads(body)
            print(json.dumps(parsed, ensure_ascii=False, indent=2))
        except Exception:
            print(body[:2000])

        # v3 MMR（Henrik 新版）
        url_v3 = f"{BASE}/valorant/v3/mmr/{region}/{quote(name)}/{quote(tag)}"
        section(f"v3 MMR  →  {url_v3}")
        status, body = await fetch(session, url_v3)
        print(f"HTTP {status}")
        try:
            parsed = json.loads(body)
            print(json.dumps(parsed, ensure_ascii=False, indent=2))
        except Exception:
            print(body[:2000])

        # v1 account（確認帳號存在）
        url_acc = f"{BASE}/valorant/v1/account/{quote(name)}/{quote(tag)}"
        section(f"v1 account  →  {url_acc}")
        status, body = await fetch(session, url_acc)
        print(f"HTTP {status}")
        try:
            parsed = json.loads(body)
            print(json.dumps(parsed, ensure_ascii=False, indent=2))
        except Exception:
            print(body[:2000])


if __name__ == "__main__":
    asyncio.run(main())
