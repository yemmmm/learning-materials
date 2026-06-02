# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Overview

RAGFlow Retrieval API benchmarking toolkit with interactive orchestration. Supports:
- Retrieval API concurrency stress testing
- Embedding model concurrency testing (short bursts to avoid rate limiting)
- Docker container + server resource monitoring
- Retrieval pipeline step-by-step timing analysis (requires RAGFlow source instrumentation)

## Quick Start

```bash
# Interactive mode (recommended)
python run_bench.py

# Use specific config file
python run_bench.py --config my_config.json

# Skip certain phases
python run_bench.py --skip-embedding --skip-monitor
```

## Architecture

### run_bench.py — Interactive Orchestrator

Main entry point. On first run, prompts user for all configuration parameters interactively and saves to `bench_config.json`. On subsequent runs, displays the saved config and asks whether to modify before executing.

Execution flow:
1. Load/setup config (interactive)
2. Start resource monitor (background) if enabled
3. Run retrieval benchmark
4. Run embedding benchmark if enabled
5. Wait for monitor to complete
6. Collect logs and analyze timing if enabled
7. Generate resource charts

### bench_retrieval.py — Retrieval API Stress Test

Concurrent load testing against `/api/v1/retrieval`. Supports multiple KB-query pairs with round-robin distribution. Outputs both console report and optional JSON results.

### bench_embedding.py — Embedding Model Concurrency Test

Tests embedding API concurrency with short, controlled bursts to avoid triggering rate limits. Supports OpenAI-compatible and RAGFlow-internal API formats. Default: 5 concurrency, 20 requests. Includes warnings for high concurrency/request counts.

### monitor_resources.sh — Resource Monitor

Shell script that samples Docker container stats and server metrics (CPU, memory, load, disk) at configurable intervals. Outputs CSV files.

### plot_monitor.py — Resource Visualization

Reads monitor CSVs and generates grouped charts (CPU, memory, network, block I/O, heatmap) per service type with multi-node support.

### analyze_logs.py — Retrieval Timing Analysis

Parses `[RETRIEVAL_TIMING]` log lines from Docker container logs or disk files. Aggregates timing by pipeline step (embedding, doc_search, rerank_model, rerank_hybrid, total). Reports mean, median, P95/P99, and identifies the biggest bottleneck.

## RAGFlow Source Changes Required for Log Analysis

The `analyze_logs.py` tool requires timing instrumentation in RAGFlow's `rag/nlp/search.py`. The changes add structured log lines at key pipeline steps:

```
[RETRIEVAL_TIMING] step=embedding elapsed=0.123
[RETRIEVAL_TIMING] step=doc_search elapsed=0.045 total=256
[RETRIEVAL_TIMING] step=rerank_model elapsed=0.089 chunks=64
[RETRIEVAL_TIMING] step=total elapsed=0.267 chunks_returned=30
```

Steps instrumented:
- `embedding`: Query vector encoding time (in `Dealer.search()`)
- `doc_search`: Document store query time (ES/Infinity)
- `rerank_model` or `rerank_hybrid`: Reranking time (model-based or hybrid similarity)
- `total`: Full `Dealer.retrieval()` execution time

## Configuration File Format

`bench_config.json` stores all parameters and is auto-generated on first run.

## Multi-Node Support

All tools support multi-node deployments:
- `monitor_resources.sh`: `-c "ha-node1-web ha-node2-web ha-node1-worker ha-node2-worker"`
- `analyze_logs.py`: `--containers ha-node1-web ha-node2-web` — aggregates timing across nodes
- `plot_monitor.py`: Groups by service type with color/linestyle per node
- Run retrieval bench through LB to test load distribution

## Commands

```bash
# Install dependencies
uv sync

# Full interactive run
python run_bench.py

# Individual tools
python bench_retrieval.py --base-url http://localhost:18080 --api-key ragflow-xxx --kb <id> --query "test" --concurrency 10 --duration 30 --output-json results.json
python bench_embedding.py --api-url https://api.openai.com/v1/embeddings --api-key sk-xxx --model text-embedding-ada-002 --concurrency 5 --count 20
python analyze_logs.py --containers ha-node1-web ha-node2-web --since 5m --output-json analysis.json
python plot_monitor.py -d ./bench-output -o ./plots
```
