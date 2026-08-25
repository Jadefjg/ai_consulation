# AI 智能医疗问诊平台 — 业务逻辑与技术架构

## 1. 项目定位

本项目是一套面向患者、医生、管理员的 **AI 智能医疗问诊平台**，核心能力是：

- 患者侧：AI 问诊、症状图谱推理、在线咨询医生、预约挂号、健康档案、健康资讯
- 医生侧：待回复咨询、预约处理、患者档案维护
- 管理侧：用户/医生/科室/知识库/知识图谱/咨询/预约/文章/公告全量管理，以及运营数据看板

技术主线为 **FastAPI 后端 + Vue 3 前端**，AI 能力由 **RAG（Chroma 向量检索 + 大模型流式生成）** 与 **Neo4j 医疗知识图谱推理** 共同支撑。系统声明为「基于 RAG + LangChain + Neo4j 的 AI 智能医疗问诊平台」。

> 说明：本系统提供的 AI 回答与图谱推理仅供健康参考，业务提示中明确不能替代专业医生诊断。

---

## 2. 总体架构

系统采用前后端分离的 B/S 架构，三套数据存储各司其职：

```
┌─────────────────────────────────────────────────────────────────┐
│  浏览器                                                          │
│  Vue 3 + Vite + Element Plus + Pinia + Vue Router + ECharts     │
│  三角色入口：/portal（患者） /doctor（医生） /admin（管理员）      │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP / SSE
                             │ /api/v1/*   /uploads33/*
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  FastAPI（uvicorn）                                              │
│  路由层 api/v1 → 服务层 services → ORM models / RAG / Graph      │
│  JWT 鉴权 + 角色守卫 require_roles(user/doctor/admin)            │
└──────┬─────────────────┬──────────────────┬─────────────────────┘
       │                 │                  │
       ▼                 ▼                  ▼
   MySQL 业务库      Chroma 向量库       Neo4j 知识图谱
   db_ai_medical     medical_knowledge   Disease/Symptom/...
       │                 │                  │
       │            阿里云 MaaS             │
       │         qwen3.6-plus              │
       │         text-embedding-v4         │
```

开发时前端 Vite 将 `/api` 与 `/uploads33` 代理到后端 `127.0.0.1:8000`。

---

## 3. 技术栈

### 3.1 前端（`client/`）

| 类别 | 技术 | 用途 |
|------|------|------|
| 框架 | Vue 3（`<script setup>`） | SPA |
| 构建 | Vite 8 | 开发服务器、生产打包 |
| UI | Element Plus + 图标 | 表格、表单、布局、消息提示 |
| 状态 | Pinia | 登录态、用户资料 |
| 路由 | Vue Router 4 | 角色分区路由 + 守卫 |
| 请求 | Axios | 统一 token、业务码、401 退出 |
| 图表 | ECharts + vue-echarts | 管理端数据看板 |
| Markdown | markdown-it | AI 回复渲染 |

关键路径：

- 入口：`client/src/main.js`
- 路由：`client/src/router/index.js`
- 请求：`client/src/utils/request.js`（`baseURL: /api/v1`）
- 认证状态：`client/src/stores/user.js`
- 布局：`PortalLayout.vue`（患者顶栏）、`AdminLayout.vue`（医生/管理员侧栏）

### 3.2 后端（`server/`）

| 类别 | 技术 | 用途 |
|------|------|------|
| Web 框架 | FastAPI | REST + SSE 流式问诊 |
| ORM | SQLAlchemy 2 | MySQL 映射 |
| 驱动 | PyMySQL | 连接 MySQL |
| 鉴权 | python-jose JWT | Bearer Token，有效期 24 小时 |
| LLM | LangChain ChatOpenAI | 流式对话 |
| Embedding | OpenAI SDK 兼容接口 | 文档/查询向量化 |
| 向量库 | Chroma（持久化） | 知识库检索 |
| 图谱 | neo4j Python Driver | 症状→疾病推理与可视化 |
| 文档解析 | pypdf / python-docx | PDF、Word 入库 |

分层约定：

