# 德勤定位环境事实

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
