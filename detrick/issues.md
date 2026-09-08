# 德勤问题定位记录

## WF-20260908：WebApp 权限操作401与提示词重进为空

状态：提示词问题已定位待修复；WebApp401仍在排查。环境 A，并据用户描述在多套环境出现；两个症状不必同时出现。

### 症状与范围

同一 admin 在不同 workspace 表现不同：部分工作流设置 WebApp 访问权限返回401；另一些修改 LLM 提示词、Publish Update、退出重进后提示词为空。

### 2026-09-08 已知证据

来源：用户执行命令提交 `09ea418` 后回传。

- API/WebSocket 的数据库及鉴权变量比较一致；Redis 比较缺行，不能排除协同存储配置问题。
- RBAC 拒绝 scene=app_view_layout，whitelist_denial=true，account_role_ids 非空，matched_role_ids=[]。日志应用 ID 的可辨识前缀为92714548，与本轮查询的43c6d3bb不同；其余 ID 有错行，不能关联到此次 WebApp 401，也不能推出用户没有角色。
- 查询应用43c6d3bb…，mode=advanced-chat；本次实际对象为 Chatflow。草稿更新时间06:29:06.754219，当前发布版本创建于06:27:07.265530（保留数据库输出时刻，时区待确认）。草稿、当前发布版均有1个LLM节点，但二者的提示词长度行未回传。
- 另外两个旧发布快照的LLM提示词长度均为414。旧版仍有提示词内容，不能证明最新修改被保存，也不足以承诺完整恢复。
- ws 配置是候选线索；页面协议及浏览器实际连接状态未确认。
- 参考公开源码60a18fa：发布读取已存储草稿；WebApp访问范围调用enterprise/webapp接口。尚未验证服务器完整源码一致性，不能直接作为根因。

### 2026-09-08 后续回传（命令提交7a647d7）

- 再次回传相同草稿/发布时刻和旧版414字符；draft/current的PROMPT行仍缺失。缺行不等于0字符，用户开头“112”无字段上下文，未解释为长度。
- 实际workflow控制器指纹d4eb1fccf9d3aebd；DraftWorkflowApi GET/POST和PublishedWorkflowApi GET均标记APP_VIEW_LAYOUT，发布POST标记APP_RELEASE_AND_VERSION。不能将草稿保存直接归因于缺APP_EDIT；装饰器输出不代表已验证所有内部检查。
- 本轮改成两个独立只读命令，分别仅输出DRAFT和CURRENT的一行提示词统计，固定应用43c6d3bb…和节点llm。待证据到齐后再区分持久化与界面问题。

### 2026-09-08 提示词统计回传（命令提交e6abbe1）

- 用户报告两条均为“draft promt=list items=2 chars=414”。据此确认本次查询的目标节点草稿提示词非空；不能证明最新编辑已保存，亦不能排除之前曾发生清空。
- 本机核对已推送命令：第二条传CURRENT，代码原样打印此标签。用户概述中两条均为draft，故当前发布版结果待澄清，不能默认为已查到。
- 草稿与旧快照长度同为414只说明长度相等，不代表内容相同。下一步必须区分界面显示空、接口返回空和新增编辑未保存，避免继续仅统计字数。

### 2026-09-08 用户澄清CURRENT与Process Data

- 用户明确第二条为CURRENT：草稿和当前发布版均为list、items=2、chars=414；前一条“当前发布版待澄清”的状态已解除。长度相同仍不代表内容相同或最新编辑已保存。
- 节点编辑器Prompt显示为空；Process Data中存在疑似很早写入的提示词。Process Data具体所在界面尚未确认；若来自上次运行，则是执行记录，不可当作当前草稿响应。
- 当前最小证据缺口是浏览器GET workflows/draft响应的目标llm节点：两项prompt_template各自role、text是否为空/旧/新，以及data.model.mode。无需继续重复数据库字数统计，不以此判断根因已定位。

### 2026-09-08 浏览器响应与Console新证据

