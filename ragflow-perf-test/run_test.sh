#!/usr/bin/env bash
# ===========================================================================
# RAGFlow 分布式性能压测编排脚本
# ===========================================================================
# 功能:
#   1. 在远程服务器上启动 monitor.py（通过 SSH, 可选）
#   2. 执行 bench_retrieval.py 并发梯度压测
#   3. 收集所有监控数据到本地
#   4. 运行 analyze.py 生成分析报告
#
# 用法:
#   source config.env
#   bash run_test.sh
#
#   # 仅运行压测，跳过监控
#   MONITOR_HOSTS="" bash run_test.sh
#
#   # 自定义并发梯度
#   CONCURRENCIES="10,50,100,200,500" bash run_test.sh
# ===========================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ---- 配置加载 ----
if [ -f config.env ]; then
    echo ">>> 加载配置: config.env"
    source config.env
fi

# ---- 默认值 ----
CONCURRENCIES="${CONCURRENCIES:-10,30,50,100,200,500}"
DURATION="${DURATION:-60}"
WARMUP="${WARMUP:-15}"
OUTPUT_DIR="${OUTPUT_DIR:-./results}"
MONITOR_HOSTS="${MONITOR_HOSTS:-}"
MODE="${MODE:-retrieval}"

# ---- 颜色 ----
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ---- 日期标签 ----
TAG="$(date +%Y%m%d_%H%M%S)"
RESULT_DIR="$OUTPUT_DIR/$TAG"

echo "============================================================"
echo " RAGFlow 分布式性能压测"
echo " 时间: $(date)"
echo " 结果目录: $RESULT_DIR"
echo "============================================================"

# ---- 前置检查 ----
check_command() {
    if ! command -v "$1" &>/dev/null; then
        echo -e "${RED}[ERROR]${NC} 缺少命令: $1"
        exit 1
    fi
}

check_command python3

# 检查 httpx
if ! python3 -c "import httpx" 2>/dev/null; then
    echo -e "${YELLOW}[WARN]${NC} httpx 未安装，尝试安装..."
    pip install httpx
fi

# 验证必要环境变量
if [ "$MODE" = "retrieval" ]; then
    if [ -z "${RAGFLOW_URL:-}" ]; then
        echo -e "${RED}[ERROR]${NC} 请设置 RAGFLOW_URL"
        exit 1
    fi
    if [ -z "${RAGFLOW_API_KEY:-}" ]; then
        if [ -z "${RAGFLOW_EMAIL:-}" ] || [ -z "${RAGFLOW_PASSWORD:-}" ]; then
            echo -e "${RED}[ERROR]${NC} 请设置 RAGFLOW_EMAIL/RAGFLOW_PASSWORD 或 RAGFLOW_API_KEY"
            exit 1
        fi
    fi
fi

# ---- 步骤 1: 启动远程监控 ----
MONITOR_PIDS=()
MONITOR_FILES=()

