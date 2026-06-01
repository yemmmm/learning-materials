#!/usr/bin/env python3
"""
RAGFlow 分布式检索性能压测脚本

功能：
  - 异步高并发压测 (httpx.AsyncClient)，单进程支撑数千并发
  - 并发梯度自动扫描，绘制 QPS/延迟曲线
  - 错误分类：502/503/504、客户端超时、API 错误、连接拒绝
  - 双模式：检索压测 + 健康检查（隔离 HTTP 层 vs 检索管线）
  - 输出 CSV 明细 + JSON 汇总，可直接喂给 analyze.py

用法:
  python bench_retrieval.py \
    --url       http://10.0.0.100:18080 \
    --email     admin@example.com \
    --password  your_password \
    --kb-ids    kb_id_1,kb_id_2,kb_id_3

依赖: pip install httpx

环境变量（优先级：CLI > 环境变量）:
  RAGFLOW_URL       LB 地址
  RAGFLOW_EMAIL     登录邮箱
  RAGFLOW_PASSWORD  登录密码
  RAGFLOW_KB_IDS    知识库 ID（逗号分隔）
"""

import argparse
import asyncio
import csv
import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import httpx

# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------


@dataclass
class RequestResult:
    success: bool
    latency_s: float
    status_code: int = 0
    error_type: str = ""  # timeout / 502 / 503 / 504 / api_error / connection_error
    error_msg: str = ""
    upstream: str = ""    # X-Upstream 响应头，标识处理请求的后端服务器


@dataclass
class RoundResult:
    concurrency: int
    duration_s: float
    total: int = 0
    success: int = 0
    failure: int = 0
    qps: float = 0.0
    latencies: List[float] = field(default_factory=list)
    error_dist: Dict[str, int] = field(default_factory=dict)
    requests: List[RequestResult] = field(default_factory=list)
    upstream_dist: Dict[str, int] = field(default_factory=dict)
    p50: float = 0.0
    p75: float = 0.0
    p95: float = 0.0
    p99: float = 0.0
    avg: float = 0.0
    min_: float = 0.0
    max_: float = 0.0


# ---------------------------------------------------------------------------
# 百分位计算
# ---------------------------------------------------------------------------


def percentile(sorted_data: List[float], p: float) -> float:
    """线性插值百分位。"""
    if not sorted_data:
        return 0.0
    n = len(sorted_data)
    k = (n - 1) * p / 100.0
    f = int(k)
    c = k - f
    if f + 1 < n:
        return sorted_data[f] + c * (sorted_data[f + 1] - sorted_data[f])
    return sorted_data[f]


# ---------------------------------------------------------------------------
# RAGFlow 客户端
# ---------------------------------------------------------------------------


