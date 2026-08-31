# AI 智能医疗问诊平台 — Docker 部署文档

本文说明如何用 Docker Compose 一键部署前端、后端、MySQL、Neo4j，并完成知识图谱与本地 LLM（Ollama）对接。

业务与架构说明见 [note.md](./note.md)。

---

## 1. 系统架构

### 1.1 容器拓扑

浏览器只访问前端 Nginx（默认 80 端口）。API 与头像文件由 Nginx 反向代理到后端。

```
浏览器
  │
  │  http://localhost
  ▼
frontend (Nginx :80)
  ├─ /                     Vue 静态资源（SPA history 回退）
  ├─ /api/*                → backend:8000
  ├─ /api/v1/chat/send     → backend:8000（SSE，关闭缓冲）
  └─ /uploads33/avatar/*   → backend:8000（仅头像公开）
          │
          ▼
     backend (FastAPI :8000)
          ├─ mysql:3306           业务数据（用户/医生/预约/问诊等）
          ├─ neo4j:7687           知识图谱（症状-疾病推理）
          ├─ host.docker.internal:11434   宿主机 Ollama（对话 + 向量嵌入）
          └─ 数据卷
             ├─ chroma_data      Chroma 向量库（RAG 检索）
             └─ uploads_data      知识库原始文件 / 用户头像
```

### 1.2 服务清单

| 服务 | 镜像 / 构建 | 作用 |
|------|-------------|------|
| `frontend` | `client/Dockerfile`（Node 22 构建 + Nginx 1.27） | 用户访问入口、反向代理 |
| `backend` | `server/Dockerfile`（Python 3.11） | REST API、RAG、图谱、后台向量化 |
| `mysql` | `mysql:8.0` | 业务库 `db_ai_medical` |
| `neo4j` | `neo4j:5-community` | 医疗知识图谱 |

### 1.3 智能能力依赖关系

| 功能 | 依赖组件 | 说明 |
|------|----------|------|
| AI 问诊对话 | Ollama `LLM_MODEL` | 流式 SSE，需宿主机 Ollama 持续运行 |
| 知识库向量化 | Ollama `EMBEDDING_MODEL` | 上传 pdf/doc/txt 后后台嵌入，**与对话共用 Ollama 地址** |
| RAG 检索 | Chroma + 嵌入模型 | 向量写入 `chroma_data` 卷 |
| 症状推理 | Neo4j 图谱 | 启动时 `INIT_GRAPH=true` 自动导入 |

