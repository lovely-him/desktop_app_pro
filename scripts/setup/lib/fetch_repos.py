#!/usr/bin/env python3
"""按 repos.json 拉取第三方库，并写出依赖状态快照。

由 scripts/setup/setup.sh 调用，不单独作为入口使用。
只依赖 Python 标准库。
"""

import json
import os
import subprocess
import sys

# ── 路径与常量 ────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # scripts/setup/lib
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))

CONFIG_PATH = os.path.join(ROOT_DIR, "repos.json")
STATE_PATH = os.path.join(ROOT_DIR, "dependencies", ".state.json")

# ── 函数 ─────────────────────────────────────────────────────


def head_commit(path):
    """返回仓库当前 HEAD 的 commit；不是 git 仓库则返回 None。"""
    try:
        out = subprocess.run(
            ["git", "-C", path, "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        return None
    return out.stdout.strip()


def sync_repo(repo):
    """把单个仓库同步到目标 commit，返回 (动作, 实际 commit)。"""
    path = os.path.join(ROOT_DIR, repo["path"])
    commit = repo.get("commit")

    if head_commit(path) is None:
        # 浅克隆：只取目标分支的单个 commit
        # pin 到 tag 会处于 detached HEAD，属预期行为，关掉 git 的提示
        cmd = ["git", "clone", "--config", "advice.detachedHead=false", "--depth", "1"]
        if repo.get("branch"):
            cmd += ["-b", repo["branch"]]
        cmd += [repo["url"], path]
        os.makedirs(os.path.dirname(path), exist_ok=True)
        subprocess.run(cmd, check=True)
        action = "cloned"
    else:
        action = "kept"

    actual = head_commit(path)
    if commit and actual != commit:
        # 目标 commit 不在浅克隆里时，按 sha 单独取一次
        subprocess.run(
            ["git", "-C", path, "fetch", "--depth", "1", "origin", commit],
            check=True,
        )
        subprocess.run(
            [
                "git",
                "-c",
                "advice.detachedHead=false",
                "-C",
                path,
                "checkout",
                "--detach",
                "FETCH_HEAD",
            ],
            check=True,
        )
        actual = head_commit(path)
        action = "checked out"

    return action, actual


def main():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        repos = json.load(f)

    state = {}
    failed = []

    for repo in repos:
        try:
            action, actual = sync_repo(repo)
        except subprocess.CalledProcessError as e:
            failed.append(repo["url"])
            print(f"[     failed] {repo['path']}  ({e})", file=sys.stderr)
            continue

        state[repo["path"]] = {"url": repo["url"], "commit": actual}
        print(f"[{action:>11}] {repo['path']}  {actual[:12]}")

    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4, ensure_ascii=False)
        f.write("\n")

    if failed:
        print(f"\n{len(failed)} 个仓库拉取失败：", file=sys.stderr)
        for url in failed:
            print(f"    - {url}", file=sys.stderr)
        return 1

    return 0


# ── main ─────────────────────────────────────────────────────
if __name__ == "__main__":
    sys.exit(main())