class RAGFlowClient:
    """异步 RAGFlow HTTP 客户端，封装认证与检索请求。"""

    def __init__(
        self,
        base_url: str,
        email: str = "",
        password: str = "",
        api_key: str = "",
        total_timeout: float = 120.0,
        connect_timeout: float = 10.0,
        max_connections: int = 200,
    ):
        self.base_url = base_url.rstrip("/")
        self.email = email
        self.password = password
        self.api_key = api_key
        self.total_timeout = total_timeout
        self.connect_timeout = connect_timeout
        self.max_connections = max_connections
        # API token 需要 Bearer 前缀；登录返回的 token 自带前缀
        self._token: Optional[str] = None
        if api_key:
            self._token = api_key if api_key.startswith("Bearer ") else "Bearer " + api_key
        self._client: Optional[httpx.AsyncClient] = None

    # ---- auth ----

    async def login(self) -> str:
        """登录并获取 Authorization token。

        RAGFlow 需要客户端对密码加密后发送。优先使用 API Token
        (--api-key) 避免此复杂度。
        """
        if self._token:
            return self._token

        # 尝试加密密码
        password_payload = self.password
        try:
            from api.utils.crypt import crypt
            password_payload = crypt(self.password)
        except ImportError:
            raise RuntimeError(
                "邮箱登录需要 pycryptodomex 库，请安装后重试，"
                "或使用 API Token: --api-key <token>\n"
                "  pip install pycryptodomex\n"
                "  (API Token 可在 RAGFlow Web UI → 个人设置 → API Token 中获取)"
            )

        async with httpx.AsyncClient(
            base_url=self.base_url, timeout=30.0, verify=False
        ) as client:
            resp = await client.post(
                "/v1/user/login",
                json={"email": self.email, "password": password_payload},
            )
            data = resp.json()
            if data.get("code") != 0:
                raise RuntimeError(
                    "登录失败: " + data.get("message", "unknown")
                )
            token = resp.headers.get("Authorization")
            if not token:
                raise RuntimeError("登录成功但未返回 Authorization header")
            self._token = token
            return token

    # ---- client lifecycle ----

    async def start(self):
        if not self._token:
            await self.login()
        limits = httpx.Limits(
            max_keepalive_connections=self.max_connections,
            max_connections=self.max_connections,
            keepalive_expiry=30,
        )
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": self._token},
            timeout=httpx.Timeout(self.total_timeout, connect=self.connect_timeout),
            limits=limits,
            verify=False,
        )

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    # ---- requests ----

    async def retrieval(self, question: str, kb_ids: List[str]) -> RequestResult:
        """单次检索请求，记录延迟、错误类型与上游服务器。"""
        t0 = time.monotonic()
        try:
            resp = await self._client.post(
                "/api/v1/retrieval",
                json={"question": question, "dataset_ids": kb_ids},
            )
            latency = time.monotonic() - t0
            upstream = resp.headers.get("X-Upstream", "")

            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0:
                    return RequestResult(True, latency, 200, upstream=upstream)
                return RequestResult(
                    False, latency, 200, "api_error",
                    "code=" + str(data.get("code", "")) + ": " + str(data.get("message", ""))[:200],
                    upstream=upstream,
                )
            elif resp.status_code in (502, 503, 504):
                return RequestResult(
                    False, latency, resp.status_code,
                    "http_" + str(resp.status_code), resp.text[:200], upstream,
                )
            else:
                return RequestResult(
                    False, latency, resp.status_code,
                    "http_" + str(resp.status_code), resp.text[:200], upstream,
                )

        except httpx.TimeoutException:
            return RequestResult(
                False, time.monotonic() - t0, 0, "client_timeout", "httpx timeout"
            )
        except httpx.ConnectError as e:
            return RequestResult(
                False, time.monotonic() - t0, 0, "connection_error", str(e)[:200]
            )
        except Exception as e:
            return RequestResult(
                False, time.monotonic() - t0, 0, "unknown",
                type(e).__name__ + ": " + str(e)[:200],
            )

    async def health_check(self) -> RequestResult:
        """轻量健康检查：调用 /api/v1/system/version 测试 HTTP 层吞吐。"""
        t0 = time.monotonic()
        try:
            resp = await self._client.get("/v1/system/version")
            latency = time.monotonic() - t0
            upstream = resp.headers.get("X-Upstream", "")
            ok = resp.status_code == 200
            return RequestResult(
                ok, latency, resp.status_code,
                "" if ok else "http_" + str(resp.status_code),
                upstream=upstream,
            )
        except httpx.TimeoutException:
            return RequestResult(
                False, time.monotonic() - t0, 0, "client_timeout", ""
            )
        except httpx.ConnectError as e:
            return RequestResult(
                False, time.monotonic() - t0, 0, "connection_error", str(e)[:200]
            )
        except Exception as e:
            return RequestResult(
                False, time.monotonic() - t0, 0, "unknown",
                type(e).__name__ + ": " + str(e)[:200],
            )


# ---------------------------------------------------------------------------
# 并发压测执行器
# ---------------------------------------------------------------------------


