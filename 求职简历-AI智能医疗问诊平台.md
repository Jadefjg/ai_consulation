# 项目经历（精简版 · 可直接粘贴）

> 已压缩篇幅：简述不重复责任细节；技术只保留核心栈；责任每条一行说清「做了什么 + 结果」。

---

## AI 智能医疗问诊平台（AI-Medical-Consultation）

**[2025/06 – 2025/09]**  
**全栈开发工程师**

**简述：**  
独立设计开发患者 / 医生 / 管理三角色 AI 医疗问诊系统，覆盖智能问诊、图谱推理、咨询预约与运营后台，提升健康咨询与运维效率。

**技术：**  
Python、FastAPI、MySQL、Neo4j、Chroma、LangChain、JWT、Vue3、Element Plus、Docker、Nginx、SSE

**责任：**  
1. 负责三角色业务架构与接口分层（api/services/models），提升安全性与可维护性。  
2. 设计实现 JWT + RBAC 权限模型（含 root 超管继承），完成角色隔离与接口守卫。  
3. 落地 RAG 问诊链路：知识库解析嵌入、向量检索与 LLM SSE 流式对话（支持 Ollama / 云端双方案）。  
4. 基于 Neo4j 构建疾病-症状-科室图谱，实现症状推理与管理端可视化。  
5. 开发咨询工单、预约流转、健康档案与数据看板，打通「AI 初筛 → 人工跟进」闭环。  
6. 使用 Docker Compose 多环境部署与 Nginx 反代（SSE 防缓冲），借助 AI IDE 重构优化，提升交付效率。

---

## 一页粘贴版

```
[2025/06 – 2025/09]  AI智能医疗问诊平台（AI-Medical-Consultation）  全栈开发工程师

简述：独立设计开发患者/医生/管理三角色AI医疗问诊系统，覆盖智能问诊、图谱推理、咨询预约与运营后台，提升健康咨询与运维效率。

技术：Python、FastAPI、MySQL、Neo4j、Chroma、LangChain、JWT、Vue3、Element Plus、Docker、Nginx、SSE

责任：
1.负责三角色业务架构与接口分层（api/services/models），提升安全性与可维护性。
2.设计实现JWT + RBAC权限模型（含root超管继承），完成角色隔离与接口守卫。
3.落地RAG问诊链路：知识库解析嵌入、向量检索与LLM SSE流式对话（支持Ollama/云端双方案）。
4.基于Neo4j构建疾病-症状-科室图谱，实现症状推理与管理端可视化。
5.开发咨询工单、预约流转、健康档案与数据看板，打通「AI初筛→人工跟进」闭环。
6.使用Docker Compose多环境部署与Nginx反代（SSE防缓冲），借助AI IDE重构优化，提升交付效率。
```
