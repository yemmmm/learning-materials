#!/usr/bin/env bash

# 保留 Shell 入口，实际的交互控制由 Expect 完成。

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
EXPECT_SCRIPT="${SCRIPT_DIR}/ssh-sudo-rootsh-ls-poc.exp"

if ! command -v expect >/dev/null 2>&1; then
    printf '%s\n' \
        '错误：当前操作机未安装 expect。' \
        'Linux Mint/Ubuntu 安装命令：sudo apt update && sudo apt install -y expect' >&2
    exit 2
fi

if ! command -v ssh >/dev/null 2>&1; then
    printf '%s\n' '错误：当前操作机未安装 OpenSSH 客户端。' >&2
    exit 2
fi

if [ ! -r "$EXPECT_SCRIPT" ]; then
    printf '错误：无法读取 Expect 执行器：%s\n' "$EXPECT_SCRIPT" >&2
    exit 2
fi

exec expect "$EXPECT_SCRIPT" "$@"
