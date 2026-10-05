
# cmake — 桌面端构建

配置 / 编译 / 清理桌面端 CMake 工程：构建目录固定 `build/desktop/`，每次动作的完整输出按时间戳落到 `build/logs/`。

## 用法

```bash
scripts/cmake/cmake.sh            # 配置 + 编译（默认动作）
scripts/cmake/cmake.sh build      # 同上
scripts/cmake/cmake.sh configure  # 只配置，不编译
scripts/cmake/cmake.sh clean      # 只清产物，保留构建目录
scripts/cmake/cmake.sh rebuild    # 删除 build/desktop 后重新配置编译
```

`build` 动作后面多写的参数会原样传给 `cmake --build`（例如 `--target app_desktop_build`）。

## 行为

| 动作 | 说明 |
| --- | --- |
| `configure` | `cmake -B build/desktop -S <仓库根>`，构建哪个平台由根 `CMakeLists.txt` 决定 |
| `build` | 先幂等配置一遍，再 `cmake --build build/desktop -j $(nproc)` |
| `clean` | 走 `cmake --build --target clean`；构建目录不存在时直接跳过 |
| `rebuild` | `rm -rf build/desktop` 后重新配置编译 |

## 注意事项

1. **`build/` 不入库**（见 `.gitignore`），日志同理；命令失败先看 `build/logs/` 里最新那份日志。
2. **`clean` 不重置 CMake 缓存**：改了 `CMakeLists.txt` 里的选项或换了平台，用 `rebuild` 才干净。
3. **换平台不改构建目录**：改的是根 `CMakeLists.txt` 的 `add_subdirectory`（见 [`../../platforms/README.md`](../../platforms/README.md)）。
4. **退出码即结果**：脚本开了 `set -o pipefail`，cmake 失败不会被 `tee` 掩盖，日志里有完整输出。