```
server/
├── main.py                 # 应用入口、CORS、异常处理、静态文件
├── core/                   # 配置、JWT、依赖注入、统一响应
├── api/v1/                 # 接口层（按业务拆分 router）
├── services/               # 认证、RAG、图谱、统计
├── models/                 # SQLAlchemy ORM
├── schemas/common.py       # Pydantic 入参/出参
├── rag/                    # 文档加载、分块、嵌入、向量库
├── db/                     # Engine / Session
├── scripts/                # 图谱初始化、知识库种子、SQL 导入
└── docs_seed/              # 示例医学文档（感冒/高血压/糖尿病）
```

### 3.3 数据与外部服务

| 组件 | 用途 |
|------|------|
| MySQL（库名 `db_ai_medical`） | 用户、医生、预约、问诊会话、知识库元数据等业务数据 |
| Chroma（`server/chroma_db`，集合 `medical_knowledge`） | 知识库文本向量，余弦相似度检索 Top-K=5 |
| Neo4j | 疾病-症状-科室-药物-检查-食物知识图谱 |
| 阿里云 MaaS（OpenAI 兼容） | 对话模型 `qwen3.6-plus`，嵌入模型 `text-embedding-v4`（2048 维） |
| 本地上传目录 | 知识库文件与头像（配置项 `UPLOAD_DIR`，静态挂载 `/uploads33`） |

配置集中在 `server/core/config.py`，LLM Key 通过环境变量 `OPENAI_API_KEY` 注入。

---

## 4. 角色与权限模型

系统采用 **三角色分表 + JWT 载荷携带 role** 的方式，而不是一张用户表加角色字段。

| 角色 | 数据表 | 登录后首页 | 注册 |
|------|--------|------------|------|
| 患者 `user` | `t_user` | `/portal/home` | 开放注册 |
| 医生 `doctor` | `t_doctor` | `/doctor/dashboard` | 仅管理员创建 |
| 管理员 `admin` | `t_admin` | `/admin/dashboard` | 无自助注册 |

登录流程（`AuthService.login`）：

1. 按 `role` 查询对应表
2. 明文密码比对（当前未做哈希）
3. `status == 0` 则拒绝（账号禁用）
4. 签发 JWT：`{ sub: username, user_id, role }`

前端路由守卫：

- 未登录访问业务页 → `/login`
- 已登录访问登录/注册 → 跳转角色首页
- 访问非本角色路由 → 强制回到本角色首页
- token 存在但 role 非法 → 清理登录态

后端接口通过 `require_roles("user")` 等依赖注入做二次校验。科室列表、医生公开列表、文章/公告部分接口无需登录。

---

## 5. 业务功能逻辑

### 5.1 患者门户（`/portal`）

患者布局为顶部导航，功能入口如下。

#### 首页

- 展示个人统计：咨询数、预约数、健康档案数、AI 会话数（`/stat/user-overview`）
- 快捷入口：AI 问诊、症状推理、在线咨询、预约挂号
- 最新公告列表

#### AI 问诊（核心）

这是平台的智能咨询主路径，前后端通过 **SSE（Server-Sent Events）** 流式交互。

```
患者输入问题
    │
    ├─ 若无 session_id → 新建 t_consult_session（标题取问题前 20 字）
    ├─ 写入用户消息 t_consult_message(role=user)
    ├─ 读取本会话历史（发给 LLM 时最多带最近 6 条）
    │
    ▼
RagService.chat_stream
    ├─ Chroma 向量检索（Top 5）→ 拼装「参考知识」
    ├─ 从问题中匹配常见症状词 → Neo4j 共现推理疾病与建议科室
    ├─ 系统提示：仅供参考、严重症状建议就医
    └─ LLM 流式输出 content 块
    │
    ▼
前端逐字渲染 Markdown
完成后写入 assistant 消息（含 references_json、graph_json、耗时）
```

SSE 事件类型：

- `session`：回传会话 ID（新对话时前端据此绑定）
- `content`：增量文本
- `done`：引用文档、图谱推理结果、耗时
- `error`：异常信息

知识库为空时仍可对话，上下文退化为「暂无相关知识库内容」。

#### 症状推理

与 AI 问诊互补：用户手动添加症状标签，调用 `/graph/infer`，图谱按 **匹配症状数量** 排序返回可能疾病、匹配度、建议科室。可再查 `/graph/disease/{name}` 查看症状、药物、检查、并发症、宜忌食物。

