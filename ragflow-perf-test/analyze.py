#!/usr/bin/env python3
"""
RAGFlow 压测结果分析脚本

读取 bench_retrieval.py 输出的 summary.json 和（可选的）monitor.py CSV，
生成瓶颈分析报告。

用法:
  # 单次结果分析
  python analyze.py --input results/20240601_120000/

  # 对比两次测试（如调优前后）
  python analyze.py --input results/test1 --compare results/test2

  # 输出 Markdown 报告
  python analyze.py --input results/20240601_120000/ --output report.md
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# 报告生成
# ---------------------------------------------------------------------------


def generate_report(
    summary: dict,
    monitor_data: Optional[Dict[str, List[Dict]]] = None,
    label: str = "",
) -> str:
    """根据 summary.json 生成 Markdown 格式分析报告。"""
    cfg = summary.get("test_config", {})
    rounds = summary.get("rounds", [])
    ba = summary.get("bottleneck_analysis", {})

    lines = []
    title = "RAGFlow 性能压测分析报告"
    if label:
        title += " - " + label
    lines.append("# " + title)
    lines.append("")
    lines.append("**测试时间**: " + cfg.get("timestamp", "N/A"))
    lines.append("**目标地址**: " + cfg.get("url", "N/A"))
    lines.append("**测试模式**: " + cfg.get("mode", "N/A"))
    lines.append("**测试时长**: " + str(cfg.get("duration_s", "N/A")) + "s/轮")
    lines.append("")

    # ---- 结果汇总表 ----
    lines.append("## 1. 结果汇总")
    lines.append("")
    lines.append("| 并发 | QPS | P50(s) | P95(s) | P99(s) | Avg(s) | 成功 | 失败 | 成功率 |")
    lines.append("|------|-----|--------|--------|--------|--------|------|------|--------|")
    for r in rounds:
        rate = (r["success"] / r["total"] * 100) if r["total"] > 0 else 0
        lines.append(
            "| {c} | {qps} | {p50} | {p95} | {p99} | {avg} | {ok} | {fail} | {rate:.1f}% |".format(
                c=r["concurrency"],
                qps=r["qps"],
                p50=r["p50_s"],
                p95=r["p95_s"],
                p99=r["p99_s"],
                avg=r["avg_s"],
                ok=r["success"],
                fail=r["failure"],
                rate=rate,
            )
        )
    lines.append("")

    # ---- QPS 趋势 ----
    lines.append("## 2. QPS 与延迟趋势")
    lines.append("")
    if len(rounds) >= 2:
        lines.append("### QPS 随并发变化")
        lines.append("")
        qps_vals = " → ".join(str(r["qps"]) for r in rounds)
        lines.append("```")
        lines.append("并发: " + " → ".join(str(r["concurrency"]) for r in rounds))
        lines.append("QPS:  " + qps_vals)
        lines.append("```")
        lines.append("")

        lines.append("### P50/P95/P99 延迟随并发变化")
        lines.append("")
        lines.append("| 并发 | P50(s) | P95(s) | P99(s) | P95/P50 |")
        lines.append("|------|--------|--------|--------|---------|")
        for r in rounds:
            ratio = (r["p95_s"] / r["p50_s"]) if r["p50_s"] > 0 else 0
            lines.append(
                "| {c} | {p50} | {p95} | {p99} | {ratio:.1f}x |".format(
                    c=r["concurrency"], p50=r["p50_s"],
                    p95=r["p95_s"], p99=r["p99_s"], ratio=ratio,
                )
            )
        lines.append("")

        # P95/P50 比值 > 3 说明排队严重
        for r in rounds:
            ratio = (r["p95_s"] / r["p50_s"]) if r["p50_s"] > 0 else 0
            if ratio > 3:
                lines.append(
                    "> **警告**: 并发 {c} 时 P95 是 P50 的 {ratio:.1f} 倍，"
                    "尾部延迟严重，请求排队时间过长。".format(c=r["concurrency"], ratio=ratio)
                )
                lines.append("")
                break

    # ---- 错误分析 ----
    lines.append("## 3. 错误分析")
    lines.append("")
    has_errors = False
    for r in rounds:
        if r.get("error_distribution"):
            has_errors = True
            lines.append("### 并发 " + str(r["concurrency"]))
            lines.append("")
            for etype, count in r["error_distribution"].items():
                lines.append("- **" + etype + "**: " + str(count) + " 次")
            lines.append("")

    if not has_errors:
        lines.append("全部请求成功，无错误。")
        lines.append("")

    # ---- 瓶颈分析 ----
    lines.append("## 4. 瓶颈分析")
    lines.append("")
    lines.append("| 瓶颈类型 | 概率 |")
    lines.append("|----------|------|")
    lines.append("| CPU | " + ba.get("cpu_bottleneck_probability", "N/A") + " |")
    lines.append("| Embedding API | " + ba.get("embedding_bottleneck_probability", "N/A") + " |")
    lines.append("| Elasticsearch | " + ba.get("es_bottleneck_probability", "N/A") + " |")
    lines.append("")

    findings = ba.get("findings", [])
    if findings:
        lines.append("### 分析结论")
        lines.append("")
        for f in findings:
            lines.append("- " + f)
        lines.append("")

    lines.append("### 推荐配置")
    lines.append("")
    lines.append("- **推荐并发上限**: " + str(ba.get("recommended_max_concurrency", "N/A")))
    lines.append("- **预估最大 QPS**: " + str(ba.get("estimated_max_qps", "N/A")))
    lines.append("")

    # ---- 对比分析 ----
    if monitor_data:
        lines.append("## 5. 服务端资源概览")
        lines.append("")
        for host, metrics in monitor_data.items():
            if not metrics:
                continue
            lines.append("### " + host)
            lines.append("")
            # 聚合统计
            cpu_vals = [m["cpu_pct"] for m in metrics if m.get("cpu_pct", 0) > 0]
            mem_vals = [m["mem_pct"] for m in metrics if m.get("mem_pct", 0) > 0]
            if cpu_vals:
                lines.append("- CPU: avg {:.1f}%, max {:.1f}%".format(
                    sum(cpu_vals) / len(cpu_vals), max(cpu_vals)))
            if mem_vals:
                lines.append("- Memory: avg {:.1f}%, max {:.1f}%".format(
                    sum(mem_vals) / len(mem_vals), max(mem_vals)))
            # 网络
            net_rx = [m["net_rx_bytes_s"] for m in metrics if m.get("net_rx_bytes_s", 0) > 0]
            net_tx = [m["net_tx_bytes_s"] for m in metrics if m.get("net_tx_bytes_s", 0) > 0]
            if net_rx:
                lines.append("- Network RX: avg {:.1f} MB/s, max {:.1f} MB/s".format(
                    sum(net_rx) / len(net_rx) / 1e6, max(net_rx) / 1e6))
            if net_tx:
                lines.append("- Network TX: avg {:.1f} MB/s, max {:.1f} MB/s".format(
                    sum(net_tx) / len(net_tx) / 1e6, max(net_tx) / 1e6))
            lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 对比分析
# ---------------------------------------------------------------------------


def compare_reports(summary_a: dict, summary_b: dict, label_a: str, label_b: str) -> str:
    """生成两个测试结果的对比报告。"""
    rounds_a = summary_a.get("rounds", [])
    rounds_b = summary_b.get("rounds", [])

    lines = []
    lines.append("# 性能对比报告: " + label_a + " vs " + label_b)
    lines.append("")

    # 找到共同并发
    concurrency_a = {r["concurrency"]: r for r in rounds_a}
    concurrency_b = {r["concurrency"]: r for r in rounds_b}
    common = sorted(set(concurrency_a.keys()) & set(concurrency_b.keys()))

    if not common:
        lines.append("两次测试的并发梯度不同，无法直接对比。")
        return "\n".join(lines)

    lines.append("## QPS 对比")
    lines.append("")
    lines.append("| 并发 | " + label_a + " QPS | " + label_b + " QPS | 变化 |")
    lines.append("|------|------|------|------|")
    for c in common:
        qps_a = concurrency_a[c]["qps"]
        qps_b = concurrency_b[c]["qps"]
        delta = ((qps_b - qps_a) / qps_a * 100) if qps_a > 0 else 0
        sign = "+" if delta >= 0 else ""
        lines.append("| {c} | {a} | {b} | {sign}{delta:.1f}% |".format(
            c=c, a=qps_a, b=qps_b, sign=sign, delta=delta))
    lines.append("")

    lines.append("## P95 延迟对比")
    lines.append("")
    lines.append("| 并发 | " + label_a + " P95(s) | " + label_b + " P95(s) | 变化 |")
    lines.append("|------|------|------|------|")
    for c in common:
        p95_a = concurrency_a[c]["p95_s"]
        p95_b = concurrency_b[c]["p95_s"]
        delta = ((p95_b - p95_a) / p95_a * 100) if p95_a > 0 else 0
        sign = "+" if delta >= 0 else ""
        lines.append("| {c} | {a} | {b} | {sign}{delta:.1f}% |".format(
            c=c, a=p95_a, b=p95_b, sign=sign, delta=delta))
    lines.append("")

    lines.append("## 结论")
    lines.append("")

    # 总体 QPS 差异
    avg_delta = 0
    count = 0
    for c in common:
        qps_a = concurrency_a[c]["qps"]
        qps_b = concurrency_b[c]["qps"]
        if qps_a > 0:
            avg_delta += (qps_b - qps_a) / qps_a * 100
            count += 1
    avg_delta = avg_delta / count if count > 0 else 0

    if avg_delta > 10:
        lines.append("- " + label_b + " 的 QPS 比 " + label_a
                     + " 平均提升 {:.1f}%".format(avg_delta))
    elif avg_delta < -10:
        lines.append("- " + label_b + " 的 QPS 比 " + label_a
                     + " 平均下降 {:.1f}%".format(abs(avg_delta)))
    else:
        lines.append("- 两次测试 QPS 差异在 10% 以内，无明显变化")

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 主程序
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="RAGFlow 压测结果分析脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python analyze.py --input results/20240601_120000/
  python analyze.py --input results/test1 --compare results/test2
  python analyze.py --input results/20240601_120000/ --output report.md
        """,
    )
    parser.add_argument("--input", required=True,
                        help="结果目录路径（包含 summary.json）")
    parser.add_argument("--compare", default="",
                        help="对比的另一个结果目录路径")
    parser.add_argument("--output", default="",
                        help="输出报告路径（默认打印到终端）")
    parser.add_argument("--label", default="",
                        help="当前测试的标签")
    parser.add_argument("--label-compare", default="",
                        help="对比测试的标签")

    args = parser.parse_args()

    input_dir = Path(args.input)
    summary_path = input_dir / "summary.json"
    if not summary_path.exists():
        print("错误: 找不到 " + str(summary_path))
        sys.exit(1)

    summary = json.loads(summary_path.read_text())
    label = args.label or input_dir.name

    # 加载监控数据（如果存在）
    monitor_data = {}
    for f in input_dir.glob("monitor_*.csv"):
        host = f.stem.replace("monitor_", "")
        monitor_data[host] = _load_monitor_csv(f)

    # 生成报告
    report = generate_report(summary, monitor_data or None, label)

    # 对比分析
    if args.compare:
        compare_dir = Path(args.compare)
        compare_summary_path = compare_dir / "summary.json"
        if compare_summary_path.exists():
            compare_summary = json.loads(compare_summary_path.read_text())
            label_compare = args.label_compare or compare_dir.name
            compare_report = compare_reports(
                summary, compare_summary, label, label_compare
            )
            report += "\n\n" + compare_report
        else:
            print("警告: 找不到对比文件 " + str(compare_summary_path))

    # 输出
    if args.output:
        Path(args.output).write_text(report)
        print("报告已保存: " + args.output)
    else:
        print(report)


def _load_monitor_csv(path: Path) -> List[Dict]:
    """加载 monitor.py 输出的 CSV 文件。"""
    import csv
    rows = []
    try:
        with open(path, newline="") as f:
            for row in csv.DictReader(f):
                for k in ("cpu_pct", "mem_pct", "net_rx_bytes_s", "net_tx_bytes_s"):
                    try:
                        row[k] = float(row.get(k, 0))
                    except (ValueError, TypeError):
                        row[k] = 0.0
                rows.append(row)
    except Exception:
        pass
    return rows


if __name__ == "__main__":
    main()