- 用户回传GET草稿节点的两个角色分别为system、user，text为旧提示词。结合编辑器显示空：已观察到接口内容和编辑器显示不一致；预期新提示词不在本次草稿响应内，仍需区分未保存与后续覆盖。
- Console显示401，资源路径被截断为 /console/api/enter...p/app/access-mode:1。参考接口定义对应 /enterprise/webapp/app/access-mode，GET读取访问范围、POST修改；完整请求路径和方法仍需Network核实。末尾:1是Console来源行号形式，不当作接口路径。
- 此请求不是 /workflows/draft；尚无证据说明草稿保存也发生401，两个症状继续分别定位。
- 下一项关键证据：access-mode请求的Request Method、Response原文中的错误码/消息以及appId，用于关联目标应用；不收集Cookie或Authorization。

### 2026-09-08 模型模式与提示词结构不一致

- 新回传：目标节点data.model.mode=completion；点击节点无Console新错误；socket.io返回101。101仅证明WebSocket升级成功，不证明协同事件或保存成功。
- 已有数据：prompt_template为system/user两项列表，GET返回旧文本，界面Prompt为空。当前节点的模式与提示词结构不匹配，作为空白显示的高置信原因；尚未验证远程前端构建完全匹配参考源码，尚未修复验收。
- 参考公开源码60a18fa：use-config.ts以model.mode==chat决定Chat分支；components/config-prompt.tsx第260–264行completion分支读payload.text（或jinja2_text），不会读取列表条目的text。第142–147行编辑时按单个PromptItem写入，同样与列表结构冲突。不能仅据源码断言实际服务器必然抛错或必然丢弃某字段。
- 源码：https://github.com/langgenius/dify/blob/60a18fa/web/app/components/workflow/nodes/llm/components/config-prompt.tsx
- 用户此前纠正access-mode401来自更改WebApp权限操作的残留，进入编排页未观察到该请求；401继续独立排查。
- 下一步确认具体模型/供应商的真实类型，在备份或复制的应用中验证：真实Chat模型应使用chat+列表；真实Completion模型应使用completion+单个提示词对象。不直接批量改库，不盲目将全部模型设成chat。验收包含编辑显示、保存后重开、发布后重开和实际节点执行。

### 2026-09-08 Chat模型对照正常

- 用户确认模型真实类型是Completion；新增Chat模型并配置提示词后不再出现消失。此证据支持模式相关分支，但未证明全新Completion节点也必现，不认定整个Completion功能都损坏。
- 参考源码新线索：llm/default.ts初始mode=chat且prompt_template为列表；use-config.ts切换mode仅在defaultConfig已就绪时替换模板；use-llm-input-manager.ts初始化effect在inputs.prompt_template存在时跳过。默认配置未就绪可能保留错误结构，这是待验证候选，远程前端源码尚未核验。
- 最小实验：同一workspace的临时Chatflow，全新添加LLM节点、选择同一Completion模型，输入DIAG_COMPLETION_20260908；先不发布，等保存后重进。浏览器看default-workflow-block-configs请求状态，以及POST workflows/draft负载中的mode、prompt_template形状和标记。随后才测试发布是否改变结果。无须运行模型。
- cmds.sh两条只读命令用于服务镜像核对、临时应用草稿结构/标记前后快照；不修改原应用。临时app ID由用户填入。

### 2026-09-08 编辑后POST草稿负载已为空

- 用户回传：不发布也会丢失，编辑后等待Network出现draft请求，其Payload内prompt_template已为空。此证据将本次提示词缺失的首个已观察故障点前移到前端请求构造之前/之中；发布不是触发条件，也不能由数据库/worker解释请求内一开始就没有文本。
- “为空”的精确JSON形态尚未回传，可能为数组、对象、空text、null或字段缺失；不猜测是哪一种。测试是否使用全新临时节点未单独明确，不扩大为所有新建Completion节点必现。
- 参考编辑回调handleCompletionPromptChange使用Immer produce(payload as PromptItem)，给draft.text或jinja2_text赋值；TypeScript断言不转换运行时数组。若输入仍是数组，写入自定义属性不受数组契约支持；Immer官方说明数组仅支持索引/length，自定义属性不保留。这支持结构冲突假设，但未在远程实际构建复现该具体丢失机制。
- 参考：https://immerjs.github.io/immer/pitfalls/；Dify参考文件见此前条目。
- 下一步只取两个前端证据：POST中prompt_template的精确JSON结构（正文可改成占位符，保留字段名和括号），default-workflow-block-configs请求状态及LLM completion_model.prompt结构。不再重复数据库计数字数、worker或WebSocket握手检查。

