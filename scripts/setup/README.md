
# setup — 依赖与环境准备

把本仓库跑起来所需的环境一次备齐：创建 `.venv` 并按 `requirements.txt` 安装 Python 依赖，生成 `.env` 占位文件，再按 `repos.json` 把第三方库拉到 `dependencies/`。

## 用法

```bash
scripts/setup/setup.sh
```

可重复执行：已存在的 `.venv` 与已拉取的仓库都不会重建，只做补齐。

## 行为

| 步骤 | 说明 |
| --- | --- |
| 虚拟环境 | `.venv` 不存在才创建，随后始终执行 `.venv/bin/pip install -r requirements.txt` |
| 本地配置 | `.env` 不存在才创建空文件，已有内容不会被覆盖；该文件不入库 |
| 第三方库 | `lib/fetch_repos.py` 逐个同步 `repos.json` 中的仓库：浅克隆（`--depth 1`）；已存在则保持现状，只有 `commit` 对不上时才 fetch + checkout |
| 状态快照 | 每个仓库的实际 commit 写入 `dependencies/.state.json`，用于和 `repos.json` 对账 |

## repos.json

```json
[
    {
        "path": "dependencies/foo",
        "url": "https://github.com/example/foo.git",
        "branch": "main",
        "commit": "0123456789abcdef0123456789abcdef01234567"
    }
]
```

- `path`、`url` 必填；`path` 相对仓库根，约定第三方库统一放在 `dependencies/` 下。
- `branch` 可选：浅克隆时的初始分支，省略则用远端默认分支。
- `commit` 可选：目标版本；与当前 HEAD 不一致时单独 `fetch --depth 1` 该 commit 再 detached checkout（浅克隆里没有该 commit 也能取到）。

## 注意事项

1. **`dependencies/` 不入库**（见 `.gitignore`），依赖版本以 `repos.json` 为准，换机器跑一次即可复现同一套依赖。
2. **拉取脚本只用标准库**：以系统 `python3` 运行，`.venv` 没装好也能拉依赖。
3. **单个仓库失败不阻断其余仓库**：失败的 URL 汇总打印，脚本以退出码 1 结束。
4. **`repos.json` 为空数组时只建环境**：不拉任何仓库，只产出空的 `.state.json`。
5. **`.env` 是空占位**：setup 只负责在缺失时创建，内容自行填写；`.gitignore` 已忽略，本地配置不会入库。
