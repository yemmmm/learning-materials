#!/usr/bin/env python3
"""RAGFlow Retrieval API 压力测试脚本

对 RAGFlow 的 /api/v1/retrieval 接口进行并发压测，
支持同时指定多个知识库及其对应的查询文本。

用法示例:
    # 单知识库，10并发，持续30秒
    python bench_retrieval.py \
        --base-url http://localhost:18080 \
        --api-key ragflow-xxxx \
        --kb kb_id_1 --query "什么是机器学习" \
        --concurrency 10 --duration 30

    # 多知识库，每个KB对应一条查询
    python bench_retrieval.py \
        --base-url http://localhost:18080 \
        --api-key ragflow-xxxx \
        --kb kb_id_1 --query "查询一" \
        --kb kb_id_2 --query "查询二" \
        --kb kb_id_3 --query "查询三" \
        --concurrency 20 --duration 60
"""

import argparse
import asyncio
import json
import statistics
import sys
import time
from dataclasses import dataclass, field

import httpx


@dataclass
class RequestResult:
    ok: bool
    latency: float  # seconds
    status_code: int | None = None
    error: str | None = None


@dataclass
class BenchConfig:
    base_url: str
    api_key: str
    kb_queries: list[tuple[str, str]]  # [(dataset_id, query), ...]
    concurrency: int
    duration: float
    top_k: int = 1024
    similarity_threshold: float = 0.2
    vector_similarity_weight: float = 0.3
    verify_ssl: bool = True


@dataclass
class BenchStats:
    results: list[RequestResult] = field(default_factory=list)
    start_time: float = 0.0
    end_time: float = 0.0

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def successes(self) -> int:
        return sum(1 for r in self.results if r.ok)

    @property
    def failures(self) -> int:
        return self.total - self.successes

    @property
    def success_rate(self) -> float:
        return self.successes / self.total if self.total else 0.0

    @property
    def elapsed(self) -> float:
        return self.end_time - self.start_time

    @property
    def qps(self) -> float:
        return self.total / self.elapsed if self.elapsed > 0 else 0.0

    @property
    def latencies(self) -> list[float]:
        return [r.latency for r in self.results]

    def percentile(self, p: float) -> float:
        if not self.latencies:
            return 0.0
        sorted_lat = sorted(self.latencies)
        idx = int(len(sorted_lat) * p / 100)
        idx = min(idx, len(sorted_lat) - 1)
        return sorted_lat[idx]

    def error_breakdown(self) -> dict[str, int]:
        breakdown: dict[str, int] = {}
        for r in self.results:
            if not r.ok:
                key = r.error or f"HTTP {r.status_code}"
                breakdown[key] = breakdown.get(key, 0) + 1
        return breakdown


def build_payload(dataset_id: str, query: str, config: BenchConfig) -> dict:
    return {
        "dataset_ids": [dataset_id],
        "question": query,
        "top_k": config.top_k,
        "similarity_threshold": config.similarity_threshold,
        "vector_similarity_weight": config.vector_similarity_weight,
        "page": 1,
        "page_size": 30,
    }


async def send_request(
    client: httpx.AsyncClient, config: BenchConfig, dataset_id: str, query: str
) -> RequestResult:
    url = f"{config.base_url}/api/v1/retrieval"
    payload = build_payload(dataset_id, query, config)
    start = time.monotonic()
    try:
        resp = await client.post(url, json=payload)
        latency = time.monotonic() - start
        if resp.status_code == 200:
            body = resp.json()
            if body.get("code") == 0:
                return RequestResult(ok=True, latency=latency, status_code=200)
            return RequestResult(
                ok=False,
                latency=latency,
                status_code=200,
                error=f"API code={body.get('code')}: {body.get('message', '')}",
            )
        return RequestResult(
            ok=False, latency=latency, status_code=resp.status_code
        )
    except httpx.ConnectError as e:
        return RequestResult(
            ok=False, latency=time.monotonic() - start, error=f"ConnectError: {e}"
        )
    except httpx.ReadTimeout:
        return RequestResult(
            ok=False, latency=time.monotonic() - start, error="ReadTimeout"
        )
    except Exception as e:
        return RequestResult(
            ok=False, latency=time.monotonic() - start, error=f"{type(e).__name__}: {e}"
        )


async def worker(
    client: httpx.AsyncClient,
    config: BenchConfig,
    deadline: float,
    stats: BenchStats,
    worker_id: int,
):
    kb_count = len(config.kb_queries)
    idx = worker_id % kb_count
    while time.monotonic() < deadline:
        dataset_id, query = config.kb_queries[idx]
        result = await send_request(client, config, dataset_id, query)
        stats.results.append(result)
        idx = (idx + 1) % kb_count


