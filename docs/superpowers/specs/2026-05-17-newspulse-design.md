# NewsPulse 新闻脉搏 — 设计文档

## 概述

每天推送重要新闻精选 + 实时追踪用户关注的人/事，Android App 接收，全程 0 元。

## 技术栈

| 层 | 技术 | 说明 |
|---|------|------|
| Android App | Kotlin 原生 + Jetpack Compose | APK 直接安装，不走商店 |
| 推送 | Firebase FCM | 完全免费 |
| 后端 | Python FastAPI | 轻量、异步、生态好 |
| 数据库 | Supabase PostgreSQL | 免费 500MB |
| 部署 | Railway | 免费 tier，cron-job.org 唤醒防休眠 |
| 新闻源 | NewsAPI + RSS（头条、知乎、GitHub Trending 等）| 免费额度 |
| AI 匹配 | text2vec-base-chinese 本地或硅基流动免费 API | embedding 语义兜底 |
| 定时任务 | APScheduler | 进程内调度，0 额外依赖 |

**每月费用：0 元。**

## 架构

```
Android App (Kotlin + Compose)
  ├── 每日精选 Tab
  ├── 消息追踪 Tab
  └── 订阅管理
      │ FCM
Python FastAPI 后端
  ├── 新闻聚合器 → 拉取/去重/入库
  ├── 匹配引擎 → 关键词精确 + embedding 语义
  ├── 推送调度器 → 每日汇总(8:00) + 即时追踪
  └── 用户系统 → 注册/登录/订阅/FCM Token
      │
Supabase PG  ← → 免费 RSS/API 源
```

## 数据库模型

- **users**: id, email, password_hash, fcm_token, created_at
- **subscriptions**: id, user_id(FK), keyword, type(name/topic), created_at
- **articles**: id, title, summary, source, source_url, published_at, fetched_at, score, embedding(可选)
- **notifications**: id, user_id(FK), article_id(FK), type(daily/track), sent_at, read
- **daily_digest**: id, date, article_ids(JSON), title, created_at

## 核心流程

### 新闻采集
1. APScheduler 每 15 分钟触发新闻聚合器
2. 拉取 NewsAPI + 各 RSS 源新文章
3. 去重（URL/标题相似度）
4. 计算热度 score，清洗后入库

### 匹配推送
1. 新文章入库后触发匹配引擎
2. 第一层：关键词/名称精确命中标题+摘要
3. 第二层：embedding 语义相似度 > 阈值 即命中
4. 命中 → 立即通过 FCM 推送单条通知

### 每日汇总
1. 每天 8:00 触发
2. 查询过去 24 小时 score 最高的 15 条
3. 生成 daily_digest 记录
4. FCM 推送给所有用户（一条汇总通知）

## 限制与注意

- NewsAPI 免费版 100 次/天，15 分钟频率 = 96 次/天，刚好够
- Railway 免费额度休眠问题用 cron-job.org 定时唤醒
- FCM 免费不限量，但单条推送 payload 限 4KB
- Supabase 500MB，约可存 50 万条精简文章，够用
