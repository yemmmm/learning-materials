#!/usr/bin/env python3
"""
RAGFlow 检索性能压测工具 —— 交互式主控脚本

功能:
  - 检索 API 并发压测
  - Embedding 模型并发测试
  - Docker 容器资源监控
  - 检索管道耗时分析 (需配合 RAGFlow 源码 timing 日志)
  - 交互式配置: 首次执行配置参数，后续执行确认或修改

用法:
    python run_bench.py                        # 交互式执行
    python run_bench.py --config bench_config.json  # 使用指定配置文件
    python run_bench.py --skip-retrieval       # 跳过检索压测
    python run_bench.py --skip-embedding       # 跳过 embedding 测试
    python run_bench.py --skip-monitor         # 跳过资源监控

配置持久化:
    配置文件默认保存在 ./bench_config.json
    首次运行会引导用户输入所有参数
    再次运行会展示当前配置，询问是否修改
"""

import json
import os
import shlex
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = SCRIPT_DIR / "bench_config.json"
MONITOR_SCRIPT = SCRIPT_DIR / "monitor_resources.sh"
BENCH_RETRIEVAL = SCRIPT_DIR / "bench_retrieval.py"
BENCH_EMBEDDING = SCRIPT_DIR / "bench_embedding.py"
ANALYZE_LOGS = SCRIPT_DIR / "analyze_logs.py"


def green(s):
    return f"\033[32m{s}\033[0m"


def yellow(s):
    return f"\033[33m{s}\033[0m"


def cyan(s):
    return f"\033[36m{s}\033[0m"


def bold(s):
    return f"\033[1m{s}\033[0m"


def dim(s):
    return f"\033[2m{s}\033[0m"


def ask(prompt: str, default: str = "") -> str:
    """询问用户输入."""
    if default:
        prompt_str = f"  {prompt} [{default}]: "
    else:
        prompt_str = f"  {prompt}: "
    try:
        val = input(prompt_str).strip()
    except (EOFError, KeyboardInterrupt):
        print("\n\n取消")
        sys.exit(0)
    return val if val else default


def ask_yn(prompt: str, default: bool = True) -> bool:
    """询问 yes/no."""
    suffix = " [Y/n]: " if default else " [y/N]: "
    try:
        val = input(f"  {prompt}{suffix}").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\n\n取消")
        sys.exit(0)
    if not val:
        return default
    return val in ("y", "yes", "1")


def print_header(title: str):
    print(f"\n{bold('=' * 60)}")
    print(bold(f"  {title}"))
    print(bold("=" * 60))


def print_section(num: int, total: int, title: str):
    print(f"\n{cyan(f'[{num}/{total}]')} {bold(title)}")


def get_default_config() -> dict:
    return {
        "base_url": "http://localhost:18080",
        "api_key": "",
        "kb_queries": [],
        "retrieval": {
            "concurrency": 10,
            "duration": 30,
            "top_k": 1024,
            "similarity_threshold": 0.2,
            "vector_similarity_weight": 0.3,
            "verify_ssl": True,
        },
        "embedding": {
            "enabled": False,
            "api_url": "",
            "api_key": "",
            "api_format": "openai",
            "model": "text-embedding-ada-002",
            "input_text": "测试文本",
            "concurrency": 5,
            "request_count": 20,
            "verify_ssl": True,
        },
        "monitor": {
            "enabled": True,
            "interval": 2,
            "duration": 60,
            "containers": [],
        },
        "log_analysis": {
            "enabled": True,
            "containers": [],
            "log_files": [],
            "since": "",
        },
        "output_dir": "./bench-output",
    }


def load_config(path: str) -> dict:
    if os.path.exists(path):
        try:
            with open(path) as f:
                cfg = json.load(f)
            # Merge with defaults for any missing keys
            default = get_default_config()
            for k, v in default.items():
                if k not in cfg:
                    cfg[k] = v
                elif isinstance(v, dict) and isinstance(cfg.get(k), dict):
                    for sk, sv in v.items():
                        if sk not in cfg[k]:
                            cfg[k][sk] = sv
            return cfg
        except (json.JSONDecodeError, Exception) as e:
            print(yellow(f"警告: 配置文件 {path} 解析失败: {e}"))
            print("将使用默认配置")
    return get_default_config()