症状别名会规范化（如「发烧」→「发热」，「头疼」→「头痛」）。

#### 在线咨询（人工问诊）

工单模型：`t_doctor_consult` + `t_doctor_reply`。

- 患者选择医生并填写主诉（前端把标题+内容拼成 `chief_complaint`）
- `status`：`0` 待回复，`1` 已回复
- 医生可接尚未指定医生（`doctor_id` 为空）的工单；首次回复时自动认领
- 患者可查看自己工单及医生回复列表

#### 预约挂号

- 选择科室 → 筛选医生 → 就诊日期 + 时段（上午/下午/晚上）+ 备注
- 写入 `t_appointment`，初始 `status=0`（待确认）
- 状态机：`0 待确认 → 1 已确认 → 2 已完成`，也可 `3 已取消`
- 医生或管理员可改状态；管理员可删除

#### 健康档案

患者只读本人档案。档案由医生创建，字段包括档案类型、诊断、治疗方案、处方、就诊日期。

#### 健康资讯 / 公告

- 文章公开列表（仅 `status=1`），详情页会累加浏览量
- 公告公开列表与详情

#### 个人中心

三角色共用 `/profile/*`：查看资料、改资料、改密码、上传头像。患者可维护昵称、性别、年龄、手机、过敏史。

---

### 5.2 医生工作台（`/doctor`）

侧栏菜单：工作台、待回复咨询、我的预约、患者档案、个人中心。

| 模块 | 逻辑 |
|------|------|
| 工作台 | 待回复咨询数（含未分配工单）、今日预约、关联患者去重人数、已回复咨询数 |
| 待回复咨询 | 列出指定自己或尚未分配、且 status=0 的工单，可回复并认领 |
| 我的预约 | 查看指向自己的预约，可更新状态 |
| 患者档案 | 仅能操作 `doctor_id=自己` 的档案；可选患者来自「曾预约 / 曾咨询 / 已有档案」的交集用户 |

医生不能管理知识库、用户、科室等后台资源。

---

### 5.3 管理后台（`/admin`）

管理员覆盖运营与知识工程：

| 模块 | 能力 |
|------|------|
| 数据概览 | 用户/医生/AI 会话/预约/知识库/文章总量；近 7 日问诊趋势、用户增长；科室预约分布；知识库文件类型分布（ECharts） |
| 用户管理 | 增删改查、启停、关键词搜索；删除时级联清理 AI 会话、人工咨询、预约、档案 |
| 医生管理 | 创建登录账号、绑定科室、职称/擅长/简介；删除时级联清理其咨询、预约、档案 |
| 科室管理 | CRUD、排序、名称唯一；有医生挂靠时禁止删除 |
| 知识库 | 上传 txt/md/pdf/doc(x)，后台异步解析→分块→向量化；可重新向量化、删除（同时清 Chroma 与磁盘文件） |
| 知识图谱 | 全图可视化、实体搜索、子图、节点类型统计 |
| 咨询管理 | 人工问诊工单分页检索、删除 |
| 预约管理 | 按患者/医生/科室/日期/状态筛选、改状态、删除 |
| 文章 / 公告 | 全状态 CRUD，患者端只展示已发布 |

公开医生列表仅返回 `status=1` 的医生，供患者选医生/预约使用。

---

## 6. 核心智能链路

### 6.1 RAG 知识库流水线

```
管理员上传文件
    → 落盘到 UPLOAD_DIR/knowledge
    → t_knowledge_file（vector_status: 0未处理 / 1处理中 / 2完成 / 3失败）
    → BackgroundTasks 调用 RagService.process_file
         1. loader：按扩展名解析文本（utf-8/gbk 兜底）
         2. splitter：RecursiveCharacterTextSplitter
            chunk_size=500，overlap=80，中文标点优先切分
         3. 删除该文件旧 chunk 与旧向量
         4. 写入 t_knowledge_chunk，batch=10 调用 embedding
         5. 写入 Chroma，id 形如 file_{id}_chunk_{idx}
```

