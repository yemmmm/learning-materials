# WebApp访问范围401：Enterprise自身RBAC开关线索

日期：2026-09-08。状态：高可信配置根因候选，现场3.12.1补查与修复验收待完成。

## 现场证据

目标app daeaaeb3-6875-4f73-adad-0f1312dbd5ce；workspace a5bcd310-2e74-4f89-9a32-70a56694cb35；account dc81582c-3934-4d8f-b034-9cb7809dce2b。
传统成员role=normal，RBAC拥有角色；白名单包含账号/default策略；显式view_layout、release_and_version、access_config均允许；API/Enterprise RBAC目标同源、密钥相等。

d418df6回传：GetWebAppWhitelistSubjects=200；UpdateWebAppWhitelistSubjects=401/ErrUnauthorized。参考合同前者是GET /enterprise/webapp/app/subjects，后者是POST /enterprise/webapp/app/access-mode，不把200当作access-mode GET的结果。日志摘要未提供原请求tenant/account/trace，不能证明使用了诊断请求的同一上下文。起点日期原文为2026-09-02T12：27：29Z，可能OCR或主机时钟差异，尚未核实。

## 本机镜像静态证据（不是现场3.12.1执行结果）

从本机langgenius/dify-ee-enterprise:3.12.0创建未启动的临时容器，复制/app/enterprise后删除临时容器；没有启动服务或连库。
镜像ID sha256:35693f5932767b291748e25c6422a30cd0494741538f32acda372cb2984d6fc2。
二进制SHA256 fc77dcbc8d0920ad0a640b33d6846f77d6931a6fcf13aeb528ba76bf660a2c7d。
ELF x86-64，未剥离符号。使用objdump检查：

- service.(*WebAppService).UpdateWebAppWhitelistSubjects在0x2ace368调用biz.(*WebAppUsecase).IsDifyUserAllowedToChangeAppSettings；返回false后0x2ace505取ErrorWebAppModifyUnauthorized。
- IsDifyUserAllowedToChangeAppSettings为0x28c45e0，长度0x3e5。读取用户/仓库上下文并校验active；比较返回角色admin/owner/editor。0x28c47cb调用IsRBACEnabled；false分支0x28c4939直接返回上述角色比较结果；true时传统角色满足则允许，否则尝试RBAC客户端判定（客户端为空仍拒绝）。
- biz.IsRBACEnabled为0x28a15e0，长度0x3f：os.Getenv -> strconv.ParseBool；解析失败返回false。读取字符串地址0x34377ea，长度12，字节确认为RBAC_ENABLED。

这说明不能把Go Enterprise容器的RBAC_ENABLED未设置当作无关项。API开启RBAC并不自动开启Enterprise。尚未反汇编现场3.12.1，不能把这份3.12.0静态证据称作现场根因已验证。

## 官方3.12.1配置交叉核对

2026-09-08从官方发布页链接下载tgz，内存读取归档，没有执行或解压脚本：
https://ee.dify.ai/releases/v3.12.1/
https://langgenius.github.io/dify-enterprise-docker-compose/dify-docker-compose-3.12.1.tgz

根docker-compose.yaml中：API/worker引用envs/enterprise/shared.env，文件含RBAC_ENABLED=true。dify-enterprise的env_file仅含enterprise/core.env、db.env、redis.env、enterprise.env及可选根.env；没有引用shared.env，environment也未显式配置RBAC_ENABLED。因此可选根.env或其他本地覆盖没有补值时存在传递缺口，不应先归咎用户的合并程序。这是下载时版本包事实，不证明所有安装或镜像默认环境相同。

## 下一步与候选修复

只读确认现场running_container和compose_resolved中api/dify-enterprise各自RBAC_ENABLED。
若Enterprise未设置/false且API=true：候选最小修复为在dify-enterprise现有environment映射中增加RBAC_ENABLED: "true"（不新建第二个environment键），只重建该服务，使授权模式与已启用的RBAC配置一致。必须先确认部署目录/合并结果；本轮没有修改或重启现场。
若Compose已经true而容器未设置，应排查容器未重建或实际配置文件选择不同。
复测同app修改权限、退出重进读取范围，并核对原授权边界；现场仍401时继续查实际上下文与3.12.1实现。不要把tenant_account_joins.normal改admin，不用白名单批量回填。


## 现场配置确认与修复交付（2026-09-08）

c829013回传：API运行/Compose均true，Enterprise运行/Compose均unset，配置缺失已确认。待执行修复：在实际Enterprise服务已有environment中显式加入RBAC_ENABLED: "true"，检查合并结果后执行up -d --no-deps --no-build --force-recreate，仅重建该服务。不要只restart；不要修改normal成员行。

cmds.sh已交付操作与环境验证，服务名从镜像识别。现场验收仍待用户执行：同账号/同workspace/同app POST access-mode成功，退出重进访问范围保持；若仍401继续检查实际身份/3.12.1分支。没有声称修复已完成。
