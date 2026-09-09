# 德勤定位环境事实

> 目录于 2026-09-10 整理；下文历史文件名按当时记录保留，新位置见[目录导航与迁移表](../README.md)。

仅记录脱敏摘要；远程事实来源为用户回传，不代表本机运行环境。最后更新：2026-09-08。

## 环境 A：本轮受影响环境

- 2026-09-08 用户回传：RBAC 镜像 3.12.1，运行中；其他服务完整镜像行未回传，本轮不能据此确认全部版本。
- API、api_websocket：RBAC_ENABLED=true、ENTERPRISE_ENABLED=true；WebSocket 服务存在。
- API/WebSocket database、auth 比较：different_keys=[]、both_unset=[]。仅证明上一轮脚本所列变量一致；Redis 比较行未回传，尚未确认。
- web 容器 NEXT_PUBLIC_SOCKET_URL：ws 协议、内部主机、空路径。控制台页面协议和浏览器实际 Socket.IO 地址未确认，不能据此直接判定 mixed-content。
- 2026-09-08 浏览器回传：受影响编排页socket.io状态101，点击LLM节点无新Console错误；此证据仅限本次观察，不代表协同保存已验收。
- 宿主机 docker-compose 是用户当前 shell 中的函数；直接粘贴命令块执行，避免 Python subprocess 或新 bash 调用该函数。宿主 Python 不支持 capture_output；使用兼容写法。
- 对照环境 B：此前用户报告为 3.12.0；本轮尚无 B 的此问题专项证据。不能将 B 或本机配置套用到 A。

- 2026-09-08 web目录排查：用户回传挂载目标为/usr/local/share/ca-certification（按原文记录，不猜改路径）；前轮3个预设chunks路径未找到。web实际工作目录及完整镜像行尚待回传，不认定代码缺失或镜像被挂载覆盖。

- 2026-09-08 实际web路径：node_cwd=/app，pid1_cwd=/app/targets/next/web，cwd_dirs=targets；已找到/app/targets/next/web/.next/static/chunks。扫描发现2个chunks根，第二个路径未回传。后续使用已确认目录，避免重复猜测。

## 取证方式

- 封闭服务器无法由助手直连；2–3 条有输出上限的命令写入 cmds.sh，用户执行回传。
- 浏览器取证只回传路径、方法、状态、脱敏响应，不回传 Authorization/Cookie 或完整 cURL。

- 2026-09-08 环境A，416aba6用户回传：API ENTERPRISE_RBAC_API_URL path=/inner/api；Enterprise RBAC_INNER_BASE_URL已设置、path空，两者同源；ENTERPRISE_API_SECRET_KEY比较相等。Enterprise WEBAPP_PUBLIC_ACCESS_ENABLED未设置，不能据此认定关闭。

- 2026-09-08 新静态证据纠正：本机3.12.0 Enterprise程序读取自身RBAC_ENABLED，未设置会关闭该RBAC分支。此前只确认API=true不足以认定整条链路开启；现场Enterprise当前值待新一轮确认，不能把Go Enterprise未设该变量一概当作正常。此结论不泛化到独立rbac服务。

- 2026-09-08 c829013用户回传确认：环境A运行容器与Compose有效配置均API RBAC_ENABLED=true、Enterprise未设置。用户文字服务名enterprise-aoi与前轮dify-enterprise不一致，修复通过镜像名识别真实服务；尚未收到修复后的环境状态。

- 2026-09-08 最终用户回传：环境A的Enterprise变量名纠正为RBAC_ENABLED，执行修复命令后WebApp权限修改恢复。视为业务修复已确认；未额外回传新的inspect原文，不把其他环境状态或全量回归记为完成。后续部署保持API与Enterprise均启用原已使用的企业RBAC。

## Agent访问403专项环境（2026-09-08用户回传）

- 用户为工作空间admin。api_websocket、worker、worker_beat镜像为dify-ee-api:3.12.1，web为dify-ee-web:3.12.1，collector和rbac均3.12.1。私有仓库域名不记录或推送。
- 回传没有普通api服务完整行，存在一行不完整字符；不据此判断api服务缺失或全部服务版本一致。与此前环境A是否同一环境仍待确认。

