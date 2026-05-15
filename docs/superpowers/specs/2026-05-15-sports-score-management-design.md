# 学生体育成绩管理系统 — 设计文档

## 概述

面向初中学校体育组的成绩管理系统。体育老师录入学生成绩、查看统计分析；学生登录查询个人成绩和趋势。部署于云服务器，通过浏览器访问。

## 技术方案

- **后端**: Python FastAPI（异步框架，自动生成 API 文档）
- **前端**: Vue 3 + Element Plus（UI 组件）+ ECharts（图表）
- **数据库**: 开发期 SQLite，部署切换 PostgreSQL
- **语音**: 浏览器内置 Web Speech API（Chrome 中文识别），固定 1.5 秒录音
- **认证**: JWT（管理端）/ 学号+密码（学生端）

## 数据模型

### classes
| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| grade | string | 年级，如"2027届" |
| name | string | 班级名，如"3班" |

### students
| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| student_id | string(6) | 学号，如 270301（毕业年+班+序号） |
| name | string | 姓名 |
| gender | enum(M/F) | 性别 |
| class_id | int | 外键 → classes |
| password_hash | string | 密码哈希，默认学号后6位 |

### sport_events
| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| name | string | 项目名称 |
| gender | enum(M/F/both) | 适用性别 |
| higher_better | bool | true=越大分越高，false=越小分越高 |
| unit | string | 单位（秒/米/次）|
| input_format | enum | time_ms / decimal_seconds / decimal_meters / integer |
| sort_order | int | 展示排序 |

### scoring_standards
| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| event_id | int | 外键 → sport_events |
| score | int(1-10) | 分值 |
| standard_value | string | 标准值（按 input_format 对应格式存储） |

### scores
| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| student_id | int | 外键 → students |
| event_id | int | 外键 → sport_events |
| raw_value | string | 原始成绩（保持录入格式） |
| earned_score | int(1-10) | 得分 |
| test_date | date | 测试日期 |
| recorder_id | int | 录入老师（外键 → admins） |

### admins
| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| username | string | 登录名 |
| password_hash | string | 密码哈希 |
| is_super | bool | 是否超管 |
| display_name | string | 显示名称 |

### system_config
| 字段 | 类型 | 说明 |
|------|------|------|
| key | string | 配置键 |
| value | string | 配置值 |

预置配置项：`school_name`、`praise_threshold`（默认 1）、`warning_threshold`（默认 2）、`designer`（默认"tequila"，显示于登录页底部）

## 输入格式与评分规则

### 四种输入格式

| 格式类型 | 适用项目 | 输入示例 | 存储格式 | 比较方式 |
|---------|---------|---------|---------|---------|
| `time_ms` | 800米跑、1000米跑 | `3'30` | 字符串 `3'30` | 解析(分,秒)元组比较 |
| `decimal_seconds` | 50米跑、足球运球、篮球运球投篮 | `8.1` / `22.51` | 浮点数 | 直接数值比较 |
| `decimal_meters` | 立定跳远、掷实心球 | `1.95` | 浮点数 | 直接数值比较 |
| `integer` | 跳绳、仰卧起坐、引体向上、游泳 | `170` | 整数 | 直接数值比较 |

### 评分规则

取低分制：成绩落在标准表中相邻两档之间时，取较低分值。

- 对于 `higher_better=true` 的项目：标准值 ≤ 实际值 < 上一档标准值 → 取当前档分值
- 对于 `higher_better=false` 的项目：标准值 ≥ 实际值 > 上一档标准值 → 取当前档分值
- 成绩超出满分标准 → 10 分
- 成绩低于最低标准 → 1 分

### 进步/预警规则

- 进步表扬：本次分值 − 上次分值 ≥ praise_threshold（默认 1）→ ✨
- 橙色预警：上次分值 − 本次分值 ≥ warning_threshold（默认 2）→ 🟠
- 首次测试无上次成绩 → 显示 "-"

## 页面设计

### 0. 导航结构

两个独立入口：
- `/admin`：管理端，老师/超管登录（JWT）
- `/student`：学生端，学号+密码登录

管理端侧边栏：仪表盘、成绩录入、学生管理、统计分析、开发人员选项（仅超管）
学生端：登录页 → 成绩总览页

### 1. 成绩录入（核心页面）

URL: `/admin/score-entry`

**进入前选择**：先锁定班级、项目和测试日期（默认当天），再进入逐人录入。

