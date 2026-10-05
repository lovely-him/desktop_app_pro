
# platforms — 平台适配

应用层代码与硬件/平台解耦：每个平台一个子目录，目录内自带 `CMakeLists.txt` 与入口源文件，各自实现硬件抽象层。根 [`CMakeLists.txt`](../CMakeLists.txt) 用 `add_subdirectory` 决定本次构建哪一个。

| 平台 | 说明 |
| --- | --- |
| `desktop` | 桌面端（本机自测与调试），可执行目标 `app_desktop_build`，目前是最小骨架 |
| `example` | 新平台模板占位，未参与构建 |

## 约定

- **公共编译选项留在根 `CMakeLists.txt`**：C++ 标准、`CMAKE_RUNTIME_OUTPUT_DIRECTORY` 等统一设置，平台目录只声明自己的目标与源文件。
- **产物落在构建目录根部**：由根的 `CMAKE_RUNTIME_OUTPUT_DIRECTORY` 决定，平台目录内不要另设输出路径。

## 相关

- 构建与清理：`scripts/cmake/cmake.sh`（见 [`../scripts/README.md`](../scripts/README.md)）
- 项目定位与平台引用方式：根 [`README.md`](../README.md)
