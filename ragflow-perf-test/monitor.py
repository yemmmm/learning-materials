#!/usr/bin/env python3
"""
RAGFlow 服务端资源监控脚本

在每个 RAGFlow 节点服务器上运行，采集系统资源指标。
零外部依赖 — 仅使用 Python 3 标准库。

采集指标:
  - CPU 使用率 (%)        — 整体及 per-core
  - 内存使用率 (%)        — 总量 / 已用 / 可用
  - 网络 IO (bytes/s)    — 接收 / 发送
  - 磁盘 IO (读写/s)     — 针对指定挂载点
  - 系统负载             — 1min / 5min / 15min
  - 文件描述符           — 已分配 / 最大
  - Docker 容器统计      — 可选，需 docker 命令可用

用法（在每台 RAGFlow 服务器上执行）:
  python monitor.py --output server1_metrics.csv --interval 2

  # 同时监控 Docker 容器和磁盘 IO
  python monitor.py --output metrics.csv --docker --disk /data

  # 采集指定时长后自动停止
  python monitor.py --output metrics.csv --duration 600

输出:
  CSV 文件，每分钟约 30 行（interval=2），可直接导入 Excel / Python 分析。
"""

from __future__ import annotations

import argparse
import csv
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Linux /proc 读取工具
# ---------------------------------------------------------------------------


def _read_lines(path: str) -> list[str]:
    try:
        return Path(path).read_text().splitlines()
    except Exception:
        return []


def _read_first_line(path: str) -> str:
    try:
        return Path(path).read_text().splitlines()[0]
    except Exception:
        return ""


def _read_kv(path: str) -> dict[str, str]:
    """读取 key:value 格式的文件（如 /proc/meminfo）。"""
    result = {}
    for line in _read_lines(path):
        parts = line.split(":", 1)
        if len(parts) == 2:
            result[parts[0].strip()] = parts[1].strip()
    return result


# ---------------------------------------------------------------------------
# 指标采集器
# ---------------------------------------------------------------------------


