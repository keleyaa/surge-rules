#!/usr/bin/env python3
"""
Surge Rules 自动更新脚本
从上游数据源采集游戏平台域名，生成 Surge 规则文件

上游源:
  - v2fly/domain-list-community  (社区维护的域名列表)
  - blackmatrix7/ios_rule_script (每日更新的编译规则)

用法:
  python3 scripts/update.py          # 更新所有规则
  python3 scripts/update.py --dry-run # 仅检查，不写入文件
"""

import urllib.request
import json
import os
import sys
import re
from datetime import datetime, timezone
from collections import OrderedDict

# ============================================================
# 配置
# ============================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
RULES_DIR = os.path.join(REPO_ROOT, "rules")

# v2fly 上游: 每个文件是纯域名列表（无前缀）
V2FLY_BASE = "https://raw.githubusercontent.com/v2fly/domain-list-community/master/data"
V2FLY_SOURCES = {
    "nintendo":    {"file": "nintendo",    "desc": "Nintendo Switch / Pokemon / 3DS"},
    "steam":       {"file": "steam",       "desc": "Steam / Valve / Dota 2 / Steam Deck"},
    "epicgames":   {"file": "epicgames",   "desc": "Epic Games Store / Fortnite / Unreal Engine"},
    "blizzard":    {"file": "blizzard",    "desc": "Battle.net / WoW / OW / Diablo / Hearthstone"},
    "riot":        {"file": "riot",        "desc": "Riot Games / LoL / Valorant / TFT"},
    "ea":          {"file": "ea",          "desc": "EA / Origin / Apex / Battlefield / FIFA / Sims"},
    "ubisoft":     {"file": "ubisoft",     "desc": "Ubisoft / Uplay / Ubisoft Connect"},
    "sony":        {"file": "sony",        "desc": "PlayStation / PSN / Sony Entertainment"},
    "xbox":        {"file": "xbox",        "desc": "Xbox / Game Pass / Xbox Live / Minecraft"},
    "supercell":   {"file": "supercell",   "desc": "Clash of Clans / Brawl Stars / Clash Royale"},
    "mihoyo":      {"file": "mihoyo",      "desc": "miHoYo / 原神 / 崩坏3 / 崩坏：星穹铁道"},
    "hoyoverse":   {"file": "hoyoverse",   "desc": "HoYoverse / Genshin Impact Global / ZZZ"},
    "rockstar":    {"file": "rockstar",    "desc": "Rockstar Games / GTA Online / RDR2"},
    "garena":      {"file": "garena",      "desc": "Garena / Free Fire / RoV"},
    "wargaming":   {"file": "wargaming",   "desc": "World of Tanks / Warships / Warplanes"},
    "cygames":     {"file": "cygames",     "desc": "Cygames / Granblue Fantasy / Uma Musume / Priconne"},
    "nexon":       {"file": "nexon",       "desc": "NEXON / MapleStory / KartRider"},
}

# blackmatrix7 上游: 编译好的 Surge DOMAIN-SUFFIX 格式
BLACKMATRIX7_BASE = "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Surge/Game"
BLACKMATRIX7_SOURCES = {
}

# 手动维护的补充域名（上游可能遗漏或不够全面）
MANUAL_EXTRAS = {
    "nintendo": [
        # Nintendo 区域 TLD（上游可能不全）
        "nintendo.at", "nintendo.be", "nintendo.ch", "nintendo.cz",
        "nintendo.de", "nintendo.dk", "nintendo.es", "nintendo.fi",
        "nintendo.fr", "nintendo.gr", "nintendo.hu", "nintendo.it",
        "nintendo.nl", "nintendo.no", "nintendo.pl", "nintendo.pt",
        "nintendo.ru", "nintendo.se", "nintendo.co.za", "nintendo.co.nz",
        "nintendods.cz",
    ],
    "epicgames": [
        "epicgames.dev",
    ],
    "blizzard": [
        "blizzardgames.cn", "blzstatic.cn",
    ],
    "riot": [
        "lolpcs.com", "lpl.com.cn",
    ],
    "ea": [
        "frostbite.com", "bioware.com", "dice.se", "maxis.com",
        "popcap.com", "pogo.com", "chillingo.com",
    ],
}