- 2026-09-08 第3轮用户回传：命令1两个API服务均3.12.1，RBAC_ENABLED和ENTERPRISE_ENABLED均true。已确认的api_websocket源码存在AgentChatMessageListApi及APP_VIEW_LAYOUT装饰器。回传有OCR错行/拼写损坏，不能据此报告源码语法错误。


## Agent权限正常环境对照（2026-09-09用户新增线索）

- 用户报告另一套环境的Agent能够由其他用户访问。该环境的准确版本、RBAC开关、成员角色、维护者关系和资源访问策略尚未回传。
- 不认定该环境就是上文历史环境B，也不据此前资料推定它一定为3.12.0。
- 用户明确本轮不接受源码修改；现场未执行此前本地补丁方案。当前仅进行两套环境的只读配置/授权对照。


## Agent对照环境纠正（2026-09-09，第14轮用户回传）

- 用户撤回“另一环境正常”：3.12.0存在账号A可访问别人创建的Agent、其他人不能访问A创建的Agent的不对称现象。
- 3.12.0：api/api_websocket的RBAC_ENABLED和ENTERPRISE_ENABLED均true；dify-enterprise两变量均UNSET。该环境的账号/资源详情探针为ValueError，尚未取得角色/白名单策略证据。
- 3.12.1：api/api_websocket两变量均true；dify-enterprise RBAC_ENABLED=true、ENTERPRISE_ENABLED未设置。两边该配置差异已确认，但不是Agent访问差异根因的充分证据。
- 前端及collector/rbac等服务所示UNSET按原样记录，不由其他服务的配置要求推断其错误；3.12.0回传未含独立rbac服务行，也不能认定该服务不存在。


## 3.12.0账号不对称对照结果（2026-09-09，第15轮）

- A角色：global_system_default/owner；其可访问的别人创建的Agent为active/roster/agent_app，资源访问scope=specific且白名单不包含A。维护者关系及check-access的allowed/reason缺回传，Owner特权解释尚未核实具体分支。
- B角色：回传计数4，可见admin、normal及自定义App查看/编辑/调试权限。B有agent_manage，但查看/编辑目标Agent被资源白名单拒绝。不存在“3.12.0所有成员都能访问所有Agent”的已验证基线。


## 3.12.0工作空间规则核对（2026-09-09，第16轮）

- B具备agent.manage及App查看/编辑/调试权限，目标资源为specific且没有B的成员策略；查看与调试明确被资源白名单拒绝。
- 工作空间存在full_access/can_edit/can_view_and_use等App访问规则，部分绑定回传损坏；不得将操作权限匹配与目标资源白名单开放混为一谈。
- workspace_policy输出的permission_keys是筛选后的交集，空列表不代表完整策略为空。


## n8n分布式环境（2026-09-09，用户描述，脱敏）

- 主服务器：main、worker、Traefik、Redis；另一服务器：worker，连接主服务器Redis。
- 用户报告外部访问任务分派到另一服务器时发生证书验证错误；服务器名证书部署在主服务器，n8n使用服务器名访问。
- 未确认n8n/Node版本、证书实际挂载位置、失败目标、代理及两台worker的CA配置；本机配置不作为远端事实。


### n8n第1轮回传（2026-09-09，用户提供）

- 两台受测worker：n8n 2.31.7、Node v24.16.0，runtime_worker_env=FOUND。两台各列出两个worker及runner，不能将单个worker探针概括为所有副本。
- 主服务器受测worker：NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt，HTTP_PROXY/HTTPS_PROXY/NO_PROXY=SET；CA文件129个PEM。用户回传sha256疑似缺位，不保存为精确指纹。直连探针ENOTFOUND。
- 另一服务器受测worker：NODE_EXTRA_CA_CERTS及代理变量均UNSET，CA文件128个PEM；直连探针UNABLE_TO_VERIFY_LEAF_SIGNATURE（用户小写回传）。
- 两台SSL_CERT_FILE/SSL_CERT_DIR/NODE_USE_SYSTEM_CA均UNSET、CA_flags为空、custom_CA_dir=ENOENT。用户文本中个别变量带空格/OCR字符，不据此认定实际变量拼错。
- 同一原工作流在主服务器是否成功、探针目标是否完全相同、节点是否实际采用环境代理，待用户确认。
