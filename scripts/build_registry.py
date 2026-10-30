#!/usr/bin/env python3
"""把 plugins/*.json 合成客户端读的 registry.json。"""
import json
from datetime import datetime, timezone
from pathlib import Path

FIELDS = ("id", "name", "author", "version", "description", "download_url", "sha256")
DISCLAIMER = (
    "本表只登记插件信息，不审核、不托管插件文件，也不保证插件安全。"
    "插件由各自作者开发和发布，安装与使用风险自负。"
    "详见 https://github.com/Lamitis/Natsume-Registry/blob/main/DISCLAIMER.md"
)


def main():
    items = []
    for path in sorted(Path("plugins").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        items.append({k: data[k] for k in FIELDS})
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