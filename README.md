# Natsume-Registry

NatsumeQuizMaster 的插件登记表。客户端定时拉 `registry.json`，里面是过了校验的插件。

## 结构

- `plugins/<id>.json` —— 一个插件一个文件，作者在 PR 里加
- `scripts/validate_pr.py` —— PR 校验
- `scripts/build_registry.py` —— 把 `plugins/*.json` 合成 `registry.json`
- `.github/workflows/verify-plugin.yml` —— 校验通过后自动 squash merge
- `.github/workflows/build-registry.yml` —— main 上 `plugins/` 变了就重建 `registry.json`

## 客户端读哪个

https://raw.githubusercontent.com/Lamitis/Natsume-Registry/main/registry.json

## 提交插件

1. fork 本仓库，新建 `plugins/<id>.json`
2. 本地算哈希：`sha256sum your-plugin.zip`
3. 提 PR，校验过了会自己合并

字段（必填 7 个，一个不多一个不少）：

```json
{
  "id": "weekly-stats",
  "name": "每周统计",
  "author": "someone",
  "version": "1.0.0",
  "description": "一句话说明，240 字以内",
  "download_url": "https://github.com/someone/x/releases/download/v1.0.0/weekly-stats.zip",
  "sha256": "64 位小写十六进制"
}
```

可选字段（v1.36 起客户端支持，写了就要合法；不写就是默认值）：

| 字段 | 作用 | 限制 |
| --- | --- | --- |
| `category` | 插件市场的分类（不写/空 → 显示「未分类」；市场里的分类筛选栏由数据自动生成，不需要在客户端配置） | ≤ 24 字 |
| `tags` | 搜索与卡片标签 | ≤ 6 个、每个 ≤ 16 字 |
| `permissions` | 安装确认页展示的能力声明 | ≤ 12 条、每条 ≤ 32 字 |
| `repo_url` / `changelog_url` | 详情页「看仓库 / 更新日志」 | https，域名限 github.com / gitee.com / gitlab.com |

```json
{
  "id": "weekly-stats",
  "name": "每周统计",
  "author": "someone",
  "version": "1.0.0",
  "description": "一句话说明，240 字以内",
  "download_url": "https://github.com/someone/x/releases/download/v1.0.0/weekly-stats.zip",
  "sha256": "64 位小写十六进制",
  "category": "学习辅助",
  "tags": ["统计", "周报"]
}
```

## 校验什么

- JSON 合法、必填字段齐全、没有多余字段（可选字段见上表，写了要合法）
- id 只用小写字母数字和 `._-`，且和文件名一致；version 写成 `1.2.3`
- `download_url` 必须是 https，域名在 `scripts/validate_pr.py` 的 `ALLOWED_HOSTS` 里
- 真的把文件下载下来算 sha256，跟清单里的比对
- 描述里不能出现 keylogger / ransomware 这类词
- 一次 PR 只允许动一个 `plugins/*.json`，改别的文件直接拒

## 风险声明
- 校验只证明「这个链接现在发出的确实是这个哈希」，不证明插件本身安全。

## 免责声明

本表只登记插件信息，不审核、不托管插件文件，也不保证插件安全；校验只证明链接与哈希一致，不证明代码安全。装与不装、装哪个，判断在你自己。完整条款见 [DISCLAIMER.md](DISCLAIMER.md)。`registry.json` 里的 `disclaimer` 字段是同一句话，客户端应该把它显示在插件列表旁边。
