# Dify API：DSL 导入 + 添加模板 + 鉴权机制

## 需求场景

通过 API 接口导入 Workflow DSL，并将其发布为 Explore 模板，供其他用户安装使用。适用于将 Dify 集成到其他应用后端的场景。

---

## 接口 1：导入 DSL 创建应用

```
POST /console/api/apps/imports
```

### 请求体

```json
{
  "mode": "yaml-content",
  "yaml_content": "<DSL YAML 字符串>",
  "name": "My App",
  "description": "可选描述",
  "icon_type": "emoji",
  "icon": "🤖",
  "icon_background": "#FFEAD5",
  "app_id": null
}
```

- `mode`: `"yaml-content"`（传 YAML 字符串）或 `"yaml-url"`（传 URL 拉取，GitHub blob URL 会自动转 raw）
- `app_id`: 不为空时是更新已有应用（仅 workflow/advanced-chat 模式）

### 返回

```json
{
  "id": "import-uuid",
  "status": "completed",
  "app_id": "新创建的应用 UUID",
  "app_mode": "workflow",
  "current_dsl_version": "0.1.3",
  "imported_dsl_version": "0.1.2",
  "error": null
}
```

- `status: "completed"` → 200，导入成功
- `status: "pending"` → 202，DSL 版本比当前 Dify 版本新，需调用确认接口
- `status: "failed"` → 400，导入失败

### 确认导入（pending 时）

```
POST /console/api/apps/imports/{import_id}/confirm
```

注意参数是返回的 `id`（import_id），不是 `app_id`。

---

## 接口 2：发布为模板

```
POST /console/api/admin/insert-explore-apps
```

### 请求体

```json
{
  "app_id": "第一步返回的 app_id",
  "desc": "模板描述",
  "language": "en-US",
  "category": "Chatbot",
  "position": 1,
  "can_trial": true,
  "trial_limit": 100
}
```

- 如果 app 已在 explore 列表中 → 更新（200）
- 不在 → 新增 RecommendedApp 记录，设 app.is_public = True（201）

### 限制

该接口有 `@only_edition_cloud` 装饰器，仅 Dify Cloud 版可用。社区自部署版会返回 403。

---

## 鉴权方式

### 后端集成的正确方式：ADMIN_API_KEY

Dify 的 `ext_login.py` 中 `load_user_from_request` 在执行 JWT 校验之前，会先检查 ADMIN_API_KEY：

```
第 32-49 行逻辑：
1. 从 Cookie 或 Authorization header 提取 token
2. 如果 ADMIN_API_KEY_ENABLE=true 且 token == ADMIN_API_KEY
3. 读取 X-WORKSPACE-ID header
4. 找到该工作区的 Owner 账号作为 current_user
5. 跳过后续 JWT 验证
```

同时 `libs/token.py` 中 CSRF 检查也会自动跳过 ADMIN_API_KEY 请求。

### 配置

```bash
# api/.env
ADMIN_API_KEY_ENABLE=true
ADMIN_API_KEY=<你的密钥>
```

ADMIN_API_KEY 无格式要求，任何非空字符串即可。生成随机 key：

```bash
openssl rand -hex 32
```

### 请求示例

```
POST /console/api/apps/imports
Authorization: Bearer <ADMIN_API_KEY>
X-WORKSPACE-ID: <workspace-uuid>

POST /console/api/admin/insert-explore-apps
Authorization: Bearer <ADMIN_API_KEY>
```

一个 ADMIN_API_KEY 通吃所有 `/console/api/*` 接口，无需调 login 接口、无需 JWT、无需处理 CSRF。

---

## 为什么不建议用用户登录 JWT 做后端集成

1. 有有效期，过期需重新登录刷新
2. 语义上这是用户会话凭据，不适合服务间调用
3. 需要额外处理 CSRF token

ADMIN_API_KEY 是 Dify 为服务端集成设计的机制。

---

## 完整流程

```
1. openssl rand -hex 32  → 生成 ADMIN_API_KEY
2. 配置 .env: ADMIN_API_KEY_ENABLE=true, ADMIN_API_KEY=xxx
3. 重启 API
4. POST /console/api/apps/imports
   Header: Authorization: Bearer <ADMIN_API_KEY>
           X-WORKSPACE-ID: <workspace-id>
   Body: { mode: "yaml-content", yaml_content: "...", name: "..." }
   → 得到 app_id
5. POST /console/api/admin/insert-explore-apps  (仅 Cloud 版)
   Header: Authorization: Bearer <ADMIN_API_KEY>
   Body: { app_id: "...", language: "en-US", category: "...", position: 1 }
```

## 鉴权机制全景

| 蓝图 | 凭据 | Token 类型 | 获取方式 |
|---|---|---|---|
| console | Cookie / Bearer | JWT (HS256, SECRET_KEY) | /console/api/login |
| console | Bearer + X-WORKSPACE-ID | ADMIN_API_KEY | .env 配置 |
| service_api | Bearer | App API Token (随机串) | 控制台 App → API 访问 |
| web | X-App-Code + X-App-Passport | JWT | WebApp 嵌入 |

### ADMIN_API_KEY vs JWT 分发路径

```
extract_access_token()
  ├── Cookie: access_token 或 __Host-access_token
  └── Authorization: Bearer <token>
         │
         ▼
load_user_from_request()
  ├── [优先] token == ADMIN_API_KEY? → 取 X-WORKSPACE-ID → 返回 Owner
  ├── blueprint=console → PassportService.verify(JWT) → 返回 Account
  ├── blueprint=web → PassportService.verify(JWT) → 返回 EndUser
  └── blueprint=mcp → server_code 查库 → 返回 EndUser
```