def save_config(cfg: dict, path: str):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    print(green(f"\n配置已保存至: {path}"))


def configure_interactive(existing: dict) -> dict:
    """交互式配置所有参数."""
    cfg = existing.copy()
    default = get_default_config()

    print_header("RAGFlow 检索性能压测 —— 参数配置")
    print(dim("按 Enter 使用默认值，Ctrl+C 退出"))
    print(dim("提示: 可指定多个 KB，每个 KB 对应一个查询"))

    # [1/5] API Settings
    print_section(1, 5, "API 服务配置")
    cfg["base_url"] = ask("RAGFlow 服务地址", cfg.get("base_url", default["base_url"]))
    cfg["api_key"] = ask("API Key", cfg.get("api_key", ""))

    # [2/5] KB Settings
    print_section(2, 5, "知识库配置")
    existing_kbs = cfg.get("kb_queries", [])
    if existing_kbs:
        print(f"  当前已配置 {len(existing_kbs)} 个知识库:")
        for i, (kb, q) in enumerate(existing_kbs, 1):
            q_short = q[:50] + "..." if len(q) > 50 else q
            print(f"    {i}. KB: {kb}  查询: \"{q_short}\"")
        if not ask_yn("  是否重新配置知识库?", default=False):
            kb_queries = existing_kbs
        else:
            kb_queries = _configure_kb_queries()
    else:
        kb_queries = _configure_kb_queries()
    cfg["kb_queries"] = kb_queries

    # [3/5] Retrieval Test
    print_section(3, 5, "检索压测参数")
    ret = cfg.get("retrieval", default["retrieval"])
    ret["concurrency"] = int(ask("并发数", str(ret.get("concurrency", 10))))
    ret["duration"] = float(ask("持续时间 (秒)", str(ret.get("duration", 30))))
    ret["top_k"] = int(ask("top_k", str(ret.get("top_k", 1024))))
    ret["similarity_threshold"] = float(ask("相似度阈值", str(ret.get("similarity_threshold", 0.2))))
    ret["vector_similarity_weight"] = float(ask("向量相似度权重", str(ret.get("vector_similarity_weight", 0.3))))
    cfg["retrieval"] = ret

    # [4/5] Embedding Test
    print_section(4, 5, "Embedding 模型并发测试")
    emb = cfg.get("embedding", default["embedding"])
    emb["enabled"] = ask_yn("是否启用 Embedding 测试?", default=emb.get("enabled", False))
    if emb["enabled"]:
        emb["api_url"] = ask("Embedding API 地址", emb.get("api_url", ""))
        emb["api_key"] = ask("Embedding API Key (留空则使用 RAGFlow API Key)", emb.get("api_key", ""))
        if not emb["api_key"]:
            emb["api_key"] = cfg.get("api_key", "")
        emb["model"] = ask("模型名称", emb.get("model", "text-embedding-ada-002"))
        emb["input_text"] = ask("测试输入文本", emb.get("input_text", "测试文本"))
        emb["concurrency"] = int(ask("并发数 (建议 ≤10)", str(emb.get("concurrency", 5))))
        emb["request_count"] = int(ask("总请求数 (建议 ≤50)", str(emb.get("request_count", 20))))
        emb["api_format"] = ask("API 格式 (openai/ragflow)", emb.get("api_format", "openai"))
        emb["verify_ssl"] = ask_yn("验证 SSL 证书?", default=emb.get("verify_ssl", True))
    cfg["embedding"] = emb

    # [5/5] Monitoring & Log Analysis
    print_section(5, 5, "资源监控 & 日志分析")
    mon = cfg.get("monitor", default["monitor"])
    mon["enabled"] = ask_yn("启用资源监控?", default=mon.get("enabled", True))
    if mon["enabled"]:
        mon["interval"] = int(ask("监控采样间隔 (秒)", str(mon.get("interval", 2))))
        mon["duration"] = int(ask("监控总时长 (秒)", str(mon.get("duration", 60))))
        containers_str = ask(
            "监控容器 (空格分隔，留空自动检测)",
            " ".join(mon.get("containers", []))
        )
        mon["containers"] = containers_str.split() if containers_str.strip() else []
    cfg["monitor"] = mon

    log_cfg = cfg.get("log_analysis", default["log_analysis"])
    log_cfg["enabled"] = ask_yn("启用日志分析?", default=log_cfg.get("enabled", True))
    if log_cfg["enabled"]:
        containers_str = ask(
            "日志容器 (空格分隔)",
            " ".join(log_cfg.get("containers", []))
        )
        log_cfg["containers"] = containers_str.split() if containers_str.strip() else []
        log_files_str = ask(
            "日志文件路径 (空格分隔，可选)",
            " ".join(log_cfg.get("log_files", []))
        )
        log_cfg["log_files"] = log_files_str.split() if log_files_str.strip() else []
        log_cfg["since"] = ask("Docker logs --since (如 10m, 1h, 留空不限)", log_cfg.get("since", ""))
    cfg["log_analysis"] = log_cfg

    # Output
    cfg["output_dir"] = ask("输出目录", cfg.get("output_dir", "./bench-output"))

    return cfg


