@echo off
setlocal enabledelayedexpansion
REM ===========================================================================
REM RAGFlow 分布式性能压测脚本 (Windows CMD)
REM ===========================================================================
REM 功能:
REM   1. 加载 config.bat 配置
REM   2. 执行 bench_retrieval.py 并发梯度压测
REM   3. 运行 analyze.py 生成分析报告
REM
REM 用法:
REM   run_test.bat
REM
REM   REM 跳过配置加载，使用当前环境变量
REM   run_test.bat --skip-config
REM
REM   REM 自定义并发梯度
REM   set CONCURRENCIES=10,50,100,200,500
REM   run_test.bat
REM ===========================================================================

set SCRIPT_DIR=%~dp0
set SKIP_CONFIG=0

REM 检查参数
if "%1"=="--skip-config" set SKIP_CONFIG=1

REM ---- 加载配置 ----
if %SKIP_CONFIG%==0 (
    if exist "%SCRIPT_DIR%config.bat" (
        echo [1/4] 加载配置: config.bat
        call "%SCRIPT_DIR%config.bat"
    ) else (
        echo [WARN] config.bat 未找到，使用当前环境变量
    )
) else (
    echo [1/4] 跳过配置加载
)

REM ---- 默认值 ----
if "%CONCURRENCIES%"=="" set CONCURRENCIES=10,30,50,100,200,500
if "%DURATION%"=="" set DURATION=60
if "%WARMUP%"=="" set WARMUP=15
if "%OUTPUT_DIR%"=="" set OUTPUT_DIR=.\results
if "%MODE%"=="" set MODE=retrieval
if "%MAX_CONNECTIONS%"=="" set MAX_CONNECTIONS=200
if "%TOTAL_TIMEOUT%"=="" set TOTAL_TIMEOUT=120
if "%CONNECT_TIMEOUT%"=="" set CONNECT_TIMEOUT=10

REM ---- 生成时间标签 ----
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set DT=%%I
set TAG=%DT:~0,8%_%DT:~8,6%
set RESULT_DIR=%OUTPUT_DIR%\%TAG%

echo ============================================================
echo  RAGFlow 分布式性能压测
echo  时间: %DATE% %TIME%
echo  结果目录: %RESULT_DIR%
echo  并发梯度: %CONCURRENCIES%
echo ============================================================

REM ---- 前置检查 ----
echo.
echo [2/4] 环境检查 ...

REM 检查 Python
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] 未找到 python，请确认 Python 已安装并加入 PATH
    exit /b 1
)
for /f "tokens=2" %%V in ('python --version 2^>^&1') do echo   Python: %%V

REM 检查 httpx
python -c "import httpx" 2>nul
if %ERRORLEVEL% neq 0 (
    echo   [WARN] httpx 未安装，尝试安装...
    pip install httpx
    if %ERRORLEVEL% neq 0 (
        echo   [ERROR] httpx 安装失败
        exit /b 1
    )
)
echo   httpx: OK

REM 验证必要环境变量
if "%MODE%"=="retrieval" (
    if "%RAGFLOW_URL%"=="" (
        echo [ERROR] 请设置 RAGFLOW_URL 环境变量
        exit /b 1
    )
    if "%RAGFLOW_API_KEY%"=="" (
        if "%RAGFLOW_EMAIL%"=="" (
            echo [ERROR] 请设置 RAGFLOW_API_KEY 或 RAGFLOW_EMAIL/RAGFLOW_PASSWORD
            exit /b 1
        )
    )
)
echo   配置检查: OK

REM ---- 执行压测 ----
echo.
echo [3/4] 执行压测 ...

set BENCH_ARGS=--url "%RAGFLOW_URL%" --mode "%MODE%" --concurrencies "%CONCURRENCIES%" --duration %DURATION% --warmup %WARMUP% --output-dir "%OUTPUT_DIR%" --tag "%TAG%" --max-connections %MAX_CONNECTIONS% --total-timeout %TOTAL_TIMEOUT% --connect-timeout %CONNECT_TIMEOUT%

REM 认证方式
if not "%RAGFLOW_API_KEY%"=="" (
    set BENCH_ARGS=!BENCH_ARGS! --api-key "%RAGFLOW_API_KEY%"
) else (
    set BENCH_ARGS=!BENCH_ARGS! --email "%RAGFLOW_EMAIL%" --password "%RAGFLOW_PASSWORD%"
)

REM KB IDs
if not "%RAGFLOW_KB_IDS%"=="" (
    set BENCH_ARGS=!BENCH_ARGS! --kb-ids "%RAGFLOW_KB_IDS%"
)

REM 问题文件
if not "%QUESTIONS_FILE%"=="" (
    set BENCH_ARGS=!BENCH_ARGS! --questions-file "%QUESTIONS_FILE%"
)

python "%SCRIPT_DIR%bench_retrieval.py" !BENCH_ARGS!

if %ERRORLEVEL% neq 0 (
    echo [ERROR] 压测执行失败
    exit /b 1
)

REM ---- 生成报告 ----
echo.
echo [4/4] 生成分析报告 ...

set REPORT_PATH=%RESULT_DIR%\report.md
python "%SCRIPT_DIR%analyze.py" --input "%RESULT_DIR%" --output "%REPORT_PATH%"

REM ---- 完成 ----
echo.
echo ============================================================
echo  测试完成
echo  结果目录: %RESULT_DIR%
echo  汇总 JSON:  %RESULT_DIR%\summary.json
echo  请求明细:  %RESULT_DIR%\requests.csv
echo  分析报告:  %REPORT_PATH%
echo ============================================================

endlocal
