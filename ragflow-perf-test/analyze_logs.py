#!/usr/bin/env python3
"""
RAGFlow 检索日志分析工具

从 Docker 容器日志或磁盘日志文件中提取 [RETRIEVAL_TIMING] 行，
分析检索管道中每个步骤的耗时分布。

数据来源:
  - Docker 容器日志: 通过 docker logs 获取
  - 磁盘日志文件: 直接读取 .log 文件

用法:
    # 从 Docker 容器获取日志
    python analyze_logs.py --containers ha-node1-web ha-node2-web

    # 从磁盘日志文件读取
    python analyze_logs.py --log-files /path/to/ragflow_server.log

    # 从配置文件加载
    python analyze_logs.py --config bench_config.json

    # 保存 JSON 结果
    python analyze_logs.py --containers ha-node1-web --output-json analysis.json
"""

import argparse
import json
import os
import re
import statistics
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone

TIMING_PATTERN = re.compile(
    r"\[RETRIEVAL_TIMING\]\s+step=(\S+)\s+elapsed=([0-9.]+)"
    r"(?:\s+total=(\d+))?"
    r"(?:\s+chunks=(\d+))?"
    r"(?:\s+chunks_returned=(\d+))?"
)


@dataclass
class TimingRecord:
    step: str
    elapsed: float
    timestamp: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class StepStats:
    step: str
    count: int = 0
    total_time: float = 0.0
    min_time: float = float("inf")
    max_time: float = 0.0
    values: list[float] = field(default_factory=list)

    def add(self, elapsed: float):
        self.count += 1
        self.total_time += elapsed
        self.min_time = min(self.min_time, elapsed)
        self.max_time = max(self.max_time, elapsed)
        self.values.append(elapsed)

    @property
    def mean(self) -> float:
        return self.total_time / self.count if self.count else 0.0

    @property
    def median(self) -> float:
        if not self.values:
            return 0.0
        s = sorted(self.values)
        return s[len(s) // 2]

    def percentile(self, p: float) -> float:
        if not self.values:
            return 0.0
        s = sorted(self.values)
        idx = int(len(s) * p / 100)
        return s[min(idx, len(s) - 1)]

    @property
    def pct_of_total(self) -> float:
        return 0.0

    def to_dict(self) -> dict:
        result = {
            "step": self.step,
            "count": self.count,
            "min": round(self.min_time, 3),
            "max": round(self.max_time, 3),
            "mean": round(self.mean, 3),
            "median": round(self.median, 3),
            "p95": round(self.percentile(95), 3),
            "p99": round(self.percentile(99), 3),
        }
        if self.count > 1:
            result["stdev"] = round(statistics.stdev(self.values), 3) if len(self.values) > 1 else 0
        return result


def fetch_docker_logs(container: str, since: str = "") -> list[str]:
    """获取 Docker 容器的日志行。"""
    cmd = ["docker", "logs", container]
    if since:
        cmd.extend(["--since", since])
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30
        )
        return result.stdout.splitlines()
    except FileNotFoundError:
        print(f"  错误: docker 命令不可用", file=sys.stderr)
        return []
    except subprocess.TimeoutExpired:
        print(f"  错误: docker logs {container} 超时", file=sys.stderr)
        return []
    except Exception as e:
        print(f"  错误: 获取 {container} 日志失败: {e}", file=sys.stderr)
        return []


def read_log_files(paths: list[str]) -> list[str]:
    """从磁盘日志文件读取行。"""
    lines = []
    for path in paths:
        if not os.path.exists(path):
            print(f"  跳过不存在的文件: {path}", file=sys.stderr)
            continue
        try:
            with open(path) as f:
                lines.extend(f.readlines())
        except Exception as e:
            print(f"  读取 {path} 失败: {e}", file=sys.stderr)
    return lines


def parse_timing_lines(lines: list[str]) -> list[TimingRecord]:
    """从日志行中提取 [RETRIEVAL_TIMING] 记录。"""
    records = []
    for line in lines:
        m = TIMING_PATTERN.search(line)
        if not m:
            continue
        step = m.group(1)
        elapsed = float(m.group(2))
        total_val = m.group(3)
        chunks = m.group(4)
        chunks_returned = m.group(5)

        meta = {}
        if total_val is not None:
            meta["total"] = int(total_val)
        if chunks is not None:
            meta["chunks"] = int(chunks)
        if chunks_returned is not None:
            meta["chunks_returned"] = int(chunks_returned)

        # Try to extract timestamp from log line
        ts_match = re.match(r"^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}[.,]\d+)", line)
        ts = ts_match.group(1) if ts_match else ""

        records.append(TimingRecord(step=step, elapsed=elapsed, timestamp=ts, metadata=meta))

    return records


def analyze_records(records: list[TimingRecord]) -> dict[str, StepStats]:
    """按步骤聚合 timing 记录。"""
    stats: dict[str, StepStats] = {}
    for r in records:
        if r.step not in stats:
            stats[r.step] = StepStats(step=r.step)
        stats[r.step].add(r.elapsed)
    return stats


