# Coding Memory retrieval method

## Status

This repository is developing a Coding Memory specialization of ChronoHybridMem. The current change improves lexical candidate recall for engineering records. It has not been run through the official Coding Smoke or Full evaluation, and it has no Coding leaderboard result. The Rank 5 / Overall 44.33 result mentioned in the README belongs to the separate Textual track.

## Method

The service keeps the existing Add/Search API, SQLite database schema, FTS5 channels, `gpt-4o-mini` query planning and candidate ordering, user isolation, and original-evidence response behavior.

At Add time, the indexer scans each message for code-shaped identifiers: camelCase and acronym boundaries, `snake_case`, qualified symbols, and path-like tokens. It splits those forms into lowercase lexical terms and appends the derived terms to the existing FTS index text. For example, `QueryPlanBuilder::reifyMemoryToken` contributes terms such as `query`, `plan`, `builder`, `reify`, `memory`, and `token`; `src/index/planBuilder.py` contributes its path and filename components.

The derived text is used only to improve candidate retrieval. The original `raw_messages.content` is stored unchanged and Search returns that original source evidence. The method does not generate answers, add benchmark-specific facts, alter query options, or share memories across `user_id` values. No database migration or runtime dependency is introduced.

## Scope and limits

- This is lexical expansion, not code parsing or semantic understanding. It does not infer call graphs, resolve aliases, or know whether two symbols are equivalent.
- Query-side camelCase splitting is not added yet; current benefits come from matching ordinary query terms against expanded source-side index terms.
- The synthetic relevant/noisy fixture is a regression check only. It is not CAMBench data and does not establish benchmark performance.
- The existing Textual research baseline and its reported scores are inherited project history, not evidence of Coding track performance.

## Reproduction

From the repository root, run the focused retrieval and API checks without model credentials:

```powershell
Remove-Item Env:OPENAI_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:MEMORY_REQUIRE_MODEL -ErrorAction SilentlyContinue
python -m pytest tests/test_hybrid_retrieval.py tests/test_api.py tests/test_model_mode.py -q
```

The suite covers symbol/path token expansion, retrieval of a relevant record in the presence of a noisy distractor, and preservation of the original evidence. Official Coding Smoke and Full still need to be run through the competition platform before any result is claimed.