async def run_concurrency_round(
    client: RAGFlowClient,
    concurrency: int,
    duration_s: float,
    warmup_s: float,
    questions: List[str],
    kb_ids: List[str],
    mode: str = "retrieval",
) -> RoundResult:
    """运行一轮固定时长的并发压测。

    参数:
        client:      已认证的 RAGFlowClient
        concurrency: 并发 worker 数
        duration_s:  正式压测时长（秒）
        warmup_s:    预热时长（秒），数据丢弃
        questions:   问题池（循环使用）
        kb_ids:      知识库 ID 列表
        mode:        "retrieval" | "health"
    """
    stop = asyncio.Event()
    results: asyncio.Queue = asyncio.Queue()
    q_idx = 0
    lock = asyncio.Lock()

    async def worker():
        nonlocal q_idx
        while not stop.is_set():
            if mode == "health":
                rr = await client.health_check()
            else:
                async with lock:
                    question = questions[q_idx % len(questions)]
                    kb_id = kb_ids[q_idx % len(kb_ids)]
                    q_idx += 1
                rr = await client.retrieval(question, [kb_id])
            await results.put(rr)

    # 启动所有 worker
    tasks = [asyncio.create_task(worker()) for _ in range(concurrency)]

    # 预热期
    if warmup_s > 0:
        await asyncio.sleep(warmup_s)
        while not results.empty():
            try:
                results.get_nowait()
            except asyncio.QueueEmpty:
                break

    # 正式压测期
    t_start = time.monotonic()
    await asyncio.sleep(duration_s)
    elapsed = time.monotonic() - t_start
    stop.set()

    # 等待 worker 退出
    await asyncio.gather(*tasks, return_exceptions=True)

    # 收集结果
    latencies: List[float] = []
    error_dist: Dict[str, int] = {}
    upstream_dist: Dict[str, int] = {}
    all_results: List[RequestResult] = []
    ok = 0
    fail = 0

    while not results.empty():
        try:
            rr = results.get_nowait()
            all_results.append(rr)
            latencies.append(rr.latency_s)
            if rr.success:
                ok += 1
            else:
                fail += 1
                error_dist[rr.error_type] = error_dist.get(rr.error_type, 0) + 1
            if rr.upstream:
                upstream_dist[rr.upstream] = upstream_dist.get(rr.upstream, 0) + 1
        except asyncio.QueueEmpty:
            break

    sorted_lats = sorted(latencies)
    total = ok + fail

    return RoundResult(
        concurrency=concurrency,
        duration_s=elapsed,
        total=total,
        success=ok,
        failure=fail,
        qps=total / elapsed if elapsed > 0 else 0.0,
        latencies=sorted_lats,
        error_dist=error_dist,
        upstream_dist=upstream_dist,
        requests=all_results,
        p50=percentile(sorted_lats, 50),
        p75=percentile(sorted_lats, 75),
        p95=percentile(sorted_lats, 95),
        p99=percentile(sorted_lats, 99),
        avg=sum(latencies) / len(latencies) if latencies else 0.0,
        min_=sorted_lats[0] if sorted_lats else 0.0,
        max_=sorted_lats[-1] if sorted_lats else 0.0,
    )


# ---------------------------------------------------------------------------
# 瓶颈分析
# ---------------------------------------------------------------------------


def analyze_bottleneck(rounds: List[RoundResult], mode: str) -> Dict:
    """基于压测数据自动推测瓶颈位置。"""
    if not rounds:
        return {
            "findings": ["无数据"],
            "cpu_bottleneck_probability": "N/A",
            "embedding_bottleneck_probability": "N/A",
            "es_bottleneck_probability": "N/A",
            "recommended_max_concurrency": "N/A",
            "estimated_max_qps": "N/A",
        }

    findings = []
    cpu_prob = "低"
    emb_prob = "低"
    es_prob = "低"

    # QPS 饱和分析
    qps_values = [r.qps for r in rounds]
    max_qps = max(qps_values)
    max_qps_concurrency = rounds[qps_values.index(max_qps)].concurrency

    if len(rounds) >= 2:
        first_qps_per_conn = qps_values[0] / rounds[0].concurrency if rounds[0].concurrency > 0 else 0
        last_qps_per_conn = qps_values[-1] / rounds[-1].concurrency if rounds[-1].concurrency > 0 else 0

        if last_qps_per_conn < first_qps_per_conn * 0.3:
            findings.append("QPS 增长严重放缓 → 存在明确瓶颈，并发已超出系统处理能力")
        elif last_qps_per_conn < first_qps_per_conn * 0.6:
            findings.append("QPS 增长放缓 → 接近系统容量上限")
        else:
            findings.append("QPS 随并发近似线性增长 → 系统仍有扩容空间")

    # 错误分析
    has_timeout = any("client_timeout" in r.error_dist for r in rounds)
    has_502 = any(r.error_dist.get("http_502", 0) > 0 for r in rounds)
    has_api_error = any("api_error" in r.error_dist for r in rounds)

    if has_502:
        findings.append("检测到 502 错误 → Web 服务端过载，accept 队列满")
        cpu_prob = "中"
    if has_timeout:
        findings.append("检测到客户端超时 → 请求排队时间过长，通常是 Embedding API 延迟导致")
        emb_prob = "高"
    if has_api_error:
        findings.append("检测到 API 级错误 → Embedding API 可能限流或异常")

    # P50 分析
    if rounds:
        p50_min = min(r.p50 for r in rounds)
        p50_max = max(r.p50 for r in rounds)
        if p50_min < 0.05:
            findings.append("低并发下 P50 < 50ms → HTTP 层和 ES 检索不是瓶颈")
            es_prob = "低"
        elif p50_min < 0.2:
            findings.append("低并发下 P50 < 200ms → ES 检索和 Embedding 延迟均很低，系统健康")
            es_prob = "低"
            emb_prob = "低"
        elif p50_min > 0.5:
            findings.append(
                "低并发下 P50 > 500ms → 单次检索延迟高，"
                "大概率是 Embedding API 延迟 (400-600ms/次)"
            )
            emb_prob = "高"

    # P95/P50 比值
    for r in rounds:
        if r.p50 > 0 and r.p95 > 0:
            ratio = r.p95 / r.p50
            if ratio > 5:
                findings.append(
                    "并发=" + str(r.concurrency) + " 时 P95/P50="
                    + str(round(ratio, 1)) + " → 排队严重，大量请求在等待"
                )
                break

    # 健康检查模式
    if mode == "health":
        findings.append("health 模式 → 测试的是纯 HTTP 吞吐，不含检索管线")
        if rounds and rounds[-1].qps > 100:
            findings.append("health QPS > 100 → HTTP 层不是瓶颈")
        emb_prob = "N/A (health 模式)"

    # 推荐并发上限
    recommended = rounds[0].concurrency if rounds else 0
    for r in rounds:
        error_rate = r.failure / r.total if r.total > 0 else 1.0
        if error_rate < 0.01 and r.p95 < 10.0:
            recommended = r.concurrency
        else:
            break

    return {
        "findings": findings if findings else ["未检测到明显瓶颈，建议增加并发梯度继续测试"],
        "cpu_bottleneck_probability": cpu_prob,
        "embedding_bottleneck_probability": emb_prob,
        "es_bottleneck_probability": es_prob,
        "recommended_max_concurrency": recommended,
        "estimated_max_qps": round(max_qps, 1),
        "max_qps_at_concurrency": max_qps_concurrency,
    }


