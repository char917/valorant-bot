# Valorant Discord Bot

這是一個用 `discord.py` 製作的 Valorant Discord Bot，可以透過 Slash Command 查詢玩家段位、賽季紀錄，以及近期競技對戰統計。資料來源使用 Henrik API，牌位素材與地圖名稱來自 valorant-api。

## 功能

- `/ping`：確認 Bot 是否正常在線，並回傳延遲。
- `/setregion`：設定目前 Discord 伺服器預設 Valorant 區域。
- `/rank RiotID#Tag`：查詢目前段位、RR、歷史最高段位與各賽季 Act Rank。
- `/stats RiotID#Tag`：查詢最近 15 場競技對戰，顯示勝率、KDA、爆頭率、ACS、ADR 與 RR 變化。

## 畫面預覽

### 段位總覽

![rank 生涯總覽](docs/images/rank-overview.png)

### 近期戰績

![stats 近期戰績](docs/images/stats-overview.png)

### 賽季紀錄

![rank 賽季紀錄](docs/images/rank-season.png)

## 安裝

建議使用 Python 3.11 以上版本。

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

macOS / Linux 可以改用：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## 環境變數

編輯 `.env`，填入以下設定：

```env
DISCORD_TOKEN=your_discord_bot_token
HENRIK_API_KEY=your_henrik_api_key
GUILD_ID=
```

`GUILD_ID` 可選填。開發時建議填入測試伺服器 ID，Slash Command 會同步到指定伺服器並較快生效；留空時會使用全域同步，可能需要等待一段時間才會出現在 Discord。

## 取得 Discord Bot Token

1. 前往 [Discord Developer Portal](https://discord.com/developers/applications)。
2. 建立或選擇一個 Application。
3. 到 `Bot` 頁面建立 Bot，複製 Token 後填入 `.env` 的 `DISCORD_TOKEN`。
4. 到 `OAuth2 > URL Generator` 產生邀請連結。
5. Scopes 勾選 `bot` 與 `applications.commands`。
6. 將 Bot 邀請到你的 Discord 伺服器。

這個 Bot 使用 Slash Command，不需要開啟 Message Content Intent。

## 取得 Henrik API Key

前往 [Henrik API Docs](https://docs.henrikdev.xyz/) 依照文件申請 API Key，並填入 `.env` 的 `HENRIK_API_KEY`。

## 啟動

```bash
python bot.py
```

啟動成功後，終端機會顯示 Bot 已登入，以及 Slash Command 同步結果。

## 指令說明

### `/setregion`

設定伺服器預設查詢區域，只有具備管理伺服器權限的成員可以使用。

支援區域：

- `ap`
- `na`
- `eu`
- `kr`
- `latam`
- `br`

設定後，`/rank` 和 `/stats` 會直接使用這個區域，不需要每次查詢都重新選擇。

### `/rank`

查詢指定 RiotID 的段位資訊。

```text
/rank Ka1Ø#sabar
```

會顯示：

- 目前段位與 RR
- 歷史最高段位
- 賽季紀錄選單
- Act Rank 金字塔圖片

### `/stats`

查詢指定 RiotID 的近期競技戰績。

```text
/stats Ka1Ø#sabar
```

會顯示：

- 最近 15 場競技戰績
- 勝敗、勝率、KDA
- 爆頭率、ACS、ADR
- 每場地圖、角色、比分與 RR 變化

## Henrik API 測試工具

提供了一個簡單腳本，可以用來確認 Henrik API 是否正常回傳資料。

```bash
python scripts/check_henrik.py RiotID#Tag [區域]
```

範例：

```bash
python scripts/check_henrik.py Charlie#1234 ap
```

## 專案結構

```text
valorant-bot/
├── bot.py
├── cogs/
│   ├── rank.py
│   ├── region.py
│   └── stats.py
├── services/
│   └── henrik_api.py
├── scripts/
│   └── check_henrik.py
└── utils/
    ├── assets.py
    ├── constants.py
    ├── pyramid.py
    ├── rank_ui.py
    ├── settings.py
    ├── stats_card.py
    └── stats_ui.py
```

## 備註

- 伺服器區域設定會儲存在 `data/guild_settings.json`，該資料夾已加入 `.gitignore`。
- 下載過的 Valorant 素材會快取在 `.asset_cache/`，避免重複請求。
- 若查不到玩家資料，請確認 RiotID、Tag 和伺服器區域是否正確。