def _configure_kb_queries() -> list:
    """配置知识库和查询列表."""
    kb_queries = []
    print("  请输入知识库 ID 和对应的查询文本")
    print("  (每行一对，先输入 KB ID 再输入查询，KB ID 留空结束)")
    i = 1
    while True:
        kb = ask(f"KB ID #{i} (留空结束)", "")
        if not kb:
            break
        query = ask(f"查询 #{i}", "")
        if not query:
            break
        kb_queries.append([kb, query])
        i += 1
    if not kb_queries:
        print(yellow("  警告: 未配置任何知识库，请至少配置一个"))
        return _configure_kb_queries()
    return kb_queries


def display_config(cfg: dict):
    """展示当前配置."""
    print_header("当前配置")

    print(f"\n  {cyan('API 服务:')}")
    print(f"    地址: {cfg['base_url']}")
    print(f"    Key:  {cfg['api_key'][:20]}..." if len(cfg.get("api_key", "")) > 20 else f"    Key:  {cfg.get('api_key', '(未设置)')}")

    print(f"\n  {cyan('知识库:')}")
    for i, (kb, q) in enumerate(cfg.get("kb_queries", []), 1):
        q_short = q[:60] + "..." if len(q) > 60 else q
        print(f"    {i}. {kb} → \"{q_short}\"")

    print(f"\n  {cyan('检索压测:')}")
    ret = cfg.get("retrieval", {})
    print(f"    并发: {ret.get('concurrency', 0)}, 持续: {ret.get('duration', 0)}s")
    print(f"    top_k: {ret.get('top_k', 0)}, 阈值: {ret.get('similarity_threshold', 0)}, 向量权重: {ret.get('vector_similarity_weight', 0)}")

    print(f"\n  {cyan('Embedding 测试:')}")
    emb = cfg.get("embedding", {})
    if emb.get("enabled"):
        print(f"    启用: 是")
        print(f"    API: {emb.get('api_url', '')}, 模型: {emb.get('model', '')}")
        print(f"    并发: {emb.get('concurrency', 0)}, 请求数: {emb.get('request_count', 0)}")
    else:
        print(f"    启用: 否")

    print(f"\n  {cyan('资源监控:')}")
    mon = cfg.get("monitor", {})
    if mon.get("enabled"):
        print(f"    启用: 是, 间隔: {mon.get('interval', 0)}s, 时长: {mon.get('duration', 0)}s")
        if mon.get("containers"):
            print(f"    容器: {', '.join(mon['containers'])}")
        else:
            print(f"    容器: (自动检测 ha-* 容器)")
    else:
        print(f"    启用: 否")

    print(f"\n  {cyan('日志分析:')}")
    log_cfg = cfg.get("log_analysis", {})
    if log_cfg.get("enabled"):
        print(f"    启用: 是")
        if log_cfg.get("containers"):
            print(f"    容器: {', '.join(log_cfg['containers'])}")
        if log_cfg.get("log_files"):
            print(f"    文件: {', '.join(log_cfg['log_files'])}")
    else:
        print(f"    启用: 否")

    print(f"\n  {cyan('输出目录:')} {cfg.get('output_dir', './bench-output')}")


