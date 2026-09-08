# 德勤定位环境事实

仅记录脱敏摘要；远程事实来源为用户回传，不代表本机运行环境。最后更新：2026-09-08。

## 环境 A：本轮受影响环境

- 2026-09-08 用户回传：RBAC 镜像 3.12.1，运行中；其他服务完整镜像行未回传，本轮不能据此确认全部版本。
- API、api_websocket：RBAC_ENABLED=true、ENTERPRISE_ENABLED=true；WebSocket 服务存在。
- API/WebSocket database、auth 比较：different_keys=[]、both_unset=[]。仅证明上一轮脚本所列变量一致；Redis 比较行未回传，尚未确认。
- web 容器 NEXT_PUBLIC_SOCKET_URL：ws 协议、内部主机、空路径。控制台页面协议和浏览器实际 Socket.IO 地址未确认，不能据此直接判定 mixed-content。
- 宿主机 docker-compose 是用户当前 shell 中的函数；直接粘贴命令块执行，避免 Python subprocess 或新 bash 调用该函数。宿主 Python 不支持 capture_output；使用兼容写法。
- 对照环境 B：此前用户报告为 3.12.0；本轮尚无 B 的此问题专项证据。不能将 B 或本机配置套用到 A。

## 取证方式

- 封闭服务器无法由助手直连；2–3 条有输出上限的命令写入 cmds.sh，用户执行回传。
- 浏览器取证只回传路径、方法、状态、脱敏响应，不回传 Authorization/Cookie 或完整 cURL。
