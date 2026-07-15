#!/usr/bin/env python3
"""
Dify Workflow Performance Log Analyzer

Analyzes [PERF_TIMING] logs collected by collect_perf_logs.py.
Generates a detailed performance report showing time spent at each stage.
Compatible with Python 3.6+, no third-party dependencies.

Usage:
    python3 analyze_perf_logs.py perf_logs.json
    python3 analyze_perf_logs.py perf_logs.json --report report.txt
    python3 analyze_perf_logs.py perf_logs.json --csv perf_data.csv
"""

from __future__ import print_function, division

import argparse
import json
import os
import sys
from collections import defaultdict


def group_by_workflow_run(entries):
    """Group PERF_TIMING entries by workflow_run_id."""
    groups = defaultdict(list)
    for entry in entries:
        run_id = entry.get("workflow_run_id")
        if run_id:
            groups[run_id].append(entry)
    return dict(groups)


def analyze_workflow_run(run_id, entries):
    """Analyze a single workflow run's timing data."""
    result = {
        "workflow_run_id": run_id,
        "workflow_id": None,
        "app_id": None,
        "queue_wait_time": None,
        "total_elapsed": None,
        "node_count": 0,
        "nodes": [],
        "llm_nodes": [],
    }

    enqueue_ts = None
    dequeue_ts = None

    # Use the first entry's workflow_id/app_id as fallback
    for e in entries:
        if e.get("workflow_id"):
            result["workflow_id"] = e["workflow_id"]
            break
    for e in entries:
        if e.get("app_id"):
            result["app_id"] = e["app_id"]
            break

    # Phase 1: extract timing data
    node_start_times = {}
    node_info = {}

    for entry in entries:
        event = entry.get("event", "")

        if event == "task_enqueue":
            enqueue_ts = entry.get("timestamp")
        elif event == "task_dequeue":
            dequeue_ts = entry.get("timestamp")

        elif event == "node_start":
            nid = entry.get("node_id")
            if nid:
                node_start_times[nid] = entry.get("timestamp")
                node_info[nid] = {
                    "node_type": entry.get("node_type", "unknown"),
                    "node_title": entry.get("node_title", "unknown"),
                }

        elif event == "node_succeeded":
            nid = entry.get("node_id")
            elapsed = entry.get("elapsed")
            if nid and elapsed is not None:
                info = node_info.get(nid, {})
                result["nodes"].append({
                    "node_id": nid,
                    "node_type": info.get("node_type", entry.get("node_type", "unknown")),
                    "node_title": info.get("node_title", "unknown"),
                    "elapsed": elapsed,
                })
                result["node_count"] += 1

        elif event == "node_failed":
            nid = entry.get("node_id")
            if nid:
                info = node_info.get(nid, {})
                result["nodes"].append({
                    "node_id": nid,
                    "node_type": info.get("node_type", entry.get("node_type", "unknown")),
                    "node_title": info.get("node_title", "unknown"),
                    "elapsed": entry.get("elapsed", 0),
                    "error": entry.get("error", ""),
                })

        elif event == "llm_invoke_completed":
            result["llm_nodes"].append({
                "node_id": entry.get("node_id", "unknown"),
                "model": entry.get("model", "unknown"),
                "latency": entry.get("latency", 0),
                "time_to_first_token": entry.get("time_to_first_token", 0),
                "time_to_generate": entry.get("time_to_generate", 0),
                "prompt_tokens": entry.get("prompt_tokens", 0),
                "completion_tokens": entry.get("completion_tokens", 0),
                "total_tokens": entry.get("total_tokens", 0),
            })

        elif event == "graph_end":
            result["total_elapsed"] = entry.get("total_elapsed")

    # Calculate queue wait time
    if enqueue_ts is not None and dequeue_ts is not None:
        result["queue_wait_time"] = dequeue_ts - enqueue_ts

    return result


