# serial-console — 串口控制台工具

通过 **UART 串口**访问 Linux 开发板控制台（如 Radxa ROCK 2A / RK3528 等）：自动登录、执行**一条**命令、输出流式打印；看到 shell 提示符即返回，不必等满超时。

用于板子还没网络/没装 SSH、或系统起不来时做排障与验证（看系统状态、装包报错、服务是否运行等）。

## 依赖

- Python 3 + `pyserial`
- 现成可用：`.venv/bin/python`（已含 pyserial）
- 或自行安装：`python3 -m pip install pyserial`

## 用法

```bash
# 执行一条命令（使用默认参数）
.venv/bin/python tools/serial-console/serial_console.py "<命令>"

# 覆盖默认参数（设备、波特率、提示符、账号）
.venv/bin/python tools/serial-console/serial_console.py --port <串口设备> --baud <波特率> "<命令>"
.venv/bin/python tools/serial-console/serial_console.py --prompt '<提示符>' --user <用户名> "<命令>"

# 不给命令：只唤醒/（必要时）登录，并打印当前控制台输出
.venv/bin/python tools/serial-console/serial_console.py

# 查看全部参数与默认值
.venv/bin/python tools/serial-console/serial_console.py --help
```

参数默认值集中在脚本里（面向常见 Radxa 出厂配置），首次连接板子请先确认端口与波特率再使用。

## 行为

- **一次一条命令**：每次调用只执行一条命令。串口没有流控与纠错，逐条执行才能判断"是否还在运行"、输出归属哪条命令。
- **流式输出**：边收边打印（实时 flush），不是攒够时间再一次性打印。
- **提示符判定结束**：命中 `--prompt` 指定的提示符并短暂静默即返回；否则等到 `--timeout`。匹配前会先去除 ANSI 转义序列，因此带颜色的提示符（如 Zephyr Shell 的 `uart:~$`）同样可识别。
- **自动登录**：若控制台停在 `login:`，用 `--user` / `--password` 自动登录。

退出码：

| 退出码 | 含义 |
|---|---|
| 0 | 命令执行完毕，已回到 shell 提示符 |
| 1 | 达到 `--timeout` 上限（命令可能仍在运行） |
| 2 | 串口打不开（设备不存在、被占用、无权限等） |
| 130 | 手动中断（Ctrl+C）；命令可能仍在板子上执行 |

## 注意事项

1. **端口与波特率因板而异**：不同厂商/不同 BSP 的调试串口波特率差别很大（部分 Rockchip 板使用远高于常见默认值的波特率）。没有任何输出时，先确认这两项，再检查 TX/RX 是否接反、地线是否接好。
2. **提示符要匹配实际登录身份**：提示符决定"命令是否结束"。换了主机名、用户名或切到 root 后，提示符会变，必须用 `--prompt` 覆盖，否则每次都会等到超时（退出码 1）。
3. **宿主侧权限**：串口设备通常属于 `dialout`/`plugdev` 组并可能带 ACL；当前用户既不在组内、也没有 ACL 时会打不开（退出码 2）。
4. **长命令**：`apt-get update/install`、内核刷写等耗时命令请放宽 `--timeout`。
5. **不转发交互输入**：脚本只发一条命令行，不转发 Ctrl+C 等按键。命令卡住时只能等超时，或另开一个串口终端（如 `minicom`）处理。
6. **板子系统很旧时的报错**：过期发行版（例如已 EOL 的 Debian 版本）会出现软件源 404、安全更新缺失等问题 —— 那是发行版生命周期问题，与串口/本脚本无关。
7. **账号默认值面向出厂配置**：默认用户名/密码仅针对出厂默认账号；生产环境请用参数覆盖，不要把生产凭据写进仓库。
8. **Ctrl+C 只中断本地读取**：手动中断时打印一句提示并返回退出码 130（不打印 traceback）；它**不会取消板子上正在执行的命令**，也不向串口补发任何按键 —— 需要停止板子上的任务时请另行处理。

## 相关

- AI 入口（按需加载的触发说明）：`.github/skills/serial-console/SKILL.md`
- 工具总索引：`tools/README.md`