def run_monitor(cfg: dict, output_dir: str, ts: str) -> subprocess.Popen | None:
    """启动资源监控后台进程."""
    mon = cfg.get("monitor", {})
    if not mon.get("enabled"):
        return None

    cmd = [
        "bash", str(MONITOR_SCRIPT),
        "-i", str(mon.get("interval", 2)),
        "-d", str(mon.get("duration", 60)),
        "-o", output_dir,
    ]
    if mon.get("containers"):
        cmd.extend(["-c", " ".join(mon["containers"])])

    print(f"\n启动资源监控: {' '.join(cmd)}")
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def run_retrieval_bench(cfg: dict, output_dir: str, ts: str) -> dict | None:
    """运行检索压测."""
    ret = cfg.get("retrieval", {})
    kb_queries = cfg.get("kb_queries", [])

    cmd = [
        sys.executable, str(BENCH_RETRIEVAL),
        "--base-url", cfg["base_url"],
        "--api-key", cfg["api_key"],
        "--concurrency", str(ret.get("concurrency", 10)),
        "--duration", str(ret.get("duration", 30)),
        "--top-k", str(ret.get("top_k", 1024)),
        "--similarity-threshold", str(ret.get("similarity_threshold", 0.2)),
        "--vector-similarity-weight", str(ret.get("vector_similarity_weight", 0.3)),
        "--output-json", os.path.join(output_dir, f"retrieval_result_{ts}.json"),
    ]
    if not ret.get("verify_ssl", True):
        cmd.append("--no-verify-ssl")
    for kb, q in kb_queries:
        cmd.extend(["--kb", kb, "--query", q])

    print(f"\n启动检索压测...", flush=True)
    print(f"  命令: {' '.join(shlex.quote(c) for c in cmd[:12])}...")
    sys.stdout.flush()
    result = subprocess.run(cmd, capture_output=False)
    return None


def run_embedding_bench(cfg: dict, output_dir: str, ts: str) -> dict | None:
    """运行 Embedding 测试."""
    emb = cfg.get("embedding", {})
    if not emb.get("enabled"):
        return None

    cmd = [
        sys.executable, str(BENCH_EMBEDDING),
        "--api-url", emb["api_url"],
        "--api-key", emb.get("api_key", cfg.get("api_key", "")),
        "--model", emb.get("model", "text-embedding-ada-002"),
        "--input", emb.get("input_text", "测试文本"),
        "--concurrency", str(emb.get("concurrency", 5)),
        "--count", str(emb.get("request_count", 20)),
        "--api-format", emb.get("api_format", "openai"),
        "--output-json", os.path.join(output_dir, f"embedding_result_{ts}.json"),
    ]
    if not emb.get("verify_ssl", True):
        cmd.append("--no-verify-ssl")

    print(f"\n启动 Embedding 测试...", flush=True)
    sys.stdout.flush()
    result = subprocess.run(cmd, capture_output=False)
    return None


def run_log_analysis(cfg: dict, output_dir: str, ts: str, since: str = ""):
    """运行日志分析."""
    log_cfg = cfg.get("log_analysis", {})
    if not log_cfg.get("enabled"):
        return

    cmd = [
        sys.executable, str(ANALYZE_LOGS),
        "--output-json", os.path.join(output_dir, f"log_analysis_{ts}.json"),
    ]
    containers = log_cfg.get("containers", [])
    if containers:
        cmd.extend(["--containers"] + containers)
    log_files = log_cfg.get("log_files", [])
    if log_files:
        cmd.extend(["--log-files"] + log_files)
    since_val = log_cfg.get("since", "") or since
    if since_val:
        cmd.extend(["--since", since_val])

    print(f"\n运行日志分析...")
    subprocess.run(cmd, capture_output=False)


def run_plots(cfg: dict, output_dir: str):
    """生成资源监控图表."""
    import glob
    csv_files = glob.glob(os.path.join(output_dir, "container_stats_*.csv"))
    if not csv_files:
        return
    print(f"\n生成资源监控图表...")
    plot_script = SCRIPT_DIR / "plot_monitor.py"
    cmd = [sys.executable, str(plot_script), "-d", output_dir, "-o", output_dir]
    subprocess.run(cmd, capture_output=False)


