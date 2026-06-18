# Surge Rules

游戏平台域名规则集，适用于 Surge / Clash / sing-box 等代理客户端。

## 📦 规则列表

| 平台 | 文件 | 域名数 | 说明 |
|------|------|--------|------|
| **Game (合集)** | `rules/Game.list` | 749 | 全平台合并，一条搞定 |
| Nintendo | `rules/nintendo.list` | 130 | Switch / Pokemon / 3DS |
| EA | `rules/ea.list` | 165 | Origin / Apex / Battlefield / FIFA / Sims |
| Sony | `rules/sony.list` | 115 | PlayStation / PSN |
| Riot | `rules/riot.list` | 54 | LoL / Valorant / TFT |
| Steam | `rules/steam.list` | 58 | Steam / Valve / Dota 2 / Steam Deck |
| Xbox | `rules/xbox.list` | 45 | Xbox / Game Pass / Minecraft |
| Epic | `rules/epicgames.list` | 32 | Epic Games / Fortnite / Unreal |
| Ubisoft | `rules/ubisoft.list` | 32 | Ubisoft / Uplay / Ubisoft Connect |
| Blizzard | `rules/blizzard.list` | 25 | Battle.net / WoW / OW / Diablo |
| miHoYo | `rules/mihoyo.list` | 26 | 原神 / 崩坏3 / 星穹铁道 |
| Supercell | `rules/supercell.list` | 23 | CoC / Brawl Stars / CR |
| Garena | `rules/garena.list` | 16 | Free Fire / RoV |
| Wargaming | `rules/wargaming.list` | 11 | WoT / WoWS / WoWP |
| HoYoverse | `rules/hoyoverse.list` | 9 | Genshin Global / ZZZ |
| NEXON | `rules/nexon.list` | 6 | MapleStory / KartRider |
| Rockstar | `rules/rockstar.list` | 6 | GTA Online / RDR2 |
| Cygames | `rules/cygames.list` | 5 | Granblue / Uma Musume |

## 🔗 引用方式

### 全平台合集（推荐）

```
# Surge RULE-SET
RULE-SET,https://raw.githubusercontent.com/keleyaa/surge-rules/main/rules/Game.list,Proxy

# Clash
rule-providers:
  game:
    type: http
    behavior: domain
    url: https://raw.githubusercontent.com/keleyaa/surge-rules/main/rules/Game.list
    interval: 86400
```

### 单平台

```
RULE-SET,https://raw.githubusercontent.com/keleyaa/surge-rules/main/rules/nintendo.list,Proxy
RULE-SET,https://raw.githubusercontent.com/keleyaa/surge-rules/main/rules/steam.list,Proxy
```

## 🔄 自动更新

规则文件 **每天自动更新**（北京时间 05:00），通过 GitHub Actions 从上游数据源采集。

上游源：
- [v2fly/domain-list-community](https://github.com/v2fly/domain-list-community) — 社区维护的域名列表（主源）
- [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script) — 每日编译规则（备用）

### 手动触发

在 Actions 页面点击 "Run workflow" 即可手动触发更新。

## 📋 数据源说明

v2fly 数据支持 `include:` 递归展开，确保子品牌/子公司的域名也被完整收录（如 mihoyo → hoyoverse + mihoyo-cn，ea → origin，xbox → bethesda + mojang 等）。

## ⚠️ 注意事项

- `DOMAIN-SUFFIX,nintendo.com` 会匹配 `*.nintendo.com` 所有子域名
- 同一域名可能出现在多个平台文件中，Game.list 已自动去重
- 如发现遗漏域名，可提 Issue 或直接修改 `scripts/update.py` 中的 `MANUAL_EXTRAS`
