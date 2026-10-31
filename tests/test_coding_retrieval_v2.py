"""Independent synthetic engineering fixtures, never official task data."""

import pytest

from app.coding_retrieval import evidence_excerpt
from app.model import MemoryModel
from app.schemas import AddRequest
from app.storage import MemoryStore


CASES = [
    ("LeaseEpochGuard", "lease_epoch_guard"),
    ("RetryBudgetFence", "retry_budget_fence"),
    ("SocketDrainBarrier", "socket_drain_barrier"),
    ("ShardOwnerProbe", "shard_owner_probe"),
    ("SnapshotFlushGate", "snapshot_flush_gate"),
    ("BuildArtifactIndex", "build_artifact_index"),
    ("HTTPResponseCache", "http_response_cache"),
    ("CommitCursorTracker", "commit_cursor_tracker"),
]


@pytest.mark.parametrize("query,symbol", CASES)
@pytest.mark.parametrize("noisy", [False, True])
def test_query_code_shape_recalls_original_source(tmp_path, query, symbol, noisy):
    results = {}
    source = f"The {symbol} failed after reuse; a generation guard fixed it. Regression passed."
    for enabled in (False, True):
        store = MemoryStore(str(tmp_path / f'{enabled}.db'), coding_retrieval=enabled)
        store.initialize()
        messages = [{"role": "assistant", "content": source}]
        if noisy:
            messages += [{"role": "user", "content": f"Unrelated cache maintenance note {i}"} for i in range(24)]
        store.add(AddRequest(request_id="fixture", user_id="u", session_id="s", messages=messages))
        results[enabled] = store.search(user_id="u", query=query, top_k=1)
        assert store.search(user_id="other", query=query, top_k=100) == []
    assert results[False] == []
    assert [item.content for item in results[True]] == [source]


def test_excerpt_finds_late_evidence_and_stays_verbatim():
    source = "irrelevant build output. " * 900 + "\nlease_epoch_guard: validation completed with generation guard."
    excerpt = evidence_excerpt(source, ["LeaseEpochGuard", "generation", "guard"])
    assert len(excerpt) <= 2400
    assert "validation completed" in excerpt
    for span in excerpt.split("\n[... source gap ...]\n"):
        assert span in source
    assert evidence_excerpt("short source", ["source"]) == "short source"


def test_coding_ranker_view_is_bounded_but_api_returns_full_record(tmp_path):
    class RecordingModel:
        candidates = None

        def extract_facts(self, content, **kwargs):
            return []

        def plan_query(self, query, options):
            return []

        def rank_candidates(self, *args):
            raise AssertionError("Coding mode should use the engineering ranker")

        def rank_coding_candidates(self, query, options, candidates):
            self.candidates = candidates
            return [item['id'] for item in candidates]

    model = RecordingModel()
    store = MemoryStore(str(tmp_path / 'memory.db'), model=model, coding_retrieval=True)
    store.initialize()
    content = "tool output line. " * 1000 + "\nlease_epoch_guard: validation completed."
    store.add(AddRequest(request_id="fixture", user_id="u", session_id="s",
                         messages=[{"role": "assistant", "content": content}]))
    results = store.search(user_id="u", query="LeaseEpochGuard validation", top_k=1)
    assert results[0].content == content
    assert all(len(item['content']) <= 2400 for item in model.candidates)
    assert "validation completed" in model.candidates[0]['content']


def test_ranker_filters_unknown_ids_duplicates_and_non_list_output():
    model = object.__new__(MemoryModel)
    calls = []

    def response(prompt, payload, max_tokens):
        calls.append((prompt, payload, max_tokens))
        return {"ordered_ids": ["unknown", "a", "a", {}, "b"]}

    model._json_response = response
    candidates = [{"id": "a", "content": "root cause"}, {"id": "b", "content": "regression"}]
    assert model.rank_coding_candidates("bug", [], candidates) == ["a", "b"]
    assert calls[0][1]['query'] == 'bug'
    assert 'Do not answer' in calls[0][0]
    model._json_response = lambda *args, **kwargs: {"ordered_ids": "a"}
    assert model.rank_coding_candidates("bug", [], candidates) == []


def test_coding_ranker_runtime_fallback_is_logged_without_payload(caplog):
    import logging

    model = object.__new__(MemoryModel)

    def fail(*args, **kwargs):
        raise RuntimeError("synthetic upstream failure")

    model._json_response = fail
    with caplog.at_level(logging.WARNING, logger="chrono_hybrid_mem"):
        result = model.rank_coding_candidates(
            "private-query-marker",
            [],
            [{"id": "mem_1", "content": "private-memory-marker"}],
        )
    assert result == []
    assert "coding_ranker_fallback reason=model_response_runtime_error" in caplog.text
    assert "private-query-marker" not in caplog.text
    assert "private-memory-marker" not in caplog.text


