# AI 智能医疗问诊平台 — Docker 部署文档

本文说明如何用 Docker Compose 一键拉起前端、后端、MySQL 与 Neo4j，并完成知识图谱初始化。

业务架构说明见 [note.md](./note.md)。

---

## 1. 容器架构

浏览器只访问前端 Nginx（默认 80 端口）。接口与上传文件由 Nginx 反向代理到后端。

```
浏览器
  │
  │  http://localhost
  ▼
frontend (Nginx :80)
  ├─ /                Vue 静态资源（history 路由回退 index.html）
  ├─ /api/*           → backend:8000
  ├─ /api/v1/chat/send → backend:8000（SSE，关闭缓冲）
  └─ /uploads33/*     → backend:8000
          │
          ▼
     backend (FastAPI :8000)
          ├─ mysql:3306        业务数据
          ├─ neo4j:7687        知识图谱
          └─ 卷 chroma_data    向量库
             卷 uploads_data   知识库文件 / 头像
```

| 服务 | 镜像 / 构建 | 作用 |
|------|-------------|------|
| `frontend` | `client/Dockerfile`（Node 构建 + Nginx） | 用户访问入口 |
| `backend` | `server/Dockerfile`（Python 3.11） | API、RAG、图谱、文件服务 |
| `mysql` | `mysql:8.0` | 业务库 `db_ai_medical` |
| `neo4j` | `neo4j:5-community` | 症状-疾病知识图谱 |

首次启动时，backend 入口脚本会：等待 MySQL / Neo4j → 建表 → 写入演示账号 → 导入约 60 种常见疾病图谱 → 启动 uvicorn。

---

## 2. 环境要求

- Docker Engine 20.10+ 与 Docker Compose v2（Docker Desktop 已包含）
- 建议内存 **不少于 4 GB**（Neo4j + MySQL + 后端模型依赖同时占用）
- 磁盘预留约 3 GB（镜像与数据卷）
- **本机 Ollama** 已安装并拉好对话模型（见第 5 节）。Docker 中的 backend 通过 `host.docker.internal:11434` 访问宿主机 Ollama，请保持 Ollama 在跑

本机无需预先安装 Python、Node、MySQL、Neo4j。

---

## 3. 快速启动

在项目根目录执行：

```bash
cp .env.example .env
```

编辑 `.env`。本机 Ollama 方案（当前默认）无需云端 Key，确认这几项：

```env
OPENAI_API_KEY=ollama
OPENAI_BASE_URL=http://127.0.0.1:11434/v1
DOCKER_OPENAI_BASE_URL=http://host.docker.internal:11434/v1
LLM_MODEL=qwen3.6-plus
EMBEDDING_MODEL=nomic-embed-text
```

首次在本机执行一次模型准备（只需一次）：

```bash
ollama pull qwen3:latest
ollama cp qwen3:latest qwen3.6-plus
ollama pull nomic-embed-text
```

`qwen3.6-plus` 是项目约定的调用名；本机 Ollama 里实际对应已安装的 `qwen3:latest`。

启动：

```bash
docker compose up -d --build
```

查看状态与日志：

```bash
docker compose ps
docker compose logs -f backend
```

首次启动 backend 需要等待 Neo4j 就绪并导入图谱，大约 **2～5 分钟**。当日志出现 `启动 uvicorn` 且 `docker compose ps` 中 backend 为 healthy 后即可访问。

| 地址 | 说明 |
|------|------|
| http://localhost | 系统首页（登录页） |
| http://localhost:8000/docs | FastAPI 接口文档 |
| http://localhost:7474 | Neo4j Browser（用户 `neo4j`） |

若 80 端口被占用，在 `.env` 中修改 `WEB_PORT=8080`，然后访问 http://localhost:8080。

---

## 4. 演示账号

空库首次启动会自动写入（密码均为 `123456`）：

| 角色 | 用户名 | 密码 | 登录后入口 |
|------|--------|------|------------|
| 管理员 | `admin` | `123456` | `/admin/dashboard` |
| 医生 | `doctor` | `123456` | `/doctor/dashboard` |
| 医生 | `doctor2` | `123456` | `/doctor/dashboard` |
| 患者 | `user` | `123456` | `/portal/home` |

登录页需选择对应角色。也可在登录页使用「注册」创建新的患者账号。

---

## 5. 环境变量