class MetricsCollector:
    def __init__(self, monitor_docker: bool = False, disk_mount: str = ""):
        self.monitor_docker = monitor_docker
        self.disk_mount = disk_mount

        # 缓存上一次采集值（用于计算速率）
        self._prev_cpu: Optional[list[int]] = None
        self._prev_net_rx: int = 0
        self._prev_net_tx: int = 0
        self._prev_disk_read: int = 0
        self._prev_disk_write: int = 0
        self._prev_time: float = 0.0

    def collect(self) -> dict:
        """采集当前时刻所有指标，返回 dict。"""
        now = time.time()
        metrics = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cpu_pct": 0.0,
            "mem_total_gb": 0.0,
            "mem_used_gb": 0.0,
            "mem_pct": 0.0,
            "load_1m": 0.0,
            "load_5m": 0.0,
            "load_15m": 0.0,
            "net_rx_bytes_s": 0.0,
            "net_tx_bytes_s": 0.0,
            "open_fds": 0,
            "max_fds": 0,
        }

        # --- CPU ---
        cpu_pct, cpu_detail = self._read_cpu()
        metrics["cpu_pct"] = cpu_pct

        # --- Memory ---
        mem = self._read_memory()
        metrics.update(mem)

        # --- Load ---
        load = self._read_load()
        metrics.update(load)

        # --- Network (速率) ---
        net = self._read_network_rate(now)
        metrics.update(net)

        # --- File descriptors ---
        fd = self._read_fd()
        metrics.update(fd)

        # --- Disk IO (速率) ---
        if self.disk_mount:
            disk = self._read_disk_rate(now)
            metrics.update(disk)

        # --- Docker ---
        if self.monitor_docker:
            docker_stats = self._read_docker()
            if docker_stats:
                metrics["docker_stats"] = docker_stats

        self._prev_time = now
        return metrics

    def _read_cpu(self) -> tuple[float, str]:
        """读取 /proc/stat 计算 CPU 使用率。"""
        line = _read_first_line("/proc/stat")
        if not line or not line.startswith("cpu "):
            return 0.0, ""

        parts = [int(x) for x in line.split()[1:]]
        if len(parts) < 4:
            return 0.0, ""

        cpu_idle = parts[3]
        cpu_total = sum(parts)

        if self._prev_cpu is None:
            self._prev_cpu = [cpu_total, cpu_idle]
            return 0.0, ""

        prev_total, prev_idle = self._prev_cpu
        total_diff = cpu_total - prev_total
        idle_diff = cpu_idle - prev_idle

        self._prev_cpu = [cpu_total, cpu_idle]

        if total_diff == 0:
            return 0.0, ""
        return round((1 - idle_diff / total_diff) * 100, 1), line

    def _read_memory(self) -> dict:
        """读取 /proc/meminfo。"""
        mem = _read_kv("/proc/meminfo")
        total_kb = _parse_kb(mem.get("MemTotal", "0 kB"))
        avail_kb = _parse_kb(mem.get("MemAvailable", "0 kB"))
        used_kb = total_kb - avail_kb
        return {
            "mem_total_gb": round(total_kb / 1024 / 1024, 2),
            "mem_used_gb": round(used_kb / 1024 / 1024, 2),
            "mem_pct": round(used_kb / total_kb * 100, 1) if total_kb > 0 else 0.0,
        }

    def _read_load(self) -> dict:
        """读取 /proc/loadavg。"""
        line = _read_first_line("/proc/loadavg")
        if not line:
            return {"load_1m": 0.0, "load_5m": 0.0, "load_15m": 0.0}
        parts = line.split()
        return {
            "load_1m": float(parts[0]) if len(parts) > 0 else 0.0,
            "load_5m": float(parts[1]) if len(parts) > 1 else 0.0,
            "load_15m": float(parts[2]) if len(parts) > 2 else 0.0,
        }

    def _read_network_rate(self, now: float) -> dict:
        """读取 /proc/net/dev 计算网络速率。"""
        rx, tx = 0, 0
        for line in _read_lines("/proc/net/dev"):
            if ":" not in line or "lo:" in line:
                continue
            parts = line.split(":")[1].split()
            if len(parts) >= 9:
                rx += int(parts[0])
                tx += int(parts[8])

        result = {"net_rx_bytes_s": 0.0, "net_tx_bytes_s": 0.0}
        if self._prev_net_rx > 0 and self._prev_time > 0:
            elapsed = now - self._prev_time
            if elapsed > 0:
                result["net_rx_bytes_s"] = round((rx - self._prev_net_rx) / elapsed, 1)
                result["net_tx_bytes_s"] = round((tx - self._prev_net_tx) / elapsed, 1)

        self._prev_net_rx = rx
        self._prev_net_tx = tx
        return result

    def _read_fd(self) -> dict:
        """读取 /proc/sys/fs/file-nr。"""
        line = _read_first_line("/proc/sys/fs/file-nr")
        if not line:
            return {"open_fds": 0, "max_fds": 0}
        parts = line.split()
        return {
            "open_fds": int(parts[0]) if len(parts) > 0 else 0,
            "max_fds": int(parts[2]) if len(parts) > 2 else 0,
        }

    def _read_disk_rate(self, now: float) -> dict:
        """读取 /proc/diskstats 计算磁盘 IO 速率。"""
        # 找到设备名
        try:
            mount_info = subprocess.check_output(
                ["df", self.disk_mount], stderr=subprocess.DEVNULL, text=True
            )
            dev = mount_info.splitlines()[-1].split()[0].split("/")[-1] if mount_info else ""
        except Exception:
            dev = ""

        read_sectors = 0
        write_sectors = 0
        for line in _read_lines("/proc/diskstats"):
            parts = line.split()
            if len(parts) < 14:
                continue
            if dev and parts[2] != dev:
                continue
            read_sectors += int(parts[5])
            write_sectors += int(parts[9])

        result = {"disk_read_kb_s": 0.0, "disk_write_kb_s": 0.0}
        if self._prev_disk_read > 0 and self._prev_time > 0:
            elapsed = now - self._prev_time
            if elapsed > 0:
                result["disk_read_kb_s"] = round(
                    (read_sectors - self._prev_disk_read) * 0.5 / elapsed, 1
                )
                result["disk_write_kb_s"] = round(
                    (write_sectors - self._prev_disk_write) * 0.5 / elapsed, 1
                )

        self._prev_disk_read = read_sectors
        self._prev_disk_write = write_sectors
        return result

    def _read_docker(self) -> str:
        """执行 docker stats --no-stream 获取容器统计。"""
        try:
            out = subprocess.check_output(
                ["docker", "stats", "--no-stream", "--no-trunc",
                 "--format", "{{.Name}},{{.CPUPerc}},{{.MemUsage}},{{.MemPerc}},{{.NetIO}}"],
                stderr=subprocess.DEVNULL, text=True, timeout=5,
            )
            return out.strip()
        except Exception:
            return ""


