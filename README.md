# leaflowapis

Leaflow 平台公开接口的契约。

```
leaflow/<服务>/<版本>/
```

`leaflow/` 是命名空间层,与 googleapis 的 `google/` 对应。

## SDK

由本仓库生成,分语言维护。

| 语言 | 安装 | 仓库 |
| --- | --- | --- |
| Go | `go get github.com/leaflowapis/leaflow-go/<服务>` | [leaflow-go](https://github.com/leaflowapis/leaflow-go) |
| TypeScript | `npm i @leaflow/sdk` | [leaflow-ts](https://github.com/leaflowapis/leaflow-ts) |

## 服务

| 服务 | 说明 |
| --- | --- |
| `account` | 账号、协议、实名、项目令牌 |
| `iam` | 项目内的成员、角色、邀请、SSH 密钥 |
| `compute` | 云服务器、云硬盘、镜像、网络、公网 IP |
| `monitoring` | 主机监控、告警、可用性检查、SLO |
| `canopy` | 模型网关的密钥与用量 |
| `assistant` | 对话与工具调用 |
| `tunnel` | 隧道与订阅 |
| `dns` | 多云 DNS 凭据、域名与解析记录 |
