# 编程赛道规格：ChronoHybridMem Coding Track

## Assumptions

1. 新仓库为公开仓库 Tin11Mn/chrono-hybrid-mem-coding，面向 Agent Memory Leaderboard Cycle 2 的 Open-source Methods / Coding Memory 赛道。
2. 从已冻结的 ChronoHybridMem Cycle 2 版本继承实现和 Git 历史；不修改或替换正在运行的文本赛道服务。
3. 本项目只针对 Coding Memory 做检索适配；Textual / Coding 共用文本请求格式，暂不支持多模态内容数组。
4. 当前优先目标是按截止时间完成一份可复核的 Coding 提交；不预设分数目标，也不把本地实验结果称为官方成绩。

## Objective

基于 ChronoHybridMem 构建并提交 Coding Memory 版本，帮助系统从同一代码仓库的工程记录中找回相关经验，并在噪声记忆中筛选可复用的工程证据。系统负责存储和检索，Search 只返回排序后的原始记忆证据；平台负责生成最终答案与评分。

## Competition contract

- Add 接收 request_id、按原顺序排列的 messages、user_id 和 session_id；Coding 的 messages[].content 是非空字符串。
- Add 只有在记录已持久化且可立即检索后才返回 success=true，并逐字回显 request_id、user_id、session_id。
- Search 接收原始 query 字符串、可选的顶层 options 数组、同一 user_id 和 top_k；返回 data 数组，按相关性排序且数量不超过 top_k。
- Search 不生成最终答案，不伪装答案为记忆，也不跨 user_id、任务、样本或团队共享数据。
- 不使用测试题答案硬编码、隐藏评测轨迹、提示词注入或人工实时答题。
- Open-source Methods 赛道的 LLM 相关组件使用 gpt-4o-mini；若采用 embedding，则使用 text-embedding-v4。Reranker 不限。

## Tech stack

- Python、FastAPI、Pydantic、SQLite FTS5，沿用当前仓库依赖。
- 继续使用来源可追溯的原始记录和现有 user_id 隔离边界。
- 默认不增加依赖；任何新增依赖需在规格审阅后说明必要性。

## Commands

从仓库根目录执行：

- 本地 API：python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
- 回归验证：python -m pytest
- Docker 本地运行命令以 README.md 中的正式示例为准。

## Project structure

- app/：Add/Search API、数据模型、持久化、检索和模型适配。
- tests/：API 契约、样本隔离、持久化、检索排序和 Coding 定向用例。
- docs/：赛道规格、协议审计、提交材料和方法说明。
- scripts/：可复现的本地评测与报告工具；不得包含密钥或私有评测数据。

## Code style

- 沿用项目现有 Python 类型标注、Pydantic 模型、明确错误处理和来源保留方式。
- 不破坏原始 memory content；检索增强只影响候选生成与排序，Search 响应仍返回原始证据。
- 示例沿用现有模型风格：

    class Message(BaseModel):
        role: NonEmptyText
        content: NonEmptyText
        timestamp: Optional[int] = None

## Testing strategy

- 先检查 Add/Search 的官方 Coding Smoke，覆盖响应字段、鉴权和同步持久化。
- 用自造工程记忆样例覆盖缺陷根因、修复提交、回归结果、路径/符号检索、相关与噪声混杂、空结果和 top_k 边界。
- 验证同一 user_id 下可检索，其他 user_id 绝不可见；Search 只返回原文证据，不生成答案。
- 跑现有回归测试，确认文本路径未被破坏；再运行 Coding Smoke。Full 前固定并记录代码版本、配置和 API 镜像版本。
- 不对隐藏 CAMBench 数据作本地拟合，不把 Smoke 通过等同于成绩达标。

## Boundaries

- Always: 保持 Add/Search 契约、来源可追溯、user_id 隔离、原始证据返回和版本可复现。
- Ask first: 更改数据库格式、增加运行时依赖、修改模型类型、调整现有文本赛道生产服务或新增服务器公网端口。
- Never: 提交密钥、把私有评测数据放入仓库、在 Search 中回答问题、跨样本复用记忆、硬编码 benchmark 问题或答案。

## Success criteria

1. 新版本能按官方 Coding Add/Search 格式完成写入与检索，响应字段和 top_k 限制通过平台 Smoke。
2. 针对相关/噪声工程记忆的检索用例能稳定返回排序后的原始证据，并满足 user_id 隔离。
3. 现有 Textual API 行为不回退；部署和评测使用明确、固定、公开可核验的 commit。
4. Coding Full 完成、无缺失或重复任务，并通过赛事版本与合规复核后，才称为有效参赛结果。

## Open questions

- Coding 赛道是否允许绑定当前文本服务的同一公网 endpoint，需以 Evaluation 页面/官方审核结果为准；任何 Coding 专用变更都不得覆盖文本赛道服务。
- 赛道 Smoke 暴露的真实问题和可用的公开 CAMBench 样例，将决定后续优化优先级；在此之前不设具体分数承诺。
