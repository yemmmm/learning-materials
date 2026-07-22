# Dify 企业版 3.9–3.11 版本特性讲解站 — 设计文档

> 创建：2026-07-22
> 数据来源：ee.dify.ai（Dify Enterprise 发布信息站，即 release.dify.ai）
> 产出目录：`~/learning-materials/dify/dify-enterprise-versions/`

## 背景与目标

制作一个静态 HTML 讲解站，讲解 Dify 企业版 3.9.0–3.11.1 各版本的特性，用于版本选型与升级参考。形态为分章节式（每个大版本一个页面），风格简洁，内容以功能特性为主。

## 信息源

- 官网首页：`https://ee.dify.ai`
- 单版本详情：`https://ee.dify.ai/releases/v{版本}`
- 每版本详情页含：What Changed（NEW FEATURES + BUG FIXES）、Upgrade Impact、Upgrade Guide、Security & CVE、Benchmark、License
- 注意：企业版 release 信息为 confidential，公开搜索引擎不可得，只能从官网获取

## 版本范围（共 12 个版本）

| 版本 | 类型 | 发布日期 |
| --- | --- | --- |
| 3.9.0 | LTS | 2026-03-31 |
| 3.9.1 | LTS | 2026-04-13 |
| 3.9.2 | LTS | 2026-04-28 |
| 3.9.3 | LTS | 2026-05-08 |
| 3.9.4 | LTS | 2026-05-21 |
| 3.9.5 | LTS | 2026-06-04 |
| 3.10.0 | NON-SKIP / MAINTENANCE | 2026-05-28 |
| 3.9.6 | LTS | 2026-06-15 |
| 3.9.7 | LTS | 2026-07-01 |
| 3.11.0 | MAINTENANCE | 2026-06-30 |
| 3.9.8 | LTS（REC 推荐） | 2026-07-15 |
| 3.11.1 | NON-SKIP / LATEST | 2026-07-15 |

## 信息架构（4 个文件）

目录 `dify-enterprise-versions/`：

- `index.html` — 总览首页：12 版本时间线 + 三章入口卡 + 类型图例（LTS / LATEST / NON-SKIP / MAINTENANCE）
- `3.9.html` — 3.9.0 → 3.9.8（9 个补丁，LTS 线）
- `3.10.html` — 3.10.0
- `3.11.html` — 3.11.0 / 3.11.1

每页顶部固定导航（Overview / 3.9 / 3.10 / 3.11），页内锚点跳转到具体版本。

## 每个版本块的结构（特性为主）

- **版本头**：版本号 + 类型徽章 + 发布日期 + Community/Enterprise 对应版本 + 升级影响徽章（BREAKING / CHANGES / DOWNTIME）
- **★ 新特性详解**：每条 = 标题 + 是什么 + 价值/场景 +（如适用）如何启用；无新功能的补丁版本如实标注"本版本为安全/修复版本"
- **问题修复（归类简表）**：按 安全 / RBAC / 插件 / 工作流 / UI 分类，每类一行概述
- **升级影响（一句话）**：是否破坏性、是否需迁移、停机情况

## 视觉风格

- 复用资料库现成深色主题（`#0f172a` 背景 + CSS 变量 + fixed nav），与 `common/sso-oidc-guide.html` 一致、简洁
- 语义色徽章：LTS=蓝、LATEST=绿、Critical CVE=红、High=橙
- 每页内联 CSS，自包含、离线可看、零外部依赖

## 实现方式

- `frontend-design` skill 指导 HTML 生成
- chrome-devtools 抓取官网各版本详情页内容
- 中文讲解（原文英文，翻译提炼）
- 诚实呈现：3.9.x 部分补丁只有安全修复、无新特性时如实说明，不硬凑

## 归档

产出纳入 `~/learning-materials/dify/dify-enterprise-versions/`，按全局规则 commit + push。
