# Coding retrieval v2: bounded evidence views and batch indexing

## Evidence and scope

The October 30 platform screenshot reports a successful one-task Coding Smoke
with zero solve score. This establishes API integration, not overall retrieval
quality or a root cause. Its reported file-localization rate is 100%, so the
solve failure cannot simply be equated with failure to locate a file.
Runtime inspection was limited to aggregate metadata:
the registered b460e75 container was healthy with zero restarts, seven successful
Adds, eight successful Searches, 1,409 messages, and no logged lock, model-auth,
timeout, or context-limit errors. No private benchmark content, questions,
answers, or stored trajectories were inspected or used for development.

## Changes

`MEMORY_CODING_RETRIEVAL=true` enables this path; ordinary deployments default
to false. The Coding Compose profile enables it for newly built versions.

1. Split code-shaped queries using the same identifier rules as source indexing.
   Previously a camelCase query could miss a snake_case source even though the
   source index contained the component words. Coding indexes retain up to 512
   derived terms per record instead of 96. Existing databases remain readable;
   only newly ingested records receive the larger derived-term budget.
2. Give the engineering ranker up to three query-relevant, verbatim windows from
   each candidate, capped at 2,400 characters. The 30-candidate model pool thus
   uses at most 72,000 candidate-content characters, excluding JSON and query.
   Source gaps are labeled. The API still returns the complete original record.
3. Rank explicit failure, cause, change and validation evidence with a Coding
   rubric. The same gpt-4o-mini model is used, and model output IDs are checked
   against the supplied candidate set. The ranker generates neither answers nor
   patches. It cannot establish outcomes absent from source evidence.
4. Generate Coding index cues in batches of at most 16 records, before opening
   the database write transaction. Each internal model view is capped at 1,600
   characters. Full raw records remain unchanged and Add returns only after
   persistence. Duplicate request IDs skip model work; concurrent duplicates
   are resolved by the existing unique ingestion key. Remote failures propagate
   so a failed annotation call cannot produce a false success response.

The annotation call count changes from N to sum(ceil(batch_size / 16)) per Add
request. Search still uses its planner and one ranker call. No dependency,
database schema, embedding model, or public API field changes are introduced.

## Reference review and disclosure

These are publicly inspected reference snapshots, not asserted Cycle 1 winners
or proven Coding benchmarks. Implementation here was independently written;
no reference source code was copied.

| Reference | Snapshot | Inspected idea | Decision |
| --- | --- | --- | --- |
| [0xboyu/aml-memory-mvp](https://github.com/0xboyu/aml-memory-mvp) | a28e0ad0466c0f976f57b3b109d8e365fbf9beb8 | Bounded batch indexing, evidence windows, coverage/MMR | Adopt bounded indexing/views; defer output-window/MMR changes to preserve the raw-record contract. MIT. |
| [JingxuanC/causal-memory](https://github.com/JingxuanC/causal-memory) | 39053ff6fd7a18771d59f0c10240b19c37f412b6 | Typed decision/outcome relations and hybrid RRF | Use failure-to-validation reasoning in the ranking rubric; defer graph storage/runtime migration. Apache-2.0. |
| [lin-guan/aml-rag-v2](https://github.com/lin-guan/aml-rag-v2) | 1aa0e2cdb99622afe02931cdfd846d79f057f433 | Hybrid recall, code anchors, neighboring evidence | Use as design comparison; do not introduce its mpnet embeddings under current model restrictions. No root LICENSE was found; no source copied. |
| [himalalps/nano-memory](https://github.com/himalalps/nano-memory) | a85668ce086b12e9a3a8e3fbf9d6b2061fd365d1 | Deterministic BM25 and source preservation | Preserve lexical fallback; avoid unconditional zero-match records that can add noise. MIT. |

## Verification and limits

Independent fixtures cover eight identifier pairs in relevant-only and noisy
conditions (16 cases), unchanged response sources, user isolation, long-record
tail evidence, bounded model views, rank-ID validation, source-index validation,
batch call counts, retry idempotency, and database writer availability during
model work. They test specific failure mechanisms, not CAMBench solve quality.

Observed local results (October 30): the 16 identifier-normalization cases have
zero retrieved matches with the flag off and all 16 recover the correct original
record with it on. This is a narrow mechanical ablation, not a solve-rate
estimate. The focused v2 suite passes 22 tests. The broader suite passes 734
tests and fails five inherited tests: multilingual README parity (one) and the
disabled legacy session-fact schema path (four). Running those same tests on
the untouched b460e75 snapshot reproduces all five failures. No database schema
repair is included in this change. A separately added API flag test also passes.

An isolated Ubuntu Docker candidate built from
`5b698720d7a1f8996717c5842e9ec5ebf3a1625b` also passed one real gpt-4o-mini
synthetic check. Twelve independently written engineering records were added in
3.08 seconds; Search completed in 4.71 seconds and returned both the fix and its
regression validation in Top 3, with all returned records identical to inputs.
This is one integration measurement, not a production latency distribution or
an official score. The candidate used a new empty volume and loopback port
18003, then was stopped. The public registered b460e75 container stayed healthy
and retained its original image and volume throughout.

No official score improvement is claimed. Dense semantic recall, graph
traversal, API-level rate limiting, and the Answer context cost of full raw
records remain limitations. Real gpt-4o-mini ranking quality requires a fresh
platform Smoke against the newly declared fixed version. Never redeploy this
candidate under the old registered version name while an evaluation is active.
