# Coding Memory retrieval method

## Status

This repository is developing a Coding Memory specialization of ChronoHybridMem. The v2 version completed official Coding Smoke with a 0.00 score; this is a one-task smoke result, not a Full evaluation or a Coding leaderboard result. The Rank 5 / Overall 44.33 result mentioned in the README belongs to the separate Textual track.

## Method

The service keeps the existing Add/Search API, SQLite database schema, FTS5 channels, `gpt-4o-mini` query planning, user isolation, and original-evidence response behavior. The v2 Coding profile enables `MEMORY_CODING_RETRIEVAL`, which adds query identifier splitting, bounded engineering-ranker views, a Coding ranking rubric, and batch index annotations outside database write transactions. The v3 candidate additionally caps Coding responses at 12 original records and enables bounded adjacent-turn context for Coding only. See [the v2 design and reference disclosure](CODING_RETRIEVAL_V2.md) and [the v3 compact-evidence proposal](CODING_RETRIEVAL_V3.md).

At Add time, the indexer scans each message for code-shaped identifiers: camelCase and acronym boundaries, `snake_case`, qualified symbols, and path-like tokens. It splits those forms into lowercase lexical terms and appends the derived terms to the existing FTS index text. For example, `QueryPlanBuilder::reifyMemoryToken` contributes terms such as `query`, `plan`, `builder`, `reify`, `memory`, and `token`; `src/index/planBuilder.py` contributes its path and filename components.

The derived text is used only to improve candidate retrieval. The original `raw_messages.content` is stored unchanged and Search returns that original source evidence. The method does not generate answers, add benchmark-specific facts, alter query options, or share memories across `user_id` values. No database migration or runtime dependency is introduced.

## Scope and limits

- This is lexical expansion, not code parsing or semantic understanding. It does not infer call graphs, resolve aliases, or know whether two symbols are equivalent.
- Query-side camelCase/snake_case splitting is enabled by the v2 Coding profile. Ordinary deployments leave this optional path disabled.
- The v3 candidate limits Coding Search to at most 12 records and adds at most four same-session adjacent records to the reranking pool. Other tracks retain their existing defaults.
- The synthetic relevant/noisy fixture is a regression check only. It is not CAMBench data and does not establish benchmark performance.
- The v2 Smoke score and the existing Textual research baseline are not evidence of Coding full-suite performance.

## Reproduction

From the repository root, run the focused retrieval and API checks without model credentials:

```powershell
Remove-Item Env:OPENAI_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:MEMORY_REQUIRE_MODEL -ErrorAction SilentlyContinue
python -m pytest tests/test_hybrid_retrieval.py tests/test_api.py tests/test_model_mode.py -q
```

The suite covers symbol/path token expansion, retrieval of a relevant record in the presence of a noisy distractor, output bounds, adjacent-turn retrieval, and preservation of original evidence. The v3 candidate still needs a newly registered fixed version before its official Smoke; no Full result is claimed.

The isolated Docker Compose deployment profile is documented in [CODING_DEPLOYMENT.md](CODING_DEPLOYMENT.md).
