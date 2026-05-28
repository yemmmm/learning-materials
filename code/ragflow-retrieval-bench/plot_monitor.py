#!/usr/bin/env python3
"""
RAGFlow HA 集群资源监控数据可视化

用法:
    python plot_monitor.py                          # 查找当前目录最新的 CSV
    python plot_monitor.py -c container_stats.csv -s server_stats.csv
    python plot_monitor.py -c container_stats.csv -s server_stats.csv -o plots/
"""

import argparse
import glob
import os
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

# 配色
PALETTE = [
    "#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f",
    "#edc948", "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac",
]


def find_latest(prefix: str, directory: str = ".") -> str | None:
    files = sorted(glob.glob(os.path.join(directory, f"{prefix}_*.csv")))
    return files[-1] if files else None


def load_container_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    # 过滤已停止的容器
    df = df[df["cpu_pct"] != "STOPPED"].copy()
    df["cpu_pct"] = pd.to_numeric(df["cpu_pct"], errors="coerce").fillna(0)
    for col in ["mem_usage_mb", "mem_limit_mb", "mem_pct",
                "net_in_kb", "net_out_kb", "block_in_kb", "block_out_kb"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def load_server_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    for col in ["cpu_pct", "mem_used_gb", "mem_total_gb", "mem_pct",
                "load_1m", "load_5m", "load_15m",
                "disk_used_gb", "disk_total_gb", "disk_pct"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def time_axis(ax, df: pd.DataFrame):
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right")


def plot_container_cpu(df: pd.DataFrame, output_dir: str):
    fig, ax = plt.subplots(figsize=(14, 5))
    for i, (name, grp) in enumerate(df.groupby("container")):
        ax.plot(grp["timestamp"], grp["cpu_pct"],
                label=name, color=PALETTE[i % len(PALETTE)], linewidth=1)
    ax.set_title("Container CPU Usage")
    ax.set_ylabel("CPU %")
    ax.set_xlabel("")
    ax.legend(loc="upper left", fontsize=8, ncol=3)
    ax.grid(True, alpha=0.3)
    time_axis(ax, df)
    fig.savefig(os.path.join(output_dir, "container_cpu.png"))
    plt.close(fig)


def plot_container_memory(df: pd.DataFrame, output_dir: str):
    fig, axes = plt.subplots(1, 2, figsize=(16, 5))

    # 内存使用量
    ax = axes[0]
    for i, (name, grp) in enumerate(df.groupby("container")):
        ax.plot(grp["timestamp"], grp["mem_usage_mb"],
                label=name, color=PALETTE[i % len(PALETTE)], linewidth=1)
    ax.set_title("Container Memory Usage")
    ax.set_ylabel("Memory (MB)")
    ax.legend(loc="upper left", fontsize=8, ncol=3)
    ax.grid(True, alpha=0.3)
    time_axis(ax, df)

    # 内存百分比
    ax = axes[1]
    for i, (name, grp) in enumerate(df.groupby("container")):
        ax.plot(grp["timestamp"], grp["mem_pct"],
                label=name, color=PALETTE[i % len(PALETTE)], linewidth=1)
    ax.set_title("Container Memory %")
    ax.set_ylabel("Memory %")
    ax.legend(loc="upper left", fontsize=8, ncol=3)
    ax.grid(True, alpha=0.3)
    time_axis(ax, df)

    fig.savefig(os.path.join(output_dir, "container_memory.png"))
    plt.close(fig)


def plot_container_network(df: pd.DataFrame, output_dir: str):
    fig, axes = plt.subplots(1, 2, figsize=(16, 5))

    for metric, ax, title in [
        ("net_in_kb", axes[0], "Network In (KB)"),
        ("net_out_kb", axes[1], "Network Out (KB)"),
    ]:
        for i, (name, grp) in enumerate(df.groupby("container")):
            ax.plot(grp["timestamp"], grp[metric],
                    label=name, color=PALETTE[i % len(PALETTE)], linewidth=1)
        ax.set_title(title)
        ax.set_ylabel("KB")
        ax.legend(loc="upper left", fontsize=8, ncol=3)
        ax.grid(True, alpha=0.3)
        time_axis(ax, df)

    fig.savefig(os.path.join(output_dir, "container_network.png"))
    plt.close(fig)


def plot_container_block_io(df: pd.DataFrame, output_dir: str):
    fig, axes = plt.subplots(1, 2, figsize=(16, 5))

    for metric, ax, title in [
        ("block_in_kb", axes[0], "Block I/O Read (KB)"),
        ("block_out_kb", axes[1], "Block I/O Write (KB)"),
    ]:
        for i, (name, grp) in enumerate(df.groupby("container")):
            ax.plot(grp["timestamp"], grp[metric],
                    label=name, color=PALETTE[i % len(PALETTE)], linewidth=1)
        ax.set_title(title)
        ax.set_ylabel("KB")
        ax.legend(loc="upper left", fontsize=8, ncol=3)
        ax.grid(True, alpha=0.3)
        time_axis(ax, df)

    fig.savefig(os.path.join(output_dir, "container_block_io.png"))
    plt.close(fig)


def plot_server_overview(df: pd.DataFrame, output_dir: str):
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))

    # CPU
    ax = axes[0][0]
    ax.fill_between(df["timestamp"], 0, df["cpu_pct"], alpha=0.3, color=PALETTE[0])
    ax.plot(df["timestamp"], df["cpu_pct"], color=PALETTE[0], linewidth=1)
    ax.set_title("Server CPU Usage")
    ax.set_ylabel("CPU %")
    ax.set_ylim(0, min(105, df["cpu_pct"].max() * 1.3 + 5))
    ax.grid(True, alpha=0.3)
    time_axis(ax, df)

    # 内存
    ax = axes[0][1]
    ax.fill_between(df["timestamp"], 0, df["mem_pct"], alpha=0.3, color=PALETTE[1])
    ax.plot(df["timestamp"], df["mem_pct"], color=PALETTE[1], linewidth=1)
    ax.set_title("Server Memory Usage")
    ax.set_ylabel("Memory %")
    ax.set_ylim(0, min(105, df["mem_pct"].max() * 1.3 + 5))
    ax.grid(True, alpha=0.3)
    time_axis(ax, df)

    # 负载
    ax = axes[1][0]
    ax.plot(df["timestamp"], df["load_1m"], label="1m", color=PALETTE[2], linewidth=1)
    ax.plot(df["timestamp"], df["load_5m"], label="5m", color=PALETTE[3], linewidth=1)
    ax.plot(df["timestamp"], df["load_15m"], label="15m", color=PALETTE[4], linewidth=1)
    ax.set_title("Server Load Average")
    ax.set_ylabel("Load")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    time_axis(ax, df)

    # 磁盘
    ax = axes[1][1]
    ax.fill_between(df["timestamp"], 0, df["disk_pct"], alpha=0.3, color=PALETTE[5])
    ax.plot(df["timestamp"], df["disk_pct"], color=PALETTE[5], linewidth=1)
    ax.set_title("Server Disk Usage (Root)")
    ax.set_ylabel("Disk %")
    ax.set_ylim(0, min(105, df["disk_pct"].max() * 1.3 + 5))
    ax.grid(True, alpha=0.3)
    time_axis(ax, df)

    fig.savefig(os.path.join(output_dir, "server_overview.png"))
    plt.close(fig)


