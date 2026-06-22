# RAGFlow Tenant not Found - 本轮定位命令

## 当前线索判读

- Step 1 全空 → 所有用户的 tenant / user_tenant 行都存在
- 改了 `common_service.py:get_by_id` 没看到 debug 日志 → **修改没被加载执行**

最可能的原因：**容器跑的是镜像里的代码，宿主机改的文件没挂载进去**。本轮先验证这点，再决定下一步。

---

## Step 1：验证容器里的代码是不是改过

```bash
# 1.1 看容器里 get_by_id 有没有 DEBUG 字样
docker exec -it ragflow-server grep -c "DEBUG get_by_id" /ragflow/api/db/services/common_service.py

# 1.2 看容器里实际生效的函数体
docker exec -it ragflow-server sed -n '/def get_by_id/,/return False, None/p' /ragflow/api/db/services/common_service.py
```

**判读**：
- 返回 `0` 或函数体里没 `[DEBUG]` 字样 → **修改没进容器**，走 Step 2
- 返回 `>0` 或函数体里有 `[DEBUG]` 字样 → 修改进容器了，但没执行，走 Step 3

---

## Step 2：把修改注入容器（Step 1 判读为"没进容器"时执行）

### 方式 A：宿主机 → 容器 `docker cp`（推荐）

```bash
# 2.A.1 把宿主机改过的文件复制进容器（替换 <宿主机路径>）
docker cp <宿主机路径>/common_service.py ragflow-server:/ragflow/api/db/services/common_service.py

# 2.A.2 清理 .pyc 缓存，避免 Python 加载旧字节码
docker exec -it ragflow-server find /ragflow -name "*.pyc" -path "*common_service*" -delete
docker exec -it ragflow-server find /ragflow -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# 2.A.3 重启 ragflow_server
docker exec -it ragflow-server supervisorctl restart ragflow_server

# 2.A.4 等 5 秒后验证函数体
sleep 5
docker exec -it ragflow-server grep -c "DEBUG get_by_id" /ragflow/api/db/services/common_service.py
```

### 方式 B：直接在容器里改（不想 docker cp）

```bash
# 2.B.1 进容器
docker exec -it ragflow-server bash

# 容器内执行：
# 2.B.2 备份原文件
cp /ragflow/api/db/services/common_service.py /ragflow/api/db/services/common_service.py.bak

# 2.B.3 用 sed 在 get_by_id 函数 try: 之后插入调试日志
python3 -c "
import re
p = '/ragflow/api/db/services/common_service.py'
s = open(p).read()
s = re.sub(
    r'(def get_by_id\(cls, pid\):\s*\n\s*try:\s*\n)(\s*)(obj = cls\.model\.get_or_none)',
    r'\1\2logging.warning(f\"[DEBUG] get_by_id cls={cls.__name__} pid={pid!r}\")\n\2\3',
    s
)
open(p, 'w').write(s)
print('patched')
"

# 2.B.4 清缓存、重启
find /ragflow -name '*.pyc' -delete
supervisorctl restart ragflow_server
exit
```

---

## Step 3：修改进了容器但没执行（Step 1 判读为"已进容器"时执行）

### 3.1 确认 ragflow_server 进程的启动时间和 PID

```bash
docker exec -it ragflow-server supervisorctl status ragflow_server
docker exec -it ragflow-server ps -eo pid,etime,cmd | grep ragflow_server | grep -v grep
```

如果 `etime`（运行时长）显示进程是几小时前启动的，说明重启没生效。

### 3.2 强杀等自动拉起

```bash
docker exec -it ragflow-server bash -c "pkill -9 -f ragflow_server && sleep 3 && supervisorctl status ragflow_server"
```

### 3.3 看启动日志有无报错（例如 import 失败导致回滚旧代码）

```bash
docker exec -it ragflow-server tail -100 /ragflow/log/ragflow_server.log
```

如果看到 `SyntaxError` / `ImportError` / 文件加载失败 → 修改的代码语法有问题，把容器里的备份还原：

