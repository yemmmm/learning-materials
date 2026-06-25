# Codex-maxxing for long-running work

OpenAI 官方发布的白皮书，作者 **Jason Liu**（OpenAI 工程师）。

分享如何把 **Codex 作为持久工作区（persistent workspace）** 的实战策略——让工作能够在单次提示之外继续推进。

## 文件

- `original.md` —— 英文原文
- `translated-zh.md` —— 中文翻译

## 来源

- **OpenAI 白皮书页面：** https://openai.com/index/codex-maxxing-long-running-work/
- **Jason Liu 原文（jxnl.co）：** https://jxnl.co/writing/2026/05/10/codex-maxxing/
- **发布时间：** 2026-05-10

## 核心思想

把 Codex 当作"工作可以存活的地方"，而不只是"代码生成器"。建立一套**运行回路（operating loop）**：

1. **Durable threads（持久化会话）** —— 给每个重要工作流保留一条置顶的、经过压缩的长期会话
2. **Voice input（语音输入）** —— 让 Agent 拿到你**未编辑过**的真实思考
3. **Steering（引导）** —— 在 Agent 工作时持续注入下一条指令，而不是等每一步完成
4. **Memory（记忆）** —— 把会话学到的知识写到磁盘（如 Obsidian vault + GitHub 仓库），让记忆可审查、可 diff
5. **Computer / Browser Use** —— `$browser`（本地 web）、`@chrome`（多标签登录态）、`@computer`（GUI 自动化）
6. **Remote control（远程控制）** —— 从手机引导桌面端的长任务
7. **Heartbeats（心跳）** —— 让会话自己定期巡检 Slack / PR / 邮件
8. **Goals（目标）** —— 设定带**真正验证标准**的雄心目标（如"必须通过原库所有单元测试"）
9. **Side panel（侧边栏）** —— 让 Codex 从"聊天应用"变成"工作发生的地方"

**关键洞见：** 工作不再因为换了地点、关了应用、隔了一晚就死掉——它能在你离开之后继续向前走。