# ============================================================
# 工具函数
# ============================================================

def fetch_url(url, timeout=30):
    """下载 URL 内容，返回文本"""
    req = urllib.request.Request(url, headers={"User-Agent": "surge-rules-updater/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        print(f"  ⚠️  获取失败: {url} -> {e}")
        return None


def parse_v2fly_domains(text, follow_includes=True, _depth=0):
    """解析 v2fly domain-list-community 格式"""
    domains = []
    for line in text.splitlines():
        line = line.strip()
        # 跳过注释和空行
        if not line or line.startswith("#"):
            continue
        # 处理 include: 引用（递归展开）
        if line.startswith("include:"):
            if follow_includes and _depth < 3:
                include_name = line[8:].strip()
                include_url = f"{V2FLY_BASE}/{include_name}"
                include_text = fetch_url(include_url)
                if include_text:
                    domains.extend(parse_v2fly_domains(include_text, follow_includes, _depth + 1))
            continue
        # 处理 full: 前缀（精确匹配）
        if line.startswith("full:"):
            domains.append(("DOMAIN", line[5:].split("@")[0].strip()))
            continue
        # 跳过 regexp: 正则 (Surge RULE-SET 不支持 DOMAIN-REGEX)
        if line.startswith("regexp:"):
            continue
        # 处理 @cn 等属性标记（忽略属性，只要域名）
        domain = line.split("@")[0].strip()
        if domain:
            domains.append(("DOMAIN-SUFFIX", domain))
    return domains


def parse_blackmatrix7_domains(text):
    """解析 blackmatrix7 Surge .list 格式 (DOMAIN-SUFFIX,domain)"""
    domains = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(",")
        if len(parts) >= 2:
            rule_type = parts[0].strip()
            domain = parts[1].strip()
            domains.append((rule_type, domain))
    return domains


def domain_to_surge_line(rule_type, domain):
    """生成 Surge 规则行"""
    return f"{rule_type},{domain}"


def generate_file_header(name, desc, sources, count):
    """生成文件头部注释"""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# {name} — {desc}",
        f"# 自动生成于 {now}",
        f"# 域名数: {count}",
        f"# 上游源:",
    ]
    for s in sources:
        lines.append(f"#   - {s}")
    lines.append(f"#")
    lines.append(f"# 用法: RULE-SET,<URL>,Proxy")
    lines.append("")
    return "\n".join(lines)


# ============================================================
# 主逻辑
# ============================================================

def update_platform(name, config, dry_run=False):
    """更新单个平台的规则"""
    print(f"\n📦 {name}: {config['desc']}")

    all_domains = OrderedDict()  # (type, domain) -> True, 保序去重

    # 1. 从 v2fly 获取
    if "v2fly" in config:
        url = f"{V2FLY_BASE}/{config['v2fly']}"
        print(f"  📥 v2fly: {url}")
        text = fetch_url(url)
        if text:
            for rtype, domain in parse_v2fly_domains(text):
                all_domains[(rtype, domain)] = True
            print(f"     获取 {len(all_domains)} 条")

    # 2. 从 blackmatrix7 获取
    if "blackmatrix7" in config:
        url = f"{BLACKMATRIX7_BASE}/{config['blackmatrix7']}"
        print(f"  📥 blackmatrix7: {url}")
        text = fetch_url(url)
        if text:
            before = len(all_domains)
            for rtype, domain in parse_blackmatrix7_domains(text):
                all_domains[(rtype, domain)] = True
            print(f"     获取 {len(all_domains) - before} 条 (累计 {len(all_domains)})")

    # 3. 添加手动补充
    if name in MANUAL_EXTRAS:
        before = len(all_domains)
        for domain in MANUAL_EXTRAS[name]:
            all_domains[("DOMAIN-SUFFIX", domain)] = True
        added = len(all_domains) - before
        if added:
            print(f"  ➕ 手动补充 {added} 条")

    if not all_domains:
        print(f"  ❌ 无数据，跳过")
        return None

    # 4. 生成 .list 文件
    sources = []
    if "v2fly" in config:
        sources.append(f"v2fly/domain-list-community/data/{config['v2fly']}")
    if "blackmatrix7" in config:
        sources.append(f"blackmatrix7/ios_rule_script/{config['blackmatrix7']}")
    if name in MANUAL_EXTRAS:
        sources.append("手动维护补充")

    header = generate_file_header(name, config["desc"], sources, len(all_domains))
    body = "\n".join(domain_to_surge_line(rtype, d) for rtype, d in all_domains.keys())
    content = header + body + "\n"

    output_path = os.path.join(RULES_DIR, f"{name}.list")
    if dry_run:
        print(f"  🔍 [dry-run] 将写入 {output_path} ({len(all_domains)} 条)")
    else:
        os.makedirs(RULES_DIR, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(content)
        print(f"  ✅ 写入 {output_path} ({len(all_domains)} 条)")

    return len(all_domains)


def generate_combined_list(platform_stats, dry_run=False):
    """生成合并的 Game.list"""
    print(f"\n📦 生成合并 Game.list ...")

    all_lines = []
    all_count = 0

    for name in sorted(platform_stats.keys()):
        if platform_stats[name] is None:
            continue
        filepath = os.path.join(RULES_DIR, f"{name}.list")
        if not os.path.exists(filepath):
            continue
        with open(filepath) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                all_lines.append(line)
        all_count += 1

    # 去重但保序
    seen = set()
    unique_lines = []
    for line in all_lines:
        if line not in seen:
            seen.add(line)
            unique_lines.append(line)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    header = "\n".join([
        f"# Game — 全平台游戏规则合集",
        f"# 自动生成于 {now}",
        f"# 包含 {all_count} 个平台, {len(unique_lines)} 条规则",
        f"# 由各平台独立规则文件合并而来",
        f"#",
        f"# 用法: RULE-SET,<URL>,Proxy",
        "",
    ])

    content = header + "\n".join(unique_lines) + "\n"

    output_path = os.path.join(RULES_DIR, "Game.list")
    if dry_run:
        print(f"  🔍 [dry-run] 将写入 {output_path} ({len(unique_lines)} 条)")
    else:
        with open(output_path, "w") as f:
            f.write(content)
        print(f"  ✅ 写入 {output_path} ({len(unique_lines)} 条)")

    return len(unique_lines)


def main():
    dry_run = "--dry-run" in sys.argv

    print("=" * 60)
    print("🎮 Surge Rules 自动更新")
    print(f"   时间: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    if dry_run:
        print("   模式: dry-run (不写入文件)")
    print("=" * 60)

    # 合并所有数据源配置
    platforms = {}
    for name, cfg in V2FLY_SOURCES.items():
        platforms[name] = {"desc": cfg["desc"], "v2fly": cfg["file"]}
    for name, cfg in BLACKMATRIX7_SOURCES.items():
        if name in platforms:
            platforms[name]["blackmatrix7"] = cfg["file"]
        else:
            platforms[name] = {"desc": cfg["desc"], "blackmatrix7": cfg["file"]}

    # 逐平台更新
    stats = {}
    for name in sorted(platforms.keys()):
        stats[name] = update_platform(name, platforms[name], dry_run)

    # 生成合并列表
    total = generate_combined_list(stats, dry_run)

    # 汇总
    print("\n" + "=" * 60)
    print("📊 更新汇总:")
    success = 0
    for name, count in sorted(stats.items()):
        if count is not None:
            print(f"   ✅ {name}: {count} 条")
            success += 1
        else:
            print(f"   ❌ {name}: 失败")
    print(f"   合并 Game.list: {total} 条")
    print(f"   成功: {success}/{len(stats)}")
    print("=" * 60)

    return 0 if success > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