### 2026-09-08 空数组已确认，最小丢失机制复现

- 用户确认POST prompt_template=[]；默认completion_model.prompt是含text和edition_type的对象。默认配置请求状态仍未明确回传。
- 本地按参考代码与其声明依赖Immer11.1.15 production复现：给空数组写text，内存可读到新文本，JSON却为[]；给旧角色数组写text，JSON仅保留旧条目；正确对象能保留新文本。3项断言通过。这与现场现象高度吻合，但远程前端构建、数组生成来源和修复仍未验收。
- 详细证据、源码链接、复现与修复边界见completion-prompt-diagnosis.md。
- 下一步在临时节点、默认模板加载后，进行Completion→Chat→Completion切换并重新输入测试文本；核对POST变为对象及保存/发布后重开。只作为有边界的诊断和候选绕过，不声称已修复。

### 2026-09-08 刷新复发：发现协同初始化无条件列表化

- 用户验证切换Chat再切回后结构正确且保存正常；直接刷新再次失效，故切模型绕过不持久。
- 参考collaboration-manager.ts的populateNodeContainer将prompt_template列入listFields，非数组一律传[]给syncList。这是比模板加载时序更直接、且与刷新复发吻合的原因；远程打包代码仍待核对。
- 提取真实源码的转换循环做本地适配器测试：Completion basic/Jinja对象均变[]，Chat列表不变。仅为prompt_template对象添加普通值写入分支后3类数据和再次加载对照通过；未执行真实CRDT集成和线上验收。
- 本轮cmds.sh两条只读命令核对web镜像/挂载目标、静态JS内列表字段及数组转换。详细记录与候选修复见completion-prompt-diagnosis.md。

### 2026-09-08 线上包定位尚未命中

- 命令466e008回传：mount_target指向证书目录；命令2 CHUNKS_NOT_FOUND。仅表示预设/app/web、/app及执行cwd下的.next/static/chunks不适用，不证明疑似转换代码不存在。
- 本轮改为读取web实际WorkingDir、Node cwd及PID1 cwd；在应用目录有限深度搜索嵌套.next/static/chunks，再扫描同样的转换代码。默认不扫描整个根文件系统、不读环境或进程参数。

### 2026-09-08 线上静态包命中，提示词问题转为已定位待修复

- 用户回传实际web路径/app/targets/next/web/.next/static/chunks。扫描器在含prompt_template等字段的列表集合附近命中syncList(...,Array.isArray(value)?value:[])，包括collaboration-manager-DGhvCEJY.js（指纹3754f2e301bf8be7）。另两项等价转换有OCR疑点，不猜补文件名或指纹。
- 共发现2根目录、扫描2106文件、命中3候选后达到上限；未穷尽全部副本，不适合只改第一个静态文件。
- 线上关键逻辑、用户刷新复现、Chat对照以及本地对象→数组→序列化丢失链路相互印证，主要修复目标确认为前端协同初始化。尚未修改部署，也未做线上修复验收。
- 长期修复应保留Completion对象、Chat列表，覆盖真实CRDT初始化/合并/切换与刷新验收。报告已整理，可用于匹配版本源码修复或提交厂商；未发送外部消息。

### 2026-09-08 公开Issue检索

- Completion刷新丢失：未找到可确认同根因的公开Issue/PR；相似但不同原因的#11874、#40041及检索范围/限制已记入completion-prompt-diagnosis.md。未确认官方已修复版本。

### 下一步

提示词：取得匹配部署版本的web源码修复/厂商补丁，修复对象被无条件列表化的问题，完成刷新、编辑保存、发布及协同回归；不再做RBAC/worker方向排查。WebApp401仍需access-mode请求方法与Response，独立推进。

