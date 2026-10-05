
# app_pro

基于应用代码，复用于不同硬件、不同平台、不同 UI 框架。

- 本仓库自带桌面端运行环境，**可独立构建运行**
- 平台（ESP-IDF / PlatformIO / nRF Connect SDK…）通过 git 子模块引用本仓库，各自实现硬件抽象层
- 应用层与 UI 框架解耦：更换 UI 框架不影响业务逻辑与硬件抽象

## 文档

开发约束（必须遵守的铁律）见 [`CLAUDE.md`](CLAUDE.md)；
工具索引见 [`tools/README.md`](tools/README.md)。
脚本细节见 [`scripts/README.md`](scripts/README.md)。
平台适配见 [`platforms/README.md`](platforms/README.md)。