# ---------------------------------------------------------------------------
# 内置问题池（通用，适配多种 KB）
# ---------------------------------------------------------------------------

_DEFAULT_QUESTIONS = [
    "什么是机器学习？",
    "Python 的 asyncio 怎么用？",
    "什么是数据库索引？",
    "SSL/TLS 握手的过程是怎样的？",
    "微服务架构有哪些优缺点？",
    "什么是深度学习的反向传播？",
    "Redis 有哪些数据结构？",
    "HTTPS 是如何保证安全的？",
    "分布式系统中 CAP 理论是什么？",
    "Python 的 GIL 是什么？",
    "什么是 SQL 注入攻击？",
    "Docker 和虚拟机有什么区别？",
    "什么是 RESTful API？",
    "Linux 内核的主要功能有哪些？",
    "什么是神经网络的激活函数？",
    "TCP 三次握手的过程是怎样的？",
    "什么是设计模式中的单例模式？",
    "Kubernetes 的核心组件有哪些？",
    "什么是 HTTP/2 的多路复用？",
    "数据库事务的 ACID 特性是什么？",
]


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------


async def main():
    parser = argparse.ArgumentParser(
        description="RAGFlow 分布式检索性能压测脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 并发梯度扫描（默认）
  python bench_retrieval.py --url http://10.0.0.100:18080 \\
      --email admin@x.com --password xxx --kb-ids kb1,kb2,kb3

  # 健康检查模式（测试纯 HTTP 吞吐）
  python bench_retrieval.py --url http://10.0.0.100:18080 --mode health

  # 自定义并发梯度和时长
  python bench_retrieval.py --url http://10.0.0.100:18080 \\
      --email admin@x.com --password xxx --kb-ids kb1,kb2 \\
      --concurrencies 10,30,50,100 --duration 120 --warmup 30
        """,
    )

    # ---- 连接参数 ----
    parser.add_argument("--url", default=os.getenv("RAGFLOW_URL", ""),
                        help="RAGFlow LB 地址，如 http://10.0.0.100:18080")
    parser.add_argument("--email", default=os.getenv("RAGFLOW_EMAIL", ""),
                        help="登录邮箱（检索模式必需）")
    parser.add_argument("--password", default=os.getenv("RAGFLOW_PASSWORD", ""),
                        help="登录密码（检索模式必需）")
    parser.add_argument("--api-key", default=os.getenv("RAGFLOW_API_KEY", ""),
                        help="API Token（可选，优先级高于邮箱登录）")

    # ---- 测试参数 ----
    parser.add_argument("--kb-ids", default=os.getenv("RAGFLOW_KB_IDS", ""),
                        help="知识库 ID，逗号分隔（检索模式必需）")
    parser.add_argument("--mode", choices=["retrieval", "health"], default="retrieval",
                        help="压测模式: retrieval(检索) | health(健康检查/纯HTTP)")
    parser.add_argument("--concurrencies", default="10,30,50,100,200,500",
                        help="并发梯度，逗号分隔 (default: 10,30,50,100,200,500)")
    parser.add_argument("--duration", type=float, default=60.0,
                        help="每轮压测时长/秒 (default: 60)")
    parser.add_argument("--warmup", type=float, default=15.0,
                        help="每轮预热时长/秒 (default: 15)")

    # ---- 输出参数 ----
    parser.add_argument("--output-dir", default="results",
                        help="结果输出目录 (default: results)")
    parser.add_argument("--tag", default="",
                        help="测试标签，用于区分多轮测试 (default: 自动生成时间戳)")

    # ---- 高级参数 ----
    parser.add_argument("--questions-file", default="",
                        help="自定义问题文件，每行一个问题 (default: 使用内置问题)")
    parser.add_argument("--max-connections", type=int, default=200,
                        help="httpx 最大连接数 (default: 200)")
    parser.add_argument("--total-timeout", type=float, default=120.0,
                        help="单请求总超时/秒 (default: 120)")
    parser.add_argument("--connect-timeout", type=float, default=10.0,
                        help="连接超时/秒 (default: 10)")

    args = parser.parse_args()

    # ---- 参数校验 ----
    if not args.url:
        parser.error("必须指定 --url 或设置 RAGFLOW_URL 环境变量")
    if args.mode == "retrieval":
        if not args.api_key and (not args.email or not args.password):
            parser.error("检索模式需要 --email/--password 或 --api-key")
        if not args.kb_ids:
            parser.error("检索模式需要 --kb-ids")

    # ---- 准备 ----
    concurrency_list = [
        int(x.strip()) for x in args.concurrencies.split(",") if x.strip()
    ]
    kb_ids = [
        x.strip() for x in args.kb_ids.split(",") if x.strip()
    ] if args.kb_ids else []
    tag = args.tag or datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_dir = Path(args.output_dir) / tag
    output_dir.mkdir(parents=True, exist_ok=True)

    # 问题池
    if args.questions_file:
        questions = Path(args.questions_file).read_text(encoding="utf-8").strip().splitlines()
    else:
        questions = _DEFAULT_QUESTIONS

    # ---- 连接测试 ----
    print("=" * 60)
    print("RAGFlow 性能压测 - " + tag)
    print("目标: " + args.url + "  模式: " + args.mode)
    concurrency_str = ",".join(str(c) for c in concurrency_list)
    print("并发梯度: " + concurrency_str
          + "  时长: " + str(args.duration) + "s  预热: " + str(args.warmup) + "s")
    print("=" * 60)

    client = RAGFlowClient(
        base_url=args.url,
        email=args.email,
        password=args.password,
        api_key=args.api_key,
        total_timeout=args.total_timeout,
        connect_timeout=args.connect_timeout,
        max_connections=args.max_connections,
    )

    # 连通性检查
    print("\n>>> 连通性检查 ...")
    try:
        await client.start()
        test_rr = await (
            client.retrieval(questions[0], [kb_ids[0]])
            if args.mode == "retrieval"
            else client.health_check()
        )
        if test_rr.success:
            print("    OK - " + args.mode + " 请求成功, 延迟 "
                  + "{:.3f}".format(test_rr.latency_s) + "s")
        else:
            print("    FAIL - " + test_rr.error_type + ": " + test_rr.error_msg)
            await client.close()
            sys.exit(1)
    except Exception as e:
        print("    FATAL - 连接失败: " + str(e))
        sys.exit(1)

    # ---- 执行压测 ----
    all_rounds: List[RoundResult] = []
    csv_path = output_dir / "requests.csv"

    # CSV header
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "concurrency", "success", "latency_s",
                          "status_code", "error_type", "upstream"])

    for i, c in enumerate(concurrency_list, 1):
        prefix = "\n>>> [" + str(i) + "/" + str(len(concurrency_list)) + "] 并发=" + str(c) + "  "
        print(prefix, end="", flush=True)

        round_result = await run_concurrency_round(
            client, c, args.duration, args.warmup,
            questions, kb_ids, args.mode,
        )

        # 写入 per-request CSV
        ts = datetime.now(timezone.utc).isoformat()
        with open(csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for rr in round_result.requests:
                writer.writerow([ts, c, rr.success, round(rr.latency_s, 4),
                                 rr.status_code, rr.error_type, rr.upstream])

        # 汇总输出
        err_items = []
        for k, v in round_result.error_dist.items():
            err_items.append(k + "=" + str(v))
        err_summary = ", ".join(err_items) if err_items else "无"
        print(
            "QPS={:.1f}  P50={:.3f}s  P95={:.3f}s  P99={:.3f}s  "
            "OK={}  FAIL={}".format(
                round_result.qps, round_result.p50, round_result.p95,
                round_result.p99, round_result.success, round_result.failure,
            )
        )
        if round_result.failure > 0:
            print("    错误分布: " + err_summary)
        if round_result.upstream_dist:
            ups_items = []
            for k, v in round_result.upstream_dist.items():
                ups_items.append(k + "=" + str(v))
            print("    上游服务器: " + ", ".join(ups_items))

        all_rounds.append(round_result)

    # ---- 关闭客户端 ----
    await client.close()

    # ---- 输出汇总 JSON ----
    summary = {
        "test_config": {
            "url": args.url,
            "mode": args.mode,
            "tag": tag,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "concurrencies": concurrency_list,
            "duration_s": args.duration,
            "warmup_s": args.warmup,
            "kb_ids": kb_ids,
            "question_count": len(questions),
        },
        "rounds": [],
        "bottleneck_analysis": {},
    }

    for r in all_rounds:
        summary["rounds"].append({
            "concurrency": r.concurrency,
            "total": r.total,
            "success": r.success,
            "failure": r.failure,
            "qps": round(r.qps, 1),
            "avg_s": round(r.avg, 3),
            "p50_s": round(r.p50, 3),
            "p75_s": round(r.p75, 3),
            "p95_s": round(r.p95, 3),
            "p99_s": round(r.p99, 3),
            "min_s": round(r.min_, 3),
            "max_s": round(r.max_, 3),
            "error_distribution": r.error_dist,
            "upstream_distribution": r.upstream_dist,
        })

    # 瓶颈分析
    summary["bottleneck_analysis"] = analyze_bottleneck(all_rounds, args.mode)

    # 全局上游服务器汇总
    all_upstream: Dict[str, int] = {}
    for r in all_rounds:
        for k, v in r.upstream_dist.items():
            all_upstream[k] = all_upstream.get(k, 0) + v
    summary["upstream_distribution"] = all_upstream

    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\n>>> 结果已保存: " + str(summary_path))

    # ---- 终端报告 ----
    ba = summary["bottleneck_analysis"]
    print("\n" + "=" * 60)
    print("瓶颈分析")
    print("=" * 60)
    for line in ba["findings"]:
        print("  " + line)
    print("\n  CPU 瓶颈概率:       " + ba["cpu_bottleneck_probability"])
    print("  Embedding 瓶颈概率: " + ba["embedding_bottleneck_probability"])
    print("  ES 瓶颈概率:        " + ba["es_bottleneck_probability"])
    print("  推荐并发上限:       " + str(ba["recommended_max_concurrency"]))
    print("  预估最大 QPS:       " + str(ba["estimated_max_qps"]))
    if all_upstream:
        print("\n  上游服务器分布:")
        for k, v in all_upstream.items():
            print("    " + k + ": " + str(v) + " 请求")

    print("\n" + "=" * 60)
    print("QPS / 延迟对比表")
    print("=" * 60)
    header = "{:>6} {:>8} {:>8} {:>8} {:>8} {:>8}".format(
        "并发", "QPS", "P50(s)", "P95(s)", "P99(s)", "成功率")
    print(header)
    print("-" * len(header))
    for r in all_rounds:
        rate = ("{:.1f}%".format(r.success / r.total * 100)
                if r.total > 0 else "N/A")
        print("{:>6} {:>8.1f} {:>8.3f} {:>8.3f} {:>8.3f} {:>8}".format(
            r.concurrency, r.qps, r.p50, r.p95, r.p99, rate))
    print("-" * len(header))

    print("\n完成。运行 analyze.py 可生成详细报告。")


if __name__ == "__main__":
    asyncio.run(main())