以 `.env` 为准，`docker-compose.yml` 会读取并注入容器。

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OPENAI_API_KEY` | `ollama` | 本地 Ollama 填占位即可；云端 MaaS 填真实 Key |
| `OPENAI_BASE_URL` | `http://127.0.0.1:11434/v1` | 本机跑后端时访问 Ollama |
| `DOCKER_OPENAI_BASE_URL` | `http://host.docker.internal:11434/v1` | Compose 里 backend 访问**宿主机** Ollama |
| `LLM_MODEL` | `qwen3.6-plus` | 对话模型名（本地需 `ollama cp qwen3:latest qwen3.6-plus`） |
| `LLM_TEMPERATURE` | `0.2` | 对话温度 |
| `LLM_REASONING` | `false` | 是否保留 Qwen3 思考过程 |
| `EMBEDDING_MODEL` | `nomic-embed-text` | RAG 向量模型（须为 embedding 模型） |
| `EMBEDDING_DIMENSIONS` | `0` | `0` 表示不传 dimensions；阿里云 v4 用 `2048` |
| `MYSQL_ROOT_PASSWORD` | `123456` | MySQL root 密码 |
| `NEO4J_PASSWORD` | `12345678` | Neo4j 密码（至少 8 位） |
| `JWT_SECRET_KEY` | 内置演示值 | 生产环境务必改为随机长字符串 |
| `INIT_GRAPH` | `true` | 首次启动导入知识图谱；库中已有疾病节点则跳过 |
| `INIT_KNOWLEDGE` | `false` | 为 `true` 时向量化 `server/docs_seed/` 中的示例文档 |
| `WEB_PORT` | `80` | 浏览器访问端口 |
| `BACKEND_PORT` | `8000` | 直接暴露后端（可选，便于看 `/docs`） |
| `MYSQL_PORT` | `3308` | 宿主机映射 MySQL（容器内仍是 3306，避开本机常用的 3306） |
| `NEO4J_HTTP_PORT` | `7474` | Neo4j Browser |
| `NEO4J_BOLT_PORT` | `7687` | Neo4j Bolt |

**注意：** MySQL / Neo4j 密码只在数据卷 **第一次创建时** 生效。改密码后若服务起不来，需要删卷重建（会清空数据），见下文「重置数据」。

---

## 6. 知识库与图谱

### 6.1 知识图谱

默认 `INIT_GRAPH=true`。backend 启动时若 Neo4j 中还没有 `Disease` 节点，会执行 `server/scripts/init_graph.py`，导入常见病、症状、科室、药物、检查、宜忌食物等关系。

也可在容器就绪后手动执行：

```bash
docker compose exec backend python scripts/init_graph.py
```

### 6.2 知识库向量化

示例文档在 `server/docs_seed/`（感冒、高血压、糖尿病）。首次启动默认 **不** 自动向量化，避免没有 API Key 时启动失败。

需要自动导入时，在 `.env` 中设置：

```env
INIT_KNOWLEDGE=true
OPENAI_API_KEY=你的密钥
```

然后重建 backend：

```bash
docker compose up -d backend
```

或在已运行的容器中执行：

```bash
docker compose exec backend python scripts/init_knowledge.py
```

管理员登录后也可在「知识库」页面上传 txt / md / pdf / doc(x)，系统会后台分块并写入 Chroma。

---

## 7. 数据持久化

| 数据卷 | 内容 |
|--------|------|
| `mysql_data` | MySQL 数据 |
| `neo4j_data` | 知识图谱 |
| `neo4j_logs` | Neo4j 日志 |
| `uploads_data` | 上传的知识库文件与头像 |
| `chroma_data` | 向量索引 |

只要不删除这些卷，`docker compose down` 后再 `up` 数据仍在。

---

## 8. 常用命令

```bash
# 构建并后台启动
docker compose up -d --build

# 只看后端日志
docker compose logs -f backend

# 停止（保留数据卷）
docker compose down

# 停止并删除数据卷（清空全部业务数据，不可恢复）
docker compose down -v

# 进入后端容器
docker compose exec backend bash

# 重新编译前端（改了 Vue 代码后）
docker compose up -d --build frontend
```

修改后端 Python 代码后需要 `--build` 重建 backend 镜像。上传文件与数据库不在镜像内，重建不会丢失卷数据。

---

## 9. 重置数据

仅当演示数据损坏、或要更换 MySQL/Neo4j 初始密码时使用：

```bash
docker compose down -v
docker compose up -d --build
```

