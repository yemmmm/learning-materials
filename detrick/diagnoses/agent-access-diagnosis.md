# Agent内容访问：已确认结论与非源码修复边界

日期：2026-09-09。状态：用户确认本轮排查闭环，已归档。单Agent/单账号查看与编辑恢复已验证；所有Agent与未来资源的统一授权尚未完成。除非用户重新提出，不继续主动排查或实施。

## 已确认

- 当前请求已具备Agents入口及相关App操作权限，仍因目标Agent关联App的资源白名单拒绝。
- 被检查的Agent资源范围为specific，访问者不在名单且无个人资源策略。工作空间访问规则存在，不代表该目标自动向该成员开放。
- 对照账号A是Owner；用户确认其能访问。[EE3.12.1官方说明](https://ee.dify.ai/releases/v3.12.1/)明确Owner一直拥有完整访问权限，与该现象一致；现场缺少完整allowed/reason与维护者关系，具体放行分支不作为已证实事实。
- 不存在“另一环境已证明所有Admin都能访问所有Agent”的证据。两个环境dify-enterprise开关的差异不是目前已证实的Agent根因。

## 当前已有资源的处理

授权对象按用户已明确规则限定：同工作空间、当前实际拥有agent.manage的成员，以及该空间active、app-backed roster Agent。排除工作流内部Agent与其他资源。

通过已有RBAC资源成员授权接口处理Agent关联App，不修改产品源码或数据库授权表。之前已验证的路径是给单个资源、单个账号分配default（按角色权限）策略：

`PUT /console/api/workspaces/current/rbac/apps/{app_id}/users/{account_id}/access-policies`

请求体：`{"access_policy_ids":["default"]}`。

内层由RBACService.AppAccess.replace_user_access_policies调用`PUT /rbac/apps/user-access-policies`，附加相同目标参数及account_ids空列表。此前单点脚本见[单成员授权脚本](../scripts/grant-agent-member-access.sh)，其已验证适用范围是EE3.12.1的builtin admin和specific资源；它不是全成员/全Agent方案。

推广前须保留已有成员策略，按实际权限筛选目标，验证查看、编辑、调试；只有agent.manage而无App操作权限的成员不能假设分配default即可满足目标。不能通过把所有人改为Owner或把整个工作空间所有App全员开放来替代所需授权。

## 持续生效的边界

已有资源成员数据修复，不等于未来新建/复制Agent或新增成员会自动继承。当前尚未确认一个仅针对Agent、能实现上述动态规则的现成全局配置开关。

默认specific/空成员究竟来自预期默认策略还是初始化缺口，仍需进一步依据受支持的配置说明或精确创建流程确认。若当前版本没有对应配置能力，长期方案应取得官方支持的配置/修复方式；外部自动授权任务属于另一种运维方案，不能冒称原生配置，也尚未部署。

源码补丁方案已撤回，不作为当前执行建议。当前不需要重复提交角色/工作空间策略日志。

## 2026-09-09上游检索补充

- [Issue #39379](https://github.com/langgenius/dify/issues/39379)仍开放，报告资源RBAC初始化缺失导致其他成员403，明确涉及Agent复制入口。与当前白名单拒绝相关，但尚未证明现场所有创建路径均为该原因。
- [PR #41768](https://github.com/langgenius/dify/pull/41768)已于2026-09-07合并main，新增Agent专用权限管理、创建/复制授权初始化、自动成员同步及旧Agent权限迁移。需要配套RBAC服务；权限管理前端标签页不包含在该PR中。
- 目前没有核实上述改造已包含于哪一受支持企业版。不能把main合并视为EE3.12.1已修复，也不能直接在旧版执行新PR迁移命令。后续优先取得厂商的版本、配套组件与迁移说明，继续遵守不修改源码的约束。
