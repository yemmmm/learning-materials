# AGENT-CONTENT-ACCESS-20260909

状态：需求已明确，设计审查PASS；实现进行中，独立测试待完成；未部署封闭现场。

## 用户确认的规则

用户原话：我希望所有能访问到agents页面的用户就可以访问页面中的所有agents（不是指web app），推进权限修复。

原问题是新版Agent内容的查看与编辑被单资源白名单拒绝。一个Agent通过单成员default策略授权后已验证查看、保存和重新进入内容保留；该操作不是产品根因修复。本需求改为产品授权规则，不逐个补白名单。

## 功能合同

- 当前工作空间拥有Agents入口权限（RBAC workspace agent.manage）的成员，可查看、编辑、调试该工作空间内所有正常roster Agent。
- 对这些操作不再要求该账号出现在单Agent资源白名单，也不再要求额外单资源查看/编辑/调试权限键。
- 覆盖已有、新建、复制的roster Agent，以及后来获得或失去agent.manage的成员。判定应使用请求时的实际权限，不能靠创建时枚举成员或定时全量回填。
- 工作空间隔离保持。工作流内部workflow-only Agent不纳入，继续受其父工作流原规则约束。
- WebApp、Backend API发布访问、API Key管理、工作流/知识库授权保持原规则；Agent删除、发布等管理操作也暂保留原权限。
- 基于此前查看/编辑问题，调试被视为内容编辑流程所需；已发可选问题确认是否还要扩大到删除/发布，尚无补充答案，按上述最小范围推进。若用户扩大范围，须同步设计与测试。

## 现状与证据边界

- 现场EE API/api_websocket/web/rbac等为3.12.1，两个API服务RBAC_ENABLED及ENTERPRISE_ENABLED均true。
- 现场AgentChatMessageListApi含APP_VIEW_LAYOUT装饰器；诊断确认角色中admin存在、agent_manage允许，但app_view_layout/app_edit因account is not in the resource whitelist拒绝，资源scope=specific。
- 普通/app/<id>/access-config不作为已验证的新版Agent操作入口。用户当前新版/agents/<id>/config仅提供发布渠道权限。
- 工作目录/home/yangxiang/deployed-services/dify-enterprise-0325仅部署配置，本身未纳入父仓库跟踪；有大量无关未跟踪文件，禁止打包或修改。
- 修复交付仓库/home/yangxiang/learning-materials，目录detrick/agent-content-access-fix；用户规则要求每轮相关资料修改commit并push，禁止提交无关内容。
- 精确公开基线为Dify 60a18fa。快照/tmp/dify-rbac-review-60a18fa与tree.json供只读研究；不把已有快照等同现场全部源码。
- 本机镜像langgenius/dify-ee-api:3.12.0的controllers/common/wraps.py与公开60a18fa字节一致，SHA256 a55bde316d9550353d2f2b4f3c9aa83f9085cbe34cc1f01767d50c6b11c11d9c。原件在/tmp/detrick-agent-content-20260909/wraps.ee3120.py及wraps.upstream.py。
- 此本机镜像可在隔离临时容器导入controllers.common.wraps，内含Python3.12.13和pytest9.0.3。现场3.12.1待部署前核对实际文件，不能直接覆盖不匹配版本。

## 交付与验收

- 最小范围源码补丁；可从现场原文件验证/生成持久化补丁，具备明确部署与移除回滚步骤。优先只改必要公共权限入口，不修改整个Dify产品或构建无关架构。
- 必须审查前端和列表是否还有资源权限过滤；不能只证明单一GET接口通过就宣称Agent编辑可用。
- 设计和共用测试计划由planner编写；plan_reviewer审查严重问题；requirement_developer实现；requirement_tester独立验证；主协调者记录结论并提交。
- 设计复审已通过：新增授权严格限定console blueprint，OpenAPI继续原规则；已有legacy路由守卫保持基线，不将本次正向授权需求扩展为全接口权限重构。审查处置见design.md。
- 本地至少覆盖同租户、跨租户、无agent.manage、仅agent.manage而无app权限、既有specific例外、老/新Agent、workflow-only、非目标scene、权限撤销、RBAC关闭、安装版本不匹配及回滚。
- 尽量在本机真实API镜像和独立临时数据库执行组件测试。区分真实代码/数据库测试与外部RBAC模拟，不冒充完整现场验收。
- 现场运行由用户在封闭服务器执行。需验证至少两个账号及旧/新Agent，查看/编辑/调试成功，发布渠道和非目标资源权限未扩大；在回传前总体状态保留PARTIAL/待现场验收。
