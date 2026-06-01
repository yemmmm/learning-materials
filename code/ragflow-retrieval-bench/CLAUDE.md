# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

RAGFlow Retrieval API benchmarking toolkit. Three tools designed to run together: a benchmark driver, a resource monitor, and a visualization script.

## Commands

```bash
# Install dependencies (uv is the project's Python toolchain)
uv sync

# Run benchmark (single KB)
python bench_retrieval.py --base-url http://localhost:18080 --api-key ragflow-xxx --kb <id> --query "test" --concurrency 10 --duration 30

# Run resource monitor (auto-detects ha-* Docker containers)
./monitor_resources.sh -i 5 -d 120 -o ./bench-data

# Generate charts from CSVs
python plot_monitor.py -d ./bench-data -o ./plots
```

## Architecture

### Data flow: monitor → CSV → plot

`monitor_resources.sh` writes two CSVs per run (`container_stats_*.csv`, `server_stats_*.csv`). `plot_monitor.py` reads ALL matching CSVs in a directory, merges them into a single DataFrame (handling multi-run data), and renders grouped charts.

### Container naming convention

Container names follow the pattern `ha-[node<N>-]<service>`:
- `ha-node1-web` → service=`web`, node=`node1`
- `ha-node2-worker` → service=`worker`, node=`node2`
- `ha-mysql` → service=`mysql`, node=`infra` (no node prefix → infra service)

`parse_container_name()` in `plot_monitor.py` is the single parser for this convention. Charts group by service type, using color+linestyle to distinguish nodes within each group.

### RAGFlow API response convention

The retrieval endpoint returns HTTP 200 even for application-level errors. Success is `HTTP 200` AND `body["code"] == 0`. Any non-zero code is treated as failure (see `send_request()` in `bench_retrieval.py`).

### Benchmark internals

`bench_retrieval.py` uses `httpx.AsyncClient` + `asyncio.gather` for concurrent requests. Workers round-robin across KB-query pairs (worker_id % kb_count). Statistics use `dataclass` objects (`BenchConfig`, `BenchStats`, `RequestResult`) — `BenchStats` computes percentiles, QPS, and error breakdowns.

### Server stats collection

`monitor_resources.sh` reads `/proc/stat` (CPU), `/proc/meminfo` (memory), `/proc/loadavg` (load), and `df` (disk) directly — no `top`/`free` dependency. CPU % is computed from the delta between consecutive `/proc/stat` snapshots, with sampling overhead compensated in the sleep interval.
