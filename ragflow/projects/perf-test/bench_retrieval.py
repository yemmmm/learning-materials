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

    # 从配置文件加载
    python bench_retrieval.py --config bench_config.json

    # 保存 JSON 结果
    python bench_retrieval.py ... --output-json results.json
"""

import argparse
import asyncio
import json
import os
import statistics
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

import httpx


@dataclass
class RequestResult:
    ok: bool
    latency: float
    status_code: int | None = None
    error: str | None = None
    timestamp: str = ""


@dataclass
class BenchConfig:
    base_url: str = ""
    api_key: str = ""
    kb_queries: list[tuple[str, str]] = field(default_factory=list)
    concurrency: int = 10
    duration: float = 30
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

    @property
    def success_latencies(self) -> list[float]:
        return [r.latency for r in self.results if r.ok]

    def percentile(self, p: float) -> float:
        vals = self.success_latencies
        if not vals:
            return 0.0
        sorted_lat = sorted(vals)
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

    def to_dict(self, config: BenchConfig) -> dict:
        latencies = self.success_latencies
        result = {
            "target": f"{config.base_url}/api/v1/retrieval",
            "kb_queries": [{"kb_id": k, "query": q} for k, q in config.kb_queries],
            "concurrency": config.concurrency,
            "duration_s": round(self.elapsed, 1),
            "total_requests": self.total,
            "successes": self.successes,
            "failures": self.failures,
            "success_rate": round(self.success_rate, 4),
            "qps": round(self.qps, 2),
        }
        if latencies:
            result["latency"] = {
                "min": round(min(latencies), 3),
                "max": round(max(latencies), 3),
                "mean": round(statistics.mean(latencies), 3),
                "median": round(statistics.median(latencies), 3),
                "p95": round(self.percentile(95), 3),
                "p99": round(self.percentile(99), 3),
            }
            if len(latencies) > 1:
                result["latency"]["stdev"] = round(statistics.stdev(latencies), 3)
        errors = self.error_breakdown()
        if errors:
            result["errors"] = errors
        return result

    def save_json(self, config: BenchConfig, path: str):
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        data = {"timestamp": ts, "type": "retrieval_bench", "config": {}, "results": {}}
        data["config"] = {
            "base_url": config.base_url,
            "concurrency": config.concurrency,
            "duration": config.duration,
            "top_k": config.top_k,
            "similarity_threshold": config.similarity_threshold,
            "vector_similarity_weight": config.vector_similarity_weight,
            "kb_count": len(config.kb_queries),
        }
        data["results"] = self.to_dict(config)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\nJSON 结果已保存至: {path}")


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
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    start = time.monotonic()
    try:
        resp = await client.post(url, json=payload)
        latency = time.monotonic() - start
        if resp.status_code == 200:
            body = resp.json()
            if body.get("code") == 0:
                return RequestResult(ok=True, latency=latency, status_code=200, timestamp=ts)
            return RequestResult(
                ok=False, latency=latency, status_code=200, timestamp=ts,
                error=f"API code={body.get('code')}: {body.get('message', '')}",
            )
        return RequestResult(
            ok=False, latency=latency, status_code=resp.status_code, timestamp=ts
        )
    except httpx.ConnectError as e:
        return RequestResult(
            ok=False, latency=time.monotonic() - start, timestamp=ts, error=f"ConnectError: {e}"
        )
    except httpx.ReadTimeout:
        return RequestResult(
            ok=False, latency=time.monotonic() - start, timestamp=ts, error="ReadTimeout"
        )
    except Exception as e:
        return RequestResult(
            ok=False, latency=time.monotonic() - start, timestamp=ts, error=f"{type(e).__name__}: {e}"
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
    backoff = 0.0
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        dataset_id, query = config.kb_queries[idx]
        try:
            result = await asyncio.wait_for(
                send_request(client, config, dataset_id, query),
                timeout=min(remaining, 30.0),
            )
        except asyncio.TimeoutError:
            break
        stats.results.append(result)
        # Rate-limit: if the request returned faster than 100ms with an error,
        # the server is likely failing fast (e.g. 502 from nginx). Wait briefly
        # to avoid tight-loop spinning that inflates request counts.
        if not result.ok and result.latency < 0.1:
            backoff = min(backoff + 0.05, 1.0)
            await asyncio.sleep(backoff)
        else:
            backoff = max(backoff - 0.05, 0.0)
        idx = (idx + 1) % kb_count


async def run_bench(config: BenchConfig, stats: BenchStats) -> None:
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
        try:
            await asyncio.gather(*tasks)
        finally:
            stats.end_time = time.monotonic()


def print_report(stats: BenchStats, config: BenchConfig):
    print("\n" + "=" * 60)
    print("  RAGFlow Retrieval 压测报告")
    print("=" * 60)

    print(f"\n  目标:        {config.base_url}/api/v1/retrieval")
    kb_info = ", ".join(f"{kid} ({q[:30]}...)" if len(q) > 30 else f"{kid} ({q})" for kid, q in config.kb_queries)
    print(f"  知识库:      {kb_info}")
    print(f"  并发数:      {config.concurrency}")
    print(f"  持续时间:    {stats.elapsed:.1f}s")

    print(f"\n  --- 请求统计 ---")
    print(f"  总请求数:    {stats.total}")
    print(f"  成功:        {stats.successes}")
    print(f"  失败:        {stats.failures}")
    print(f"  成功率:      {stats.success_rate:.1%}")
    print(f"  QPS:         {stats.qps:.2f}")

    latencies = stats.success_latencies
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


def load_config_from_file(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def build_config_from_dict(data: dict) -> BenchConfig:
    return BenchConfig(
        base_url=data.get("base_url", "").rstrip("/"),
        api_key=data.get("api_key", ""),
        kb_queries=[(k, q) for k, q in data.get("kb_queries", [])],
        concurrency=data.get("concurrency", 10),
        duration=data.get("duration", 30),
        top_k=data.get("top_k", 1024),
        similarity_threshold=data.get("similarity_threshold", 0.2),
        vector_similarity_weight=data.get("vector_similarity_weight", 0.3),
        verify_ssl=data.get("verify_ssl", True),
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description="RAGFlow Retrieval API 压力测试工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--config", help="从 JSON 配置文件加载参数")
    parser.add_argument("--base-url", help="RAGFlow 服务地址，如 http://localhost:18080")
    parser.add_argument("--api-key", help="RAGFlow API Key")
    parser.add_argument("--kb", action="append", help="知识库 ID（可多次指定）")
    parser.add_argument("--query", action="append", help="查询文本（可多次指定）")
    parser.add_argument("--concurrency", type=int, default=10, help="并发数（默认 10）")
    parser.add_argument("--duration", type=float, default=30, help="压测持续时间，秒（默认 30）")
    parser.add_argument("--top-k", type=int, default=1024, help="top_k 参数（默认 1024）")
    parser.add_argument("--similarity-threshold", type=float, default=0.2)
    parser.add_argument("--vector-similarity-weight", type=float, default=0.3)
    parser.add_argument("--no-verify-ssl", action="store_true")
    parser.add_argument("--output-json", help="保存 JSON 结果到指定路径")

    args = parser.parse_args()

    if args.config:
        data = load_config_from_file(args.config)
        ret = data.get("retrieval", data)
        config = build_config_from_dict({**ret, "base_url": ret.get("base_url", data.get("base_url", "")),
                                         "api_key": ret.get("api_key", data.get("api_key", "")),
                                         "kb_queries": data.get("kb_queries", [])})
        return config, args

    if not args.base_url or not args.api_key or not args.kb:
        parser.error("需要 --base-url, --api-key, --kb 参数，或使用 --config 加载配置文件")

    if len(args.kb) != len(args.query or []):
        parser.error(f"--kb 和 --query 数量不匹配: {len(args.kb)} 个 --kb, {len(args.query or [])} 个 --query")

    kb_queries = list(zip(args.kb, args.query or []))
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
    return config, args


def main():
    config, args = parse_args()

    print(f"启动压测: {config.concurrency} 并发 × {config.duration}s")
    print(f"知识库数量: {len(config.kb_queries)}")
    for kid, q in config.kb_queries:
        print(f"  - {kid}: \"{q}\"")
    print("按 Ctrl+C 可提前终止...\n")

    stats = BenchStats()
    try:
        asyncio.run(run_bench(config, stats))
    except KeyboardInterrupt:
        print("\n\n用户中断，正在生成报告...")
        if stats.end_time == 0.0:
            stats.end_time = time.monotonic()

    print_report(stats, config)

    output_json = getattr(args, 'output_json', None)
    if output_json:
        stats.save_json(config, output_json)

    if stats.failures > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
