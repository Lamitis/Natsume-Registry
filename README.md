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

字段（一个不多一个不少）：

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

## 校验什么

- JSON 合法、必填字段齐全、没有多余字段
- id 只用小写字母数字和 `._-`，且和文件名一致；version 写成 `1.2.3`
- `download_url` 必须是 https，域名在 `scripts/validate_pr.py` 的 `ALLOWED_HOSTS` 里
- 真的把文件下载下来算 sha256，跟清单里的比对
- 描述里不能出现 keylogger / ransomware 这类词
- 一次 PR 只允许动一个 `plugins/*.json`，改别的文件直接拒

## 这个方案的风险

- 校验只证明「这个链接现在发出的确实是这个哈希」，不证明插件本身安全。插件在客户端里跑起来能干什么，没有人审。
- 所以客户端不能默认自动安装或者静默升级，至少得让用户自己点一下。
- 想更稳就把 `ALLOWED_HOSTS` 收紧，只留作者自己仓库的下载域名。