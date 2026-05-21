"""Connector contract enforcement at orchestrator dispatch."""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path
from typing import Any

import pytest

from research_agent.orchestrator.loop import default_handlers, run_loop
from research_agent.orchestrator.plan import Plan, Subgoal, TaskSpec
from research_agent.storage import db
from research_agent.storage.jobs import Job
from research_agent.storage.markdown import write_plan
from research_agent.storage.tasks import enqueue
from research_agent.tools import _registry
from research_agent.tools._registry import BaseSearchPayload, KindEntry
from research_agent.tools.models import SearchResult


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "index.sqlite"
    db.migrate(path=path).close()
    return path


@pytest.fixture
def job(tmp_path: Path, db_path: Path) -> Job:
    return Job.create(
        {"goal": "Investigate connector contracts"},
        jobs_root=tmp_path / "jobs",
        db_path=db_path,
    )


def _open_plan(job: Job) -> Plan:
    plan = Plan(
        version=1,
        objective="Investigate connector contracts",
        subgoals=[Subgoal(id=1, description="Run connector", done=False)],
        task_template=[],
        expected_iterations=1,
    )
    write_plan(job, plan.model_dump())
    return plan


def _task_rows(db_path: Path, job_id: str) -> list[dict[str, Any]]:
    conn = db.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT kind, status, error FROM tasks WHERE job_id = ? ORDER BY id ASC",
            (job_id,),
        ).fetchall()
    finally:
        conn.close()
    return [dict(row) for row in rows]


def _event_payloads(db_path: Path, job_id: str, kind: str) -> list[dict[str, Any]]:
    conn = db.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT payload_json FROM events"
            " WHERE job_id = ? AND kind = ? ORDER BY id ASC",
            (job_id, kind),
        ).fetchall()
    finally:
        conn.close()
    return [json.loads(row["payload_json"]) for row in rows]


@pytest.mark.asyncio
async def test_dispatch_rejects_invalid_direct_connector_before_call(
    job: Job,
    db_path: Path,
) -> None:
    plan = _open_plan(job)
    enqueue(
        job,
        [
            TaskSpec(
                kind="state_election_search",
                payload={
                    "query": "2026 House candidates",
                    "sub_question": "Find state candidate rows",
                },
            )
        ],
        plan.version,
    )

    await run_loop(
        job,
        router=object(),
        plan=plan,
        handlers=default_handlers(object()),
        max_tasks=1,
        retry_waits=(0,),
        retry_max_attempts=1,
    )

    [task] = _task_rows(db_path, job.id)
    assert task["status"] == "failed"
    assert "state" in task["error"]
    [event] = _event_payloads(db_path, job.id, "connector_contract_rejected")
    assert event["stage"] == "dispatch"
    assert event["kind"] == "state_election_search"
    assert "state" in event["message"]


@pytest.mark.asyncio
async def test_default_handlers_import_registered_module_name(
    job: Job,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called: dict[str, Any] = {}

    class _Payload(BaseSearchPayload):
        pass

    async def _search(query: str) -> list[SearchResult]:
        called["query"] = query
        return [
            SearchResult(
                url="https://example.test/result",
                title="Alias result",
                snippet="ok",
                source_kind="web",
            )
        ]

    async def _fetch(url: str) -> None:
        return None

    module = types.SimpleNamespace(search=_search, fetch=_fetch)
    monkeypatch.setitem(sys.modules, "research_agent.tools.alias_module", module)
    entry = KindEntry(
        name="alias_search",
        payload_schema=_Payload,
        search_fn=_search,
        fetch_fn=_fetch,
        host_patterns=(),
        skill_name=None,
        description="Alias connector",
        optional_payload_knobs="",
        example_query="alias",
        module_name="alias_module",
    )
    monkeypatch.setitem(_registry._REGISTRY, "alias_search", entry)  # noqa: SLF001

    handlers = default_handlers(object())
    result = await handlers["alias_search"](
        job,
        {
            "id": 1,
            "kind": "alias_search",
            "payload": {"query": "needle", "sub_question": "needle"},
        },
    )

    assert called == {"query": "needle"}
    assert result is not None
    assert result["results"][0]["title"] == "Alias result"