## RBAC-20260907：新增Agent与受邀成员访问旧应用受限

状态：用户已暂停，根因未闭环；不是已解决问题。

2026-09-08检索补充（不恢复暂停任务）：https://github.com/langgenius/dify/issues/39736 明确报告All members按成员快照授权、后来加入成员不能访问旧应用/数据集，与此前受邀成员问题高度相关；页面显示Closed，但没有取得对应修复提交或企业版修复版本，不能将关闭等同已修复。

既有资料：rbac-config-merge-audit.md、fix-rbac-workflow-access.sh。临时白名单脚本不是通用修复，也没有证明本轮WebApp 401适用。此前发现版本与配置合并风险，生产根因尚未确认。

## 已验证解决的问题

当前记录没有足够验收证据可列入此类。后续定位完成时在对应条目记录根因、修复和验收，不将推测或脚本发布视为已解决。

## WEBAPP-20260908：恢复access-mode 401专项定位

状态：排查中，2026-09-08用户要求优先解决；Completion缺陷已定位待修复，新Agent/成员授权旧任务继续暂停。

### 检索先行

已更新两处detrick-troubleshoot skill，要求新问题先搜索已有Issue/PR/官方说明；后续有关键新证据时补查，并记录匹配程度。

搜索关键词：dify access-mode 401、webapp permission admin 401、access-mode unauthorized；优先GitHub官方仓库和ee.dify.ai。

- https://github.com/langgenius/dify/discussions/20904 发布记录列出PR20785“only enterprise version request app access mode”；这是非企业版请求边界的历史修复，与本次企业版、同账号部分workspace异常不直接吻合。PR页面本轮读取失败，未将其当作已确认同根因。
- https://github.com/langgenius/dify/issues/39736 涉及后来加入成员访问旧资源，属于既有暂停问题的相关资料，不等同WebApp访问范围管理接口401。
- 暂未搜索到可直接套用的同根因修复。

### 当前已知与缺口

- 发生在点击修改WebApp访问范围操作时；Console路径截断为/console/api/enter...p/app/access-mode。实际GET/POST、Response、目标appId仍未收到。
- 同一admin账号不同workspace表现不同。旧的app_view_layout拒绝日志app不一致，不能直接关联本次请求。
- 下一步同时取得Network精确请求（方法/Response/appId）及新cmds.sh只读结果：目标app的tenant与账号成员关系、同时段enterprise/rbac拒绝元数据。
- 命令中的账号默认沿用此前dc81582c…，要求用户确认是否本次登录账号；不把传统tenant_account_joins.role/current当作有效RBAC角色或本次请求上下文证明。
- 尚未改配置、回填权限或发出外部消息。后续按实际错误原因定位，不能仅凭401推定token过期或admin无效。

### 2026-09-08 WebApp POST与目标身份已确认

- app=daeaaeb3-6875-4f73-adad-0f1312dbd5ce，tenant=a5bcd310-2e74-4f89-9a32-70a56694cb35，account=dc81582c-3934-4d8f-b034-9cb7809dce2b；mode=advanced-chat，成员1行，传统role=normal/current=true。
- 用户明确POST Payload为appId及accessMode=public；其中一次OCR把0写为ø，已有完整正确UUID，命令沿用确认值。Response正文仍缺，不能用发送Payload替代。
- 同期日志约09:32:38Z：source=enterprise/status=401，access_mode_request=false，关键词可辨识unauthorized/whitelist（原文OCR损坏）。无app或scene，仍不能确定就是本次请求。
- 新关键词先搜索：access-mode+whitelist、WebApp public权限。官方文档存在WEBAPP_PUBLIC_ACCESS_ENABLED开关，但仅凭public目标和401不能认定该开关是根因；暂未查到同根因修复。#38232是接口合同迁移事项，不是本次401修复证据。
- 本轮固定上述身份，只读查询真实RBAC角色、应用白名单/用户策略，并显式check-access查看/发布scene。诊断check-access可能产生新拒绝日志，要与原WebApp POST区分；不预设enterprise必然使用发布scene。
- normal是传统成员角色存储，不直接改成admin。尚未进行任何授权修改。