**重要：** 知识库显示「失败」通常是 **嵌入模型连不上 Ollama**，而非文件上传失败。见 [11.4 知识库向量化失败](#114-知识库向量化失败)。

---

## 2. 环境要求

### 2.1 硬件与软件

| 项目 | 要求 |
|------|------|
| Docker | Engine 20.10+，Compose v2（Docker Desktop 已包含） |
| 内存 | 建议 **≥ 8 GB**（Neo4j + MySQL + Ollama 大模型同时占用） |
| 磁盘 | 预留约 **5 GB**（镜像、数据卷、Ollama 模型） |
| Ollama | **必须**在宿主机安装并运行（见第 5 节） |

本机 **无需** 预装 Python、Node、MySQL、Neo4j（均由容器提供）。

### 2.2 端口占用（宿主机）

| 端口 | 服务 | 可在 `.env` 中修改 |
|------|------|-------------------|
| 80 | 前端 Nginx | `WEB_PORT` |
| 8000 | 后端 API（可选暴露） | `BACKEND_PORT` |
| 3308 | MySQL（映射容器 3306） | `MYSQL_PORT` |
| 7474 | Neo4j Browser | `NEO4J_HTTP_PORT` |
| 7687 | Neo4j Bolt | `NEO4J_BOLT_PORT` |
| 11434 | Ollama（宿主机，非容器） | — |

若本机 3306 已被占用，默认已映射为 **3308**，容器内互联仍使用 `mysql:3306`，无需改后端配置。

---

## 3. 快速部署（推荐流程）

### 3.1 准备 Ollama（宿主机，先于 Docker 启动）

```bash
# 安装 Ollama 后，绑定所有网卡以便 Docker 访问（macOS / Linux 推荐）
export OLLAMA_HOST=0.0.0.0:11434
ollama serve
```

另开终端拉取模型（**对话 + 知识库各需一个**）：

```bash
# 对话模型（项目调用名 qwen3.6-plus，由 qwen3:latest 别名而来）
ollama pull qwen3:latest
ollama cp qwen3:latest qwen3.6-plus

# 嵌入模型（知识库向量化必需，缺一不可）
ollama pull nomic-embed-text
```

验证本机可用：

```bash
curl http://127.0.0.1:11434/api/tags
```

应返回 JSON，且列表中包含 `qwen3.6-plus` 与 `nomic-embed-text`。

### 3.2 配置环境变量

在项目根目录：

```bash
cp .env.example .env
```

本机 Ollama 方案（默认）核心配置：

```env
OPENAI_API_KEY=ollama
OPENAI_BASE_URL=http://127.0.0.1:11434/v1
DOCKER_OPENAI_BASE_URL=http://host.docker.internal:11434/v1
LLM_MODEL=qwen3.6-plus
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_DIMENSIONS=0
```

### 3.3 启动容器

```bash
docker compose up -d --build
```

查看状态：

```bash
docker compose ps
docker compose logs -f backend
```

### 3.4 首次启动时间线

| 阶段 | 耗时 | 日志关键字 |
|------|------|------------|
| MySQL / Neo4j 健康检查 | 30s～2min | `Healthy` |
| 建表、演示数据、root 账号 | ~10s | `[seed]`、`[root]` |
| Neo4j 图谱导入 | 1～3min | `init_graph` |
| Uvicorn 启动 | 即时 | `启动 uvicorn`、`服务已就绪` |

`docker compose ps` 中 **backend** 为 `healthy` 后即可访问。

### 3.5 访问地址

| 地址 | 说明 |
|------|------|
| http://localhost | 系统首页（登录） |
| http://localhost:8000/docs | FastAPI 接口文档 |
| http://localhost:7474 | Neo4j Browser（`neo4j` / 见 `.env` 密码） |

---

## 4. 账号与权限

### 4.1 超级管理员（root）

每次 backend 启动会自动执行 `ensure_root.py`，保证以下账号存在：

| 用户名 | 密码 | 角色 | 登录方式 |
|--------|------|------|----------|
| `admin` | `feng1010` | root（超级管理员） | 登录页选 **「管理员」** |

root 拥有全部管理后台权限，JWT 中 `role=root`，在用户管理列表显示为 **「超级管理员」**。

手动重置 root 账号：

```bash
docker compose exec backend python scripts/ensure_root.py
```

### 4.2 演示账号（仅空库首次 seed 时写入）

密码均为 `123456`（root 账号会被 `ensure_root` 覆盖密码为 `feng1010`）：

| 角色 | 用户名 | 登录身份 |
|------|--------|----------|
| 医生 | `doctor` / `doctor2` | 医生 |
| 患者 | `user` | 用户 |

### 4.3 自助注册

| 注册身份 | 说明 |
|----------|------|
| 用户 | 公开注册，写入 `t_user` |
| 医生 | 公开注册，需选择科室，写入 `t_doctor` |
| 管理员 | **不可**公开注册，仅后台创建或 seed / ensure_root |

登录页须选择与账号表一致的身份；选错会提示「登录身份不正确」。

### 4.4 用户管理列表

管理后台「用户管理」聚合展示 **用户 / 医生 / 管理员** 三类账号，含「角色」列。患者账号可在本页编辑；医生与管理员请前往对应管理页操作。

---

## 5. Ollama 与 LLM 配置详解

### 5.1 两套 URL 的含义

| 变量 | 使用场景 | 典型值 |
|------|----------|--------|
| `OPENAI_BASE_URL` | 本机直接跑 `uvicorn`（非 Docker 后端） | `http://127.0.0.1:11434/v1` |
| `DOCKER_OPENAI_BASE_URL` | Docker Compose 中 backend 容器 | `http://host.docker.internal:11434/v1` |

`docker-compose.yml` 将 `DOCKER_OPENAI_BASE_URL` 注入为容器内 `OPENAI_BASE_URL`。

### 5.2 模型对照

| 用途 | 环境变量 | Ollama 准备命令 |
|------|----------|-----------------|
| AI 对话 | `LLM_MODEL=qwen3.6-plus` | `ollama pull qwen3:latest && ollama cp qwen3:latest qwen3.6-plus` |
| 知识库向量 | `EMBEDDING_MODEL=nomic-embed-text` | `ollama pull nomic-embed-text` |

`EMBEDDING_DIMENSIONS=0` 表示不向 API 传递 `dimensions` 参数（Ollama 本地嵌入适用）。使用阿里云 `text-embedding-v4` 时改为 `2048`。

### 5.3 从容器内验证 Ollama 连通性

```bash
docker compose exec backend curl -s http://host.docker.internal:11434/api/tags
```

若 `Connection refused` 或 `Network is unreachable`：

1. 确认宿主机 `ollama serve` 正在运行  
2. 使用 `OLLAMA_HOST=0.0.0.0:11434 ollama serve`  
3. 确认 `docker-compose.yml` 中 backend 有 `extra_hosts: host.docker.internal:host-gateway`  
4. Linux 无 `host.docker.internal` 时，可改为宿主机局域网 IP，例如 `http://192.168.x.x:11434/v1`

### 5.4 方案 B：阿里云 MaaS

在 `.env` 中注释 Ollama 配置，改为：

```env
OPENAI_API_KEY=你的真实Key
OPENAI_BASE_URL=https://llm-ddxbqu7e4h6kc0lq.cn-beijing.maas.aliyuncs.com/compatible-mode/v1
DOCKER_OPENAI_BASE_URL=https://llm-ddxbqu7e4h6kc0lq.cn-beijing.maas.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen3.6-plus
EMBEDDING_MODEL=text-embedding-v4
EMBEDDING_DIMENSIONS=2048
```

云端方案无需本机 Ollama，知识库向量化同样走嵌入 API。

---

## 6. 环境变量完整说明

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OPENAI_API_KEY` | `ollama` | 本地 Ollama 填占位；云端填真实 Key |
| `OPENAI_BASE_URL` | `http://127.0.0.1:11434/v1` | 本机后端访问 LLM |
| `DOCKER_OPENAI_BASE_URL` | `http://host.docker.internal:11434/v1` | 容器内 backend 访问宿主机 Ollama |
| `LLM_MODEL` | `qwen3.6-plus` | 对话模型名 |
| `LLM_TEMPERATURE` | `0.2` | 对话温度 |
| `LLM_REASONING` | `false` | 是否输出 Qwen3 思考链 |
| `EMBEDDING_MODEL` | `nomic-embed-text` | RAG 嵌入模型 |
| `EMBEDDING_DIMENSIONS` | `0` | Ollama 用 0；阿里云 v4 用 2048 |
| `MYSQL_ROOT_PASSWORD` | `123456` | MySQL root 密码 |
| `NEO4J_PASSWORD` | `12345678` | Neo4j 密码（≥8 位） |
| `JWT_SECRET_KEY` | 内置演示值 | **生产必须改为随机长字符串** |
| `INIT_GRAPH` | `true` | 首次启动导入 Neo4j 图谱 |
| `INIT_KNOWLEDGE` | `false` | 为 true 时向量化 `server/docs_seed/` |
| `WEB_PORT` | `80` | 浏览器访问端口 |
| `BACKEND_PORT` | `8000` | 宿主机暴露后端 |
| `MYSQL_PORT` | `3308` | 宿主机映射 MySQL |
| `NEO4J_HTTP_PORT` | `7474` | Neo4j Browser |
| `NEO4J_BOLT_PORT` | `7687` | Neo4j Bolt |

**密码卷注意：** MySQL / Neo4j 密码仅在数据卷 **首次创建** 时生效。修改 `.env` 密码后若连不上，需 `docker compose down -v` 重建（清空数据）。

---

## 7. 启动流程（backend 入口）

`server/scripts/docker_entrypoint.py` 依次执行：

1. `wait_for_mysql` / `wait_for_neo4j`
2. `ensure_schema` — ORM 建表、password 字段扩容、admin_role 列兼容
3. `seed_demo` — 空库写入科室、演示医生/患者（已有管理员则跳过）
4. `ensure_root_admin` — 创建/更新 `admin / feng1010` root 账号
5. `INIT_GRAPH=true` → `init_graph.py`
6. `INIT_KNOWLEDGE=true` → `init_knowledge.py`（需可用嵌入 API）
7. 启动 `uvicorn main:app --host 0.0.0.0 --port 8000`

---

## 8. 知识库与知识图谱

### 8.1 知识图谱（Neo4j）

默认 `INIT_GRAPH=true`。若库中无 `Disease` 节点，导入约 60 种常见病及症状、科室、药物等关系。

手动重导：

```bash
docker compose exec backend python scripts/init_graph.py
```

管理后台「知识图谱」页可可视化查看（需管理员登录）。

### 8.2 知识库（RAG）

**支持格式：** txt、md、markdown、pdf、doc、docx（单文件 ≤ 20MB）

**上传流程：**

1. 管理员在「知识库」页上传 → 文件存入 `uploads_data` 卷  
2. 后台任务解析文本、分块 → 调用 **嵌入模型** 写入 Chroma  
3. 列表「状态」列反映结果

**向量化状态码：**

| vector_status | 界面显示 | 含义 |
|---------------|----------|------|
| 0 | 待处理 | 刚上传 |
| 1 | 处理中 | 正在解析/嵌入 |
| 2 | 成功 | 可参与 RAG 检索 |
| 3 | 失败 | 解析或嵌入出错（多见 Ollama 不可用） |

失败后在列表点击 **「重新向量化」**，或查看日志：

```bash
docker compose logs backend | grep -i knowledge
```

**预置文档：** `server/docs_seed/` 含感冒、高血压、糖尿病示例。自动导入：

```env
INIT_KNOWLEDGE=true
```

然后 `docker compose up -d --build backend`，或：

```bash
docker compose exec backend python scripts/init_knowledge.py
```

**安全说明：** 知识库原始文件 **不** 通过 `/uploads33` 公开访问，仅头像目录对外；知识文件仅管理员通过后台管理。

---

## 9. 数据持久化

| 数据卷 | 内容 |
|--------|------|
| `mysql_data` | 用户、医生、预约、问诊记录等 |
| `neo4j_data` | 知识图谱 |
| `neo4j_logs` | Neo4j 日志 |
| `uploads_data` | 知识库文件、用户头像 |
| `chroma_data` | 向量索引 |

`docker compose down` 不删卷；`docker compose down -v` **清空全部数据**。

### 9.1 备份建议

```bash
# 示例：打包数据卷（需根据实际 volume 名调整）
docker run --rm -v ai_consultation_mysql_data:/data -v $(pwd):/backup alpine \
  tar czf /backup/mysql_backup.tar.gz -C /data .
```

生产环境应定期备份上述四个业务卷。

---

## 10. 常用运维命令

```bash
# 构建并启动
docker compose up -d --build

# 仅重建后端 / 前端
docker compose up -d --build backend
docker compose up -d --build frontend

# 日志
docker compose logs -f backend
docker compose logs -f neo4j

# 停止（保留数据）
docker compose down

# 停止并清空所有数据
docker compose down -v

# 进入后端容器
docker compose exec backend bash

# 重置 root 超级管理员
docker compose exec backend python scripts/ensure_root.py

# 手动向量化单文件（file_id 见知识库列表）
docker compose exec backend python -c "
from db.session import SessionLocal
from models.knowledge import KnowledgeFile
from services.rag_service import get_rag_service
db = SessionLocal()
f = db.query(KnowledgeFile).filter(KnowledgeFile.id==2).first()
print(get_rag_service().process_file(db, f))
db.close()
"
```

修改 Python / Vue 代码后必须 `--build` 对应服务；数据卷内容不受重建影响。

---

## 11. 故障排查

### 11.1 backend 一直 unhealthy

- Neo4j 冷启动慢，多等 2～5 分钟，看 `docker compose logs neo4j`
- 内存不足时 Neo4j 反复重启，建议关闭其他占内存应用
- `NEO4J_PASSWORD` 与首次建卷时不一致 → 需 `down -v` 重建或改回旧密码

### 11.2 AI 问诊报错 / 无回复

| 现象 | 处理 |
|------|------|
| 连接超时 | 本机执行 `ollama serve`；首问加载大模型需 1～2 分钟 |
| 模型不存在 | `ollama list` 确认有 `qwen3.6-plus` |
| Docker 连不上 Ollama | `OLLAMA_HOST=0.0.0.0:11434`；容器内 `curl host.docker.internal:11434/api/tags` |
| 日志 | `docker compose logs backend` 搜索 `[RAG-LLM]` |

### 11.3 症状推理无结果

- 图谱未导入：`docker compose exec backend python scripts/init_graph.py`
- 使用标准症状词：发热、头痛、咳嗽等（支持部分别名如「发烧」→「发热」）

### 11.4 知识库向量化失败

**典型现象：** 上传成功，列表状态为 **「失败」**，`vector_status=3`，`chunk_count=0`。

**原因分析（按频率）：**

1. **Ollama 未运行或未拉取嵌入模型**（最常见）  
   - 对话模型与嵌入模型是 **两个不同模型**  
   - 仅配置 `qwen3.6-plus` 不够，必须：`ollama pull nomic-embed-text`

2. **Docker 无法访问宿主机 11434**  
   - 容器内错误：`Connection error` / `Network is unreachable`  
   - 处理：见 [5.3 从容器内验证 Ollama](#53-从容器内验证-ollama-连通性)

3. **文件解析结果为空**（少见）  
   - 损坏的 pdf/doc、扫描版 PDF 无文本层  
   - 日志中分块数为 0 且未报连接错误

**处理步骤：**

```bash
# 1. 宿主机确认 Ollama 与嵌入模型
ollama serve
ollama pull nomic-embed-text
curl http://127.0.0.1:11434/api/tags

# 2. 容器内确认连通
docker compose exec backend curl -s http://host.docker.internal:11434/api/tags

# 3. 后台点击「重新向量化」，或看日志
docker compose logs backend | grep knowledge
```

### 11.5 登录失败

| 现象 | 处理 |
|------|------|
| 用户名或密码错误 | 确认登录身份（用户/医生/管理员）与注册时一致 |
| root 管理员 | 用户名 `admin`，密码 `feng1010`，选「管理员」 |
| 医生注册后无法登录 | 须选「医生」；仅注册页选「用户」的账号在患者表 |
| 账号被禁用 | 管理后台启用，或 `status=1` |

### 11.6 端口冲突

```env
# MySQL 宿主机 3306 被占用
MYSQL_PORT=3308

# 前端 80 被占用
WEB_PORT=8080
```

修改后：`docker compose down && docker compose up -d`

### 11.7 修改代码后页面未更新

- 前端：`docker compose up -d --build frontend`
- 后端：`docker compose up -d --build backend`

### 11.8 头像 404

- 通过 `http://localhost`（Nginx）访问，不要只用 Vite 开发端口
- 头像 URL 前缀：`/uploads33/avatar/...`

---

## 12. 本地开发（混合模式）

可不跑前后端容器，仅用 Compose 起中间件：

```bash
docker compose up -d mysql neo4j
```

后端环境变量示例：

```bash
export MYSQL_HOST=127.0.0.1
export MYSQL_PORT=3308
export NEO4J_URI=bolt://127.0.0.1:7687
export NEO4J_PASSWORD=12345678
export OPENAI_API_KEY=ollama
export OPENAI_BASE_URL=http://127.0.0.1:11434/v1
cd server && uvicorn main:app --reload --port 8000
```

前端：

```bash
cd client && npm install && npm run dev
```

Vite 默认 `5173`，已将 `/api` 代理到 `127.0.0.1:8000`。

---

## 13. 生产环境建议

1. **修改默认密码：** `MYSQL_ROOT_PASSWORD`、`NEO4J_PASSWORD`、`JWT_SECRET_KEY`；root 管理员密码在 `scripts/ensure_root.py` 中配置后重建或手动改库  
2. **网络暴露：** 仅开放 `WEB_PORT`；不要对公网暴露 3306 / 7474 / 7687 / 8000  
3. **HTTPS：** 在 Nginx 或云负载均衡配置 TLS  
4. **备份：** 定期备份 `mysql_data`、`neo4j_data`、`chroma_data`、`uploads_data`  
5. **Ollama：** 生产建议独立 GPU 服务器或改用云端 MaaS，避免单机内存不足  
6. **进程模型：** backend 保持单 worker（SSE 流式 + Chroma 本地文件），勿随意增加 uvicorn workers  
7. **安全：** 密码已 PBKDF2 哈希存储；知识库文件不公开静态目录；管理接口需 JWT + 角色校验

---

## 14. 目录与关键文件

| 路径 | 说明 |
|------|------|
| `docker-compose.yml` | 四服务编排、卷、健康检查 |
| `.env.example` | 环境变量模板 |
| `client/Dockerfile` | 前端多阶段构建 |
| `client/nginx.conf` | 反向代理、SSE、上传代理 |
| `server/Dockerfile` | 后端镜像（Python 3.11） |
| `server/scripts/docker_entrypoint.py` | 启动入口：等依赖、建表、seed、root、图谱 |
| `server/scripts/ensure_root.py` | root 超级管理员 `admin/feng1010` |
| `server/scripts/seed_demo.py` | 演示科室、医生、患者 |
| `server/scripts/init_graph.py` | Neo4j 图谱导入 |
| `server/scripts/init_knowledge.py` | 预置文档向量化 |
| `server/sql/db_ai_medical.sql` | MySQL 建库建表（容器首次初始化） |
| `server/core/roles.py` | root / admin 权限扩展 |
| `note.md` | 业务逻辑与技术架构说明 |

---

## 15. 部署检查清单

上线或验收前可按表自检：

| # | 检查项 | 命令 / 预期 |
|---|--------|-------------|
| 1 | 容器全部 healthy | `docker compose ps` |
| 2 | 本机 Ollama 运行 | `curl localhost:11434/api/tags` |
| 3 | 对话模型存在 | `ollama list` 含 `qwen3.6-plus` |
| 4 | 嵌入模型存在 | `ollama list` 含 `nomic-embed-text` |
| 5 | 容器可访问 Ollama | `docker compose exec backend curl host.docker.internal:11434/api/tags` |
| 6 | 首页可打开 | http://localhost |
| 7 | root 可登录 | admin / feng1010，身份「管理员」 |
| 8 | 图谱有数据 | 管理后台「知识图谱」有节点 |
| 9 | 知识库可成功 | 上传小 txt 测试，状态为「成功」 |
| 10 | AI 问诊有回复 | 患者端发起一问，有流式输出 |

全部通过后，系统即处于可演示 / 可交付状态。
