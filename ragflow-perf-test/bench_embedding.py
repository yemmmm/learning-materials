#!/usr/bin/env python3
"""Embedding 模型并发能力测试脚本

直接测试 embedding API 的并发能力，使用短时间、少量请求以避免触发风控。

支持的 API 格式:
  - OpenAI 兼容: POST /v1/embeddings  (input, model, encoding_format)
  - 自定义格式: 通过 --api-format 指定请求体和响应解析

用法示例:
    # 测试 OpenAI 兼容的 embedding 服务
    python bench_embedding.py \
        --api-url https://api.openai.com/v1/embeddings \
        --api-key sk-xxxx \
        --model text-embedding-ada-002 \
        --concurrency 5 --count 20

    # 从配置文件加载
    python bench_embedding.py --config bench_config.json

    # 自定义并发级别和请求数
    python bench_embedding.py \
        --api-url http://localhost:18080/api/v1/embeddings \
        --api-key ragflow-xxxx \
        --model bge-large-zh-v1.5 \
        --concurrency 3 --count 10 \
        --input "测试文本"
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
class EmbeddingResult:
    ok: bool
    latency: float
    embedding_size: int = 0
    error: str | None = None
    timestamp: str = ""


@dataclass
class EmbeddingStats:
    results: list[EmbeddingResult] = field(default_factory=list)
    config: dict = field(default_factory=dict)

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
    def latencies(self) -> list[float]:
        return [r.latency for r in self.results if r.ok]

    def percentile(self, p: float) -> float:
        vals = self.latencies
        if not vals:
            return 0.0
        sorted_lat = sorted(vals)
        idx = int(len(sorted_lat) * p / 100)
        return sorted_lat[min(idx, len(sorted_lat) - 1)]

    def error_breakdown(self) -> dict[str, int]:
        breakdown: dict[str, int] = {}
        for r in self.results:
            if not r.ok:
                key = r.error or "unknown"
                breakdown[key] = breakdown.get(key, 0) + 1
        return breakdown

    def to_dict(self) -> dict:
        lats = self.latencies
        result = {
            "model": self.config.get("model", ""),
            "api_url": self.config.get("api_url", ""),
            "concurrency": self.config.get("concurrency", 0),
            "request_count": self.total,
            "successes": self.successes,
            "failures": self.failures,
            "success_rate": round(self.success_rate, 4),
        }
        if lats:
            result["latency"] = {
                "min": round(min(lats), 3),
                "max": round(max(lats), 3),
                "mean": round(statistics.mean(lats), 3),
                "median": round(statistics.median(lats), 3),
                "p95": round(self.percentile(95), 3),
                "p99": round(self.percentile(99), 3),
            }
            if len(lats) > 1:
                result["latency"]["stdev"] = round(statistics.stdev(lats), 3)
            result["embedding_sizes"] = list(set(
                r.embedding_size for r in self.results if r.ok
            ))
        errors = self.error_breakdown()
        if errors:
            result["errors"] = errors
        return result

    def save_json(self, path: str):
        data = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "type": "embedding_bench",
            "config": self.config,
            "results": self.to_dict(),
        }
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\nJSON 结果已保存至: {path}")


async def send_one(
    client: httpx.AsyncClient,
    api_url: str,
    model: str,
    input_text: str,
    api_format: str,
) -> EmbeddingResult:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    start = time.monotonic()

    if api_format == "openai":
        payload = {"input": input_text, "model": model, "encoding_format": "float"}
    elif api_format == "ragflow":
        payload = {"text": input_text, "model": model}
    else:
        payload = {"input": input_text, "model": model}

    try:
        resp = await client.post(api_url, json=payload)
        latency = time.monotonic() - start
        if resp.status_code == 200:
            body = resp.json()
            if api_format == "openai":
                emb = body.get("data", [{}])[0].get("embedding", [])
            elif api_format == "ragflow":
                data = body.get("data", {})
                if isinstance(data, dict) and "embedding" in data:
                    emb = data["embedding"]
                else:
                    emb = body.get("embedding", [])
            else:
                emb = body.get("data", [{}])[0].get("embedding", [])
            return EmbeddingResult(
                ok=True, latency=latency, embedding_size=len(emb), timestamp=ts
            )
        return EmbeddingResult(
            ok=False, latency=latency, error=f"HTTP {resp.status_code}", timestamp=ts
        )
    except httpx.ConnectError as e:
        return EmbeddingResult(
            ok=False, latency=time.monotonic() - start,
            error=f"ConnectError: {e}", timestamp=ts
        )
    except httpx.ReadTimeout:
        return EmbeddingResult(
            ok=False, latency=time.monotonic() - start,
            error="ReadTimeout", timestamp=ts
        )
    except Exception as e:
        return EmbeddingResult(
            ok=False, latency=time.monotonic() - start,
            error=f"{type(e).__name__}: {e}", timestamp=ts
        )


async def run_bench(
    api_url: str,
    api_key: str,
    model: str,
    input_text: str,
    concurrency: int,
    request_count: int,
    verify_ssl: bool,
    api_format: str,
    stats: EmbeddingStats,
):
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(120.0, connect=10.0),
        headers=headers,
        verify=verify_ssl,
    ) as client:
        sem = asyncio.Semaphore(concurrency)

        async def bounded_request():
            async with sem:
                return await send_one(client, api_url, model, input_text, api_format)

        tasks = [bounded_request() for _ in range(request_count)]
        results = await asyncio.gather(*tasks)
        stats.results = list(results)


def print_report(stats: EmbeddingStats):
    print("\n" + "=" * 60)
    print("  Embedding 模型并发测试报告")
    print("=" * 60)

    cfg = stats.config
    print(f"\n  目标:        {cfg.get('api_url', '')}")
    print(f"  模型:        {cfg.get('model', '')}")
    print(f"  并发数:      {cfg.get('concurrency', 0)}")
    print(f"  请求总数:    {stats.total}")

    print(f"\n  --- 请求统计 ---")
    print(f"  成功:        {stats.successes}")
    print(f"  失败:        {stats.failures}")
    print(f"  成功率:      {stats.success_rate:.1%}")

    lats = stats.latencies
    if lats:
        print(f"\n  --- 延迟统计 (秒) ---")
        print(f"  最小:        {min(lats):.3f}")
        print(f"  最大:        {max(lats):.3f}")
        print(f"  平均:        {statistics.mean(lats):.3f}")
        if len(lats) > 1:
            print(f"  中位数:      {statistics.median(lats):.3f}")
            print(f"  标准差:      {statistics.stdev(lats):.3f}")
        print(f"  P95:         {stats.percentile(95):.3f}")
        print(f"  P99:         {stats.percentile(99):.3f}")

        sizes = set(r.embedding_size for r in stats.results if r.ok)
        if sizes:
            print(f"\n  --- Embedding 维度 ---")
            for s in sorted(sizes):
                count = sum(1 for r in stats.results if r.ok and r.embedding_size == s)
                print(f"  {s}: {count} 次")

    errors = stats.error_breakdown()
    if errors:
        print(f"\n  --- 错误分布 ---")
        for err, count in sorted(errors.items(), key=lambda x: -x[1]):
            print(f"  {err}: {count}")

    # Concurrency analysis
    if len(lats) >= 2:
        sorted_lats = sorted(lats)
        first_half = sorted_lats[:len(sorted_lats)//2]
        second_half = sorted_lats[len(sorted_lats)//2:]
        print(f"\n  --- 并发分析 ---")
        print(f"  前一半请求平均延迟: {statistics.mean(first_half):.3f}s")
        print(f"  后一半请求平均延迟: {statistics.mean(second_half):.3f}s")
        slowdown = statistics.mean(second_half) / max(0.001, statistics.mean(first_half))
        print(f"  延迟增长倍数:       {slowdown:.2f}x")
        if slowdown > 1.5:
            print(f"  ⚠ 注意: 并发可能导致明显的排队延迟")

    print("=" * 60)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Embedding 模型并发能力测试",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--config", help="从 JSON 配置文件加载参数")
    parser.add_argument("--api-url", help="Embedding API 地址")
    parser.add_argument("--api-key", default="", help="API Key")
    parser.add_argument("--model", default="text-embedding-ada-002", help="模型名称")
    parser.add_argument("--input", default="测试文本", help="测试输入文本")
    parser.add_argument("--concurrency", type=int, default=5, help="并发数（默认 5，建议不超过 10）")
    parser.add_argument("--count", type=int, default=20, help="总请求数（默认 20，建议不超过 50）")
    parser.add_argument("--api-format", default="openai",
                        choices=["openai", "ragflow"],
                        help="API 格式: openai (OpenAI兼容), ragflow (RAGFlow内部)")
    parser.add_argument("--no-verify-ssl", action="store_true", help="跳过 SSL 证书验证")
    parser.add_argument("--output-json", help="保存 JSON 结果到指定路径")

    args = parser.parse_args()

    if args.config:
        with open(args.config) as f:
            data = json.load(f)
        emb_cfg = data.get("embedding", {})
        args.api_url = emb_cfg.get("api_url", args.api_url)
        args.api_key = emb_cfg.get("api_key", data.get("api_key", args.api_key))
        args.model = emb_cfg.get("model", args.model)
        args.input = emb_cfg.get("input_text", args.input)
        args.concurrency = emb_cfg.get("concurrency", args.concurrency)
        args.count = emb_cfg.get("request_count", args.count)
        args.api_format = emb_cfg.get("api_format", args.api_format)
        args.no_verify_ssl = not emb_cfg.get("verify_ssl", True)

    if not args.api_url:
        parser.error("需要 --api-url 参数，或使用 --config 加载配置文件")

    return args


def main():
    args = parse_args()

    if args.count > 100:
        print("⚠ 警告: 请求数超过 100，可能触发 API 风控。建议使用 --count 50 或更小的值。")
        print("按 Ctrl+C 取消，或等待 3 秒继续...")
        time.sleep(3)

    if args.concurrency > 20:
        print("⚠ 警告: 并发数超过 20，可能触发 API 限流。建议使用 --concurrency 10 或更小的值。")
        time.sleep(2)

    print(f"Embedding 模型并发测试")
    print(f"  API:  {args.api_url}")
    print(f"  Model: {args.model}")
    print(f"  Input: \"{args.input[:50]}{'...' if len(args.input) > 50 else ''}\"")
    print(f"  并发: {args.concurrency}, 请求数: {args.count}")
    print()

    stats = EmbeddingStats(config={
        "api_url": args.api_url,
        "model": args.model,
        "input_text": args.input,
        "concurrency": args.concurrency,
        "request_count": args.count,
        "api_format": args.api_format,
    })

    t0 = time.monotonic()
    try:
        asyncio.run(run_bench(
            api_url=args.api_url,
            api_key=args.api_key,
            model=args.model,
            input_text=args.input,
            concurrency=args.concurrency,
            request_count=args.count,
            verify_ssl=not args.no_verify_ssl,
            api_format=args.api_format,
            stats=stats,
        ))
    except KeyboardInterrupt:
        print("\n用户中断")

    elapsed = time.monotonic() - t0
    stats.config["total_time"] = round(elapsed, 1)
    stats.config["effective_qps"] = round(stats.total / elapsed, 2) if elapsed > 0 else 0

    print_report(stats)

    if args.output_json:
        stats.save_json(args.output_json)

    if stats.failures > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