def _parse_kb(text: str) -> int:
    """解析 MemTotal 格式: '32874012 kB' → int。"""
    try:
        return int(text.split()[0])
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# CSV 字段定义
# ---------------------------------------------------------------------------

BASE_FIELDS = [
    "timestamp", "cpu_pct", "mem_total_gb", "mem_used_gb", "mem_pct",
    "load_1m", "load_5m", "load_15m",
    "net_rx_bytes_s", "net_tx_bytes_s",
    "open_fds", "max_fds",
]
DISK_FIELDS = ["disk_read_kb_s", "disk_write_kb_s"]
DOCKER_FIELD = ["docker_stats"]


# ---------------------------------------------------------------------------
# 主程序
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="RAGFlow 服务端资源监控脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--output", default="monitor.csv", help="CSV 输出路径")
    parser.add_argument("--interval", type=float, default=2.0,
                        help="采集间隔/秒 (default: 2)")
    parser.add_argument("--duration", type=float, default=0,
                        help="采集时长/秒，0 表示持续运行直到 Ctrl+C (default: 0)")
    parser.add_argument("--docker", action="store_true",
                        help="同时采集 docker stats")
    parser.add_argument("--disk", default="",
                        help="监控磁盘 IO 的挂载点 (如 /data)")

    args = parser.parse_args()

    collector = MetricsCollector(
        monitor_docker=args.docker,
        disk_mount=args.disk,
    )

    # 确定输出字段
    fields = list(BASE_FIELDS)
    if args.disk:
        fields.extend(DISK_FIELDS)
    if args.docker:
        fields.extend(DOCKER_FIELD)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"监控已启动 → {output_path}")
    print(f"采集间隔: {args.interval}s  "
          f"{'时长: ' + str(args.duration) + 's' if args.duration > 0 else '持续运行 (Ctrl+C 停止)'}")
    print(f"字段: {fields}")

    t_start = time.time()

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()

        try:
            while True:
                # 检查是否超时
                if args.duration > 0 and (time.time() - t_start) >= args.duration:
                    break

                metrics = collector.collect()

                # 展平 docker_stats
                row = {k: metrics[k] for k in BASE_FIELDS}
                if args.disk:
                    for k in DISK_FIELDS:
                        row[k] = metrics.get(k, 0.0)
                if args.docker:
                    row["docker_stats"] = metrics.get("docker_stats", "")

                writer.writerow(row)
                f.flush()

                time.sleep(args.interval)

        except KeyboardInterrupt:
            pass

    elapsed = time.time() - t_start
    print(f"监控已停止。采集时长: {elapsed:.0f}s, 数据保存至: {output_path}")


if __name__ == "__main__":
    main()