### 2026-09-08 白名单与查看/发布判定通过，转查访问配置与Enterprise链路

- e11e1c3用户回传：目标app/account沿用上一节；member_roles=2，权限列表OCR截断，不能证明每项有效权限。白名单13人且has_account=true；scope=all、目标行1、策略default。
- 显式app_view_layout和app_release_and_version均allowed=true。这排除了该次诊断上下文中的缺白名单和这两项判定拒绝，不能代表Enterprise实际POST上下文或其他scene。
- 原POST响应已补齐：code=401、reason=ErrUnauthorized、message=unauthorized to access this resource、metadata={}。错误不区分token、角色、资源策略等，不能据此判断登录过期。
- 补查搜索dify + ErrUnauthorized + access-mode、webapp + app.acl.access_config、unauthorized to access this resource，未发现可核实同根因的官方Issue；不据搜索缺失排除产品缺陷。
- 参考60a18fa api/core/rbac/entities.py确认独立scene APP_ACCESS_CONFIG=app_access_config；下一轮仅检查此scene及Enterprise的RBAC_INNER_BASE_URL和API目标是否同源、内部密钥是否一致、public开关状态。不重复授予白名单或改normal角色。
- 源码参考：https://github.com/langgenius/dify/blob/60a18fa/api/core/rbac/entities.py 。尚无原POST关联的scene/tenant日志，根因未确认。


### 2026-09-08 三项诊断允许，Enterprise同源；转原请求日志

- 416aba6回传：app_access_config allowed=true（用户文本为字符串true，按允许值理解，未取得原始JSON）；API目标path=/inner/api，Enterprise RBAC_INNER_BASE_URL设置且path空，rbac_same_origin=True，inner_secret=EQUAL。
- Enterprise WEBAPP_PUBLIC_ACCESS_ENABLED=UNSET。官方3.12.0说明此开关默认保持开放：https://ee.dify.ai/releases/v3.12.0/ 。因此未设置不是已证实配置缺陷；尚未读取当前二进制的配置解析逻辑，不直接补变量或重启。
- 补查上述开关及access-mode ErrUnauthorized，未找到同根因Issue。当前API显式诊断通过不能证明浏览器POST携带相同身份/workspace，也不能证明Enterprise走相同校验路径。
- 下一轮仅记录复现起点，再采集Enterprise/RBAC原请求错误的时间、caller、scene、身份及trace摘要；需同时回传GET/POST状态。无匹配日志不证明未调用RBAC。尚未修复或调整访问范围。


### 2026-09-08 写方法已定位；发现Enterprise自身RBAC_ENABLED分支

- d418df6回传：3行结构化日志，2条匹配。GetWebAppWhitelistSubjects=200；UpdateWebAppWhitelistSubjects=401/ErrUnauthorized；没有RBAC拒绝记录回传，不能据缺日志证明无检查。
- 接口合同纠正：上述GET为/app/subjects，不是/app/access-mode GET。起点原文2026-09-02T12：27：29Z保留，未猜改为9月8日。
- 用精确方法名和401补查公开Issue，未找到同根因。转静态检查本机3.12.0 Enterprise镜像，发现Update调用IsDifyUserAllowedToChangeAppSettings，该函数确实读Enterprise自身RBAC_ENABLED；未设置/解析失败时返回传统角色admin/owner/editor比较结果，normal拒绝。更正此前Enterprise的RBAC_ENABLED未设可以忽略的判断。
- 官方3.12.1 tgz同时存在shared.env有RBAC_ENABLED=true但dify-enterprise未引用该文件的配置传递缺口；根.env可本地补充，不能直接认定合并程序造成。具体镜像hash、地址和边界见webapp-access-mode-diagnosis.md。
- 下一轮确认现场运行容器及Compose解析结果。高可信根因候选，尚未修改配置、重建服务或完成验收。待确认后最小候选是只为Enterprise服务显式启用RBAC，不回填角色/白名单。
