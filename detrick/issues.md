# 德勤问题定位记录

## WF-20260908：WebApp 权限操作401与提示词重进为空

状态：排查中。环境 A，并据用户描述在多套环境出现；两个症状不必同时出现。

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

### 下一步

提示词已缩小到前端Completion编辑到draft请求负载之间。补齐空负载的精确结构及默认模板加载状态后，决定修复初始化/模型切换还是编辑状态更新；远程前端镜像版本仍待完整回传。WebApp401保持独立，仍需access-mode方法和Response。

## RBAC-20260907：新增Agent与受邀成员访问旧应用受限

状态：用户已暂停，根因未闭环；不是已解决问题。

既有资料：rbac-config-merge-audit.md、fix-rbac-workflow-access.sh。临时白名单脚本不是通用修复，也没有证明本轮WebApp 401适用。此前发现版本与配置合并风险，生产根因尚未确认。

## 已验证解决的问题

当前记录没有足够验收证据可列入此类。后续定位完成时在对应条目记录根因、修复和验收，不将推测或脚本发布视为已解决。
