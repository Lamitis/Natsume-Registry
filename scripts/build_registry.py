#!/usr/bin/env python3
"""把 plugins/*.json 合成客户端读的 registry.json。"""
import json
from datetime import datetime, timezone
from pathlib import Path

FIELDS = ("id", "name", "author", "version", "description", "download_url", "sha256")


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
        "plugins": items,
    }
    Path("registry.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(str(len(items)) + " plugins")


if __name__ == "__main__":
    main()