# Coding retrieval v3: compact evidence and adjacent turns

## Why this revision

The v2 Coding Smoke completed successfully at the API level but scored 0.00.
The result is one task and does not establish full-suite performance. The
platform's current guide describes Smoke as a private integration/compatibility
mode and Full as the formal evaluation. It also states that Answer consumes
Search candidates in returned order and may truncate the tail to fit its input
budget. See the [official evaluation guide](https://agentmemoryleaderboard.ai/api-guide).

This motivates a bounded-output hypothesis: return fewer, higher-ranked coding
records and make the immediately adjacent source turns available to ranking,
so a relevant failure, fix, or test is less likely to be separated or pushed
behind noisy records. This is an inference, not a proven explanation for the
Smoke score.

## Changes

1. Coding Search now returns at most 12 original records, even when the
   platform requests `top_k=100`. A smaller caller-supplied `top_k` remains the
   effective limit. Other deployments retain their existing output count.
2. Adjacent-turn expansion defaults on only when
   `MEMORY_CODING_RETRIEVAL=true`. It adds up to four immediate, same-session
   source records around lexical candidates for the existing bounded reranker.
   User isolation is preserved and returned evidence remains the full original
   message. `MEMORY_ADJACENT_TURN_EXPANSION` can explicitly override the default.
3. The Coding Compose profile explicitly enables the feature. No database
   migration, new runtime dependency, embedding model, or public API field is
   added.

The 12-record bound and four-neighbor expansion are conservative initial
settings. The official smoke sample is too small to tune them reliably; they
must be judged on the full allowed evaluation or independent public fixtures.

## Verification and limits

Tests use independently written synthetic records. They verify that Coding
Search caps output at 12 while honoring smaller `top_k`, non-Coding retrieval
keeps its previous limit, adjacent expansion is Coding-specific by default,
and existing same-session/user-isolation behavior remains intact. These checks
do not estimate CAMBench solve rate.

The deployed v2 container received successful Add and Search requests with no
observed non-2xx API responses or logged model/authentication/timeout errors.
This verifies the integration path only; it does not explain the zero Smoke
score. No private task text, questions, answers, or stored evaluation records
were inspected or used for tuning.

No official score improvement is claimed for v3. The public endpoint remains
bound to the registered v2 version until a new fixed version is registered.
See [the v2 reference disclosure and prior checks](CODING_RETRIEVAL_V2.md).