检索时对用户问题做 `embed_query`，按余弦距离取 Top 5，把文档片段作为 LLM 的「参考知识」，并在前端可展示引用来源文件名。

种子文档位于 `server/docs_seed/`（感冒与流感、高血压、糖尿病），可用 `scripts/init_knowledge.py` 批量入库。

### 6.2 知识图谱模型

初始化脚本 `scripts/init_graph.py` 导入约 60 种常见疾病，节点与关系如下：

```
(Disease)-[:HAS_SYMPTOM]->(Symptom)
(Disease)-[:BELONGS_TO]->(Department)
(Disease)-[:RECOMMEND_DRUG]->(Drug)
(Disease)-[:NEED_CHECK]->(Check)
(Disease)-[:ACCOMPANY_WITH]->(Disease)     # 并发症
(Disease)-[:SHOULD_EAT]->(Food)
(Disease)-[:AVOID_EAT]->(Food)
```

各节点 `name` 有唯一约束。推理 Cypher 逻辑：将用户症状 UNWIND 后匹配 `HAS_SYMPTOM` 入边，按命中症状数降序取前 10，并带出所属科室。匹配度 `probability = match_count / 症状总数`。

图谱同时服务于：

1. AI 问诊的辅助上下文（自动抽症状词后注入 prompt）
2. 患者「症状推理」页的显式查询
3. 管理端全图 / 子图可视化

AI 问诊中的症状抽取目前是 **关键词包含匹配**（内置常见症状词表），不是 NER 模型。

---

## 7. 数据模型（MySQL）

| 表名 | 含义 | 关键字段 |
|------|------|----------|
| `t_admin` | 管理员 | username, password, nickname, status |
| `t_user` | 患者 | username, real_name, gender, age, phone, allergy_history, status |
| `t_doctor` | 医生 | username, real_name, department_id, title, specialty, status |
| `t_department` | 科室 | name, description, sort_order, status |
| `t_knowledge_file` | 知识库文件 | file_path, chunk_count, vector_status |
| `t_knowledge_chunk` | 分块文本 | file_id, chunk_index, content, vector_id |
| `t_consult_session` | AI 会话 | user_id, title, message_count |
| `t_consult_message` | AI 消息 | role, content, references_json, graph_json |
| `t_doctor_consult` | 人工问诊工单 | user_id, doctor_id, chief_complaint, status |
| `t_doctor_reply` | 医生回复 | consult_id, doctor_id, content |
| `t_appointment` | 预约 | user_id, doctor_id, department_id, visit_date, time_slot, status |
| `t_health_record` | 健康档案 | user_id, doctor_id, record_type, diagnosis, treatment, prescription |
| `t_article` | 科普文章 | title, category, summary, content, view_count, status |
| `t_notice` | 系统公告 | title, content, status |

ORM 未声明 ForeignKey 约束，关联关系由业务代码维护（删除用户/医生时手工级联）。

---

## 8. API 一览

统一前缀 `/api/v1`，统一响应 `{ code, message, data }`；分页为 `{ items, total, page, page_size }`。校验失败返回中文提示。

| 前缀 | 模块 |
|------|------|
| `/auth` | 登录、患者注册 |
| `/users` | 管理员用户 CRUD |
| `/doctors` | 公开医生列表、管理员医生 CRUD |
| `/departments` | 公开科室、管理员科室 CRUD |
| `/knowledge` | 知识库上传/向量化/删除 |
| `/chat` | AI 会话列表、消息、SSE 发送 |
| `/graph` | 推理、疾病详情、全图、子图、搜索、统计 |
| `/consult` | 人工问诊创建/我的/医生待办/回复/管理 |
| `/appointments` | 预约创建/我的/医生/管理/改状态 |
| `/records` | 健康档案患者查看、医生 CRUD |
| `/articles` | 文章公开列表与后台管理 |
| `/notices` | 公告公开列表与后台管理 |
| `/stat` | 各角色概览与图表数据 |
| `/profile` | 资料、密码、头像 |

---

## 9. 前端信息架构

```
/login, /register                          公开
/portal/*          role=user
    home / chat / symptom / consult
    appointment / records / articles / notices/:id / profile
/doctor/*          role=doctor
    dashboard / consults / appointments / patients / profile
/admin/*           role=admin
    dashboard / users / doctors / departments
    knowledge / graph / consults / appointments
    articles / notices / profile
```