def print_summary(output_dir: str, ts: str):
    """打印执行摘要."""
    print_header("执行完成")
    print(f"\n  输出目录: {output_dir}")
    print(f"  时间戳:   {ts}")

    import glob
    files = sorted(glob.glob(os.path.join(output_dir, f"*{ts}*")))
    if files:
        print(f"\n  生成的文件:")
        for f in files:
            size = os.path.getsize(f)
            size_str = f"{size:,} B" if size < 1024 else f"{size/1024:.1f} KB"
            print(f"    {os.path.basename(f)} ({size_str})")

    csv_files = glob.glob(os.path.join(output_dir, "container_stats_*.csv"))
    if csv_files:
        png_files = glob.glob(os.path.join(output_dir, "*.png"))
        if png_files:
            print(f"\n  资源图表: {len(png_files)} 张")
            for p in sorted(png_files):
                print(f"    {os.path.basename(p)}")

    print(f"\n{dim('=' * 60)}")


def main():
    print_header("RAGFlow Retrieval Benchmark Tool v2.0")

    # Parse minimal args
    import argparse
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--skip-retrieval", action="store_true")
    parser.add_argument("--skip-embedding", action="store_true")
    parser.add_argument("--skip-monitor", action="store_true")
    parser.add_argument("--skip-logs", action="store_true")
    parser.add_argument("--help", action="store_true")
    args, _ = parser.parse_known_args()

    if args.help:
        print(__doc__)
        print("\n可选参数:")
        print("  --config PATH          配置文件路径 (默认: bench_config.json)")
        print("  --skip-retrieval       跳过检索压测")
        print("  --skip-embedding       跳过 Embedding 测试")
        print("  --skip-monitor         跳过资源监控")
        print("  --skip-logs            跳过日志分析")
        print("  --help                 显示此帮助")
        sys.exit(0)

    config_path = args.config
    existing = load_config(config_path)
    is_first_run = not os.path.exists(config_path)
    has_api_key = bool(existing.get("api_key"))
    has_kb = bool(existing.get("kb_queries"))

    # Determine if we need configuration
    needs_config = is_first_run or not has_api_key or not has_kb

    if is_first_run:
        print(dim("首次运行 —— 请配置压测参数"))
    else:
        display_config(existing)
        print()
        if ask_yn("修改配置?", default=False):
            needs_config = True

    if needs_config:
        cfg = configure_interactive(existing)
        display_config(cfg)
    else:
        cfg = existing

    if not ask_yn(f"\n{bold('确认执行?')}", default=True):
        save_config(cfg, config_path)
        print("已保存配置，未执行压测")
        sys.exit(0)

    save_config(cfg, config_path)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = cfg.get("output_dir", "./bench-output")
    os.makedirs(output_dir, exist_ok=True)

    # Phase 1: Start monitor
    monitor_proc = None
    if not args.skip_monitor:
        monitor_proc = run_monitor(cfg, output_dir, ts)

    # Small delay for monitor to start sampling
    if monitor_proc:
        print("等待监控启动...")
        time.sleep(2)

    # Phase 2: Retrieval bench
    if not args.skip_retrieval:
        run_retrieval_bench(cfg, output_dir, ts)

    # Phase 3: Embedding bench
    if not args.skip_embedding:
        run_embedding_bench(cfg, output_dir, ts)

    # Phase 4: Wait for monitor to finish
    if monitor_proc:
        print("\n等待资源监控完成...")
        monitor_proc.wait(timeout=cfg.get("monitor", {}).get("duration", 60) + 30)

    # Phase 5: Log analysis
    if not args.skip_logs:
        mon = cfg.get("monitor", {})
        since_seconds = mon.get("duration", 60) + 30
        since_str = f"{since_seconds}s"
        run_log_analysis(cfg, output_dir, ts, since_str)

    # Phase 6: Generate plots
    run_plots(cfg, output_dir)

    print_summary(output_dir, ts)


if __name__ == "__main__":
    main()
