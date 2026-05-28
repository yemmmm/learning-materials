#!/usr/bin/env python3
"""
RAGFlow HA 集群资源监控数据可视化

读取目录下所有 container_stats_*.csv 和 server_stats_*.csv，
按服务类型分组绘图，多节点同类服务合并展示。

用法:
    python plot_monitor.py                          # 读取当前目录所有 CSV
    python plot_monitor.py -d ./bench-data          # 指定 CSV 目录
    python plot_monitor.py -d ./bench-data -o ./plots
"""

import argparse
import glob
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

plt.rcParams["font.size"] = 10
plt.rcParams["figure.dpi"] = 150
plt.rcParams["figure.autolayout"] = True

NODE_COLORS = {
    "infra": "#76b7b2",
    "node1": "#4e79a7",
    "node2": "#f28e2b",
    "node3": "#e15759",
    "node4": "#59a14f",
    "node5": "#b07aa1",
}
NODE_LINE_STYLES = ["-", "--", ":", "-."]
DEFAULT_COLOR = "#bab0ac"


def parse_container_name(name: str) -> tuple[str, str]:
    """解析容器名 -> (service_type, node_label).

    ha-node1-web   -> ("web", "node1")
    ha-node2-web   -> ("web", "node2")
    ha-node1-worker -> ("worker", "node1")
    ha-mysql       -> ("mysql", "infra")
    ha-lb          -> ("lb", "infra")
    ha-es01        -> ("es", "infra")
    ha-minio       -> ("minio", "infra")
    ha-redis       -> ("redis", "infra")
    """
    m = re.match(r"^ha-(?:node(\d+)-)?(.+)$", name)
    if not m:
        return name, "unknown"
    node_num, svc = m.groups()
    if node_num:
        return svc, f"node{node_num}"
    return svc, "infra"


def node_label(name: str) -> str:
    """生成图例标签: infra 服务直接用服务名, 多节点服务加 node 标记."""
    svc, node = parse_container_name(name)
    if node == "infra":
        return svc
    return f"{svc} ({node})"


def get_line_style(node: str, idx: int) -> str:
    if node == "infra":
        return "-"
    return NODE_LINE_STYLES[idx % len(NODE_LINE_STYLES)]


def get_color(node: str) -> str:
    return NODE_COLORS.get(node, DEFAULT_COLOR)