请求拦截器自动附加 `Authorization: Bearer <token>`。业务 `code` 非 0/200 时弹出错误；HTTP 401 触发退出登录。AI 问诊因需要流式读取，单独用 `fetch` + `ReadableStream`，不走 Axios。

---

## 10. 关键业务状态约定

**账号 status**

- `1` 正常，`0` 禁用（登录被拒；公开医生列表不展示禁用医生）

**知识库 vector_status**

- `0` 未处理 → `1` 处理中 → `2` 成功 / `3` 失败

**人工咨询 status**

- `0` 待回复，`1` 已回复

**预约 status**

- `0` 待确认，`1` 已确认，`2` 已完成，`3` 已取消

**文章/公告 status**

- `1` 已发布（前台可见），其他为后台草稿/下架

---

## 11. 典型用户旅程

### 患者自助问诊

1. 注册/登录进入门户首页
2. 在「症状推理」输入头痛、发热 → 看到感冒/流感等候选及建议科室
3. 进入「AI 问诊」追问注意事项 → RAG 引用知识库，图谱补充可能疾病
4. 需要人工时发起「在线咨询」或「预约挂号」
5. 就诊后在「健康档案」查看医生写入的诊断与处方

### 医生接诊

1. 工作台看到待回复与今日预约
2. 回复咨询（未指定医生的工单会被认领）
3. 确认/完成预约
4. 为相关患者新建或更新健康档案

### 管理员运营

1. 维护科室与医生账号
2. 上传医学文档，等待向量化完成
3. 初始化/查看 Neo4j 图谱
4. 发布资讯与公告，监控咨询与预约数据

---

## 12. 架构特点与实现要点

**特点**

- 业务系统与 AI 能力解耦：MySQL 管事务数据，Chroma 管检索，Neo4j 管结构化医学关系
- 双通道智能：非结构化文档 RAG + 结构化图谱推理，在同一轮问诊中融合
- 三角色产品形态清晰，前后端都以 role 做隔离
- 问诊体验采用流式输出，降低长回复等待感

**实现要点（阅读代码时需注意）**

- 密码目前为明文存储与比对，适合教学演示，不适合生产
- JWT 密钥、数据库口令、上传路径等均可通过环境变量覆盖（见 `.env.example` / [DEPLOY.md](./DEPLOY.md)）
- ORM 无数据库级外键，依赖应用层级联删除
- AI 问诊保存助手消息时在 SSE 生成器内新开 `SessionLocal`，避免流式过程中原 session 失效
- 本地默认上传目录仍为 Windows 路径 `D:/uploads33`，Docker 中通过 `UPLOAD_DIR=/data/uploads` 覆盖
- 图谱疾病详情接口、全图/子图/搜索部分未强制登录，管理端可视化依赖这些公开读接口

---

## 13. 目录速查

| 路径 | 说明 |
|------|------|
| `client/src/views/portal/` | 患者全部页面 |
| `client/src/views/doctor/` | 医生工作台页面 |
| `client/src/views/admin/` | 管理后台页面 |
| `server/api/v1/` | 全部 REST/SSE 接口 |
| `server/services/rag_service.py` | RAG 问答与文件向量化 |
| `server/services/graph_service.py` | Neo4j 推理与可视化数据 |
| `server/rag/` | 加载、切分、嵌入、向量库封装 |
| `server/scripts/init_graph.py` | 图谱种子数据 |
| `server/scripts/init_knowledge.py` | 知识库种子向量化 |
| `docker-compose.yml` | 容器编排 |
| `DEPLOY.md` | Docker 部署说明 |

---

## 14. Docker 部署

四容器编排：`frontend`（Nginx）+ `backend`（FastAPI）+ `mysql` + `neo4j`。浏览器访问前端 80 端口，`/api` 与 `/uploads33` 由 Nginx 反向代理到后端。

快速启动：

```bash
cp .env.example .env   # 填写 OPENAI_API_KEY
docker compose up -d --build
```

完整步骤、端口、演示账号、数据卷与排障见 [DEPLOY.md](./DEPLOY.md)。