**逐人录入界面（移动端优先）**：
- 顶部：班级+项目名称
- 学生区域：`◀ 张三 (270301) ▶` 箭头点击切换
- 大号输入框：placeholder 根据项目格式变化
- 🎤 语音按钮：点击 → 1.5 秒录音 → 自动填入输入框
- 得分区：输入后实时显示得分 + 上次成绩 + 变化（✨/🟠）
- 底部固定按钮：💾 保存并下一个 → 保存后自动跳下一个学生

**语音流程**：点击 🎤 → 浏览器申请麦克风权限 → 录音 1.5s 自动停止 → Web Speech API 转文字 → 填入输入框 → 老师确认/修改 → 保存

### 2. 学生管理

URL: `/admin/students`

- 列表页：搜索、分页、编辑/删除
- 批量导入：下载模板 → 上传 Excel → 预览 → 确认导入（默认密码=学号后6位）
- 批量修改：选择班级范围 → 修改字段 → 确认

### 3. 统计分析

URL: `/admin/statistics`

**班级统计**：
- 选择班级 + 多选项目筛选
- 班级总览（平均分、优秀率、及格率）
- 各项目平均分柱状图
- 退步预警学生列表
- [📥 导出班级成绩]：导出选中班级+项目的 Excel

**个人统计**：
- 搜索学号/姓名定位学生
- ⭐ 中考推荐项目（得分最高的 4 项）
- 各项目得分雷达图
- 历史成绩折线图（带 ✨/🟠 标记）
- [📥 导出个人成绩]：导出含当前汇总+历史明细的 Excel

### 4. 开发人员选项

URL: `/admin/settings`（仅超管）

- **运动项目设置**：新增/删除项目、编辑评分标准（1-10 分各档标准值）
- **管理员管理**：增删老师账号
- **预警设置**：可调表扬阈值、警告阈值
- **系统设置**：学校名称（全局顶部显示）
- **系统工具**：数据备份/恢复、全量导出

### 5. 学生成绩查询

URL: `/student`

- **登录页**：学号 + 密码 + 修改密码入口
- **成绩总览页**：
  - 本学期成绩表（全部项目：成绩 + 得分）
  - 总分
  - 近期成绩走势折线图
  - ⭐ 中考推荐项目（4 项）
  - 修改密码入口

## API 设计概要

| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/auth/login` | POST | 管理员登录 |
| `/api/auth/me` | GET | 获取当前用户信息 |
| `/api/students` | GET/POST | 学生列表 / 新增 |
| `/api/students/batch-import` | POST | 批量导入（Excel） |
| `/api/students/batch-update` | PUT | 批量修改 |
| `/api/students/{id}` | GET/PUT/DELETE | 单个学生 CRUD |
| `/api/events` | GET/POST | 项目列表 / 新增 |
| `/api/events/{id}` | PUT/DELETE | 修改 / 删除项目 |
| `/api/events/{id}/standards` | PUT | 更新评分标准 |
| `/api/scores` | GET/POST | 成绩列表 / 录入 |
| `/api/scores/batch` | POST | 批量保存成绩 |
| `/api/scores/class-stats` | GET | 班级统计 |
| `/api/scores/student-stats` | GET | 个人统计 |
| `/api/scores/export` | GET | 导出成绩 |
| `/api/admins` | GET/POST | 管理员列表 / 新增 |
| `/api/admins/{id}` | PUT/DELETE | 修改 / 删除管理员 |
| `/api/config` | GET/PUT | 系统配置 |
| `/api/student/login` | POST | 学生登录 |
| `/api/student/scores` | GET | 学生查自己的成绩 |
| `/api/student/password` | PUT | 学生修改密码 |
| `/api/student/recommend` | GET | 学生推荐项目 |

## 补充说明

### 测试日期

每次成绩录入锁定一个测试日期，同一班级同一项目同一天录入的成绩同属一个"测试轮次"。学生端折线图的横轴即为测试日期，每个日期一个数据点。

### 批量导入模板格式

Excel 模板包含列：学号、姓名、性别（男/女）、班级（如"2027届3班"）。模板文件由系统生成，含示例行供参考。

## 预置数据

### 运动项目（共 11 项）

女生（9 项，不含引体向上）：800米跑、足球运球、50米跑、立定跳远、一分钟跳绳、掷实心球、篮球运球投篮、一分钟仰卧起坐、游泳
男生（9 项，不含仰卧起坐）：1000米跑、足球运球、50米跑、立定跳远、一分钟跳绳、掷实心球、篮球运球投篮、引体向上、游泳

评分标准按照用户提供的男女各 10 档分值的完整表格预置。

### 默认超管

admin / admin123（首次登录强制修改）
