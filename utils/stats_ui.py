import discord

VALORANT_RED = 0xFF4655


def build_stats_embed(name: str, tag: str, agg: dict) -> discord.Embed:
    embed = discord.Embed(
        title=f"{name}#{tag} ・ 近 {agg.get('games', 0)} 場（競技）",
        color=VALORANT_RED,
    )
    record = f"{agg['wins']} 勝 {agg['losses']} 敗"
    if agg.get("draws"):
        record += f" {agg['draws']} 平"

    embed.add_field(name="戰績", value=f"**{record}**", inline=True)
    embed.add_field(name="勝率", value=f"**{agg['winrate']:.0f}%**", inline=True)
    embed.add_field(name="KDA", value=f"**{agg['kda']:.2f}**", inline=True)
    embed.add_field(name="暴頭率", value=f"**{agg['hs']:.0f}%**", inline=True)
    embed.add_field(name="ACS", value=f"**{agg['acs']:.0f}**", inline=True)
    embed.add_field(name="ADR", value=f"**{agg['adr']:.0f}**", inline=True)

    embed.set_image(url="attachment://stats.png")
    return embed


def compute_match(m: dict) -> dict:
    st = m.get("stats") or {}
    teams = m.get("teams") or {}
    meta = m.get("meta") or {}

    k = st.get("kills") or 0
    d = st.get("deaths") or 0
    a = st.get("assists") or 0

    shots = st.get("shots") or {}
    head = shots.get("head") or 0
    body = shots.get("body") or 0
    leg = shots.get("leg") or 0
    total_shots = head + body + leg
    hs = head / total_shots * 100 if total_shots else 0

    score = st.get("score") or 0
    dmg = (st.get("damage") or {}).get("made") or 0

    red = teams.get("red") or 0
    blue = teams.get("blue") or 0
    rounds = red + blue
    acs = score / rounds if rounds else 0
    adr = dmg / rounds if rounds else 0

    team = (st.get("team") or "").lower()
    mine = red if team == "red" else blue
    opp = blue if team == "red" else red
    if mine > opp:
        result = "win"
    elif mine < opp:
        result = "loss"
    else:
        result = "draw"

    return {
        "match_id": meta.get("id", ""),
        "map": (meta.get("map") or {}).get("name", "—"),
        "map_id": (meta.get("map") or {}).get("id", ""),
        "agent": (st.get("character") or {}).get("name", "—"),
        "agent_id": (st.get("character") or {}).get("id", ""),
        "k": k, "d": d, "a": a,
        "hs": hs, "acs": acs, "adr": adr,
        "result": result,
        "mine": mine, "opp": opp,
        "score_line": f"{mine}-{opp}",
        "started_at": meta.get("started_at", ""),
        "rr": None,
    }


def aggregate(rows: list[dict]) -> dict:
    n = len(rows)
    if n == 0:
        return {}
    sk = sum(r["k"] for r in rows)
    sd = sum(r["d"] for r in rows)
    sa = sum(r["a"] for r in rows)
    wins = sum(1 for r in rows if r["result"] == "win")
    losses = sum(1 for r in rows if r["result"] == "loss")
    draws = sum(1 for r in rows if r["result"] == "draw")
    return {
        "games": n,
        "wins": wins, "losses": losses, "draws": draws,
        "winrate": wins / n * 100,
        "avg_k": sk / n, "avg_d": sd / n, "avg_a": sa / n,
        "kda": (sk + sa) / sd if sd else (sk + sa),
        "hs": sum(r["hs"] for r in rows) / n,
        "acs": sum(r["acs"] for r in rows) / n,
        "adr": sum(r["adr"] for r in rows) / n,
    }
