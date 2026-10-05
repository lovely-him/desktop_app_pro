#!/usr/bin/env bash
#
# 用法: scripts/cmake/cmake.sh [build|clean|rebuild|configure]
#
set -euo pipefail

# ── 路径与常量 ────────────────────────────────────────────────
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$(dirname "$SCRIPTS_DIR")")"
BUILD_DIR="build/desktop"
LOGS_DIR="build/logs"

# ── 函数 ─────────────────────────────────────────────────────
log_path() {
    echo "$ROOT_DIR/$LOGS_DIR/build-$(date +%Y%m%d-%H%M%S).log"
}

build_desktop() {
    local action="${1:-build}"
    shift || true
    local build_path="$ROOT_DIR/$BUILD_DIR"
    local log_file
    log_file="$(log_path)"

    mkdir -p "$ROOT_DIR/$LOGS_DIR"

    case "$action" in
        configure)
            echo "==> 配置 $build_path"
            cmake -B "$build_path" -S "$ROOT_DIR" 2>&1 | tee "$log_file"
            ;;

        build)
            echo "==> 编译 $build_path"
            # 配置（幂等）+ 构建 + 日志
            cmake -B "$build_path" -S "$ROOT_DIR"
            cmake --build "$build_path" -j "$(nproc)" "$@"  2>&1 | tee "$log_file"
            ;;

        clean)
            echo "==> 清除产物 $build_path"
            if [ -d "$build_path" ]; then
                cmake --build "$build_path" --target clean 2>&1 | tee "$log_file" || true
            else
                echo "构建目录不存在，无需清除"
            fi
            ;;

        rebuild)
            echo "==> 彻底清除 $build_path"
            rm -rf "$build_path"
            echo "==> 重新配置并编译"
            cmake -B "$build_path" -S "$ROOT_DIR"
            cmake --build "$build_path" -j "$(nproc)" 2>&1 | tee "$log_file"
            ;;

        *)
            echo "用法: $0 [build|clean|rebuild|configure]" >&2
            return 1
            ;;
    esac

    echo "==> 完成，日志：$log_file"
}

# ── main ─────────────────────────────────────────────────────
main() {
    build_desktop "$@"
}

main "$@"
