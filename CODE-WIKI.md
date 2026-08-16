# Code Wiki · 工艺文件辅助编辑系统 (localknowledgebase-word)

> **本文档为代码级 Wiki，基于仓库实际代码生成，覆盖项目架构、模块职责、关键类与函数、依赖关系、运行方式、注意事项及协作规范。**
> 架构单一事实源仍为 [ARCHITECTURE.md](ARCHITECTURE.md)；进度见 [DEV-LOG.md](DEV-LOG.md)。

---

## 目录

- [1. 项目概述](#1-项目概述)
- [2. 技术栈](#2-技术栈)
- [3. 仓库结构总览](#3-仓库结构总览)
- [4. 后端架构详解](#4-后端架构详解)
  - [4.1 应用入口与配置](#41-应用入口与配置)
  - [4.2 Agent 系统（核心）](#42-agent-系统核心)
  - [4.3 服务层 (Services)](#43-服务层-services)
  - [4.4 数据模型与存储](#44-数据模型与存储)
  - [4.5 API 路由层](#45-api-路由层)
  - [4.6 工具层 (Tools)](#46-工具层-tools)
  - [4.7 Repository 模式](#47-repository-模式)
- [5. 前端架构详解](#5-前端架构详解)
  - [5.1 应用入口与构建](#51-应用入口与构建)
  - [5.2 状态管理 (Zustand)](#52-状态管理-zustand)
  - [5.3 服务与 API 层](#53-服务与-api-层)
  - [5.4 核心组件](#54-核心组件)
  - [5.5 Hooks](#55-hooks)
  - [5.6 工具函数与类型](#56-工具函数与类型)
- [6. 端到端生成流程](#6-端到端生成流程)
- [7. 依赖关系](#7-依赖关系)
- [8. 项目运行方式](#8-项目运行方式)
- [9. 部署](#9-部署)
- [10. 注意事项（必读）](#10-注意事项必读)
- [11. 协作编辑方式与注意事项](#11-协作编辑方式与注意事项)

---

## 1. 项目概述

**工艺文件辅助编辑系统**是一个基于 AI 的工艺文件智能编辑平台，核心理念：

```
工艺意图 → 标准工艺术语 → 工艺文件生成
```

系统通过多层 Agent 架构，从工艺素材 / 用户意图出发，自动生成符合 QJ903 标准的结构化工艺文件（装配卡、工艺流程图、明细表等）。前端提供表格编辑器（Tiptap + 模板驱动），后端以 FastAPI + 多层 Agent + 层次化上下文检索为核心。

**仓库**：`github.com/alerlocked/llbased-word`（public，`main` 受 branch protection 保护）

---

## 2. 技术栈

| 层 | 技术 |
|----|------|
| 前端 | React 18 + TypeScript + Vite + Ant Design 5 + Tiptap 2 + Zustand |
| 后端 | Python 3.13 + FastAPI + SQLAlchemy 2.0 + SQLite |
| AI / LLM | LangChain + Qwen（云端 DashScope / 本地 MindIE Qwen3-30B-A3B） |
| PDF 解析 | MinerU 3.4（VLM 高精度解析）+ pdfplumber（简单表格） |
| 检索 | HierarchicalContext（关键词 + 章节结构 source-driven 直注）+ KnowledgeGraph（networkx） |
| 部署 | Windows 10 瘦客户端 + 内网服务器（LLM:1028 / VLM:1040）|

---

## 3. 仓库结构总览

```
llbased-word/
├── backend/                    # Python 后端
│   ├── app/
│   │   ├── agents/             # Agent 系统（架构层）
│   │   │   ├── core/           # 注册表 & 协议
│   │   │   ├── functional/     # 功能 Agent（writing/review/proofread）
│   │   │   ├── orchestrator/   # 编排器 + 状态机
│   │   │   └── tools/          # Agent 工具（搜索/图片/PDF表抽取）
│   │   ├── api/                # FastAPI 路由（18 个 router 文件）
│   │   ├── models/             # SQLAlchemy ORM + Pydantic 模型
│   │   ├── services/           # 业务服务层（40+ 服务文件）
│   │   ├── repositories/       # 任务记忆持久化（JSON / SQLite）
│   │   ├── shared/             # 共享配置 & 日志
│   │   ├── tools/              # PDF 解析 & 合规/术语工具
│   │   ├── tasks/              # 异步任务
│   │   ├── utils/              # 工具函数
│   │   ├── config.py           # 全局配置（pydantic-settings）
│   │   └── database.py         # SQLAlchemy engine + init_db
│   ├── data/                   # 运行数据（compliance/profiles/terminology）
│   ├── tests/                  # 测试套件（pytest）
│   ├── main.py                 # FastAPI 入口
│   ├── init_db.py              # 数据库初始化脚本
│   └── requirements.txt
├── frontend/                   # React 前端
│   ├── src/
│   │   ├── components/         # UI 组件
│   │   │   ├── AICreation/     # AI 对话面板（核心交互）
│   │   │   ├── editor/         # 表格/模板编辑器 + 布局定义
│   │   │   ├── common/         # 通用组件（PDF/Markdown/Diff）
│   │   │   ├── MaterialLibrary/# 素材库（文件树/列表/范围选择）
│   │   │   └── workspace/      # 工作区抽屉
│   │   ├── stores/             # Zustand 状态
│   │   ├── services/           # API 客户端
│   │   ├── hooks/              # 自定义 Hooks
│   │   ├── pages/              # 页面（Workspace / Profile）
│   │   ├── utils/              # 工具函数
│   │   ├── types/              # TypeScript 类型定义
│   │   └── db/                 # Dexie (IndexedDB)
│   ├── vite.config.ts
│   └── package.json
├── deploy/                     # 部署脚本（Kylin V10 / MindIE）
├── docs/                       # 架构文档 & 分析报告
├── PRPs/                       # 需求/进度/修复记录
├── scripts/                    # 生成/验证脚本
├── tests/                      # 端到端测试
├── CLAUDE.md                   # 项目策略 & 技术栈
├── ARCHITECTURE.md             # 唯一架构源
├── CONTRIBUTING.md             # 协作规范
├── ONBOARDING.md               # 新人上手
├── DEV-LOG.md                  # 进度 & 历史决策
└── VISION.md                   # 项目北极星
```

---

## 4. 后端架构详解

### 4.1 应用入口与配置

#### 入口：`backend/main.py`

FastAPI 应用实例，核心职责：

- **生命周期管理** (`lifespan`)：启动时初始化数据库 (`init_db`)、加载全局工艺知识图谱 (`init_craft_kg`)、启动 PDF 解析队列管理器 (`pdf_queue_manager`)、检查 LLM/VLM 连通性；关闭时停止 PDF 服务。
- **中间件**：CORS（允许 `localhost:3000/3001/3003/3004`）、请求日志中间件（记录所有 HTTP 请求/响应）。
- **路由注册**：挂载 18 个 API Router，涵盖 Agent 对话、创作管理、PDF 处理、导出、画像等。
- **静态文件**：挂载 `/static/data` 访问上传图片；生产模式下（`frontend/dist` 存在）后端单端口 serve 前端 SPA。
- **全局异常处理**：捕获 `RequestValidationError`，返回 422 + 错误详情。
- **服务器**：`uvicorn` 运行，`DEBUG` 模式开启热重载。

#### 配置：`backend/app/config.py`

`Settings(BaseSettings)` — pydantic-settings 驱动，`.env` 加载，全局单例 `settings`。关键配置项：

| 分类 | 配置项 | 说明 |
|------|--------|------|
| 应用 | `HOST`/`PORT`/`DEBUG`/`SQL_ECHO` | 默认 `127.0.0.1:8000`，`DEBUG` 控制 uvicorn reload |
| 路径 | `DATA_DIR`/`DB_DIR`/`DOCUMENTS_DIR` 等 | 统一存储于 `backend/data/` 下，import 时自动创建 |
| 数据库 | `DATABASE_URL` | SQLite `craftdoc.db` |
| LLM | `DASHSCOPE_API_KEY`/`DASHSCOPE_BASE_URL`/`MODEL_TIER_SIMPLE`/`MODEL_TIER_COMPLEX` | 双层模型路由：simple(qwen-turbo) / complex(qwen-plus) |
| 本地部署 | `DASHSCOPE_BASE_URL_SIMPLE/COMPLEX` | 本地 MindIE 地址（端口 1028） |
| Thinking | `THINKING_ENABLED_SIMPLE/COMPLEX`/`THINKING_BUDGET_*` | simple 关闭推理预算省 TPM，complex 开启 |
| MinerU | `MINERU_BACKEND`/`MINERU_VLM_MODEL`/`MINERU_VL_SERVER` | PDF VLM 解析后端配置 |
| 记忆 | `MEMORY_DIR`/`MEMORY_MAX_TOKENS`/`MEMORY_KEEP_COUNT` | 会话记忆系统 |
| 项目状态 | `PROJECT_STATE_DIR`/`STATE_TASK_MAX_CHARS` | 会话接续滚动状态 |
| Repository | `REPOSITORY_TYPE` | `json`（默认）/ `sqlite` |

另有 `backend/app/shared/config.py` 提供向后兼容的常量（`CSV_EXPORT_CONFIG`/`PDF_PARSER_CONFIG`/`MINERU_CONFIG` 等），动态从 `settings` 取值。

---

### 4.2 Agent 系统（核心）

> **架构层文件**：`backend/app/agents/**`，改动需独立 `[architecture]` PR + 强制 review。

#### 4.2.1 注册表与协议 (`agents/core/`)

- **`registry.py`** — 三个装饰器注册表：
  - `ToolRegistry`：`@register(tool_name)` → `get/create/list_tools`
  - `AgentRegistry`：`@register(agent_name)` → `get/create/list_agents`
  - `WorkflowRegistry`：预注册 4 个默认 workflow（`full_edit`/`quick_edit`/`review_only`/`proofread_only`），但实际调度不走 workflow 编排（已确认为死代码，2026-07-30 清理）
- **`protocols.py`** — `@runtime_checkable` Protocol：
  - `ToolProtocol`：`name`/`description` + `async execute(input_data, context) -> Dict`
  - `AgentProtocol`：`name`/`description`/`tools` + `async process(task, context) -> Dict`

#### 4.2.2 基础 Agent (`agents/base_agent.py`)

```
BaseAgent(ABC)
  ├── __init__(config) → _init_tools()  # 通过 ToolRegistry.create 解析工具
  ├── use_tool(tool_name, input_data, context)  # 分发到 tool.execute
  ├── process(task, context) [abstract]
  └── execute(input_data, context)  # 适配器，包装为标准 {success, result}
```

#### 4.2.3 编排器 (`agents/orchestrator/`)

**`orchestrator.py` — `ProcessOrchestrator`**（系统核心控制器）：

- **构造**：装配 `ProcessStateMachine`、`DialogManager`、`IntentRecognizer`、`TaskDecomposer`、`InfoAssessor`、`InteractionManager`；调用 `discover_agents()` + `_init_agents()` 实例化 writing/proofread/review agent；`_load_writing_preferences()` 加载领域画像。

- **主入口 `process_intent(user_input, context, ...)`**：
  1. 解析/创建任务，ERROR 状态自动恢复到 IDLE
  2. `_build_context` 合并对话上下文 + 任务元信息 + 文档上下文
  3. 状态机 → `INTENT_RECOGNITION`
  4. **generation_mode 快捷路径**（`generate`/`fill`）跳过 LLM 意图识别，直接路由到 `_handle_draft_complete`
  5. `IntentRecognizer.recognize` → 若 `draft_complete` → `_handle_draft_complete`
  6. `TaskDecomposer.decompose` → 逐任务 `_dispatch_to_sub_agent` → 结果聚合 → `COMPLETION`

- **任务分发 `_dispatch_to_sub_agent(task)`**：`agent_mapping` 映射 task_type → 功能 Agent：
  - `writing/edit/fill/format/generate/document_generation` → **WritingAgent**
  - `proofread/terminology_alignment/data_validation` → **ProofreadAgent**
  - `review/compliance_check/rationality_check/risk_assessment` → **ReviewAgent**

- **`_handle_draft_complete`（旗舰流程）**：初稿分析 → 加载画像 + 章节索引 → 计算素材状态 → 加载初稿内容 → LLM 检测缺失章节 → 抽取每章源文本 → 匹配 `SectionSchema` → 加载模板构建 `chapter_template_map` → 状态 `USER_CONFIRMATION` → `PAUSED` 等待用户确认

- **`_execute_chapters_parallel`（章节并行生成）**：
  - 按知识库索引解析章节顺序
  - 支持**分阶段生成**（Phase 1 骨架 → Phase 2 流程依赖 → Phase 3 独立）
  - 每阶段 `asyncio.gather` 并行
  - source-driven 直注：G25a `assembly_steps`、G22a `process_card_steps`、G5a `file_references`、G4a `doc_catalog`
  - 生成后 `_derive_strong_node` 倒推列表章节（G10a/G12a/G14a/G18a），带溯源过滤防臆造
  - review-retry 循环：每章跑 `ReviewAgent._check_output_quality`，失败重试一次

**`state_machine.py` — `ProcessStateMachine`**：
- 14 个状态：`IDLE → INTENT_RECOGNITION → INFO_ASSESSMENT/INFO_COLLECTION → ... → TASK_DECOMPOSITION → TASK_EXECUTION → RESULT_AGGREGATION → COMPLETION`
- 特殊状态：`DRAFT_ANALYSIS`（初稿分析）、`PAUSED`（等输入）、`ERROR`（自恢复 IDLE）
- `VALID_TRANSITIONS` 显式定义合法转换；支持内存模式与 Repository 持久化模式

**`intent_recognizer.py` — `IntentRecognizer`**：
- `IntentType` 枚举（10 类：CREATE_DOCUMENT/EDIT_DOCUMENT/REVIEW_DOCUMENT/GENERATE_DOCUMENT/PARSE_PDF/SEARCH_KNOWLEDGE/ALIGN_TERMINOLOGY/CHECK_COMPLIANCE/EXPORT_TO_PDM/DRAFT_COMPLETE/UNKNOWN）
- `recognize()`：预处理 → `_detect_draft_complete`（复合模式最高优先）→ `_classify_with_llm`（LLM 分类，fail-soft 退关键词正则）→ `_extract_entities` → `_calculate_confidence`

**`task_decomposer.py` — `TaskDecomposer`**：
- `TaskType` 枚举（8 类）+ `INTENT_TO_TASKS` 映射
- `decompose(intent)` → `_customize_tasks`（基于实体/置信度）→ `_add_dependencies`（线性链）→ `_add_task_parameters`

**其他编排组件**：
- `dialog_manager.py`：`DialogManager` 管理交互历史（max 100，Repository 持久化）
- `info_assessor.py`：`InfoAssessor` 评估信息完整性（高/中/低优先级缺失项）
- `interaction_manager.py` + `interaction_models.py`：交互消息管理（InfoRequest/Preview/Confirmation/Progress/Result/Error）
- `states/`：状态模式处理器（base/editing/generation/review_state）

#### 4.2.4 功能 Agent (`agents/functional/`)

**`writing_agent.py` — `WritingAgent`**（注册名 `"writing"`）：
- `ACTION_TYPES = ["edit", "fill", "format", "generate"]`
- `process(task, context)`：有预加载上下文 → 直接用；否则 `_search_knowledge`（HierarchicalContext 关键词检索）→ 分发 `_do_edit`/`_do_fill`/`_do_format`/`_do_generate`
- **`_do_template_fill`（模板填充核心）**：
  - 按 `fill_type`（structured/unstructured）分组列
  - 结构化字段走 `structured_extractor.extract_structured_fields`（无 LLM）
  - 特殊 source-driven 路径：G25a（`assembly_steps` 直填 + `_generate_g25a_per_row_parallel` 并行 `Semaphore(4)` + 3 次重试 + 完成度核对）、G22a/G5a/G4a
  - LLM 只生成非结构化 slot，返回 `[{row, slot, value}]`
  - `merge_structured_with_unstructured` 合并
  - 返回 `ChapterData`（filled_data/left_data/right_data/flow_steps/field_values）
- **`derive_list_strong`** + `_derive_list_from_upstream` + `_provenance_filter`（溯源过滤，丢弃无出处条目防臆造）
- `_quick_check_output` 守卫（占位符/裸数字/模糊用语检测）
- `handle_feedback`/`_incremental_modify`/`rollback`/`get_version_history`（迭代修改支持）

**`review_agent.py` — `ReviewAgent`**（注册名 `"review"`，tools=`["compliance_checker"]`）：
- `CHECK_TYPES = ["compliance", "rationality", "risk", "output_quality", "all"]`
- 有 `profile` → `ReviewService.review(content, profile)`（基于画像原则）
- 无 profile → fallback：`_check_compliance`（工具）、`_check_rationality`（数值范围/工序顺序/KB 比对）、`_check_risk`（关键词严重度 + 安全措施）、`_check_output_quality`（重复标题/AI 元评论/工序号断档/签名域/表格结构校验）

**`proofread_agent.py` — `ProofreadAgent`**（注册名 `"proofread"`，tools=`["terminology_mapper"]`）：
- `CHECK_TYPES = ["terminology", "data", "format", "all"]`
- `_check_terminology`（terminology_mapper 工具，置信度 < 0.9 标记）、`_check_data`（数字格式/占位符）、`_check_format`（表格标签平衡/段落长度/标题层级）
- `_generate_corrections` + `_apply_corrections`（术语自动修正）

#### 4.2.5 Agent 工具 (`agents/tools/`)

搜索/图片类工具：`aliyun_search.py`、`bing_image_search.py`、`image_search.py`、`local_search.py`、`web_search.py`、`pdf_table_extractor.py`

---

### 4.3 服务层 (Services)

> `backend/app/services/` — 40+ 服务文件，业务逻辑核心层。

#### LLM 服务

- **`llm_service.py` — `QwenLLMService`**（全局单例 `llm_service`）：
  - OpenAI 兼容异步客户端，双层路由：`_complex_client`（complex tier）/`_simple_client`（simple tier）
  - 公开 API：`generate_text(prompt, tier)`、`generate_with_messages(messages, temperature, max_tokens, tier, max_retries=2)`、`generate_with_messages_stream`（流式，yield `{type:"thinking"|"content", content}`）
  - `_generate_with_retry` 韧性包装（使用 `llm_errors` 分类 + 重试退避 + 溢出裁剪）
  - `check_llm_reachable` 同步探活（urllib `/models`）
  - `get_llm(tier)` 返回 LangChain `ChatOpenAI`

- **`llm_errors.py`**：
  - `LLMErrorClass` 枚举（7 类：TIMEOUT/CONNECTION_REFUSED/CONTEXT_OVERFLOW/EMPTY_REPLY/JSON_PARSE_FAIL/RATE_LIMIT/UNKNOWN）
  - `classify_exception`/`classify_error_text`（正则 + isinstance 分类）
  - `should_retry`（CONTEXT_OVERFLOW 不盲重试）、`trim_messages_for_overflow`（裁最长 user 消息，不动 system）
  - `USER_FACING_MESSAGES` 中文可读映射

#### 上下文与检索

- **`hierarchical_context.py` — `HierarchicalContext`**（全局单例 `hierarchical_context`）：
  - **5 层 JIT 检索 + Progressive Disclosure**：
    - L0 元信息索引（~500 tok）
    - L1 表格索引（~2000 tok）
    - L2 按需表格 HTML
    - L3 全局关键词检索（jieba 分词 + 同义词扩展）
    - L3.5 知识图谱检索（craft_kg）
    - L4 记忆
  - `build_context(query, session_id, max_tokens, mode, project_id)` — 主入口
  - 章节级抽取函数：`extract_assembly_steps`（G25a）、`extract_process_steps`（G19a）、`extract_process_card_steps`（G22a）、`extract_file_references`（G5a）、`extract_doc_catalog`（G4a）、`extract_assembly_overview`（G25a 说明）、`extract_reference_methods`（套用素材）
  - 缓存：`_meta_cache`/`_table_index_cache`/`_documents_cache`（TTL 30s），`invalidate_cache`

- **`knowledge_graph.py` — `KnowledgeGraph`**（基于 `networkx.DiGraph`）：
  - 节点类型：process_step/material/tool/parameter/spec
  - 边类型：sequential/requires/depends_on/references/used_in
  - `build_from_triples`（解析 `{s,r,o}` 三元组）、`merge_from`（累加幂等）、`expand_context`（BFS）
  - 全局单例 `craft_kg`，持久化 `data/knowledge_graph.json`，启动加载 `init_craft_kg`

- **`project_state_service.py` — `ProjectStateService`**：
  - 项目级滚动工作状态（session 接续）
  - 存储 `data/project_state/{project_id}.json`（7 字段：current_task/focus_chapters/recent_intents/user_preferences/last_session_id/updated_at/project_id）
  - 原子写（tmp + os.replace + threading.Lock）
  - `render_context_block` 生成 `## 项目当前工作状态` 提示块

- **`memory_service.py` — `MemoryService`**：
  - 追加式 markdown 会话摘要
  - `save_summary_async`（后台线程 fire-and-forget LLM 摘要）
  - `load_relevant_memory`（语义排序，fallback 到最近）
  - `get_project_memory_service(project_id)` 按项目分域缓存

#### 文档处理

- **`document_processor.py` — `DocumentProcessor`**（单例）：
  - 全流程：PDF/Word → 图片（PyMuPDF @3x）→ 批量 VL OCR（`vl_service.ocr_pages_batch_mineru`）→ DB 记录 → `content_list_v2.json`/`document.html`/`index.json` 生成 → 知识抽取
  - `process_document_from_task` 供队列调用

- **`vl_service.py`**：VLM OCR 后端（mineru/qwen/qwen_local），`ocr_pages_batch_mineru`

- **`pdf_queue_manager.py`**：PDF 解析任务队列（单队列），`PDFTask` 数据类
- **`pdf_watcher_service.py`**：文件系统监听（watchdog），自动触发 PDF 解析

#### 生成与编辑

- **`content_assembler.py`**：`assemble_content_json`/`generate_content_html`/`save_content_files` — 结构化内容组装
- **`draft_service.py` — `DraftService`**：初稿管理（上传/获取/版本/回滚/diff），快照式更新
- **`review_service.py` — `ReviewService`**：统一审查引擎（universal/sensitive_words/principles/knowledge_data/mandatory_params/preferences 多维检查）
- **`structured_extractor.py`**：`extract_structured_fields`/`merge_structured_with_unstructured`（无 LLM 结构化抽取）
- **`template_loader.py`**：`load_template`/`match_chapter_by_title`/`get_fillable_slots`/`get_generation_phases`/`get_editor_chapters`
- **`section_schemas.py`**：`SectionSchema`/`match_section_schema`/`build_schema_prompt`
- **`context_service.py` — `ContextService`**：加载 Profile/Template/Examples，`build_context`
- **`feedback_learner.py`**：`learn_from_edits`（LLM 归纳编辑 diff → 产 Principle 规则，三层 fail-soft）

#### 导出

- **`csv_export_service.py`**：pandas CSV 导出（UTF-8-sig BOM），`export_tables(format in {csv, excel, xlsx})`
- **`excel_export_service.py`**：多 Sheet Excel 导出
- **`word_export_service.py`**：Word 文档导出
- **`template_pdf_export.py`**：模板 PDF 导出

#### 其他关键服务

| 服务 | 职责 |
|------|------|
| `context_builder.py` | 合并对话/任务/文档上下文 |
| `context_engineering.py` | Embedding/相似度计算 |
| `document_indexer.py` | 文档索引构建（chapter_index.json） |
| `document_profile_learner.py` | 文档画像学习（triples 抽取 → craft_kg） |
| `knowledge_search.py` | `KnowledgeSearchService.find_material_by_code`（G18a enrich） |
| `material_classifier.py` | LLM 推断物料专业分类 |
| `image_relevance_service.py` / `image_save_service.py` | 图片相关性/保存 |
| `knowledge_extractor.py` / `standard_extractor.py` | 知识/标准抽取（QJ903） |

---

### 4.4 数据模型与存储

#### SQLAlchemy ORM (`models/database.py`)

所有模型继承 `Base`，SQLite `craftdoc.db`。核心表：

| 表 | 说明 | 关键字段 |
|----|------|----------|
| `MaterialFolder` | 素材文件夹（自引用树） | name, parent_id, sort_order |
| `Material` | 素材文档 | name, material_type, folder_id, **model**, **specialty**（检索穿透维度） |
| `MaterialPage` | 文档页 | material_id, page_number, image_path |
| `Figure` | 图片 | material_id, file_path, caption, page_number |
| `MaterialCatalog` | 物料目录 | category/name/brand/model/**standard_code**（G18a exact 查键）/spec/**tech_params**(JSON)/specialty |
| `ProcessStep` | 工序步骤 | doc_id/step_name/step_order/parent_step_id/description/specialty |
| `Standard` | 标准 | code/title/category/content_json |
| `StandardClause` | 标准条款 | standard_id/clause_number/requirement/clause_type/applies_to |
| `StepMaterial` | 工序-物料关联 | step_id/catalog_id/usage_type/quantity |
| `StepTool` | 工序-工具关联 | step_id/catalog_id |
| `CreationProject` | 创作项目 | name, content(HTML), material_ids(JSON) |
| `DraftDocument` | 初稿文档 | title/file_path/file_type/parsed_content/content/status/project_id |
| `DraftVersion` | 初稿版本 | draft_id/snapshot_content/snapshot_source |
| `NodeDocument` | 节点文档 | session_id/node_name/node_type/document_data(JSON)/state |
| `ConversationSession` | 对话会话 | session_id/project_id/current_step/state_data(JSON) |
| `Annotation` / `Citation` / `WebImage` / `UploadedImage` | 注释/引用/网络图片/上传图片 | — |

**关联关系**：`ProcessStep ←StepMaterial/StepTool→ MaterialCatalog`

#### Pydantic 模型

| 文件 | 内容 |
|------|------|
| `models/task_memory.py` | 任务记忆：`TaskMeta`/`TaskState`/`Message`/`Conversation`/`Decision`/`TaskContext` + `TaskStatus`/`ProcessState` 枚举 |
| `models/profile.py` | 领域画像：`Profile`（writing/review/knowledge/principles/preferences/triples/graph）+ `Principle`/`Preference`/`ConditionGroup`/`WritingPreferences` |
| `models/table_models.py` | 表格抽取：`ExtractedTable`/`TableMetadata`/`ParserType`/`TableType` 枚举 |
| `models/schemas.py` | `BaseResponse` + legacy `TaskPlan` |

#### 模型注册 (`models/model_registry.py`, `model_service.py`)

- `ModelRegistry`：加载 `model_config.json`，注册 deepseek_r1/bge_embedding/bge_rerank
- `ModelService`：`get_text_generation_model`/`get_embedding_model`/`get_rerank_model`
- 接口抽象：`model_interface.py`（`TextGenerationModel`/`EmbeddingModel`/`RerankModel` ABC）

#### 文件系统数据存储

| 路径 | 内容 |
|------|------|
| `backend/data/documents/{material_id}/` | `index.json`（元信息）/ `content.html`（MinerU 解析）/ `content.json`（结构化）/ `chapter_index.json` / `vlm/` |
| `backend/data/project_state/{project_id}.json` | 项目滚动工作状态 |
| `backend/data/memory/projects/{project_id}/` | 项目级会话记忆（回退全局 `data/memory/`） |
| `backend/data/knowledge_graph.json` | 全局工艺知识图谱 |
| `backend/data/profiles/` | 领域画像（assembly/welding/coating.json） |
| `backend/data/tasks/{task_id}/` | 任务记忆（meta/state/conversation/decisions.json + artifacts/） |
| `backend/data/compliance/` | 合规规则（rules.json/sensitive_words.json） |
| `backend/data/terminology/` | 术语标准（standard_terms.json） |

---

### 4.5 API 路由层

> `backend/app/api/` — 18 个 Router 文件，挂载于 `/api` 前缀下。

| Router | 前缀 | 主要端点 | 说明 |
|--------|------|----------|------|
| `agent.py` | `/api/agent` | `POST /generate-stream`（SSE 生成主链）、`/chat`、`/start-conversation`、`/reply-question-stream`、`/select-plan`、`/confirm-materials`、`/apply-suggestions`、`/export/template-pdf`、`GET /task/{task_id}`、`GET /material-report/{session_id}` | **核心对话与生成 API**（~1800 行） |
| `creation.py` | `/api/creation` | 项目 CRUD、素材管理、`/generate-draft`、`/comprehensive-search`、`/ask`、版本管理、素材索引 | 创作项目管理 |
| `process_documents.py` | `/api/process-documents` | `GET /`、`/{doc_id}/extracted`、`POST /{doc_id}/extract`、`/{doc_id}/tables/{type}`、`POST /{doc_id}/export-csv` | 工艺文档处理 |
| `pdf_status.py` | `/api/pdf` | `GET /status`、`/tasks`、`POST /tasks`、watcher 控制 | PDF 队列管理 |
| `task.py` | `/api/tasks` | 任务记忆 CRUD、`/conversation/continue`、`POST /proofread`、`POST /review` | 任务与审校 |
| `draft.py` | `/api/drafts` | `POST /upload`、`GET /`、版本管理、回滚、diff、导出 | 初稿管理 |
| `profile.py` | `/api/profile` | `GET/PUT/DELETE /{domain}`、`POST /{domain}/learn`、`learn-file`、`learn-batch`（SSE）、`learn-feedback`、知识/原则/偏好 CRUD | 用户画像 |
| `materials.py` | `/api` | `/materials/{mid}/summary`、`/materials` | 素材库 |
| `export.py` | `/api/export` | `POST /word`、`/content-pdf`、`/content-word` | 文档导出 |
| `document.py` | `/api/documents` | `GET /`、`/{doc_name}/tables`、`/{doc_name}/markdown` | 解析文档访问 |
| `context.py` | `/api/context` | `GET /template`、`/examples`、`POST /build` | 上下文构建 |
| `knowledge.py` | — | 物料/标准搜索、知识抽取 | 知识库 |
| `assistant.py` | `/api/assistant` | `/suggestions`、`/quick-actions`、`/contextual-ask` | 智能助手 |
| `deepseek.py` | `/api/deepseek` | `/chat`、`/generate-document`、`/align-terminology`、`/check-compliance` | DeepSeek LLM |
| `annotation.py` | `/api/creation` | 注释管理 | — |
| `web_image.py` | `/api/web-images` | 网络图片管理 | — |
| `process.py` | `/api/process` | `/clean-text`、`/extract-entities` | 智能处理 |
| `node_documents.py` | `/api/node-documents` | 节点文档 CRUD | — |

---

### 4.6 工具层 (Tools)

> `backend/app/tools/` — PDF 解析与合规/术语工具。

#### PDF 解析

- **`pdf_parser.py` — `PDFParser`**：双复杂度入口。`parse(pdf_source, ...)` → `ParserSelector` 选择 SIMPLE(PyMuPDF) 或 COMPLEX(MinerU-VLM)
- **`parser_selector.py` — `ParserSelector`**：`select_parser()` → 有表格 + MinerU 可用 → COMPLEX；否则 SIMPLE
- **`table_extractors/base_extractor.py`**：`BaseTableExtractor(ABC)`，抽象 `extract_tables()`
- **`table_extractors/mineru_extractor.py` — `MinerUTableExtractor`**：MinerU TableFormer 高精度（合并单元格/跨页），线程池异步，fallback pdfplumber
- **`table_extractors/pdfplumber_extractor.py` — `PDFPlumberTableExtractor`**：pdfplumber 表格抽取（线条/文本策略自动检测）

#### 合规与术语

- **`compliance_checker.py` — `ComplianceChecker`**：加载 `DATA_DIR/compliance/*.json` 规则，`check_document()` → 逐标准检查，返回 issues/warnings
- **`terminology_mapper.py` — `TerminologyMapper`**：加载 `DATA_DIR/terminology/*.json`，`map_terms()` 精确 + 模糊匹配（SequenceMatcher）

#### 其他工具

`table_merger.py`、`table_validator.py`、`table_post_processor.py`、`process_document_extractor.py`、`compliance_tool.py`、`terminology_tool.py`

---

### 4.7 Repository 模式

> `backend/app/repositories/` — 任务记忆持久化抽象。

- **`protocols.py`**：`TaskMemoryRepository(Protocol)` — 定义完整契约（create_task/get_meta/update_state/get_messages/add_message/get_decisions/get_context/list_tasks/delete_task 等）
- **`json_repository.py` — `JsonFileRepository`**（默认）：零依赖单机调试。每任务目录 `data/tasks/{task_id}/`，含 `meta.json`/`state.json`/`conversation.json`/`decisions.json` + `artifacts/`。原子 JSON 写。
- **`sqlite_repository.py` — `SQLiteRepository`**：部署用骨架（并发访问/ACID），方法暂为 `NotImplementedError`
- **`factory.py`**：`create_repository(repo_type)` + `get_repository()`（读 `settings.REPOSITORY_TYPE`，默认 json）

---

## 5. 前端架构详解

### 5.1 应用入口与构建

- **`index.html`**：最小壳，`lang="zh-CN"`，挂载 `#root`
- **`src/main.tsx`**：`<App />` 包裹于 `React.StrictMode` + antd `ConfigProvider`（`zhCN` locale）
- **`src/App.tsx`**：`ThemeProvider` + `BrowserRouter`，两条路由：
  - `/` → `WorkspacePage`（主编辑工作台）
  - `/profile` → `ProfilePage`（用户画像管理）
- **`vite.config.ts`**：
  - `@` alias → `./src`
  - Dev server 端口 3000，代理 `/api` → `localhost:8000`、`/ws` → `ws://localhost:8000`
  - 构建：`dist/`，sourcaps 开启，手动分包 `react-vendor` + `antd-vendor`

### 5.2 状态管理 (Zustand)

**`stores/creationStore.ts` — `useCreationStore`**（主 store，`persist` → localStorage `creation-storage-v2`）：
- `projects: Record<number, ProjectState>` — 每项目编辑器内容 + 对话 sessions
- `editorTemplateData: StructuredDocument | null` — 模板编辑器状态（切换 markdown/table 模式）
- `originalTemplateData: TemplateSection[] | null` — diff 基线快照（反馈学习）
- `editHistory: EditRecord[]` — 撤销栈（max 50）
- PDF 状态：`pdfDocuments`/`currentPDFDocument`/`pdfLoading`/`pdfDrawerVisible`
- Session 操作：`createNewSession`/`deleteSession`/`switchSession`/`updateSessionMessages`

**`stores/pdfDocumentStore.ts`** — `usePdfDocumentStore`：最小 stub（tables/selectedTables），待 WASM PDF viewer。

### 5.3 服务与 API 层

- **`services/apiClient.ts`**：中央 axios 实例（`baseURL: '/api'`，5 分钟超时），响应拦截器提取错误 + antd message 提示
- **`services/aiService.ts`**：封装 `/api/assistant/*`，SSE 流式处理（`response.body.getReader()` + `data:` 行解析）
- **`services/conversationService.ts`**：对话生成服务，类型定义 `Question`/`PlanOption`/`MaterialItem`/`ReviewIssue`/`SSEEvent` 联合类型
- **`services/pdfService.ts`** — `PDFService` 单例：`/api/process-documents/*`
- **`services/csvExportService.ts`** — `CSVExportService` 单例：CSV/Excel 导出
- **`services/draftApi.ts`** — `DraftApiService`：初稿生命周期

### 5.4 核心组件

#### AICreation（AI 对话面板）

| 组件 | 职责 |
|------|------|
| **`AIChatPanel.tsx`** | **核心交互面板**。直接 `fetch` 调用 `/api/agent/generate-stream` 等 SSE 端点。处理丰富 SSE 协议：`mode`/`thinking`/`content`/`pending_questions`/`plan_options`/`improvement_solutions`/`agent_call`/`collaboration`/`progress`/`result`/`warning`/`error`。支持中止/停止、生成模式（generate/fill/chat）、选区引用贴入、临时文件上传、审校按钮、模板结果交接 |
| `AgentCollaborationView.tsx` | Agent 调用历史 + 协作调用栈渲染 |
| `ConversationPanel.tsx` | 步骤式向导（需求分析→规划→素材确认→生成→评审→完成） |
| `EditorPanel.tsx` | 旧版文本编辑器 + diff 渲染 |
| `MaterialsPanel.tsx` | 项目素材列表 + 多选 + 插入编辑器 |
| `PlanOptionCard.tsx` / `SolutionCard.tsx` / `SolutionList.tsx` | 规划/改进方案卡片 |
| `MaterialReportView.tsx` | 素材报告（可选/优先级/相关性） |
| `ReviewSuggestionPanel.tsx` | 审查问题面板（严重度标签 + apply） |
| `QuestionCard.tsx` / `QuestionList.tsx` / `TodoList.tsx` | 问题渲染 / 待办列表 |

#### editor（表格/模板编辑器）

| 组件 | 职责 |
|------|------|
| **`ProcessTableEditor.tsx`** | 渲染 `TemplateSection` 为工艺表格。`contentEditable` 单元格、行增删、垂直合并/拆分（`mergeUtils`）、AI 填充高亮、DOM→数据回写 |
| **`TemplateContentEditor.tsx`** | 顶层模板编辑器，遍历 `TemplateSection[]` 委托 `ProcessTableEditor` |
| `HtmlTableEditor.tsx` | VLM 提取的 HTML 表格编辑 |
| `mergeUtils.ts` | 纯函数：垂直合并状态分类/查找/插入/删除/合并/拆分 |
| `processDocumentLayouts.ts` | 布局注册表，聚合各章节布局（G4a/G5a/G10a/B12a/G12a/G14a/G18a/G22a/G25a），`getLayout()` 剥离会签列 |
| `layouts/*.ts` | 各章节布局定义（colspan/rowspan 分组表头） |

#### common（通用组件）

| 组件 | 职责 |
|------|------|
| `MarkdownRenderer.tsx` | 手写 Markdown 渲染器（标题/图片/链接/粗斜体） |
| `MarkdownTiptapEditor.tsx` | Tiptap 编辑器（StarterKit + Placeholder + Image），MD↔HTML 转换，集成 `useSelection` + `useAIStream` + `AISuggestionBar` |
| `ProcessContentView.tsx` | 混合模式渲染（卡片 + 散文分段） |
| `InlineDiff.tsx` | 行级 diff 查看器 + `FloatingConfirmBar` |
| `ProcessCard.tsx` | 工序步骤结构化卡片 |
| `PDFViewer/WasmPDFViewer.tsx` | pdfjs-dist canvas 渲染（缩放/旋转/全屏/下载） |
| `PDFViewer/PDFTableViewer.tsx` | 提取表格查看 |
| `DocumentList/` | 文档列表组件 |

#### MaterialLibrary（素材库）

| 组件 | 职责 |
|------|------|
| `FolderTree.tsx` | 文件树（Ant Tree + 右键菜单：创建/重命名/删除/批量学习） |
| `FileList.tsx` | 文件列表（类型图标/解析状态标签/右键菜单） |
| `KnowledgeScopeSelector.tsx` | 知识库范围选择（复选框组，localStorage 持久化） |

#### workspace（工作区抽屉）

| 组件 | 职责 |
|------|------|
| `MaterialDrawer.tsx` | 集成素材库面板（文件管理/上传/知识库范围三 Tab） |
| `SettingsDrawer.tsx` | 设置表单（主题/自动保存/语言） |
| `PDFViewerDrawer.tsx` | PDF 工艺文档抽屉 |

### 5.5 Hooks

| Hook | 职责 |
|------|------|
| `useAIStream.ts` | 流式生成 Hook（状态机 idle/streaming/error/done），POST SSE，自动重试（指数退避 max 3 次），`AbortController` 取消 |
| `useSelection.ts` | Tiptap 选区追踪（防抖 150ms），返回选区文本/坐标/可见性 |
| `useSuggestions.ts` | AI 建议获取（防抖 300ms + AbortController 取消），fallback 默认建议 |

### 5.6 工具函数与类型

#### utils

| 文件 | 职责 |
|------|------|
| `markdownConverter.ts` | Markdown↔HTML（markdown-it + turndown），图片 URL 解析/剥离 |
| `processCardParser.ts` | Markdown → `ContentSegment[]`（card/prose），工序块正则识别 |
| `templateDiff.ts` | `diffTemplateSections()` → `{edits, row_changes}`（反馈学习） |
| `templateTransform.ts` | `structuredDocToSections()` 后端 StructuredDocument → 前端 TemplateSection[] |
| `htmlTableParser.ts` | VLM HTML 解析（`## 第 N 页` 分页，行分类 header/data/signature） |
| `wasm_loader.ts` | PDF WASM 加载器（当前 mock） |
| `crypto.ts` | Web Crypto（AES-GCM 加密/PBKDF2 派生/设备指纹） |

#### types

| 文件 | 内容 |
|------|------|
| `template.ts` | `TemplateColumn`/`TemplateChapter`/`ChapterData`/`StructuredDocument`/`TemplateSection`（content_type: table/dual_table/flow_chart/fields/text）/`CellMerge` |
| `process.ts` | `ProcessOperation`/`QualityRequirement`/`ProcessDocument` |

#### 其他

- `contexts/ThemeContext.tsx`：`ThemeProvider`（dark/light，CSS 变量注入，localStorage 持久化）
- `db/index.ts`：`CraftDocumentDatabase extends Dexie`（IndexedDB，4 stores：materials/projects/knowledgeCards/editorHistory）— 旧本地优先层
- `styles/design-tokens.ts`：设计系统（colors/radius/spacing/typography/shadows/animation/breakpoints/zIndex）

---

## 6. 端到端生成流程

```
用户输入 → POST /api/agent/generate-stream
  │
  ├─ generation_mode = generate/fill → 快捷路径（跳过 LLM 意图识别）
  │    → _handle_draft_complete
  │
  └─ 常规路径
       → Orchestrator.process_intent
       → IntentRecognizer.recognize (LLM 分类, fail-soft 关键词)
       → TaskDecomposer.decompose
       → _dispatch_to_sub_agent (task_type → 功能 Agent)
       → SSE 事件流 (mode/progress/content/content_section/result/warning/error)
```

**Draft-complete 旗舰流程**（`_handle_draft_complete` → `_execute_chapters_parallel`）：

```
1. 初稿分析：加载画像 + 章节索引 + 初稿内容
2. 检测缺失章节（LLM 或 force_all_chapters）
3. 抽取每章源文本 (get_chapter_content / extract_*)
4. 匹配 SectionSchema + 加载模板 → chapter_template_map
5. 状态 → USER_CONFIRMATION → PAUSED（等用户确认）
6. 用户确认 → _execute_chapters_parallel:
   a. 分阶段生成（Phase 1 骨架 → Phase 2 流程依赖 → Phase 3 独立）
   b. 每阶段 asyncio.gather 并行 WritingAgent 任务
   c. source-driven 直注（G25a/G22a/G5a/G4a）
   d. _derive_strong_node 倒推列表章节（溯源过滤防臆造）
   e. review-retry 循环（每章 ReviewAgent 质检，失败重试一次）
7. content_assembler 组装 content.json/content.html
8. DraftService.update_content（快照式更新）
9. SSE result 事件 → 前端 AIChatPanel 渲染
```

**前端渲染**：

```
AIChatPanel → SSE → 
  ├─ template_data → creationStore.editorTemplateData → TemplateContentEditor → ProcessTableEditor
  └─ markdown content → MarkdownTiptapEditor / ProcessContentView
```

**3 条检索路径**：

| 路径 | 角色 | 用途 |
|------|------|------|
| **source-driven 直注** | 主路径 | 有源章节（extract 直填，不走检索） |
| **HierarchicalContext** | 兜底 | 无源章节 / chat QA（关键词 + filter） |
| **material_catalog**（KnowledgeSearchService） | 结构化 | G18a enrich（standard_code exact 查 → name） |

---

## 7. 依赖关系

### 后端核心依赖 (`backend/requirements.txt`)

| 分类 | 依赖 | 用途 |
|------|------|------|
| Web 框架 | `fastapi` 0.104.1, `uvicorn[standard]` 0.24.0, `python-multipart`, `websockets` | API 服务 |
| 数据库 | `sqlalchemy` 2.0.23, `alembic` 1.13.0 | ORM + 迁移 |
| HTTP 客户端 | `httpx` 0.25.2, `requests`, `aiohttp` 3.9.0 | 异步/同步 HTTP |
| LLM | `openai` 1.12.0, `dashscope` 1.14.1 | Qwen/通义千问 |
| 数据验证 | `pydantic` 2.5.2, `pydantic-settings` 2.1.0 | 配置 & 模型 |
| PDF 解析 | `pymupdf` 1.23.8, `pdfplumber` 0.10.0, `mineru` >=3.4.0, `Pillow` | PDF/图片处理 |
| 文档 | `python-docx` 1.1.0, `docx2pdf` 0.1.8 | Word 文档 |
| 数据处理 | `pandas` 2.0.0, `openpyxl`, `beautifulsoup4`, `jieba`, `networkx` | 表格/HTML/分词/图谱 |
| LangChain | `langchain` 0.1.0, `langchain-openai`, `langchain-community`, `langgraph`, `chromadb`, `tiktoken` | AI 编排 |
| 多模态 | `FlagEmbedding`, `torch`, `transformers` | BGE-VL Embedding |
| 测试 | `pytest`, `pytest-asyncio`, `pytest-mock` | 测试框架 |
| 监控 | `watchdog` | 文件系统监听 |

> **注意**：`chromadb` 虽在 requirements 中，但向量检索（IndexingService/SearchAgent）已于 2026-07-05 删除，当前不再使用。`numpy<2` 约束因 chromadb 0.4.22 引用已移除的 `np.float_`。

### 前端核心依赖 (`frontend/package.json`)

| 分类 | 依赖 | 用途 |
|------|------|------|
| UI 框架 | `react` 18, `react-dom`, `antd` 5, `react-icons` | 界面 |
| 编辑器 | `@tiptap/react`, `@tiptap/starter-kit`, `@tiptap/extension-image`, `@tiptap/extension-placeholder` | 富文本 |
| 状态 | `zustand` 4 | 全局状态 |
| 路由 | `react-router-dom` 6 | 页面路由 |
| HTTP | `axios` | API 请求 |
| Markdown | `markdown-it`, `turndown`, `dompurify` | MD↔HTML |
| PDF | `pdfjs-dist` 5 | PDF 渲染 |
| 本地 DB | `dexie`, `dexie-react-hooks` | IndexedDB |
| Diff | `diff-match-patch` | 差异对比 |
| 其他 | `dayjs`, `lottie-react`, `react-dropzone` | 日期/动画/拖拽 |
| 测试 | `jest` 30, `@testing-library/react`, `ts-jest`, `vitest` | 测试 |

### 模块间依赖关系

```
前端 (React/Vite)
  └── /api → 后端 (FastAPI)
                ├── Agent 系统 (orchestrator → writing/review/proofread)
                │     ├── LLM 服务 (QwenLLMService → Qwen/MindIE)
                │     ├── 检索 (HierarchicalContext → 文档索引 + KG)
                │     └── 工具 (compliance_checker / terminology_mapper)
                ├── PDF 处理 (DocumentProcessor → MinerU VLM / pdfplumber)
                ├── 数据层 (SQLAlchemy → SQLite craftdoc.db)
                └── 持久化 (Repository → JSON files / SQLite)
```

---

## 8. 项目运行方式

### 8.1 本地开发

```bash
# === 后端 ===
cd backend
pip install -r requirements.txt
cp .env.example .env          # 填入 LLM/VLM 配置（找 @alerlocked 要）
python init_db.py             # 首次运行：初始化数据库
python main.py                # 启动 → http://127.0.0.1:8000

# === 前端（另开终端）===
cd frontend
npm install
npm run dev                   # 启动 → http://127.0.0.1:3000
```

**启动检查**：后端启动时自动检测 LLM/VLM 连通性，终端打印状态摘要。

### 8.2 生产模式（单端口）

```bash
# 构建前端
cd frontend && npm run build  # 产出 frontend/dist/

# 后端自动检测 dist 存在 → 单端口 serve SPA
cd backend && python main.py   # http://127.0.0.1:8000 同时提供 API + 前端
```

### 8.3 测试

```bash
# 后端测试
cd backend
pytest                         # 全量测试（853+ 用例）
pytest tests/                  # 指定目录
pytest -k "g25a"               # 关键词过滤

# 前端测试
cd frontend
npm test                       # Jest
npm run test:coverage          # 覆盖率

# 端到端
cd e2e && npx playwright test  # Playwright E2E
```

### 8.4 环境变量配置

从 `backend/.env.example` 拷贝为 `.env`，关键配置：

```bash
# LLM（云端 DashScope 或本地 MindIE）
DASHSCOPE_API_KEY=your-key          # 本地 MindIE 用 EMPTY
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
# 本地部署：
# DASHSCOPE_BASE_URL_COMPLEX=http://localhost:1028/v1
# MODEL_TIER_COMPLEX=qwen3-30b-a3b

# VLM（MinerU）
MINERU_VL_SERVER=http://localhost:1040/v1  # 远程 VLM 服务器

# 其他
DEBUG=true
HOST=127.0.0.1
PORT=8000
```

### 8.5 Windows 一键脚本

仓库根目录提供 Windows 批处理脚本：`install.bat`、`start.bat`、`start_backend.bat`、`start_frontend.bat`、`stop.bat`、`activate_craft_doc.bat`。

---

## 9. 部署

### 目标环境

- **瘦客户端**：Windows 10（开发/日常使用）
- **内网服务器**：Kylin V10 + Ascend NPU（LLM 推理）
- **架构**：`[前端 :3000] → [后端 :8000] → [MindIE :1025/:1028] → [Ascend NPU]`
- **模型**：Qwen3-14B（28GB，简单任务）/ Qwen3-30B-A3B（57GB，复杂生成）

### 部署步骤（详见 `deploy/README.md`）

1. 传输模型文件（~85GB）到服务器 `/data/models/`
2. 克隆仓库到服务器
3. 加载 MindIE Docker 镜像
4. 启动 MindIE 服务（`deploy/mindie/` 下脚本）
5. 配置 `backend/.env`（使用 `deploy/env-local.template`）
6. 启动后端 `python main.py`
7. 启动前端 `npm run dev` 或构建后单端口 serve

### MindIE 配置

`deploy/mindie/` 下提供多套配置：
- `config-2.2rc1-qwen3-14b.json` — Qwen3-14B
- `config-2.2rc1-qwen3-30b-a3b.json` — Qwen3-30B-A3B
- `config-2.2rc1-qwen2.5-vl-7b.json` — VLM（PDF 解析）
- `config-2.2rc1-mineru-vlm.json` — MinerU VLM 后端

---

## 10. 注意事项（必读）

### 10.1 架构层禁区

以下文件改动需**独立 `[architecture]` PR + 强制 admin review**，功能 commit 不得混入：

| 架构层 | 文件/目录 |
|--------|-----------|
| Agent 系统 | `backend/app/agents/**` |
| 上下文检索 | `backend/app/services/hierarchical_context.py`、`knowledge_graph.py` |
| 数据存储 | `backend/app/models/database.py` |
| 生成主链 | `backend/app/api/agent.py` 的 `generate-stream` 主链 |
| 架构文档 | `ARCHITECTURE.md` |

> 拿不准是否算架构层 → 当架构层处理。

### 10.2 已删除组件（勿复活）

- **向量检索**（IndexingService / chromadb / SearchAgent / UnifiedRetrieval）：2026-07-05 删除。原因：工艺文件是结构化 QJ903 表格，向量召回引噪声；source-driven 直注优于三层检索。
- **Workflow 编排**（`_select_workflow`/`execute_workflow`）：死代码已清理，实际走 `_dispatch_to_sub_agent`。
- **document_generator 工具**：死代码已清理。

### 10.3 知识图谱区分

- 2026-07-05 删除的是**老 KG 死壳**（0 调用）
- 2026-07-24 重新上的**全局 craft_kg**（`services/knowledge_graph.py`，networkx，持久化 `data/knowledge_graph.json`，L3.5 层 + G25a 相辅相成用）是**活的**，勿混淆。

### 10.4 缓存注意事项

- `HierarchicalContext` 启动时缓存文档索引（`_documents_cache`，TTL 30s）。**上传新文档后须重启后端清缓存**，否则新文档不可见。
- `ReviewService._load_sensitive_words` 模块级缓存（fail-soft）。

### 10.5 LLM 韧性

- LLM 调用经 `_generate_with_retry` 包装：1+2 次重试指数退避；`context_overflow` 裁剪后重试；`empty_reply` 同消息重试。
- `generate-stream` 入口有 `check_llm_reachable` 预探，不通则 yield SSE error + return（快速失败，不静默假成功）。
- 推理模型（qwen3）需 `enable_thinking=True`，否则 content 空 + 静默 success（已修复）。

### 10.6 防臆造机制

- **溯源过滤**（`_provenance_filter`）：丢弃无上游出处的倒推值
- **source-driven 直注**：G4a/G5a/G22a/G25a 结构化列从源文本直填，不经 LLM
- **"待补"占位符**：无法填充的字段标注"待补"，不臆造
- **审计/签名噪声清洗**：extract 时过滤审计标记行
- **fail-soft LLM 检查**：LLM 检查失败不阻断流程，降级标记

### 10.7 前后端一致性

- 前端 `ProcessTableEditor` 按前端 key 取值，后端模板 key 必须与前端 layout key 对齐（`processDocumentLayouts.ts`）。有 `guard-column-align.py` hook 检测不一致。
- 已知历史不一致白名单：G10a/G14a/G12a（已在 `column-key-align` 修复对齐）。

### 10.8 SQLite 并发限制

- 当前 SQLite 单 worker，并发读 OK，**并发写撞锁**（`database is locked`）。
- 阶段 1 规划：认证登录 / 用户数据隔离 / 多 worker 或换 PostgreSQL。

### 10.9 G25a 编号后处理

- LLM 结构化生成的编号/格式约束光靠 prompt 拉不住（会照抄原文编号），需 `re.sub` 后处理兜底：行首 `N.M` 编号第一段强制 = 工序号 i。

---

## 11. 协作编辑方式与注意事项

### 11.1 仓库状态

- 仓库 **public**：`github.com/alerlocked/llbased-word`
- `main` **受 branch protection 保护**：禁止直推、禁止 force push，所有改动走 **PR + 至少 1 个 review**
- `CODEOWNERS` 强制所有 PR 必须经 `@alerlocked`（admin）review 才能 merge；协作者互相 approve **不算数**
- 本地是 source of truth，远程跟随

### 11.2 分支模型

| 分支 | 用途 | 规则 |
|------|------|------|
| `main` | 稳定主干 | 只接 PR merge，禁直推 |
| `feature/<scope>-<desc>` | 功能/修复 | 从最新 `main` 切，完成后开 PR |
| `feature/arch-<desc>` | **架构层改动** | 独立分支，强制 review |
| `bugfix/<desc>` / `refactor/<desc>` | 修 bug/重构 | 同 feature |

命名规范：`feature/csv-export-batch`、`bugfix/g18a-part-name`、`refactor/orchestrator-cleanup`

### 11.3 标准开发流程

```bash
# 1. 同步主干
git checkout main && git pull

# 2. 开分支
git checkout -b feature/<your-feature>

# 3. 开发 + 提交
git add <files>
git commit -m "feat(xxx): 一句话描述"

# 4. 推分支（post-commit hook 会自动 best-effort push）
git push -u origin feature/<your-feature>

# 5. GitHub 开 PR：base=main ← 你的分支，填模板
# 6. 等 @alerlocked 审 → 按 review 改 → merge
```

### 11.4 Commit 规范

```
<type>(<scope>): <subject>
```

- **type**：`feat` / `fix` / `refactor` / `test` / `docs` / `chore`
- **scope**：模块名（如 `g25a`、`orchestrator`、`frontend`、`deploy`）
- **subject**：祈使句，简短描述

示例：`feat(g25a): per-row parallel generation + step numbering postprocess`

### 11.5 PR 审查流程

1. **开 PR**：填 PR 模板（`.github/pull_request_template.md`），声明改动类型 + **是否触碰架构层** + 自测结果
2. **南天门多维审查**（`/pr-review`）：AI 复用 Claude Code 底座（bug/安全）+ 补三处增量：
   - 架构层越界（§4 清单 diff 比对 + 是否同步更新 `ARCHITECTURE.md`）
   - 项目经验（`exp-*.md` 经验库 + `pitfalls.md` 踩坑匹配）
   - 品味（`guard-taste` 规则）
   - 输出分级报告：🔴 blocker（必修）/ 🟡 warn（应修）/ ⚪ nit（可选）
3. **admin 把关**：`@alerlocked` 看报告 + 自查 → approve
4. **merge**：review 通过后 merge，删分支

### 11.6 架构层改动隔离（强制）

1. 架构层改动 → **独立分支** `feature/arch-*` + **独立 PR**，标题前缀 `[architecture]`，**强制 review**
2. **功能 commit 不得混入架构层文件改动** → review 一律打回，拆成「功能 PR」+「架构 PR」分别提
3. 架构层 PR merge 前，**必须同步更新 `ARCHITECTURE.md`**
4. 纯功能改动走普通 feature 分支即可

### 11.7 禁区

- ❌ 不直推 `main`、不 force push `main`
- ❌ 不提交 `.env` / 密钥 / 内网真实 IP（脱敏用占位符 `SERVER_IP`）
- ❌ 不提交业务数据（`data/*.docx`、`backend/data/process_docs/`、`*.db` 等，`.gitignore` 已排除）
- ❌ 不擅自 pull/merge/rebase 解决分叉，分叉在 PR 里讨论

### 11.8 自动 Hook

- `.git/hooks/post-commit`（devlog-hook）：每次 commit 自动刷新 `DEV-LOG.md` 的 git 段 + best-effort push 到当前分支 upstream
- feature 分支上正常 commit 即可，hook 自动推分支，**不碰 main**

### 11.9 文档体系（单一事实源）

| 文档 | 角色 | 维护规则 |
|------|------|----------|
| `ARCHITECTURE.md` | **唯一架构源** | 架构改动 lead 收尾必须更新 |
| `DEV-LOG.md` | 进度/历史决策 | 查「做到哪了」只认这个 |
| `CLAUDE.md` | 技术栈/怎么跑 | 指针，不重复架构 |
| `VISION.md` | 项目北极星 | 愿景/验收 = 用户主权 |
| `CONTRIBUTING.md` | 协作规范 | 分支模型/PR/禁区/commit |
| `ONBOARDING.md` | 新人上手 | 5 分钟入门 |

> 约定：架构/功能描述不写进 README（写进即腐烂），真相见上表。历史在 git。

### 11.10 新协作者入门

1. `git clone` → 先读三份文档：`CLAUDE.md`（技术栈/怎么跑）、`ARCHITECTURE.md`（架构）、`DEV-LOG.md`（进度/历史决策）
2. 后端：`cd backend && pip install -r requirements.txt && python main.py`（:8000）
3. 前端：`cd frontend && npm install && npm run dev`（:3000）
4. `.env` 不进 git，从 `backend/.env.example` 拷贝，填本地 LLM/VLM 地址
5. 卡住了：环境/配置问题 → 找 @alerlocked；不确定改动是否越界 → PR 里直接问

---

> **文档生成说明**：本文档基于仓库代码实际分析生成，覆盖架构、模块、关键类函数、依赖、运行、注意事项及协作规范。如代码变更，请同步更新本文档及 `ARCHITECTURE.md`。
