#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-07-23 10:34 本机时间
# Context: 定位 RAGFlow 0.25.4 + Infinity 0.7.0-dev7 在文档解析/写入 chunk 后卡死且间歇退出的首要原因：是 Infinity 被 OOM/重启，还是进程仍存活但写入或任务执行阻塞。
# Cmds: 4 条

# 1. 查看两个关键容器的实际状态、重启次数、退出码、OOM 标记和健康状态
#    解读: oom=true 或 exit=137 通常是内存不足；restart 持续增加说明问题发生在容器进程层而非仅前端卡住。
docker-compose ps 2>&1 | head -20
for svc in infinity ragflow-cpu; do
  id="$(docker-compose ps -q "$svc")"
  if [ -n "$id" ]; then
    docker inspect --format '{{.Name}} restart={{.RestartCount}} exit={{.State.ExitCode}} oom={{.State.OOMKilled}} status={{.State.Status}} started={{.State.StartedAt}} finished={{.State.FinishedAt}} health={{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$id"
  else
    echo "$svc: container not found"
  fi
done 2>&1 | head -12

# 2. 采集 Infinity 实际内存上限、当前容器内存和宿主机剩余内存
#    解读: Infinity 的 limit 接近/低于其 buffer 配置，或 MemUsage 持续顶满、宿主机 available 很低，均支持 OOM/内存压力假设。
ids="$(docker-compose ps -q infinity; docker-compose ps -q ragflow-cpu)"
if [ -n "$ids" ]; then docker inspect --format '{{.Name}} memory_limit={{.HostConfig.Memory}} memory_swap={{.HostConfig.MemorySwap}}' $ids; docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}' $ids; fi
free -m | head -3

# 3. 提取 Infinity 最近 24 小时的崩溃、内存、超时和存储错误（不输出普通日志）
#    解读: fatal/panic/oom/killed/segfault 可直接指向退出根因；rocksdb/storage/timeout/exception 则说明进程可能仍在但存储或请求已阻塞。
docker-compose logs --since 24h --timestamps infinity 2>&1 | grep -iE 'fatal|panic|oom|out of memory|killed|segfault|error|exception|timeout|rocksdb|storage|corrupt' | tail -30

# 4. 提取 RAGFlow 最近 24 小时与解析任务、chunk 写入和 Infinity 调用相关的错误
#    解读: 若反复出现 task/chunk/insert/infinity timeout 或 connection error，记录报错时间和完整几行上下文；与第3条时间对齐可判断谁先异常。
docker-compose logs --since 24h --timestamps ragflow-cpu 2>&1 | grep -iE 'error|exception|traceback|fatal|task|chunk|insert|infinity|timeout|connection refused|unhealthy' | tail -30
