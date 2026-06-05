import os

BASE = "/app/api"

# Path to performance_timing.py source (copied separately)
PERF_SRC = "/tmp/performance_timing.py"
PERF_DST = f"{BASE}/core/workflow/graph_engine/layers/performance_timing.py"

# Copy performance_timing.py
with open(PERF_SRC) as f:
    perf_content = f.read()
with open(PERF_DST, "w") as f:
    f.write(perf_content)
print("  performance_timing.py: copied")

# __init__.py
path = f"{BASE}/core/workflow/graph_engine/layers/__init__.py"
with open(path) as f:
    content = f.read()
if "PerformanceTimingLayer" not in content:
    content = content.replace(
        "from .execution_limits import ExecutionLimitsLayer",
        "from .execution_limits import ExecutionLimitsLayer\nfrom .performance_timing import PerformanceTimingLayer",
    )
    content = content.replace(
        '    "GraphEngineLayer",',
        '    "GraphEngineLayer",\n    "PerformanceTimingLayer",',
    )
    with open(path, "w") as f:
        f.write(content)
    print("  __init__.py: updated")

# workflow_entry.py
path = f"{BASE}/core/workflow/workflow_entry.py"
with open(path) as f:
    content = f.read()
if "PerformanceTimingLayer" not in content:
    content = content.replace(
        "from core.workflow.graph_engine.layers import DebugLoggingLayer, ExecutionLimitsLayer",
        "from core.workflow.graph_engine.layers import DebugLoggingLayer, ExecutionLimitsLayer, PerformanceTimingLayer",
    )
    content = content.replace(
        "# Add observability layer when OTel is enabled",
        "# Add performance timing layer for workflow performance analysis\n        self.graph_engine.layer(PerformanceTimingLayer())\n\n        # Add observability layer when OTel is enabled",
    )
    with open(path, "w") as f:
        f.write(content)
    print("  workflow_entry.py: updated")

# workflow_execute_task.py
path = f"{BASE}/tasks/app_generate/workflow_execute_task.py"
with open(path) as f:
    content = f.read()
if "PERF_TIMING" not in content:
    if "import time\n" not in content:
        content = content.replace("import uuid\n", "import time\nimport uuid\n")
    old = '    logger.info("workflow_based_app_execution_task run with params: %s", exec_params)'
    new = (
        '    dequeue_ts = time.perf_counter()\n'
        '    logger.info(\n'
        '        "[PERF_TIMING] event=task_dequeue | workflow_id=%s | workflow_run_id=%s | app_id=%s | timestamp=%.6f",\n'
        '        exec_params.workflow_id,\n'
        '        exec_params.workflow_run_id,\n'
        '        exec_params.app_id,\n'
        '        dequeue_ts,\n'
        '    )\n'
        '\n'
        '    logger.info("workflow_based_app_execution_task run with params: %s", exec_params)'
    )
    content = content.replace(old, new)
    with open(path, "w") as f:
        f.write(content)
    print("  workflow_execute_task.py: updated")

# app_generate_service.py - only first occurrence (workflow mode)
path = f"{BASE}/services/app_generate_service.py"
with open(path) as f:
    content = f.read()
if "PERF_TIMING" not in content:
    if "import time\n" not in content:
        content = content.replace("import uuid\n", "import time\nimport uuid\n")
    old = (
        "                    def on_subscribe():\n"
        "                        workflow_based_app_execution_task.delay(payload_json)"
    )
    new = (
        "                    def on_subscribe():\n"
        "                        enqueue_ts = time.perf_counter()\n"
        "                        logger.info(\n"
        '                            "[PERF_TIMING] event=task_enqueue | workflow_id=%s | workflow_run_id=%s | app_id=%s | timestamp=%.6f",\n'
        "                            workflow.id,\n"
        "                            payload.workflow_run_id,\n"
        "                            app_model.id,\n"
        "                            enqueue_ts,\n"
        "                        )\n"
        "                        workflow_based_app_execution_task.delay(payload_json)"
    )
    idx = content.find(old)
    if idx >= 0:
        content = content[:idx] + new + content[idx + len(old):]
        with open(path, "w") as f:
            f.write(content)
        print("  app_generate_service.py: updated (workflow mode)")
    else:
        print("  app_generate_service.py: WARNING pattern not found, searching...")
        # Try partial match
        idx2 = content.find("workflow_based_app_execution_task.delay(payload_json)")
        print(f"    Found delay call at offset {idx2}")

# llm/node.py
path = f"{BASE}/core/workflow/nodes/llm/node.py"
with open(path) as f:
    content = f.read()
if "PERF_TIMING" not in content:
    old = "        yield ModelInvokeCompletedEvent("
    new = (
        '        logger.info(\n'
        '            "[PERF_TIMING] event=llm_invoke_completed | node_id=%s | node_type=%s | model=%s | "\n'
        '            "latency=%.6f | time_to_first_token=%.6f | time_to_generate=%.6f | "\n'
        '            "prompt_tokens=%d | completion_tokens=%d | total_tokens=%d",\n'
        '            node_id,\n'
        '            str(node_type),\n'
        '            model,\n'
        '            usage.latency,\n'
        '            usage.time_to_first_token if usage.time_to_first_token else 0,\n'
        '            usage.time_to_generate if usage.time_to_generate else 0,\n'
        '            usage.prompt_tokens,\n'
        '            usage.completion_tokens,\n'
        '            usage.total_tokens,\n'
        '        )\n'
        '\n'
        '        yield ModelInvokeCompletedEvent('
    )
    content = content.replace(old, new)
    with open(path, "w") as f:
        f.write(content)
    print("  llm/node.py: updated")

# Clear pycache
import subprocess
subprocess.run(["find", "/app/api", "-name", "__pycache__", "-type", "d", "-exec", "rm", "-rf", "{}", "+"], capture_output=True)
print("  pycache cleared")
print("Done!")
