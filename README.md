# Surge Rules

Surge 规则集，用于域名分流。

## 规则列表

| 规则 | 文件 | 格式 | 说明 |
|------|------|------|------|
| Nintendo Switch | `nintendo.list` | RULE-SET | 联机 / eShop / 系统更新 / NSO / 云存档 |

## 引用方式

### RULE-SET（推荐）

在 Surge 配置中添加：

```
RULE-SET,https://raw.githubusercontent.com/keleyaa/surge-rules/main/nintendo.list,Proxy
```

将 `Proxy` 替换为你的实际策略组名称。

### DOMAIN-SET

如果偏好 DOMAIN-SET 格式（更高效），使用 `nintendo-domain-set` 文件：

```
DOMAIN-SET,https://raw.githubusercontent.com/keleyaa/surge-rules/main/nintendo-domain-set,Proxy
```

## Nintendo Switch 规则说明

覆盖 Nintendo Switch 所有核心服务域名：

- **eShop** — 商店浏览、游戏购买与下载
- **NSO** — Nintendo Switch Online 联机服务
- **CDN** — 游戏更新、系统更新下载
- **云存档** — Cloud Saves (S3)
- **认证** — 账户登录、设备认证 (dauth/aauth)
- **新闻** — News 推送、BCAT 数据
- **家长控制** — Parental Controls
- **第三方手游** — Mario Kart Tour、Super Mario Run

来源：[switchbrew.org](https://switchbrew.org/wiki/Network)、[NintendoClients wiki](https://github.com/kinnay/NintendoClients/wiki)、[nh-server](https://github.com/nh-server/switch-guide)、[netify.ai](https://www.netify.ai)、[hagezi](https://github.com/hagezi/dns-blocklists)

## 更新频率

不定期更新，如有新域名或变更欢迎提 Issue / PR。