async def run_bench(config: BenchConfig) -> BenchStats:
    stats = BenchStats()
    stats.start_time = time.monotonic()
    deadline = stats.start_time + config.duration

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(300.0, connect=10.0),
        headers={"Authorization": f"Bearer {config.api_key}"},
        verify=config.verify_ssl,
    ) as client:
        tasks = [
            worker(client, config, deadline, stats, i)
            for i in range(config.concurrency)
        ]
        await asyncio.gather(*tasks)

    stats.end_time = time.monotonic()
    return stats


def print_report(stats: BenchStats, config: BenchConfig):
    print("\n" + "=" * 60)
    print("  RAGFlow Retrieval 压测报告")
    print("=" * 60)

    print(f"\n  目标:        {config.base_url}/api/v1/retrieval")
    kb_info = ", ".join(f"{kid} ({q[:20]}...)" for kid, q in config.kb_queries)
    print(f"  知识库:      {kb_info}")
    print(f"  并发数:      {config.concurrency}")
    print(f"  持续时间:    {stats.elapsed:.1f}s")

    print(f"\n  --- 请求统计 ---")
    print(f"  总请求数:    {stats.total}")
    print(f"  成功:        {stats.successes}")
    print(f"  失败:        {stats.failures}")
    print(f"  成功率:      {stats.success_rate:.1%}")
    print(f"  QPS:         {stats.qps:.2f}")

    latencies = stats.latencies
    if latencies:
        print(f"\n  --- 延迟统计 (秒) ---")
        print(f"  最小:        {min(latencies):.3f}")
        print(f"  最大:        {max(latencies):.3f}")
        print(f"  平均:        {statistics.mean(latencies):.3f}")
        if len(latencies) > 1:
            print(f"  中位数:      {statistics.median(latencies):.3f}")
            print(f"  标准差:      {statistics.stdev(latencies):.3f}")
        print(f"  P95:         {stats.percentile(95):.3f}")
        print(f"  P99:         {stats.percentile(99):.3f}")

    errors = stats.error_breakdown()
    if errors:
        print(f"\n  --- 错误分布 ---")
        for err, count in sorted(errors.items(), key=lambda x: -x[1]):
            print(f"  {err}: {count}")

    print("=" * 60)


def parse_args() -> tuple[argparse.Namespace, list[tuple[str, str]]]:
    parser = argparse.ArgumentParser(
        description="RAGFlow Retrieval API 压力测试工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--base-url", required=True, help="RAGFlow 服务地址，如 http://localhost:18080"
    )
    parser.add_argument("--api-key", required=True, help="RAGFlow API Key")
    parser.add_argument(
        "--kb",
        action="append",
        required=True,
        help="知识库 ID（可多次指定，与 --query 一一对应）",
    )
    parser.add_argument(
        "--query",
        action="append",
        required=True,
        help="查询文本（可多次指定，与 --kb 一一对应）",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=10,
        help="并发数（默认 10）",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=30,
        help="压测持续时间，秒（默认 30）",
    )
    parser.add_argument("--top-k", type=int, default=1024, help="top_k 参数（默认 1024）")
    parser.add_argument(
        "--similarity-threshold",
        type=float,
        default=0.2,
        help="相似度阈值（默认 0.2）",
    )
    parser.add_argument(
        "--vector-similarity-weight",
        type=float,
        default=0.3,
        help="向量相似度权重（默认 0.3）",
    )
    parser.add_argument(
        "--no-verify-ssl",
        action="store_true",
        help="跳过 SSL 证书验证（自签名证书时使用）",
    )

    args = parser.parse_args()

    if len(args.kb) != len(args.query):
        parser.error(
            f"--kb 和 --query 数量不匹配: {len(args.kb)} 个 --kb, {len(args.query)} 个 --query"
        )

    kb_queries = list(zip(args.kb, args.query))
    return args, kb_queries


def main():
    args, kb_queries = parse_args()

    config = BenchConfig(
        base_url=args.base_url.rstrip("/"),
        api_key=args.api_key,
        kb_queries=kb_queries,
        concurrency=args.concurrency,
        duration=args.duration,
        top_k=args.top_k,
        similarity_threshold=args.similarity_threshold,
        vector_similarity_weight=args.vector_similarity_weight,
        verify_ssl=not args.no_verify_ssl,
    )

    print(f"启动压测: {config.concurrency} 并发 × {config.duration}s")
    print(f"知识库数量: {len(config.kb_queries)}")
    for kid, q in config.kb_queries:
        print(f"  - {kid}: \"{q}\"")
    print("按 Ctrl+C 可提前终止...\n")

    try:
        stats = asyncio.run(run_bench(config))
    except KeyboardInterrupt:
        print("\n\n用户中断，正在生成报告...")
        stats = BenchStats()
        stats.end_time = time.monotonic()

    print_report(stats, config)

    if stats.failures > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
