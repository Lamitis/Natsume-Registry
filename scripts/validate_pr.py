#!/usr/bin/env python3
"""校验一个 PR 新增的插件清单：只读 JSON、只下载链接算哈希，不执行 PR 里的任何代码。"""
import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ALLOWED_HOSTS = {
    "github.com",
    "objects.githubusercontent.com",
    "release-assets.githubusercontent.com",
    "raw.githubusercontent.com",
    "codeload.github.com",
}
ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,63}$")
VER_RE = re.compile(r"^\d+\.\d+\.\d+([-+][0-9A-Za-z.-]+)?$")
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
BLOCK_WORDS = ("keylogger", "ransomware", "token-grabber", "stealer", "cryptominer")
MAX_BYTES = 32 * 1024 * 1024
REQUIRED = ("id", "name", "author", "version", "description", "download_url", "sha256")


def fail(msg):
    print("::error::" + msg)
    raise SystemExit(1)


def check_remote(url, expected):
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != "https":
        fail("下载链接必须是 https")
    if parts.hostname not in ALLOWED_HOSTS:
        fail("下载链接的域名不在白名单里：" + str(parts.hostname))
    req = urllib.request.Request(url, headers={"User-Agent": "natsume-registry"})
    digest = hashlib.sha256()
    total = 0
    with urllib.request.urlopen(req, timeout=30) as resp:
        while True:
            chunk = resp.read(65536)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_BYTES:
                fail("插件包超过 32 MB")
            digest.update(chunk)
    if digest.hexdigest() != expected:
        fail("sha256 对不上：链接里算出来是 " + digest.hexdigest() + "，清单里写的是 " + expected)


def main(argv):
    if len(argv) != 3:
        fail("用法：validate_pr.py <changed-files.txt> <pr-checkout>")
    changed = [l.strip() for l in Path(argv[1]).read_text(encoding="utf-8").splitlines() if l.strip()]
    if not changed:
        fail("这个 PR 没有改动任何文件")
    if len(changed) != 1:
        fail("一次 PR 只提交一个插件，这次改了：" + ", ".join(changed))
    rel = changed[0]
    if not re.fullmatch(r"plugins/[a-z0-9][a-z0-9._-]{2,63}\.json", rel):
        fail("只接受 plugins/<id>.json 这种路径：" + rel)
    path = Path(argv[2]) / rel
    if not path.is_file():
        fail("找不到文件：" + rel)
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        fail("不是合法 JSON：" + str(exc))
    if not isinstance(data, dict):
        fail("顶层必须是对象")
    missing = [k for k in REQUIRED if not data.get(k)]
    if missing:
        fail("缺少字段：" + ", ".join(missing))
    extra = sorted(set(data) - set(REQUIRED))
    if extra:
        fail("不认识的字段：" + ", ".join(extra))
    if not ID_RE.fullmatch(data["id"]):
        fail("id 只能用小写字母、数字、点、下划线和短横线，3-64 个字符")
    if Path(rel).stem != data["id"]:
        fail("文件名要和 id 一致")
    if not VER_RE.fullmatch(data["version"]):
        fail("version 要写成 1.2.3 这样")
    sha = str(data["sha256"]).lower()
    if not HASH_RE.fullmatch(sha):
        fail("sha256 要是 64 位十六进制")
    for key in ("name", "author"):
        if len(data[key]) > 60:
            fail(key + " 太长")
    if len(data["description"]) > 240:
        fail("description 太长")
    blob = " ".join(str(v) for v in data.values()).lower()
    for word in BLOCK_WORDS:
        if word in blob:
            fail("描述里出现了不该有的词：" + word)
    check_remote(data["download_url"], sha)
    print("OK " + data["id"] + " " + data["version"])


if __name__ == "__main__":
    main(sys.argv)