#!/usr/bin/env bash
#
# RAGFlow HA 集群资源监控脚本
# 采集 Docker 容器 + 服务器资源使用情况，输出 CSV
#
# 用法:
#   ./monitor_resources.sh                        # 默认: 每5秒采样，持续300秒
#   ./monitor_resources.sh -i 2 -d 600            # 每2秒采样，持续600秒
#   ./monitor_resources.sh -o /path/to/output     # 指定输出目录
#   ./monitor_resources.sh -c "ha-node1-web ha-node1-worker"  # 指定容器
#

set -uo pipefail

# ── 默认参数 ──
INTERVAL=5
DURATION=300
OUTPUT_DIR="."
CONTAINERS=()

usage() {
    echo "用法: $0 [-i 间隔秒] [-d 持续秒] [-o 输出目录] [-c 容器列表]"
    echo ""
    echo "  -i  采样间隔，默认 5 秒"
    echo "  -d  监控总时长，默认 300 秒"
    echo "  -o  CSV 输出目录，默认当前目录"
    echo "  -c  监控的容器名称，空格分隔；默认自动检测 ha- 前缀容器"
    echo "  -h  显示帮助"
    exit 0
}

while getopts "i:d:o:c:h" opt; do
    case $opt in
        i) INTERVAL=$OPTARG ;;
        d) DURATION=$OPTARG ;;
        o) OUTPUT_DIR=$OPTARG ;;
        c) read -ra CONTAINERS <<< "$OPTARG" ;;
        h) usage ;;
        *) usage ;;
    esac
done