`-v` 会删除全部 named volume，图谱与账号都会按首次启动流程重新生成。

---

## 10. 本地开发（不用 Docker 跑前后端）

容器化不取代本地开发。本地默认仍是：

- 前端：`client/` 下 `npm run dev`（Vite 5173，代理 `/api` 到 `127.0.0.1:8000`）
- 后端：`server/` 下配置 `core/config.py` 的默认值（MySQL `127.0.0.1:3308` 等），或用环境变量覆盖
- 也可只用 Compose 起 MySQL 与 Neo4j，本机跑前后端：把 `MYSQL_HOST=127.0.0.1`、`MYSQL_PORT=3308`、`NEO4J_URI=bolt://127.0.0.1:7687` 配进后端环境

环境变量优先级高于 `config.py` 中的默认值，例如：

```bash
export MYSQL_HOST=127.0.0.1
export MYSQL_PORT=3308
export NEO4J_URI=bolt://127.0.0.1:7687
export OPENAI_API_KEY=你的密钥
```

---

## 11. 故障排查

**backend 一直 unhealthy / 日志卡在等待 Neo4j**

- 机器内存不足时 Neo4j 启动很慢，多等几分钟
- 查看 `docker compose logs neo4j`
- 确认 `.env` 中 `NEO4J_PASSWORD` 与第一次建卷时一致

**能打开页面，AI 问诊报错**

- 本机 Ollama 未启动：执行 `ollama serve`（需一直保持运行）
- 未建立名称映射：`ollama cp qwen3:latest qwen3.6-plus` 后 `ollama list` 应能看到 `qwen3.6-plus`
- 首次提问会加载约 5GB 模型，可能要 1～2 分钟，之后会快很多
- Docker 访问不到宿主机 Ollama：把 Ollama 绑到所有网卡后再启动  
  `OLLAMA_HOST=0.0.0.0:11434 ollama serve`  
  并确认 `.env` 中 `DOCKER_OPENAI_BASE_URL=http://host.docker.internal:11434/v1`
- 查看 `docker compose logs backend` 中 `[RAG-LLM]` 日志

**症状推理没有结果**

- 图谱未导入：执行 `docker compose exec backend python scripts/init_graph.py`
- 症状请使用图谱中的标准词，如「发热」「头痛」（「发烧」会做别名映射）

**MySQL 3306 端口占用**

本机或其他 Docker 项目占用 3306 时，把宿主机映射改到 3308（容器内部仍连 `mysql:3306`，业务不受影响）：

```env
MYSQL_PORT=3308
```

然后：

```bash
docker compose down
docker compose up -d
```

**80 端口占用**

```env
WEB_PORT=8080
```

然后 `docker compose up -d frontend`。

**修改代码后页面没变化**

- 前端：必须 `--build frontend`
- 后端：必须 `--build backend`（代码打进镜像，默认不挂源码）

**上传头像或知识库文件 404**

- 确认访问的是 Nginx 入口（`http://localhost`），不要只开 Vite
- 路径前缀固定为 `/uploads33/`，由 Nginx 转到 backend

---

## 12. 生产环境建议

当前实现面向教学/演示，上线前至少做到：

1. 修改 `MYSQL_ROOT_PASSWORD`、`NEO4J_PASSWORD`、`JWT_SECRET_KEY`，不要用文档默认值
2. 不要对公网暴露 `3306` / `7474` / `7687` / `8000`，只开放 `WEB_PORT`
3. 为 Nginx 配 HTTPS（宿主机反向代理或云负载均衡）
4. 定期备份 `mysql_data`、`neo4j_data`、`chroma_data`、`uploads_data`
5. 应用内密码目前为明文存储，生产应改为哈希
6. backend 保持单进程（SSE 流式问诊 + Chroma 本地文件），不要随意加大 uvicorn workers

---

## 13. 目录与构建文件

| 路径 | 说明 |
|------|------|
| `docker-compose.yml` | 四服务编排 |
| `.env.example` | 环境变量模板 |
| `client/Dockerfile` | 前端多阶段构建 |
| `client/nginx.conf` | 反向代理与 SPA 回退 |
| `server/Dockerfile` | 后端镜像 |
| `server/scripts/docker_entrypoint.py` | 等待依赖、种子数据、启动服务 |
| `server/sql/db_ai_medical.sql` | MySQL 建库建表（容器首次初始化执行） |