if [ -n "$MONITOR_HOSTS" ]; then
    echo ""
    echo ">>> [1/4] 启动远程监控服务 ..."

    MONITOR_INTERVAL="${MONITOR_INTERVAL:-2}"
    MONITOR_DURATION=$(( (${#CONCURRENCIES//[^,]}+1) * (DURATION + WARMUP + 10) + 30 ))

    for host_info in $MONITOR_HOSTS; do
        # 格式: user@host:port:label
        IFS=':' read -r user_host port label <<< "$host_info"
        label="${label:-$(echo "$user_host" | cut -d@ -f2)}"
        port="${port:-22}"

        monitor_file="/tmp/ragflow_monitor_${label}_${TAG}.csv"
        MONITOR_FILES+=("$user_host:$monitor_file:$label")

        echo "  启动 $label ($user_host:$port) → $monitor_file"

        ssh -p "$port" -o StrictHostKeyChecking=no "$user_host" \
            "python3 -c '
import subprocess, sys
subprocess.run(sys.argv[1:])
' $SCRIPT_DIR/monitor.py --output $monitor_file --interval $MONITOR_INTERVAL --duration $MONITOR_DURATION" \
            </dev/null >/dev/null 2>&1 &

        MONITOR_PIDS+=($!)
    done

    echo "  等待监控服务就绪 (5s) ..."
    sleep 5
else
    echo ""
    echo -e "${YELLOW}>>> [1/4] 跳过远程监控 (未设置 MONITOR_HOSTS)${NC}"
    echo "    如需监控，请在每台服务器上手动运行:"
    echo "    python3 monitor.py --output /tmp/monitor_\$(hostname).csv --interval 2"
fi

# ---- 步骤 2: 执行压测 ----
echo ""
echo ">>> [2/4] 执行压测 (并发梯度: $CONCURRENCIES) ..."

BENCH_ARGS=(
    --url "$RAGFLOW_URL"
    --mode "$MODE"
    --concurrencies "$CONCURRENCIES"
    --duration "$DURATION"
    --warmup "$WARMUP"
    --output-dir "$OUTPUT_DIR"
    --tag "$TAG"
    --max-connections "${MAX_CONNECTIONS:-200}"
    --total-timeout "${TOTAL_TIMEOUT:-120}"
    --connect-timeout "${CONNECT_TIMEOUT:-10}"
)

if [ -n "${RAGFLOW_API_KEY:-}" ]; then
    BENCH_ARGS+=(--api-key "$RAGFLOW_API_KEY")
else
    BENCH_ARGS+=(--email "$RAGFLOW_EMAIL" --password "$RAGFLOW_PASSWORD")
fi

if [ -n "${RAGFLOW_KB_IDS:-}" ]; then
    BENCH_ARGS+=(--kb-ids "$RAGFLOW_KB_IDS")
fi

if [ -n "${QUESTIONS_FILE:-}" ]; then
    BENCH_ARGS+=(--questions-file "$QUESTIONS_FILE")
fi

python3 "$SCRIPT_DIR/bench_retrieval.py" "${BENCH_ARGS[@]}"

# ---- 步骤 3: 收集监控数据 ----
echo ""
echo ">>> [3/4] 收集监控数据 ..."

for entry in "${MONITOR_FILES[@]}"; do
    IFS=':' read -r user_host remote_path label <<< "$entry"
    local_path="$RESULT_DIR/monitor_${label}.csv"
    echo "  拉取 $label: $user_host:$remote_path → $local_path"
    scp -q -o StrictHostKeyChecking=no "$user_host:$remote_path" "$local_path" 2>/dev/null || {
        echo -e "  ${YELLOW}[WARN]${NC} 无法从 $user_host 拉取监控数据"
    }
done

# 清理远程监控进程
for pid in "${MONITOR_PIDS[@]}"; do
    kill "$pid" 2>/dev/null || true
done

# ---- 步骤 4: 生成报告 ----
echo ""
echo ">>> [4/4] 生成分析报告 ..."

REPORT_PATH="$RESULT_DIR/report.md"
python3 "$SCRIPT_DIR/analyze.py" --input "$RESULT_DIR" --output "$REPORT_PATH"

# ---- 完成 ----
echo ""
echo "============================================================"
echo -e " ${GREEN}测试完成${NC}"
echo " 结果目录: $RESULT_DIR"
echo " 汇总 JSON:  $RESULT_DIR/summary.json"
echo " 分析报告:  $REPORT_PATH"
echo "============================================================"

# 如果监控数据存在，补充资源信息
for entry in "${MONITOR_FILES[@]}"; do
    IFS=':' read -r _ _ label <<< "$entry"
    if [ -f "$RESULT_DIR/monitor_${label}.csv" ]; then
        echo " 监控数据 ($label): $RESULT_DIR/monitor_${label}.csv"
    fi
done
