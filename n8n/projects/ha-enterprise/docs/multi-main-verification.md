# n8n Multi-Main（双 Main）激活后验证手册

> 适用环境：德勤服务器 11vm，n8n 企业版 HA 集群（Traefik + Redis + n8n-main-1/2 + workers）
> 背景：未激活企业 license 时部署双 main 会出现双 leader 冲突，日志刷
> `Detected 2 instances claiming leader role`，定时任务重复触发。
> 激活 license 后按本手册逐项验证。

**注意：所有命令均为短单行，可直接在 MobaXterm 粘贴（长命令会被终端静默截断）。**
执行前先 `cd` 到 compose 部署目录。

---

## 1. License 确认（前提）

```bash
docker exec n8n-main-1 n8n license:info
```

- ✅ 通过：`Plan: Enterprise`（或等效企业版标识），过期时间正常
- ❌ 失败：显示 Community/Trial，说明激活未生效，后面各项不用看了

license 存在共享 PostgreSQL 中，两个 main 共用一个库，查一个即可。

## 2. 容器状态

```bash
docker ps --format '{{.Names}} {{.Status}}' | grep n8n
```

- ✅ 通过：`n8n-main-1`、`n8n-main-2` 均为 `Up`，无 `Restarting`

## 3. Leader 唯一性（核心项）

```bash
docker logs n8n-main-1 --tail 100 2>&1 | grep -i leader | tail -5
```

```bash
docker logs n8n-main-2 --tail 100 2>&1 | grep -i leader | tail -5
```

- ✅ 通过：两边都**没有** `Detected 2 instances claiming leader role`；
  日志中能看到 leader 选举相关信息，且只有一边是 leader
- ❌ 失败：该 warning 持续出现 = license 未生效或不包含 multi-main

补充：Redis 里的选举键（密码变量在 `.env` 中）

```bash
. ./.env && docker exec n8n-redis redis-cli -a "$QUEUE_BULL_REDIS_PASSWORD" --no-auth-warning keys '*leader*'
```

## 4. 双 Main 健康 + Traefik 双后端

```bash
docker inspect --format '{{.Name}} {{.State.Health.Status}}' n8n-main-1 n8n-main-2
```

- ✅ 通过：两个都是 `healthy`

Traefik 后端存活（dashboard 绑定在服务器本机 8889）：

```bash
curl -s http://127.0.0.1:8889/api/http/services | grep -o 'n8n_cluster[^}]*'
```

- ✅ 通过：能看到 `n8n_cluster` 服务，server 状态 UP
- 也可浏览器开 SSH 隧道访问 `http://127.0.0.1:8889` dashboard 直观查看

## 5. 功能级验证（终极标准）

### 5.1 定时任务不重复触发

1. 建一个测试工作流：Schedule Trigger（每 1 分钟）→ Set/NoOp 节点
2. 激活后等待 5 分钟
3. 打开 Executions 列表查看

- ✅ 通过：每个触发时间点**只有 1 条**执行记录
- ❌ 失败：成对出现 2 条 = 仍是双 leader

### 5.2 手动执行走 worker（链路完整性）

编辑器里手动执行一次工作流：

- ✅ 通过：执行正常完成；`docker logs n8n-worker-1 --tail 20` 能看到领取任务的日志
  （`OFFLOAD_MANUAL_EXECUTIONS_TO_WORKERS=true`，main 只入队不执行）

### 5.3 编辑器粘性会话

刷新几次编辑器页面，功能正常、无频繁掉线重连即视为 sticky 生效
（Traefik cookie `n8n_sid` 把浏览器固定到同一个 main）。

---

## 判定汇总

| 项 | 命令位置 | 通过标准 |
|---|---|---|
| License | §1 | Enterprise 计划 |
| Leader 唯一 | §3 | 无双 leader warning |
| 双 main 健康 | §4 | 均 healthy，Traefik 双后端 UP |
| 定时去重 | §5.1 | 每时间点 1 条执行 |
| 手动执行 | §5.2 | 完成且由 worker 消费 |

**全部通过 = multi-main 正常工作。**
其中 §3 和 §5.1 是决定性两项，其余为辅助确认。