def format_duration(seconds):
    """Format duration for display."""
    if seconds is None:
        return "N/A"
    if seconds < 1:
        return "{:.1f} ms".format(seconds * 1000)
    if seconds < 60:
        return "{:.3f} s".format(seconds)
    minutes = int(seconds // 60)
    secs = seconds % 60
    return "{}m {:.1f}s".format(minutes, secs)


def generate_text_report(analyses):
    """Generate a human-readable text report."""
    lines = []
    lines.append("=" * 80)
    lines.append("Dify Workflow Performance Analysis Report")
    lines.append("=" * 80)
    lines.append("Total workflow runs analyzed: {}".format(len(analyses)))
    lines.append("")

    # Aggregate statistics
    all_queue_times = []
    all_total_times = []
    all_node_times = defaultdict(list)
    all_llm_latencies = []
    all_llm_ttft = []
    all_llm_generate_times = []

    for result in analyses:
        qt = result["queue_wait_time"]
        if qt is not None:
            all_queue_times.append(qt)

        tt = result["total_elapsed"]
        if tt is not None:
            all_total_times.append(tt)

        for node in result["nodes"]:
            all_node_times[node["node_type"]].append(node["elapsed"])

        for llm in result["llm_nodes"]:
            if llm["latency"]:
                all_llm_latencies.append(llm["latency"])
            if llm["time_to_first_token"]:
                all_llm_ttft.append(llm["time_to_first_token"])
            if llm["time_to_generate"]:
                all_llm_generate_times.append(llm["time_to_generate"])

    # Summary statistics
    lines.append("-" * 80)
    lines.append("SUMMARY STATISTICS")
    lines.append("-" * 80)
    lines.append("")

    def print_stat(lines, name, values):
        if not values:
            lines.append("  {}: No data".format(name))
            return
        avg = sum(values) / len(values)
        lines.append("  {}:".format(name))
        lines.append("    Count:  {}".format(len(values)))
        lines.append("    Avg:    {}".format(format_duration(avg)))
        lines.append("    Min:    {}".format(format_duration(min(values))))
        lines.append("    Max:    {}".format(format_duration(max(values))))
        lines.append("")

    print_stat(lines, "Queue Wait Time (enqueue -> dequeue)", all_queue_times)
    print_stat(lines, "Total Workflow Execution Time", all_total_times)
    print_stat(lines, "LLM Total Latency", all_llm_latencies)
    print_stat(lines, "LLM Time To First Token (TTFT)", all_llm_ttft)
    print_stat(lines, "LLM Token Generation Time", all_llm_generate_times)

    for node_type, times in sorted(all_node_times.items()):
        print_stat(lines, "Node Type '{}' Execution Time".format(node_type), times)

    # Per-run details
    lines.append("-" * 80)
    lines.append("PER-RUN DETAILS")
    lines.append("-" * 80)
    lines.append("")

    for i, result in enumerate(analyses, 1):
        lines.append("--- Run #{} ---".format(i))
        lines.append("  Workflow Run ID: {}".format(result["workflow_run_id"]))
        lines.append("  Workflow ID:     {}".format(result["workflow_id"] or "N/A"))
        lines.append("  Queue Wait Time: {}".format(
            format_duration(result["queue_wait_time"])))
        lines.append("  Total Elapsed:   {}".format(
            format_duration(result["total_elapsed"])))

        # Time breakdown
        if result["total_elapsed"] and result["queue_wait_time"]:
            actual_work = result["total_elapsed"]
            queue = result["queue_wait_time"]
            total_wall = actual_work + queue
            lines.append("  Total Wall Time: {}".format(format_duration(total_wall)))
            if total_wall > 0:
                lines.append("    Queue overhead: {:.1f}%".format(
                    queue / total_wall * 100))

        # Node breakdown
        if result["nodes"]:
            lines.append("  Nodes:")
            for node in result["nodes"]:
                err = " [FAILED: {}]".format(node.get("error", "")) if node.get("error") else ""
                lines.append("    - {} ({}) {}: {}{}".format(
                    node["node_id"][:20],
                    node["node_type"],
                    node.get("node_title", ""),
                    format_duration(node["elapsed"]),
                    err,
                ))

        # LLM metrics
        if result["llm_nodes"]:
            for llm in result["llm_nodes"]:
                lines.append("  LLM Node {} (model: {}):".format(
                    llm["node_id"][:20], llm["model"]))
                lines.append("    Latency:          {}".format(
                    format_duration(llm["latency"])))
                lines.append("    Time to 1st token: {}".format(
                    format_duration(llm["time_to_first_token"])))
                lines.append("    Generate time:    {}".format(
                    format_duration(llm["time_to_generate"])))
                lines.append("    Tokens:           {} prompt + {} completion = {}".format(
                    llm["prompt_tokens"],
                    llm["completion_tokens"],
                    llm["total_tokens"],
                ))

        lines.append("")

    return "\n".join(lines)


def generate_csv(analyses, output_path):
    """Generate CSV files for further analysis."""
    # Nodes CSV
    node_csv = os.path.splitext(output_path)[0] + "_nodes.csv"
    with open(node_csv, "w") as f:
        f.write("workflow_run_id,workflow_id,node_id,node_type,node_title,elapsed_seconds\n")
        for result in analyses:
            for node in result["nodes"]:
                f.write("{},{},{},{},{},{:.6f}\n".format(
                    result["workflow_run_id"],
                    result["workflow_id"] or "",
                    node["node_id"],
                    node["node_type"],
                    node.get("node_title", "").replace(",", ";"),
                    node["elapsed"],
                ))

    # LLM CSV
    llm_csv = os.path.splitext(output_path)[0] + "_llm.csv"
    with open(llm_csv, "w") as f:
        f.write("workflow_run_id,node_id,model,latency,ttft,generate_time,prompt_tokens,completion_tokens,total_tokens\n")
        for result in analyses:
            for llm in result["llm_nodes"]:
                f.write("{},{},{},{:.6f},{:.6f},{:.6f},{},{},{}\n".format(
                    result["workflow_run_id"],
                    llm["node_id"],
                    llm["model"],
                    llm["latency"],
                    llm["time_to_first_token"],
                    llm["time_to_generate"],
                    llm["prompt_tokens"],
                    llm["completion_tokens"],
                    llm["total_tokens"],
                ))

    # Summary CSV
    summary_csv = os.path.splitext(output_path)[0] + "_summary.csv"
    with open(summary_csv, "w") as f:
        f.write("workflow_run_id,workflow_id,queue_wait_seconds,total_elapsed_seconds,node_count,llm_node_count\n")
        for result in analyses:
            qt_str = "{:.6f}".format(result["queue_wait_time"]) if result["queue_wait_time"] is not None else ""
            te_str = "{:.6f}".format(result["total_elapsed"]) if result["total_elapsed"] is not None else ""
            f.write("{},{},{},{},{},{}\n".format(
                result["workflow_run_id"],
                result["workflow_id"] or "",
                qt_str,
                te_str,
                result["node_count"],
                len(result["llm_nodes"]),
            ))

    print("CSV files written: {}, {}, {}".format(node_csv, llm_csv, summary_csv))


def main():
    parser = argparse.ArgumentParser(
        description="Analyze Dify workflow performance timing logs"
    )
    parser.add_argument(
        "input",
        help="JSON log file from collect_perf_logs.py",
    )
    parser.add_argument(
        "--report", "-r",
        default=None,
        help="Output text report file (default: print to stdout)",
    )
    parser.add_argument(
        "--csv", "-c",
        default=None,
        help="Output CSV files prefix (generates _nodes.csv, _llm.csv, _summary.csv)",
    )
    parser.add_argument(
        "--top", "-t",
        type=int,
        default=0,
        help="Show only top N slowest runs in report",
    )

    args = parser.parse_args()

    # Load data
    with open(args.input, "r") as f:
        entries = json.load(f)

    print("Loaded {} PERF_TIMING entries".format(len(entries)), file=sys.stderr)

    # Group by workflow run
    groups = group_by_workflow_run(entries)
    print("Found {} unique workflow runs".format(len(groups)), file=sys.stderr)

    # Analyze each run
    analyses = []
    for run_id, run_entries in groups.items():
        result = analyze_workflow_run(run_id, run_entries)
        analyses.append(result)

    # Sort by total elapsed (descending)
    analyses.sort(
        key=lambda r: r["total_elapsed"] if r["total_elapsed"] else 0,
        reverse=True,
    )

    # Filter top N if requested
    if args.top > 0:
        analyses = analyses[:args.top]
        print("Showing top {} slowest runs".format(args.top), file=sys.stderr)

    # Generate report
    report = generate_text_report(analyses)

    if args.report:
        with open(args.report, "w") as f:
            f.write(report)
        print("Report written to {}".format(args.report), file=sys.stderr)
    else:
        print(report)

    # Generate CSV if requested
    if args.csv:
        generate_csv(analyses, args.csv)

    return 0


if __name__ == "__main__":
    sys.exit(main())