def print_report(stats: dict[str, StepStats], source: str):
    print("\n" + "=" * 70)
    print("  RAGFlow 检索管道耗时分析")
    print("=" * 70)
    print(f"\n  数据来源: {source}")
    print(f"  总记录数: {sum(s.count for s in stats.values())}")

    if not stats:
        print("\n  ⚠ 未找到 [RETRIEVAL_TIMING] 日志记录")
        print("  请确保:")
        print("    1. RAGFlow 源码已添加 timing 日志")
        print("    2. 在压测期间或之后获取日志")
        print("    3. 容器/日志文件包含相关日志")
        return

    total_elapsed = stats.get("total", StepStats(step="total")).mean

    # Order steps logically
    step_order = ["embedding", "doc_search", "rerank_model", "rerank_hybrid", "total"]
    ordered = []
    seen = set()
    for step in step_order:
        if step in stats and step not in seen:
            ordered.append(step)
            seen.add(step)
    for step in sorted(stats.keys()):
        if step not in seen:
            ordered.append(step)

    print(f"\n  {'步骤':<20} {'次数':>6} {'平均':>8} {'中位':>8} {'P95':>8} {'最小':>8} {'最大':>8} {'占比':>8}")
    print(f"  {'-'*20} {'-'*6} {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*8}")

    for step in ordered:
        s = stats[step]
        pct = f"{s.mean / total_elapsed * 100:.1f}%" if total_elapsed > 0 and step != "total" else "-"
        print(f"  {step:<20} {s.count:>6} {s.mean:>8.3f} {s.median:>8.3f} "
              f"{s.percentile(95):>8.3f} {s.min_time:>8.3f} {s.max_time:>8.3f} {pct:>8}")

    # Breakdown analysis
    print(f"\n  --- 耗时分解 ---")
    non_total = {k: v for k, v in stats.items() if k != "total"}
    if non_total and total_elapsed > 0:
        accounted = sum(s.mean for s in non_total.values())
        print(f"  已统计步骤耗时总和: {accounted:.3f}s")

        # Find bottleneck
        slowest = max(non_total.items(), key=lambda x: x[1].mean)
        print(f"  最大瓶颈: {slowest[0]} (平均 {slowest[1].mean:.3f}s, "
              f"占已统计时间的 {slowest[1].mean/accounted*100:.1f}%)")

        if accounted < total_elapsed:
            unaccounted = total_elapsed - accounted
            print(f"  未覆盖耗时: {unaccounted:.3f}s ({unaccounted/total_elapsed*100:.1f}%)")
            print(f"  (包括: 结果组装、文档聚合、子块合并、网络传输等)")

    # Variability check
    for step in non_total:
        s = stats[step]
        if s.count >= 5 and len(s.values) > 1:
            cv = statistics.stdev(s.values) / s.mean if s.mean > 0 else 0
            if cv > 1.0:
                print(f"\n  ⚠ {step} 的变异系数为 {cv:.2f}，延迟波动很大，可能存在排队或资源竞争")

    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="RAGFlow 检索日志分析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--config", help="从 JSON 配置文件加载")
    parser.add_argument("--containers", nargs="*", default=[], help="Docker 容器名称列表")
    parser.add_argument("--log-files", nargs="*", default=[], help="日志文件路径列表")
    parser.add_argument("--since", default="", help="Docker logs --since 参数 (如 10m, 1h)")
    parser.add_argument("--output-json", help="保存 JSON 分析结果")

    args = parser.parse_args()

    if args.config:
        with open(args.config) as f:
            data = json.load(f)
        log_cfg = data.get("log_analysis", {})
        if not args.containers:
            args.containers = log_cfg.get("containers", [])
        if not args.log_files:
            args.log_files = log_cfg.get("log_files", [])
        if not args.since:
            args.since = log_cfg.get("since", "")

    if not args.containers and not args.log_files:
        parser.error("需要 --containers 或 --log-files 或 --config 参数")

    all_lines = []
    sources = []

    for c in args.containers:
        print(f"获取容器日志: {c} ...")
        lines = fetch_docker_logs(c, args.since)
        all_lines.extend(lines)
        sources.append(f"container:{c}")
        print(f"  获取到 {len(lines)} 行")

    if args.log_files:
        print(f"读取日志文件: {args.log_files}")
        lines = read_log_files(args.log_files)
        all_lines.extend(lines)
        sources.append(f"files:{','.join(args.log_files)}")
        print(f"  读取到 {len(lines)} 行")

    records = parse_timing_lines(all_lines)
    print(f"\n解析到 {len(records)} 条 timing 记录")

    stats = analyze_records(records)
    print_report(stats, ", ".join(sources))

    if args.output_json and stats:
        output = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "type": "log_analysis",
            "source": sources,
            "total_records": len(records),
            "steps": {step: s.to_dict() for step, s in stats.items()},
        }
        os.makedirs(os.path.dirname(args.output_json) or ".", exist_ok=True)
        with open(args.output_json, "w") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"\nJSON 结果已保存至: {args.output_json}")


if __name__ == "__main__":
    main()
