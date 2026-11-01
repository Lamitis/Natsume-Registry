#!/usr/bin/env python3
"""把 plugins/*.json 合成客户端读的 registry.json。"""
import json
from datetime import datetime, timezone
from pathlib import Path

FIELDS = ("id", "name", "author", "version", "description", "download_url", "sha256")

# 可选字段（v1.36 起客户端支持）：有值就带上，没写/空值就不出现在 registry.json 里，
# 免得客户端看到一个空分类被归进「未分类」之外的空桶。
OPTIONAL_FIELDS = ("category", "tags", "permissions", "repo_url", "changelog_url")
DISCLAIMER = (
    "本表只登记插件信息，不审核、不托管插件文件，也不保证插件安全。"
    "插件由各自作者开发和发布，安装与使用风险自负。"
    "详见 https://github.com/Lamitis/Natsume-Registry/blob/main/DISCLAIMER.md"
)


def main():
    items = []
    for path in sorted(Path("plugins").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        item = {k: data[k] for k in FIELDS}
        for key in OPTIONAL_FIELDS:
            value = data.get(key)
            if value:  # None / "" / [] 都不写进表
                item[key] = value
        items.append(item)
    items.sort(key=lambda x: x["id"].lower())
    out = {
        "schema": 1,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "count": len(items),
        "disclaimer": DISCLAIMER,
        "plugins": items,
    }
    Path("registry.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(str(len(items)) + " plugins")


if __name__ == "__main__":
    main()