# ── 自动检测容器 ──
if [ ${#CONTAINERS[@]} -eq 0 ]; then
    mapfile -t CONTAINERS < <(docker ps --filter "name=ha-" --format '{{.Names}}' | sort)
    if [ ${#CONTAINERS[@]} -eq 0 ]; then
        echo "错误: 未找到 ha- 前缀的运行中容器" >&2
        exit 1
    fi
fi

mkdir -p "$OUTPUT_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S%3N)
CONTAINER_CSV="$OUTPUT_DIR/container_stats_${TIMESTAMP}.csv"
SERVER_CSV="$OUTPUT_DIR/server_stats_${TIMESTAMP}.csv"

echo "监控容器: ${CONTAINERS[*]}"
echo "采样间隔: ${INTERVAL}s, 持续: ${DURATION}s"
echo "输出: ${CONTAINER_CSV}"
echo "      ${SERVER_CSV}"
echo ""

# ── CSV 表头 ──
echo "timestamp,container,cpu_pct,mem_usage_mb,mem_limit_mb,mem_pct,net_in_kb,net_out_kb,block_in_kb,block_out_kb" \
    > "$CONTAINER_CSV"

echo "timestamp,cpu_pct,mem_used_gb,mem_total_gb,mem_pct,load_1m,load_5m,load_15m,disk_used_gb,disk_total_gb,disk_pct" \
    > "$SERVER_CSV"

# ── 辅助函数 ──
now_iso() { date -Iseconds; }

# ── 单位转 MB ──
to_mb() {
    awk '{
        str = $0;
        # Extract numeric part and unit part
        if (match(str, /[0-9.]+[[:space:]]*([KkMmGgTtPp]?[iI]?[Bb])/, arr)) {
            val = str; gsub(/[^0-9.]/, "", val);
            unit = tolower(arr[1]);
            if (unit ~ /^g/) printf "%.2f", val * 1024;
            else if (unit ~ /^m/) printf "%.2f", val;
            else if (unit ~ /^k/) printf "%.2f", val / 1024;
            else if (unit ~ /^b/) printf "%.2f", val / 1048576;
            else printf "%.2f", val;
        } else {
            printf "%.2f", str + 0;
        }
    }' <<< "$1"
}

# ── 单位转 KB ──
to_kb() {
    awk '{
        str = $0;
        # Extract numeric part and unit part
        if (match(str, /[0-9.]+[[:space:]]*([KkMmGgTtPp]?[iI]?[Bb])/, arr)) {
            val = str; gsub(/[^0-9.]/, "", val);
            unit = tolower(arr[1]);
            if (unit ~ /^g/) printf "%.2f", val * 1048576;
            else if (unit ~ /^m/) printf "%.2f", val * 1024;
            else if (unit ~ /^k/) printf "%.2f", val;
            else if (unit ~ /^b/) printf "%.2f", val / 1024;
            else printf "%.2f", val;
        } else {
            printf "%.2f", str + 0;
        }
    }' <<< "$1"
}

collect_container_stats() {
    local ts
    ts=$(now_iso)

    # 并行采集所有容器的 docker stats
    local tmpdir
    tmpdir=$(mktemp -d -t mon-XXXX)
    local pids=()

    for c in "${CONTAINERS[@]}"; do
        (
            if docker inspect "$c" --format '{{.Name}}' &>/dev/null; then
                docker stats "$c" --no-stream --no-trunc --format \
                    "{{.CPUPerc}}|{{.MemUsage}}|{{.MemPerc}}|{{.NetIO}}|{{.BlockIO}}" 2>/dev/null \
                    > "$tmpdir/${c//\//_}.stats"
            fi
        ) &
        pids+=($!)
    done

    for pid in "${pids[@]}"; do
        wait "$pid" 2>/dev/null
    done

    for c in "${CONTAINERS[@]}"; do
        local sf="$tmpdir/${c//\//_}.stats"
        if [ ! -f "$sf" ]; then
            echo "$ts,$c,STOPPED,0,0,0,0,0,0,0" >> "$CONTAINER_CSV"
            continue
        fi

        local stats cpu mem_usage mem_pct net_io block_io
        IFS='|' read -r cpu mem_usage mem_pct net_io block_io < "$sf"

        local cpu_val
        cpu_val=$(echo "$cpu" | sed 's/%//' | awk '{printf "%.2f", $1}')

        local mem_used_mb mem_limit_mb
        mem_used_mb=$(to_mb "$(echo "$mem_usage" | awk -F'/' '{print $1}' || true)")
        mem_limit_mb=$(to_mb "$(echo "$mem_usage" | awk -F'/' '{print $2}' || true)")
        local mem_pct_val
        mem_pct_val=$(echo "$mem_pct" | sed 's/%//' | awk '{printf "%.2f", $1}')

        local net_in_kb net_out_kb
        net_in_kb=$(to_kb "$(echo "$net_io" | awk -F'/' '{print $1}' || true)")
        net_out_kb=$(to_kb "$(echo "$net_io" | awk -F'/' '{print $2}' || true)")

        local block_in_kb block_out_kb
        block_in_kb=$(to_kb "$(echo "$block_io" | awk -F'/' '{print $1}' || true)")
        block_out_kb=$(to_kb "$(echo "$block_io" | awk -F'/' '{print $2}' || true)")

        echo "$ts,$c,$cpu_val,$mem_used_mb,$mem_limit_mb,$mem_pct_val,$net_in_kb,$net_out_kb,$block_in_kb,$block_out_kb" \
            >> "$CONTAINER_CSV"
    done

    rm -rf "$tmpdir"
}

collect_server_stats() {
    local ts
    ts=$(now_iso)

    # CPU 使用率: 利用循环间隔作为两次采样间隔（不再额外 sleep）
    local cpu_pct="0"
    local cur_stat
    cur_stat=$(head -1 /proc/stat)
    cpu_pct=$(awk -v s1="$_prev_cpu_stat" -v s2="$cur_stat" 'BEGIN {
        split(s1, a); split(s2, b);
        idle1 = a[5]; idle2 = b[5];
        total1 = 0; total2 = 0;
        for (i = 2; i <= 8; i++) { total1 += a[i]; total2 += b[i]; }
        dt = total2 - total1; di = idle2 - idle1;
        if (dt > 0) printf "%.2f", (1 - di / dt) * 100;
        else printf "0";
    }')
    _prev_cpu_stat=$cur_stat

    # 内存 (从 /proc/meminfo 读取，避免 free 的格式差异)
    local mem_used_gb mem_total_gb mem_pct="0"
    read mem_used_gb mem_total_gb mem_pct < <(awk '
        /^MemTotal:/   { total = $2 }
        /^MemAvailable:/ { avail = $2 }
        END {
            used = total - avail;
            printf "%.2f %.2f %.2f", used/1048576, total/1048576, (total > 0 ? used/total*100 : 0);
        }
    ' /proc/meminfo)

    # 负载
    local load_1m load_5m load_15m
    read load_1m load_5m load_15m < <(awk '{print $1, $2, $3}' /proc/loadavg)

    # 磁盘 (根分区)
    local disk_used_gb disk_total_gb disk_pct="0"
    read disk_used_gb disk_total_gb disk_pct < <(df -B1G / | awk 'NR==2 {
        printf "%.2f %.2f %.2f", $3+0, $2+0, $5+0;
    }')

    echo "$ts,$cpu_pct,$mem_used_gb,$mem_total_gb,$mem_pct,$load_1m,$load_5m,$load_15m,$disk_used_gb,$disk_total_gb,$disk_pct" \
        >> "$SERVER_CSV"
}

# ── 主循环 ──
echo "开始监控 (Ctrl-C 提前结束)..."
echo ""

iterations=$((DURATION / INTERVAL))
count=0
_prev_cpu_stat=$(head -1 /proc/stat)

cleanup() {
    echo ""
    echo "监控结束, 共采集 $count 个样本"
    echo "容器数据: $CONTAINER_CSV ($(wc -l < "$CONTAINER_CSV") 行)"
    echo "服务器数据: $SERVER_CSV ($(wc -l < "$SERVER_CSV") 行)"
    exit 0
}
trap cleanup INT TERM

while [ $count -lt $iterations ]; do
    count=$((count + 1))
    loop_start=$(date +%s%N)

    printf "\r采集中... [%d/%d]" "$count" "$iterations"
    collect_container_stats
    collect_server_stats

    # 补偿采集耗时，只 sleep 不足间隔的部分
    loop_end=$(date +%s%N)
    elapsed_ms=$(( (loop_end - loop_start) / 1000000 ))
    remaining=$(( INTERVAL * 1000 - elapsed_ms ))
    if [ "$remaining" -gt 0 ]; then
        sleep "$(( remaining / 1000 )).$(( (remaining % 1000) / 100 ))"
    fi
done

cleanup
