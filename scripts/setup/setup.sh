#!/usr/bin/env bash
#
# 依赖与环境准备：创建虚拟环境、安装工具依赖、拉取第三方库。
#
set -euo pipefail

# ── 路径与常量 ────────────────────────────────────────────────
SETUP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$(dirname "$SETUP_DIR")")"

# ── 函数 ─────────────────────────────────────────────────────
setup_venv() {
    echo "==> 虚拟环境 .venv"
    if [ ! -d "$ROOT_DIR/.venv" ]; then
        python3 -m venv "$ROOT_DIR/.venv"
    fi
    "$ROOT_DIR/.venv/bin/pip" install --requirement "$ROOT_DIR/requirements.txt"
}

fetch_deps() {
    echo "==> 第三方库 dependencies/"
    # 拉取依赖只用标准库，不依赖 .venv 是否可用
    python3 "$SETUP_DIR/lib/fetch_repos.py"
}

# ── main ─────────────────────────────────────────────────────
main() {
    setup_venv
    echo
    fetch_deps
    echo
    echo "==> 完成"
}

main "$@"