def test_coding_search_summary_logs_counts_without_payload(caplog, tmp_path):
    import logging

    class RecordingModel:
        def plan_query(self, query, options):
            return []

        def extract_facts(self, content, **kwargs):
            return []

        def rank_coding_candidates(self, query, options, candidates):
            return [candidate["id"] for candidate in candidates]

        def rank_candidates(self, query, options, candidates):
            raise AssertionError("Coding mode should use the coding ranker")

    model = RecordingModel()
    store = MemoryStore(
        str(tmp_path / "summary.db"), model=model, coding_retrieval=True
    )
    store.initialize()
    store.add(AddRequest(
        request_id="summary-fixture", user_id="summary-user", session_id="s",
        messages=[{"role": "assistant", "content":
                   "path/to/private-memory-marker.py fixed the regression"}],
    ))
    with caplog.at_level(logging.INFO, logger="chrono_hybrid_mem"):
        result = store.search(
            user_id="summary-user", query="private-query-marker regression", top_k=10
        )
    assert result
    assert "coding_search_summary" in caplog.text
    assert "model_enabled=True" in caplog.text
    assert "reranked_ids=1" in caplog.text
    assert "returned=1" in caplog.text
    assert "private-query-marker" not in caplog.text
    assert "private-memory-marker" not in caplog.text


def test_batch_cues_are_bounded_and_bound_to_supplied_indices():
    model = object.__new__(MemoryModel)
    calls = []

    def response(prompt, payload, max_tokens):
        calls.append(payload)
        index = payload['messages'][0]['index']
        return {'records': [
            {'index': index, 'facts': ['explicit cue', 'explicit cue', 5]},
            {'index': True, 'facts': ['invalid boolean index']},
            {'index': -1, 'facts': ['invalid index']},
            {'index': 1000, 'facts': ['invalid index']},
        ]}

    model._json_response = response
    sources = [{'role': 'assistant', 'content': 'build output ' * 1000} for _ in range(17)]
    facts = model.extract_coding_batch(sources)
    assert len(calls) == 2
    assert len(facts) == 17
    assert facts[0] == facts[16] == ['explicit cue']
    assert all(not facts[index] for index in range(1, 16))
    assert all(len(record['source_view']) <= 1600 for call in calls for record in call['messages'])


def test_batch_annotation_precedes_write_and_duplicate_add_skips_model(tmp_path):
    import sqlite3

    database = str(tmp_path / 'batch.db')

    class BatchModel:
        calls = 0

        def extract_coding_batch(self, messages):
            self.calls += 1
            # A separate writer can acquire the database while model work runs.
            with sqlite3.connect(database, timeout=0) as connection:
                connection.execute('BEGIN IMMEDIATE')
                assert connection.execute('SELECT count(*) FROM ingestions').fetchone()[0] == 0
            return [["source supported annotation"] for _ in messages]

    model = BatchModel()
    store = MemoryStore(database, model=model, coding_retrieval=True)
    store.initialize()
    request = AddRequest(request_id='retry', user_id='u', session_id='s', messages=[
        {'role': 'user', 'content': f'Original message {index}'} for index in range(20)
    ])
    store.add(request)
    store.add(request)
    assert model.calls == 1
    with sqlite3.connect(database) as connection:
        assert connection.execute('SELECT count(*) FROM raw_messages').fetchone()[0] == 20
        assert connection.execute('SELECT content FROM raw_messages ORDER BY id').fetchall() == [
            (message.content,) for message in request.messages
        ]


def test_api_environment_enables_coding_path(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from app import main

    monkeypatch.setenv('MEMORY_CODING_RETRIEVAL', 'true')
    monkeypatch.delenv('MEMORY_SYSTEM_KEY', raising=False)
    monkeypatch.setattr(main, 'model_from_environment', lambda: None)
    client = TestClient(main.create_app(str(tmp_path / 'api.db')))
    response = client.post('/add', json={
        'request_id': 'fixture', 'user_id': 'u', 'session_id': 's',
        'messages': [{'role': 'user', 'content': 'socket_drain_barrier regression passed.'}],
    })
    assert response.status_code == 200
    response = client.post('/search', json={
        'user_id': 'u', 'query': 'SocketDrainBarrier', 'top_k': 1,
    })
    assert response.status_code == 200
    assert response.json()['data'][0]['content'] == 'socket_drain_barrier regression passed.'


def test_coding_search_returns_a_bounded_evidence_set(tmp_path):
    database = str(tmp_path / 'bounded.db')
    seed = MemoryStore(database, coding_retrieval=True)
    seed.initialize()
    seed.add(AddRequest(
        request_id='many-matches', user_id='u', session_id='s', messages=[
            {'role': 'assistant', 'content':
             f'lease_epoch_guard evidence record {index} root cause regression'}
            for index in range(24)
        ]
    ))

    coding_results = seed.search(
        user_id='u', query='lease_epoch_guard root cause regression', top_k=100
    )
    ordinary_results = MemoryStore(database).search(
        user_id='u', query='lease_epoch_guard root cause regression', top_k=100
    )

    assert len(coding_results) == MemoryStore.CODING_TOP_K_MAX
    assert len(ordinary_results) == 24
    assert len(seed.search(
        user_id='u', query='lease_epoch_guard root cause regression', top_k=5
    )) == 5


def test_adjacent_expansion_defaults_to_coding_only_and_can_be_overridden(monkeypatch):
    from app import main

    monkeypatch.delenv('MEMORY_ADJACENT_TURN_EXPANSION', raising=False)
    assert main.adjacent_turn_expansion_from_environment() is False
    assert main.adjacent_turn_expansion_from_environment(
        coding_retrieval=True
    ) is True
    monkeypatch.setenv('MEMORY_ADJACENT_TURN_EXPANSION', 'false')
    assert main.adjacent_turn_expansion_from_environment(
        coding_retrieval=True
    ) is False
