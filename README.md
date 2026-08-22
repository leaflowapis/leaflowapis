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

## 同步到 Apifox

合并到 `main` 后，GitHub Actions 会把每个服务的 `openapi.yaml` 导入对应的 Apifox 项目。目标项目不存在时会自动创建，也可以在 Actions 页面手动运行 `sync-to-apifox`。

在 GitHub 仓库或 Organization 中配置：

- Secret `APIFOX_ACCESS_TOKEN`：在 Apifox 的「账号设置 → API 访问令牌」中创建。令牌需要能够编辑目标项目。
- Variable `APIFOX_TEAM_ID`：创建项目所使用的 Apifox Team ID。

项目名取自契约的 `info.title`。工作流会先在指定团队中按完整名称查找；不存在则创建，存在则复用。同名项目超过一个时工作流会停止，避免把契约导入错误的项目。项目创建后应保持 `info.title` 稳定；如果需要重命名，应同时重命名 Apifox 项目。

工作流会在 GitHub Runner 中把每份契约及其 `$ref` 合并为单文件，再通过 Apifox 开放 API 导入；因此公开和私有仓库都可以使用，也不需要开启 Apifox 的「外部 AI 编辑权限」。导入会创建新接口并覆盖同名接口和数据模型，但不会主动删除只存在于 Apifox 中的接口。应把 `APIFOX_ACCESS_TOKEN` 作为高权限凭证管理，并限制仓库 Actions 与 Secret 的管理权限。

新增 `leaflow/<服务>/<版本>/openapi.yaml` 后不需要另外配置 Project ID。
