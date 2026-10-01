#!/usr/bin/env python3
"""通过串口访问 Linux 开发板控制台: (必要时)自动登录 + 执行一条命令, 输出流式打印。

设计要点:
  - 模块层零副作用: 导入本模块不会打开串口、不会解析参数, 便于被其它脚本复用。
  - 所有环境相关量都是带默认值的参数, 命令行可覆盖 (见 parse_args())。
  - 每次调用只执行一条命令: 串口没有流控与纠错, 逐条执行才便于判断"是否还在运行"。
  - 输出边收边打印; 看到 shell 提示符即返回, 不必等满超时。

退出码:
  0    已回到 shell 提示符 (命令执行完毕)
  1    达到超时上限 (命令可能仍在运行)
  2    串口错误 (设备不存在、被占用、无权限等)
  130  手动中断 (Ctrl+C); 命令可能仍在板子上执行

用法与注意事项见同目录 README.md。
"""

import argparse
import re
import sys
import time

import serial

# 去 ANSI 转义 (颜色/Bracketed Paste 等), 便于阅读与提示符匹配
ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]|\x1b\][^\x07]*\x07")

DEFAULT_PORT = "/dev/ttyUSB0"
DEFAULT_BAUD = 1500000
DEFAULT_USER = "radxa"
DEFAULT_PASSWORD = "radxa"
DEFAULT_PROMPT = "radxa@rock-2:~$"
DEFAULT_TIMEOUT = 120.0
DEFAULT_QUIET = 0.4


def parse_args(argv=None):
    """解析命令行参数 (唯一接触 sys.argv 的地方, 全部参数都有默认值)。"""
    parser = argparse.ArgumentParser(
        prog="serial_console.py",
        description="通过串口登录开发板并执行一条命令 (输出流式打印)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            '  serial_console.py "uname -a"\n'
            '  serial_console.py --port /dev/ttyUSB0 --baud 115200 "ip -br addr"\n'
            "  serial_console.py --prompt 'root@board:~#' --user root \"df -h /\"\n"
            "  serial_console.py                 # 不带命令: 只唤醒/登录并打印当前控制台输出\n"
        ),
    )
    parser.add_argument(
        "command",
        nargs="?",
        default=None,
        help="要执行的 shell 命令 (省略则只唤醒/登录并打印当前控制台输出)",
    )
    parser.add_argument(
        "--port", default=DEFAULT_PORT, help="串口设备 (默认 %(default)s)"
    )
    parser.add_argument(
        "--baud", type=int, default=DEFAULT_BAUD, help="波特率 (默认 %(default)s)"
    )
    parser.add_argument(
        "--user", default=DEFAULT_USER, help="登录用户名 (默认 %(default)s)"
    )
    parser.add_argument(
        "--password", default=DEFAULT_PASSWORD, help="登录密码 (默认 %(default)s)"
    )
    parser.add_argument(
        "--prompt",
        default=DEFAULT_PROMPT,
        help="shell 提示符, 用于判断命令执行结束 (默认 %(default)s)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help="单条命令的最大等待秒数 (默认 %(default)s)",
    )
    parser.add_argument(
        "--quiet",
        type=float,
        default=DEFAULT_QUIET,
        help="命中提示符后, 再静默多少秒算结束 (默认 %(default)s)",
    )
    return parser.parse_args(argv)


def _clean(text):
    """去掉 ANSI 转义序列并统一换行。"""
    return ANSI_RE.sub("", text).replace("\r\n", "\n").replace("\r", "\n")