```bash
docker exec -it ragflow-server cp /ragflow/api/db/services/common_service.py.bak /ragflow/api/db/services/common_service.py
docker exec -it ragflow-server supervisorctl restart ragflow_server
```

---

## Step 4：触发并抓日志（Step 2 或 3 完成后）

```bash
# 4.1 清空当前日志末尾位置标记
docker exec -it ragflow-server bash -c "wc -l /ragflow/log/ragflow_server.log"
```

web UI 触发一次创建 KB。

```bash
# 4.2 抓最近的 DEBUG / 错误日志（把 <上面行号+10> 替换为 4.1 的输出 + 10）
docker exec -it ragflow-server bash -c "tail -n +<上面行号+10> /ragflow/log/ragflow_server.log | grep -E 'DEBUG get_by_id|Tenant not found|ERROR|Traceback'"

# 或者直接抓最近的 200 行
docker exec -it ragflow-server bash -c "tail -200 /ragflow/log/ragflow_server.log | grep -E 'DEBUG get_by_id|Tenant not found|ERROR|Traceback'"
```

把这段输出贴出来。

---

## Step 5：可能用到的额外诊断 - 抓"哪个端点在打这条日志"

如果 Step 4 仍然没有 `[DEBUG] get_by_id` 输出，说明报错压根没走 `TenantService.get_by_id`，可能是别的代码路径。在请求触发瞬间抓 stack：

```bash
# 5.1 触发 KB 创建后立刻抓所有 ragflow_server 的 Python 进程的 stack
docker exec -it ragflow-server bash -c "for pid in \$(pgrep -f ragflow_server); do echo '=== PID:' \$pid ' ==='; py-spy dump --pid \$pid 2>/dev/null || cat /proc/\$pid/status | head -3; done"
```

如果容器没 `py-spy`：

```bash
# 5.2 改成抓 Python 进程的当前 stack（需要安装 py-spy，离线可能没法装）
docker exec -it ragflow-server pip install py-spy
```

或者更原始的办法：临时在 `get_data_error_result`（`api/utils/api_utils.py:120`）里加 traceback 打印：

```bash
# 5.3 在容器里改 api_utils.py
docker exec -it ragflow-server bash -c "
cp /ragflow/api/utils/api_utils.py /ragflow/api/utils/api_utils.py.bak
python3 -c \"
import re
p = '/ragflow/api/utils/api_utils.py'
s = open(p).read()
s = s.replace(
    'def get_data_error_result(code=RetCode.DATA_ERROR, message=\\\"Sorry! Data missing!\\\"):\n    if sys.exc_info()[0] is not None:',
    'def get_data_error_result(code=RetCode.DATA_ERROR, message=\\\"Sorry! Data missing!\\\"):\n    import traceback as _tb\n    logging.warning(f\\\"[DEBUG] get_data_error_result called: {message}\\\")\n    _tb.print_stack()\n    if sys.exc_info()[0] is not None:'
)
open(p, 'w').write(s)
print('patched')
\"
find /ragflow -name '*.pyc' -delete
supervisorctl restart ragflow_server
"
```

再次触发 KB 创建，日志里会打出完整调用栈，能看到 `Tenant not found.` 到底是哪一行触发的。

---

## Step 6：还原修改（定位完成后）

```bash
# 还原 common_service.py
docker exec -it ragflow-server cp /ragflow/api/db/services/common_service.py.bak /ragflow/api/db/services/common_service.py 2>/dev/null || \
docker cp <宿主机备份>/common_service.py.orig ragflow-server:/ragflow/api/db/services/common_service.py

# 还原 api_utils.py（如果做了 Step 5.3）
docker exec -it ragflow-server cp /ragflow/api/utils/api_utils.py.bak /ragflow/api/utils/api_utils.py

# 清缓存 + 重启
docker exec -it ragflow-server find /ragflow -name '*.pyc' -delete
docker exec -it ragflow-server supervisorctl restart ragflow_server
```
