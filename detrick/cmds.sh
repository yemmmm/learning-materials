#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-05 23:50
# Context: sandbox 容器唯一、python3 可正常执行、sandbox 日志无任何报错——怀疑 FileNotFoundError 是 API/worker 侧抛出的，本轮抓完整 traceback 定位是哪个服务哪行代码在启动 python3
# Cmds: 4 条
# 注意: 先在 Dify 界面上重新运行一次含 code 节点的工作流让其报错，然后马上执行下面命令；docker-compose 命令在 dify 部署目录下执行

# 1. 抓 api 容器里 FileNotFoundError 的完整报错栈（traceback 的文件路径能定位是哪个服务的代码）
docker-compose logs --tail=500 api 2>&1 | grep -B5 -A20 -iE 'FileNotFoundError|No such file' | tail -40

# 2. 同样抓 worker 容器（工作流可能在 celery worker 里执行，报错在 worker 而不是 api）
docker-compose logs --tail=500 worker 2>&1 | grep -B5 -A20 -iE 'FileNotFoundError|No such file' | tail -40

# 3. 查 sandbox 是否收到过代码执行请求（若一条 run 请求都没有，说明请求根本没到 sandbox）
docker-compose logs --tail=300 sandbox 2>&1 | grep -iE 'run|post' | tail -15

# 4. 查 api 的代码执行相关环境变量（确认 CODE_EXECUTION_ENDPOINT 指向哪）
docker-compose exec -T api env 2>&1 | grep -iE 'CODE_EXECUTION|SANDBOX' | head -10