def stream_until(ser, max_secs, prompt=None, stop_on=None, quiet=DEFAULT_QUIET):
    """流式读取并打印串口输出, 返回 (文本, 是否命中终止条件)。

    - prompt: 提示符; 清洗后 rstrip 结尾为 prompt 且静默超过 quiet 秒即返回。
    - stop_on: 子串; 出现即立刻返回 (用于 login: / assword: 这类"设备正等输入"的提示)。
    - 两者都不给时读满 max_secs 才返回 (用于唤醒阶段的"看看有什么输出")。
    - 输出先去除 ANSI 转义再累积/打印; 匹配针对清洗后的文本。
    """
    start = time.time()
    last_rx = time.time()
    buf = ""
    while time.time() - start < max_secs:
        pending = ser.in_waiting
        if pending:
            # 先清洗再累积: 提示符常被 ANSI 颜色/复位序列包裹 (如 Zephyr Shell
            # 的 "\x1b[1;32muart:~$ \x1b[m"), 带转义的缓冲无法用于提示符匹配。
            text = _clean(ser.read(pending).decode("utf-8", "replace"))
            buf += text
            last_rx = time.time()
            sys.stdout.write(text)
            sys.stdout.flush()
            if stop_on and stop_on in buf:
                return buf, True
        else:
            time.sleep(0.05)
            if (
                prompt
                and buf.rstrip().endswith(prompt)
                and (time.time() - last_rx) > quiet
            ):
                return buf, True
    return buf, False


def open_console(port=DEFAULT_PORT, baud=DEFAULT_BAUD):
    """打开串口, 丢弃上电/上一次会话的残留输入。"""
    ser = serial.Serial(port, baud, timeout=0.2)
    time.sleep(0.3)
    ser.reset_input_buffer()
    return ser


def login_if_needed(
    ser, user=DEFAULT_USER, password=DEFAULT_PASSWORD, prompt=DEFAULT_PROMPT
):
    """唤醒控制台; 若停在 login: 提示则用 user/password 自动登录。"""
    ser.write(b"\r")
    # 已登录(命中提示符) 或 需要登录(出现 login:) 都立刻返回, 不必读满窗口
    out, _ = stream_until(ser, 3.0, prompt=prompt, stop_on="login:")

    if "login:" not in out.lower():
        return out

    ser.write((user + "\r").encode())
    out2, _ = stream_until(ser, 3.0, stop_on="assword:")
    if "assword" in out2.lower():
        ser.write((password + "\r").encode())
        out3, _ = stream_until(ser, 10.0, prompt=prompt)
        return out3
    return out2


def run_command(
    ser, command, prompt=DEFAULT_PROMPT, timeout=DEFAULT_TIMEOUT, quiet=DEFAULT_QUIET
):
    """执行一条命令, 返回 (输出文本, 是否回到提示符)。"""
    ser.write(command.encode() + b"\r")
    return stream_until(ser, timeout, prompt=prompt, quiet=quiet)


def main(
    command=None,
    port=DEFAULT_PORT,
    baud=DEFAULT_BAUD,
    user=DEFAULT_USER,
    password=DEFAULT_PASSWORD,
    prompt=DEFAULT_PROMPT,
    timeout=DEFAULT_TIMEOUT,
    quiet=DEFAULT_QUIET,
):
    """打开串口 → (必要时)登录 → 执行 command → 打印输出。返回退出码。

    手动中断 (Ctrl+C) 时不打印 traceback: 提示一句并返回 130。
    """
    phase = "打开串口"  # 中断提示里用来区分发生阶段
    try:
        try:
            ser = open_console(port=port, baud=baud)
        except serial.SerialException as exc:
            print(f"[serial] 打开串口失败: {exc}", file=sys.stderr)
            return 2

        with ser:
            phase = "登录"
            login_if_needed(ser, user=user, password=password, prompt=prompt)
            ser.write(b"\r")
            stream_until(ser, 2.0, prompt=prompt)

            if command is None:
                return 0

            phase = "执行命令"
            print(f"\n=== $ {command}", flush=True)
            _out, finished = run_command(
                ser, command, prompt=prompt, timeout=timeout, quiet=quiet
            )
            ser.write(b"\r")
            stream_until(ser, 1.5, prompt=prompt)
    except KeyboardInterrupt:
        print(f"\n[serial] 已手动中断 (Ctrl+C, 阶段: {phase})", file=sys.stderr)
        if phase == "执行命令":
            print(
                "[serial] 注意: 中断的只是本地读取, 板子上的命令很可能仍在继续执行",
                file=sys.stderr,
            )
        return 130  # 128 + SIGINT, 便于调用方区分"被手动打断"

    if not finished:
        print(f"\n[serial] 达到上限 {timeout:g}s, 命令可能仍在运行", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(**vars(parse_args())))