@echo off
REM ===========================================================================
REM RAGFlow 性能压测配置 (Windows CMD)
REM ===========================================================================
REM 用法:
REM   config.bat          在当前 CMD 窗口中加载环境变量
REM   或在 run_test.bat 中自动 source
REM
REM 所有变量也可通过命令行参数覆盖，CLI 优先级更高。
REM ===========================================================================

REM ---- 目标服务地址 ----
REM RAGFlow 的 LB 入口地址
set RAGFLOW_URL=http://10.0.0.100:18080

REM ---- 认证信息 ----
REM 推荐使用 API Token（在 RAGFlow Web UI → 个人设置 → API Token 获取）
set RAGFLOW_API_KEY=ragflow-your-api-token-here

REM 或者使用邮箱登录（需要 pip install pycryptodomex）
REM set RAGFLOW_EMAIL=admin@ragflow.io
REM set RAGFLOW_PASSWORD=your_password_here

REM ---- 知识库 ID ----
REM 逗号分隔，建议至少 3 个
set RAGFLOW_KB_IDS=kb_id_1,kb_id_2,kb_id_3

REM ---- 并发梯度 ----
set CONCURRENCIES=10,30,50,100,200

REM ---- 测试时长（秒） ----
set DURATION=60
set WARMUP=15

REM ---- 输出目录 ----
set OUTPUT_DIR=.\results

REM ---- 高级参数 ----
set MAX_CONNECTIONS=200
set TOTAL_TIMEOUT=120
set CONNECT_TIMEOUT=10

echo [OK] RAGFlow perf test config loaded.
echo   URL: %RAGFLOW_URL%
echo   Concurrencies: %CONCURRENCIES%