def load_all_container_csvs(directory: str) -> pd.DataFrame:
    files = sorted(glob.glob(os.path.join(directory, "container_stats_*.csv")))
    if not files:
        return pd.DataFrame()
    frames = []
    for f in files:
        try:
            df = pd.read_csv(f)
            frames.append(df)
        except Exception as e:
            print(f"  跳过 {f}: {e}", file=sys.stderr)
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df[df["cpu_pct"] != "STOPPED"].copy()
    df["cpu_pct"] = pd.to_numeric(df["cpu_pct"], errors="coerce").fillna(0)
    for col in ["mem_usage_mb", "mem_limit_mb", "mem_pct",
                "net_in_kb", "net_out_kb", "block_in_kb", "block_out_kb"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["service"] = df["container"].map(lambda n: parse_container_name(n)[0])
    df["node"] = df["container"].map(lambda n: parse_container_name(n)[1])
    df["label"] = df["container"].map(node_label)
    return df


def load_all_server_csvs(directory: str) -> pd.DataFrame:
    files = sorted(glob.glob(os.path.join(directory, "server_stats_*.csv")))
    if not files:
        return pd.DataFrame()
    frames = []
    for f in files:
        try:
            df = pd.read_csv(f)
            frames.append(df)
        except Exception as e:
            print(f"  跳过 {f}: {e}", file=sys.stderr)
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    for col in ["cpu_pct", "mem_used_gb", "mem_total_gb", "mem_pct",
                "load_1m", "load_5m", "load_15m",
                "disk_used_gb", "disk_total_gb", "disk_pct"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df = df.sort_values("timestamp").drop_duplicates(subset=["timestamp"]).reset_index(drop=True)
    return df


def time_axis(ax, df: pd.DataFrame):
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right")


def plot_service_cpu(df: pd.DataFrame, output_dir: str):
    fig, ax = plt.subplots(figsize=(14, 5))
    for i, (label, grp) in enumerate(df.groupby("label", sort=False)):
        grp = grp.sort_values("timestamp")
        node = grp["node"].iloc[0]
        ax.plot(grp["timestamp"], grp["cpu_pct"],
                label=label, color=get_color(node),
                linestyle=get_line_style(node, i), linewidth=1)
    ax.set_title("All Services - CPU Usage")
    ax.set_ylabel("CPU %")
    ax.legend(loc="upper left", fontsize=8, ncol=2)
    ax.grid(True, alpha=0.3)
    time_axis(ax, df)
    fig.savefig(os.path.join(output_dir, "all_cpu.png"))
    plt.close(fig)


def plot_service_memory(df: pd.DataFrame, output_dir: str):
    fig, axes = plt.subplots(1, 2, figsize=(16, 5))

    ax = axes[0]
    for i, (label, grp) in enumerate(df.groupby("label", sort=False)):
        grp = grp.sort_values("timestamp")
        node = grp["node"].iloc[0]
        ax.plot(grp["timestamp"], grp["mem_usage_mb"],
                label=label, color=get_color(node),
                linestyle=get_line_style(node, i), linewidth=1)
    ax.set_title("All Services - Memory Usage")
    ax.set_ylabel("Memory (MB)")
    ax.legend(loc="upper left", fontsize=7, ncol=2)
    ax.grid(True, alpha=0.3)
    time_axis(ax, df)

    ax = axes[1]
    for i, (label, grp) in enumerate(df.groupby("label", sort=False)):
        grp = grp.sort_values("timestamp")
        node = grp["node"].iloc[0]
        ax.plot(grp["timestamp"], grp["mem_pct"],
                label=label, color=get_color(node),
                linestyle=get_line_style(node, i), linewidth=1)
    ax.set_title("All Services - Memory %")
    ax.set_ylabel("Memory %")
    ax.legend(loc="upper left", fontsize=7, ncol=2)
    ax.grid(True, alpha=0.3)
    time_axis(ax, df)

    fig.savefig(os.path.join(output_dir, "all_memory.png"))
    plt.close(fig)


def plot_service_network(df: pd.DataFrame, output_dir: str):
    fig, axes = plt.subplots(1, 2, figsize=(16, 5))
    for metric, ax, title in [
        ("net_in_kb", axes[0], "All Services - Network In"),
        ("net_out_kb", axes[1], "All Services - Network Out"),
    ]:
        for i, (label, grp) in enumerate(df.groupby("label", sort=False)):
            grp = grp.sort_values("timestamp")
            node = grp["node"].iloc[0]
            ax.plot(grp["timestamp"], grp[metric],
                    label=label, color=get_color(node),
                    linestyle=get_line_style(node, i), linewidth=1)
        ax.set_title(title)
        ax.set_ylabel("KB")
        ax.legend(loc="upper left", fontsize=7, ncol=2)
        ax.grid(True, alpha=0.3)
        time_axis(ax, df)
    fig.savefig(os.path.join(output_dir, "all_network.png"))
    plt.close(fig)


def plot_service_block_io(df: pd.DataFrame, output_dir: str):
    fig, axes = plt.subplots(1, 2, figsize=(16, 5))
    for metric, ax, title in [
        ("block_in_kb", axes[0], "All Services - Block I/O Read"),
        ("block_out_kb", axes[1], "All Services - Block I/O Write"),
    ]:
        for i, (label, grp) in enumerate(df.groupby("label", sort=False)):
            grp = grp.sort_values("timestamp")
            node = grp["node"].iloc[0]
            ax.plot(grp["timestamp"], grp[metric],
                    label=label, color=get_color(node),
                    linestyle=get_line_style(node, i), linewidth=1)
        ax.set_title(title)
        ax.set_ylabel("KB")
        ax.legend(loc="upper left", fontsize=7, ncol=2)
        ax.grid(True, alpha=0.3)
        time_axis(ax, df)
    fig.savefig(os.path.join(output_dir, "all_block_io.png"))
    plt.close(fig)


def plot_per_service_type(df: pd.DataFrame, output_dir: str):
    """按服务类型分组, 每种服务一张图, 多节点同图."""
    generated = []
    for svc, grp in df.groupby("service"):
        if len(grp) == 0:
            continue
        fig, axes = plt.subplots(2, 2, figsize=(16, 10))
        fig.suptitle(f"Service: {svc}", fontsize=14, fontweight="bold")

        # CPU
        ax = axes[0][0]
        for i, (label, sub) in enumerate(grp.groupby("label")):
            sub = sub.sort_values("timestamp")
            node = sub["node"].iloc[0]
            ax.plot(sub["timestamp"], sub["cpu_pct"],
                    label=label, color=get_color(node),
                    linestyle=get_line_style(node, i), linewidth=1)
        ax.set_title("CPU %")
        ax.set_ylabel("CPU %")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
        time_axis(ax, grp)

        # Memory
        ax = axes[0][1]
        for i, (label, sub) in enumerate(grp.groupby("label")):
            sub = sub.sort_values("timestamp")
            node = sub["node"].iloc[0]
            ax.plot(sub["timestamp"], sub["mem_usage_mb"],
                    label=label, color=get_color(node),
                    linestyle=get_line_style(node, i), linewidth=1)
        ax.set_title("Memory (MB)")
        ax.set_ylabel("MB")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
        time_axis(ax, grp)

        # Network
        ax = axes[1][0]
        for i, (label, sub) in enumerate(grp.groupby("label")):
            sub = sub.sort_values("timestamp")
            node = sub["node"].iloc[0]
            ax.plot(sub["timestamp"], sub["net_in_kb"],
                    label=f"{label} in", color=get_color(node), linewidth=1)
            ax.plot(sub["timestamp"], sub["net_out_kb"],
                    label=f"{label} out", color=get_color(node),
                    linestyle="--", linewidth=1)
        ax.set_title("Network I/O (KB)")
        ax.set_ylabel("KB")
        ax.legend(fontsize=7, ncol=2)
        ax.grid(True, alpha=0.3)
        time_axis(ax, grp)

        # Block I/O
        ax = axes[1][1]
        for i, (label, sub) in enumerate(grp.groupby("label")):
            sub = sub.sort_values("timestamp")
            node = sub["node"].iloc[0]
            ax.plot(sub["timestamp"], sub["block_in_kb"],
                    label=f"{label} read", color=get_color(node), linewidth=1)
            ax.plot(sub["timestamp"], sub["block_out_kb"],
                    label=f"{label} write", color=get_color(node),
                    linestyle="--", linewidth=1)
        ax.set_title("Block I/O (KB)")
        ax.set_ylabel("KB")
        ax.legend(fontsize=7, ncol=2)
        ax.grid(True, alpha=0.3)
        time_axis(ax, grp)

        fname = f"service_{svc}.png"
        fig.savefig(os.path.join(output_dir, fname))
        plt.close(fig)
        generated.append(fname)
    return generated


def plot_server_overview(dfs: list[pd.DataFrame], output_dir: str):
    """合并所有 server CSV 到一张图."""
    if not dfs:
        return
    df = pd.concat(dfs, ignore_index=True)
    df = df.sort_values("timestamp").drop_duplicates(subset=["timestamp"]).reset_index(drop=True)

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle("Server Resource Overview", fontsize=14, fontweight="bold")

    ax = axes[0][0]
    ax.fill_between(df["timestamp"], 0, df["cpu_pct"], alpha=0.3, color="#4e79a7")
    ax.plot(df["timestamp"], df["cpu_pct"], color="#4e79a7", linewidth=1)
    ax.set_title("CPU Usage")
    ax.set_ylabel("CPU %")
    ax.set_ylim(0, min(105, df["cpu_pct"].max() * 1.3 + 5))
    ax.grid(True, alpha=0.3)
    time_axis(ax, df)

    ax = axes[0][1]
    ax.fill_between(df["timestamp"], 0, df["mem_pct"], alpha=0.3, color="#f28e2b")
    ax.plot(df["timestamp"], df["mem_pct"], color="#f28e2b", linewidth=1)
    ax.set_title("Memory Usage")
    ax.set_ylabel("Memory %")
    ax.set_ylim(0, min(105, df["mem_pct"].max() * 1.3 + 5))
    ax.grid(True, alpha=0.3)
    time_axis(ax, df)

    ax = axes[1][0]
    ax.plot(df["timestamp"], df["load_1m"], label="1m", linewidth=1)
    ax.plot(df["timestamp"], df["load_5m"], label="5m", linewidth=1)
    ax.plot(df["timestamp"], df["load_15m"], label="15m", linewidth=1)
    ax.set_title("Load Average")
    ax.set_ylabel("Load")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    time_axis(ax, df)

    ax = axes[1][1]
    ax.fill_between(df["timestamp"], 0, df["disk_pct"], alpha=0.3, color="#59a14f")
    ax.plot(df["timestamp"], df["disk_pct"], color="#59a14f", linewidth=1)
    ax.set_title("Disk Usage (Root)")
    ax.set_ylabel("Disk %")
    ax.set_ylim(0, min(105, df["disk_pct"].max() * 1.3 + 5))
    ax.grid(True, alpha=0.3)
    time_axis(ax, df)

    fig.savefig(os.path.join(output_dir, "server_overview.png"))
    plt.close(fig)


def plot_heatmap(df: pd.DataFrame, output_dir: str):
    """所有容器资源热力图."""
    latest = df.groupby("container").last().reset_index()
    if latest.empty:
        return
    latest = latest.sort_values("label")

    metrics = ["cpu_pct", "mem_pct", "net_in_kb", "net_out_kb"]
    labels = ["CPU %", "Mem %", "Net In (KB)", "Net Out (KB)"]

    data = latest[metrics].copy()
    for col in metrics:
        mx = data[col].max()
        data[col] = data[col] / mx if mx > 0 else 0

    fig, ax = plt.subplots(figsize=(max(8, len(metrics) * 2.2),
                                    max(4, len(latest) * 0.6 + 1)))
    im = ax.imshow(data.values, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(range(len(metrics)))
    ax.set_xticklabels(labels)
    ax.set_yticks(range(len(latest)))
    ax.set_yticklabels(latest["label"].values)

    for i in range(len(latest)):
        for j in range(len(metrics)):
            val = latest.iloc[i][metrics[j]]
            color = "white" if data.iloc[i, j] > 0.5 else "black"
            ax.text(j, i, f"{val:.1f}", ha="center", va="center",
                    color=color, fontsize=8)

    ax.set_title("Container Resource Heatmap (Latest Snapshot)")
    fig.colorbar(im, ax=ax, shrink=0.6)
    fig.savefig(os.path.join(output_dir, "heatmap.png"))
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="RAGFlow HA 资源监控数据可视化")
    parser.add_argument("-d", "--csv-dir", default=".", help="CSV 文件目录，默认当前目录")
    parser.add_argument("-o", "--output-dir", default=None, help="图片输出目录，默认与 CSV 同目录")
    args = parser.parse_args()

    output_dir = args.output_dir or args.csv_dir
    os.makedirs(output_dir, exist_ok=True)
    generated = []

    # ── 容器数据 ──
    container_files = sorted(glob.glob(os.path.join(args.csv_dir, "container_stats_*.csv")))
    if container_files:
        print(f"读取 {len(container_files)} 个容器 CSV 文件...")
        df_c = load_all_container_csvs(args.csv_dir)
        if not df_c.empty:
            services = df_c["service"].unique()
            print(f"  服务: {', '.join(sorted(services))}")
            print(f"  容器: {', '.join(df_c['label'].unique())}")
            print(f"  数据点: {len(df_c)}")

            plot_service_cpu(df_c, output_dir)
            generated.append("all_cpu.png")

            plot_service_memory(df_c, output_dir)
            generated.append("all_memory.png")

            plot_service_network(df_c, output_dir)
            generated.append("all_network.png")

            plot_service_block_io(df_c, output_dir)
            generated.append("all_block_io.png")

            plot_heatmap(df_c, output_dir)
            generated.append("heatmap.png")

            svc_files = plot_per_service_type(df_c, output_dir)
            generated.extend(svc_files)
        else:
            print("  容器数据为空")
    else:
        print("警告: 未找到 container_stats_*.csv 文件", file=sys.stderr)

    # ── 服务器数据 ──
    server_files = sorted(glob.glob(os.path.join(args.csv_dir, "server_stats_*.csv")))
    if server_files:
        print(f"\n读取 {len(server_files)} 个服务器 CSV 文件...")
        dfs = []
        for f in server_files:
            try:
                dfs.append(load_all_server_csvs(os.path.dirname(f) or ".").pipe(
                    lambda d: d[d["timestamp"].between(
                        pd.Timestamp.min, pd.Timestamp.max
                    )]
                ))
            except Exception:
                pass
        # 简化: 直接合并所有 server CSV
        df_s = load_all_server_csvs(args.csv_dir)
        if not df_s.empty:
            print(f"  数据点: {len(df_s)}")
            plot_server_overview([df_s], output_dir)
            generated.append("server_overview.png")
        else:
            print("  服务器数据为空")
    else:
        print("警告: 未找到 server_stats_*.csv 文件", file=sys.stderr)

    if generated:
        print(f"\n已生成 {len(generated)} 张图:")
        for f in generated:
            print(f"  {os.path.join(output_dir, f)}")
    else:
        print("未生成任何图表，请检查 CSV 文件", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
