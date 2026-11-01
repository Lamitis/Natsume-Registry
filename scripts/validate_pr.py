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
# 展示型链接（仓库 / 更新日志）允许的域名，与客户端 RegistryPlugin.allowedLinkHosts 一致
ALLOWED_LINK_HOSTS = {"github.com", "gitee.com", "gitlab.com"}
ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,63}$")
VER_RE = re.compile(r"^\d+\.\d+\.\d+([-+][0-9A-Za-z.-]+)?$")
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
BLOCK_WORDS = ("keylogger", "ransomware", "token-grabber", "stealer", "cryptominer")
MAX_BYTES = 32 * 1024 * 1024
REQUIRED = ("id", "name", "author", "version", "description", "download_url", "sha256")

# v1.36 起客户端支持的可选字段（RegistryPlugin.optionalFieldNames）。
# 缺省合法；一旦写了就要合法——这里比客户端严一档：客户端会静默忽略坏值，
# 但 PR 阶段应该直接告诉作者哪里不对，否则他永远不知道为什么分类没显示。
OPTIONAL = ("category", "tags", "permissions", "repo_url", "changelog_url")
MAX_CATEGORY_CHARS = 24  # 客户端 RegistryPlugin.maxCategoryChars
MAX_TAGS, MAX_TAG_CHARS = 6, 16  # 客户端 maxTags / maxTagChars
MAX_PERMISSIONS, MAX_PERMISSION_CHARS = 12, 32  # 客户端 maxPermissions / maxPermissionChars



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


def check_optional(data):
    """可选字段（分类 / 标签 / 能力 / 链接）：可以不写，写了就得合法。"""
    category = data.get("category")
    if category is not None:
        if not isinstance(category, str) or not category.strip():
            fail("category 必须是非空字符串")
        if len(category.strip()) > MAX_CATEGORY_CHARS:
            fail("category 太长（上限 %d 字）" % MAX_CATEGORY_CHARS)

    tags = data.get("tags")
    if tags is not None:
        if not isinstance(tags, list):
            fail("tags 必须是字符串数组")
        if len(tags) > MAX_TAGS:
            fail("tags 最多 %d 个" % MAX_TAGS)
        for tag in tags:
            if not isinstance(tag, str) or not tag.strip():
                fail("tags 里有空项或非字符串")
            if len(tag.strip()) > MAX_TAG_CHARS:
                fail("tag 太长：%s（上限 %d 字）" % (tag, MAX_TAG_CHARS))

    permissions = data.get("permissions")
    if permissions is not None:
        if not isinstance(permissions, list):
            fail("permissions 必须是字符串数组")
        if len(permissions) > MAX_PERMISSIONS:
            fail("permissions 最多 %d 条" % MAX_PERMISSIONS)
        for perm in permissions:
            if not isinstance(perm, str) or not perm.strip():
                fail("permissions 里有空项或非字符串")
            if len(perm.strip()) > MAX_PERMISSION_CHARS:
                fail("permission 太长：%s（上限 %d 字）" % (perm, MAX_PERMISSION_CHARS))

    for key in ("repo_url", "changelog_url"):
        link = data.get(key)
        if link is None:
            continue
        if not isinstance(link, str):
            fail(key + " 必须是字符串")
        parts = urllib.parse.urlsplit(link.strip())
        if parts.scheme != "https":
            fail(key + " 必须是 https 链接")
        if parts.hostname not in ALLOWED_LINK_HOSTS:
            fail(key + " 的域名不在白名单里：" + str(parts.hostname))
        if not parts.path or parts.path == "/":
            fail(key + " 缺少路径：" + link)


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
    extra = sorted(set(data) - set(REQUIRED) - set(OPTIONAL))
    if extra:
        fail("不认识的字段：" + ", ".join(extra))
    check_optional(data)
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