def plot_resource_heatmap(df: pd.DataFrame, output_dir: str):
    """容器资源总览热力图 - 最终状态的快照"""
    latest = df.groupby("container").last().reset_index()
    if latest.empty:
        return

    metrics = ["cpu_pct", "mem_pct", "net_in_kb", "net_out_kb"]
    labels = ["CPU %", "Mem %", "Net In (KB)", "Net Out (KB)"]

    # 归一化到 0-1
    data = latest[metrics].copy()
    for col in metrics:
        max_val = data[col].max()
        data[col] = data[col] / max_val if max_val > 0 else 0

    fig, ax = plt.subplots(figsize=(max(8, len(metrics) * 2), max(4, len(latest) * 0.6 + 1)))
    im = ax.imshow(data.values, cmap="YlOrRd", aspect="auto")

    ax.set_xticks(range(len(metrics)))
    ax.set_xticklabels(labels)
    ax.set_yticks(range(len(latest)))
    ax.set_yticklabels(latest["container"].values)

    # 在每个格子上标注实际值
    for i in range(len(latest)):
        for j in range(len(metrics)):
            val = latest.iloc[i][metrics[j]]
            color = "white" if data.iloc[i, j] > 0.5 else "black"
            ax.text(j, i, f"{val:.1f}", ha="center", va="center",
                    color=color, fontsize=8)

    ax.set_title("Container Resource Heatmap (Latest Snapshot)")
    fig.colorbar(im, ax=ax, shrink=0.6)
    fig.savefig(os.path.join(output_dir, "container_heatmap.png"))
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="RAGFlow HA 资源监控数据可视化")
    parser.add_argument("-c", "--container-csv", help="容器 stats CSV 文件路径")
    parser.add_argument("-s", "--server-csv", help="服务器 stats CSV 文件路径")
    parser.add_argument("-d", "--csv-dir", default=".", help="CSV 文件所在目录（自动查找最新）")
    parser.add_argument("-o", "--output-dir", default=None, help="图片输出目录，默认与 CSV 同目录")
    args = parser.parse_args()

    container_csv = args.container_csv
    server_csv = args.server_csv

    if not container_csv:
        container_csv = find_latest("container_stats", args.csv_dir)
    if not server_csv:
        server_csv = find_latest("server_stats", args.csv_dir)

    output_dir = args.output_dir or args.csv_dir
    os.makedirs(output_dir, exist_ok=True)

    generated = []

    if container_csv and os.path.exists(container_csv):
        print(f"读取容器数据: {container_csv}")
        df_c = load_container_csv(container_csv)
        print(f"  容器数: {df_c['container'].nunique()}, 数据点: {len(df_c)}")

        plot_container_cpu(df_c, output_dir)
        generated.append("container_cpu.png")

        plot_container_memory(df_c, output_dir)
        generated.append("container_memory.png")

        plot_container_network(df_c, output_dir)
        generated.append("container_network.png")

        plot_container_block_io(df_c, output_dir)
        generated.append("container_block_io.png")

        plot_resource_heatmap(df_c, output_dir)
        generated.append("container_heatmap.png")
    else:
        print("警告: 未找到容器 CSV 文件", file=sys.stderr)

    if server_csv and os.path.exists(server_csv):
        print(f"读取服务器数据: {server_csv}")
        df_s = load_server_csv(server_csv)
        print(f"  数据点: {len(df_s)}")

        plot_server_overview(df_s, output_dir)
        generated.append("server_overview.png")
    else:
        print("警告: 未找到服务器 CSV 文件", file=sys.stderr)

    if generated:
        print(f"\n已生成 {len(generated)} 张图:")
        for f in generated:
            print(f"  {os.path.join(output_dir, f)}")
    else:
        print("未生成任何图表，请检查 CSV 文件是否存在", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
