"""Fixture-backed regression backtest for 2026 candidate roster jobs."""

from __future__ import annotations

import csv
import json
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

import pytest

from research_agent.orchestrator import plan as plan_module
from research_agent.orchestrator import synth as synth_module
from research_agent.orchestrator.loop import (
    HEURISTIC_CHECK_EVERY_N,
    default_handlers,
    run_loop,
)
from research_agent.orchestrator.plan import Plan, PlanParseError, Subgoal, TaskSpec
from research_agent.storage import artifacts, coverage, db
from research_agent.storage.jobs import Job
from research_agent.storage.markdown import write_plan
from research_agent.storage.tasks import STATUS_DONE, STATUS_PENDING, enqueue
from research_agent.tools import fec, state_election

GOAL = (
    "create a sourced state-by-state roster of 2026 U.S. House and Senate "
    "candidates with CSV output"
)
REQUIRED_COLUMNS = {
    "state",
    "chamber",
    "district_or_seat",
    "candidate_name",
    "party",
    "candidate_status",
    "confidence",
    "official_campaign_website",
    "source_url",
}
TERMINAL_COVERAGE = {"complete", "not_yet_public", "confirmed_gap"}


class _StubAgent:
    def __init__(
        self,
        model: Any,
        *,
        output_type: Any = None,
        system_prompt: str | None = None,
    ) -> None:
        self.model = model
        self.output_type = output_type
        self.system_prompt = system_prompt


class _FailingSynthRouter:
    tiers = {
        "frontier": {"provider": "openrouter", "model": "fixture-primary"},
        "frontier_speed": {"provider": "openrouter", "model": "fixture-fallback"},
    }

    def __init__(self) -> None:
        self.budget = SimpleNamespace(last_cost=0.0)
        self.calls: list[str] = []

    def model_for(self, tier: str) -> Any:
        return SimpleNamespace(tier=tier)

    async def call(self, tier: str, _agent: Any, *_args: Any, **_kwargs: Any) -> Any:
        self.calls.append(tier)
        raise RuntimeError(f"fixture synthesis HTTP 400 for {tier}")


def _patch_httpx(monkeypatch: pytest.MonkeyPatch, fixture_root: Path) -> None:
    payloads = json.loads(
        (fixture_root / "fec" / "candidate_enumeration_2026.json").read_text(
            encoding="utf-8"
        )
    )
    state_csv_url = "https://fixtures.example.test/co_2026.csv"
    state_csv_text = (fixture_root / "state_election" / "co_2026.csv").read_text(
        encoding="utf-8"
    )

    class _Response:
        status_code = 200

        def __init__(self, payload: dict[str, Any] | None = None, text: str = "") -> None:
            self._payload = payload
            self.text = text

        def json(self) -> dict[str, Any]:
            return self._payload or {}

    @asynccontextmanager
    async def _client_factory(*_args: Any, **_kwargs: Any):
        class _Client:
            async def get(
                self,
                url: str,
                *,
                params: dict[str, Any] | None = None,
                **_kwargs: Any,
            ) -> _Response:
                if url == state_csv_url:
                    return _Response(text=state_csv_text)
                params = params or {}
                state = str(params.get("state") or "").upper()
                office = str(params.get("office") or "").upper()
                district = str(params.get("district") or "").strip()
                key = "-".join(part for part in (state, office, district) if part)
                empty = {"pagination": {"page": 1, "pages": 1, "count": 0}, "results": []}
                return _Response(payloads.get(key, empty))

        yield _Client()

    monkeypatch.setenv("DATA_GOV_API_KEY", "test-key-1234567890abcdef")
    fec.reset_for_tests()
    monkeypatch.setattr(fec.asyncio, "sleep", AsyncMock())
    monkeypatch.setattr(fec.httpx, "AsyncClient", _client_factory)


def _patch_state_election(monkeypatch: pytest.MonkeyPatch) -> None:
    url = "https://fixtures.example.test/co_2026.csv"

    monkeypatch.setattr(
        state_election,
        "_RECIPES",
        {
            "CO": {
                "source_url": url,
                "source_type": "csv",
                "retrieval_method": "static_fetch",
                "cycle_coverage": [2026],
            },
            "MD": {
                "source_url": "https://fixtures.example.test/md_2026.csv",
                "source_type": "csv",
                "retrieval_method": "static_fetch",
                "cycle_coverage": [2026],
            },
        },
    )


def _make_job(tmp_path: Path) -> tuple[Job, Plan]:
    db_path = tmp_path / "index.sqlite"
    db.migrate(path=db_path).close()
    job = Job.create(
        {
            "goal": GOAL,
            "domain": "political",
            "enumeration": {
                "required": True,
                "coverage_units": [
                    {
                        "state": "CA",
                        "chamber": "House",
                        "district_or_seat": "01",
                        "source_type": "fec-filed",
                    },
                    {"state": "FL", "chamber": "Senate", "source_type": "fec-filed"},
                    {
                        "state": "CO",
                        "chamber": "House",
                        "district_or_seat": "12",
                        "source_type": "state-ballot-qualified",
                    },
                    {
                        "state": "MD",
                        "chamber": "House",
                        "source_type": "state-ballot-qualified",
                    },
                ],
            },
        },
        jobs_root=tmp_path / "jobs",
        db_path=db_path,
        today=date(2026, 5, 15),
    )
    plan = Plan(
        version=1,
        objective="Build a complete 2026 federal candidate roster fixture.",
        subgoals=[
            Subgoal(
                id=1,
                description="Enumerate FEC and state-election candidate rows",
                done=True,
            )
        ],
        task_template=[],
        expected_iterations=1,
        scope_class="broad",
    )
    write_plan(job, plan.model_dump())
    coverage.declare_from_intake(job)
    enqueue(
        job,
        [
            TaskSpec(
                kind="fec_search",
                payload={
                    "query": "",
                    "sub_question": "Enumerate 2026 California House candidates from FEC",
                    "kind": "candidates_enumerate",
                    "cycle": 2026,
                    "office": "H",
                    "state": "CA",
                    "district": "01",
                    "max_rows": 25,
                    "expand_top_k": 0,
                },
            ),
            TaskSpec(
                kind="fec_search",
                payload={
                    "query": "",
                    "sub_question": "Enumerate 2026 Florida Senate candidates from FEC",
                    "kind": "candidates_enumerate",
                    "cycle": 2026,
                    "office": "S",
                    "state": "FL",
                    "max_rows": 25,
                    "expand_top_k": 0,
                },
            ),
            TaskSpec(
                kind="state_election_search",
                payload={
                    "query": "House",
                    "sub_question": "Find Colorado state-election House candidate rows",
                    "cycle": 2026,
                    "state": "CO",
                    "office": "House",
                    "expand_top_k": 0,
                },
            ),
            TaskSpec(
                kind="state_election_search",
                payload={
                    "query": "2026 U.S. House candidates",
                    "sub_question": "Find Maryland state-election House candidate rows",
                    "cycle": 2026,
                    "state": "MD",
                    "office": "House",
                    "source_type": "state-ballot-qualified",
                    "empty_coverage_status": "confirmed_gap",
                    "empty_coverage_reason": "fixture intentionally lacks Maryland source",
                    "unblocker": "Refresh Maryland SBE fixture after filing lists publish",
                    "expand_top_k": 0,
                },
            ),
        ],
        plan_version=1,
    )
    return job, plan


def _make_handoff_job(tmp_path: Path, *, db_name: str = "handoff.sqlite") -> Job:
    db_path = tmp_path / db_name
    db.migrate(path=db_path).close()
    return Job.create(
        {"goal": GOAL, "domain": "political"},
        jobs_root=tmp_path / "jobs",
        db_path=db_path,
        today=date(2026, 5, 15),
    )


def _candidate_roster_handoff_plan(task_template: list[TaskSpec]) -> Plan:
    return Plan(
        version=1,
        objective="Backtest 2026 candidate-roster connector handoff.",
        subgoals=[
            Subgoal(
                id=1,
                description="Verify 2026 House and Senate candidate-roster tasks.",
            )
        ],
        task_template=task_template,
        expected_iterations=1,
        scope_class="comprehensive",
    )


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


def _task_payloads(db_path: Path, job_id: str) -> list[dict[str, Any]]:
    conn = db.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT payload_json FROM tasks WHERE job_id = ? ORDER BY id ASC",
            (job_id,),
        ).fetchall()
    finally:
        conn.close()
    return [json.loads(row["payload_json"]) for row in rows]


def _candidate_roster_stall_diagnostics(
    db_path: Path,
    job_id: str,
) -> list[dict[str, Any]]:
    conn = db.connect(db_path)
    try:
        tasks = [
            dict(row)
            for row in conn.execute(
                "SELECT id, kind, status FROM tasks"
                " WHERE job_id = ? ORDER BY id ASC",
                (job_id,),
            ).fetchall()
        ]
        checkpoints = [
            dict(row)
            for row in conn.execute(
                "SELECT kind, payload_json FROM checkpoints"
                " WHERE job_id = ? ORDER BY id ASC",
                (job_id,),
            ).fetchall()
        ]
    finally:
        conn.close()

    done_count = sum(1 for task in tasks if task["status"] == STATUS_DONE)
    pending_connector_tasks = [
        task
        for task in tasks
        if task["status"] == STATUS_PENDING
        and task["kind"] in {"fec_search", "state_election_search"}
    ]
    checkpoint_kinds = {checkpoint["kind"] for checkpoint in checkpoints}
    diagnostics: list[dict[str, Any]] = []
    if not pending_connector_tasks:
        return diagnostics

    pending_kinds = sorted({str(task["kind"]) for task in pending_connector_tasks})
    if done_count >= HEURISTIC_CHECK_EVERY_N and "synthesis_done" not in checkpoint_kinds:
        diagnostics.append(
            {
                "condition": "synthesis_cadence_pending_stall",
                "tasks_done": done_count,
                "pending_task_kinds": pending_kinds,
                "message": (
                    "candidate-roster backtest reached synthesis cadence with"
                    " pending connector tasks but no synthesis_done checkpoint"
                ),
            }
        )
    if done_count >= HEURISTIC_CHECK_EVERY_N * 2 and "critique_done" not in checkpoint_kinds:
        diagnostics.append(
            {
                "condition": "critique_cadence_pending_stall",
                "tasks_done": done_count,
                "pending_task_kinds": pending_kinds,
                "message": (
                    "candidate-roster backtest reached critique cadence with"
                    " pending connector tasks but no critique_done checkpoint"
                ),
            }
        )
    return diagnostics


def test_candidate_roster_handoff_rejects_grouped_state_task_without_state(
    tmp_path: Path,
) -> None:
    job = _make_handoff_job(tmp_path)
    plan = _candidate_roster_handoff_plan(
        [
            TaskSpec(
                kind="state_election_search",
                payload={
                    "query": "2026 House and Senate candidates in AL, AK, AZ, AR, CA",
                    "sub_question": "Find 2026 House and Senate candidates in AL, AK, AZ, AR, CA.",
                    "cycle": 2026,
                    "office": "House",
                },
            )
        ]
    )

    with pytest.raises(PlanParseError, match="state"):
        plan_module._enqueue_plan_tasks(job, plan)  # noqa: SLF001

    assert _task_payloads(job.db_path, job.id) == []
    [event] = _event_payloads(job.db_path, job.id, "connector_contract_rejected")
    assert event["stage"] == "pre_enqueue"
    assert event["kind"] == "state_election_search"
    assert event["plan_task_index"] == 0
    assert "state" in event["message"]


def test_candidate_roster_handoff_normalizes_full_state_name_before_enqueue(
    tmp_path: Path,
) -> None:
    job = _make_handoff_job(tmp_path)
    plan = _candidate_roster_handoff_plan(
        [
            TaskSpec(
                kind="state_election_search",
                payload={
                    "query": "2026 House candidates",
                    "sub_question": "Find Colorado 2026 House candidate rows.",
                    "cycle": 2026,
                    "state": "Colorado",
                    "office": "House",
                },
            )
        ]
    )

    plan_module._enqueue_plan_tasks(job, plan)  # noqa: SLF001

    [payload] = _task_payloads(job.db_path, job.id)
    assert payload["state"] == "CO"
    [event] = _event_payloads(job.db_path, job.id, "connector_contract_repaired")
    assert event["stage"] == "pre_enqueue"
    assert event["before"]["state"] == "Colorado"
    assert event["after"]["state"] == "CO"


def test_candidate_roster_handoff_repairs_empty_fec_candidates_to_enumeration(
    tmp_path: Path,
) -> None:
    job = _make_handoff_job(tmp_path)
    plan = _candidate_roster_handoff_plan(
        [
            TaskSpec(
                kind="fec_search",
                payload={
                    "query": "",
                    "sub_question": "Enumerate 2026 California House candidates from FEC.",
                    "kind": "candidates",
                    "cycle": 2026,
                    "office": "House",
                    "state": "California",
                },
            )
        ]
    )

    plan_module._enqueue_plan_tasks(job, plan)  # noqa: SLF001

    [payload] = _task_payloads(job.db_path, job.id)
    assert payload["kind"] == "candidates_enumerate"
    assert payload["office"] == "H"
    assert payload["state"] == "CA"
    [event] = _event_payloads(job.db_path, job.id, "connector_contract_repaired")
    assert event["after"]["kind"] == "candidates_enumerate"


def test_candidate_roster_handoff_rejects_empty_fec_candidates_without_filters(
    tmp_path: Path,
) -> None:
    job = _make_handoff_job(tmp_path)
    plan = _candidate_roster_handoff_plan(
        [
            TaskSpec(
                kind="fec_search",
                payload={
                    "query": "",
                    "sub_question": "Search all FEC candidates with an empty query.",
                    "kind": "candidates",
                },
            )
        ]
    )

    with pytest.raises(PlanParseError, match="query must be non-empty"):
        plan_module._enqueue_plan_tasks(job, plan)  # noqa: SLF001

    assert _task_payloads(job.db_path, job.id) == []
    [event] = _event_payloads(job.db_path, job.id, "connector_contract_rejected")
    assert event["kind"] == "fec_search"
    assert "query must be non-empty" in event["message"]


def test_candidate_roster_backtest_reports_missing_cadence_checkpoints(
    tmp_path: Path,
) -> None:
    job = _make_handoff_job(tmp_path)
    done_specs = [
        TaskSpec(kind="web_search", payload={"query": f"completed task {idx}"})
        for idx in range(HEURISTIC_CHECK_EVERY_N * 2)
    ]
    pending_spec = TaskSpec(
        kind="state_election_search",
        payload={
            "query": "2026 House candidates",
            "sub_question": "Find Colorado state-election House candidate rows.",
            "cycle": 2026,
            "state": "CO",
            "office": "House",
        },
    )
    ids = enqueue(job, [*done_specs, pending_spec], plan_version=1)
    conn = db.connect(job.db_path)
    try:
        with conn:
            for task_id in ids[:-1]:
                conn.execute(
                    "UPDATE tasks SET status = ? WHERE id = ?",
                    (STATUS_DONE, task_id),
                )
    finally:
        conn.close()

    diagnostics = _candidate_roster_stall_diagnostics(job.db_path, job.id)

    assert [item["condition"] for item in diagnostics] == [
        "synthesis_cadence_pending_stall",
        "critique_cadence_pending_stall",
    ]
    assert all(item["tasks_done"] == HEURISTIC_CHECK_EVERY_N * 2 for item in diagnostics)
    assert all(item["pending_task_kinds"] == ["state_election_search"] for item in diagnostics)


@pytest.mark.asyncio
async def test_candidate_roster_fixture_backtest_completes_or_gaps_honestly(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_root = Path(__file__).parent / "fixtures"
    _patch_httpx(monkeypatch, fixture_root)
    _patch_state_election(monkeypatch)
    monkeypatch.setattr(synth_module, "Agent", _StubAgent)
    job, plan = _make_job(tmp_path)

    result = await run_loop(
        job,
        router=_FailingSynthRouter(),
        plan=plan,
        handlers=default_handlers(_FailingSynthRouter()),
        max_tasks=20,
        retry_waits=(0,),
    )
    synth_out = await synth_module.final_synthesis(
        job,
        plan,
        router=_FailingSynthRouter(),
    )

    listed = artifacts.list_artifacts(job)
    assert [item["name"] for item in listed] == ["candidates"]
    csv_path = job.root / listed[0]["csv_path"]
    assert csv_path.exists()

    schema, rows = artifacts.read_artifact(job, "candidates")
    assert REQUIRED_COLUMNS.issubset({column.name for column in schema.columns})
    assert REQUIRED_COLUMNS.issubset(rows[0].keys())
    assert len(rows) == 3
    assert {row["candidate_name"] for row in rows} == {
        "DOE, JANE",
        "SMITH, ROBERT",
        "Ana Candidate",
    }
    assert all(row["party"] for row in rows)
    assert all(row["source_url"].startswith("http") for row in rows)
    assert not any("portal" in row["candidate_name"].lower() for row in rows)

    csv_rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
    assert len(csv_rows) == len(rows)
    assert REQUIRED_COLUMNS.issubset(csv_rows[0].keys())

    units = coverage.list_units(job)
    statuses = {unit.status for unit in units}
    assert statuses <= TERMINAL_COVERAGE
    assert "pending" not in statuses
    assert any(unit.status == "confirmed_gap" for unit in units)
    assert result["completed"] is False
    assert result["completion_reason"] == "confirmed_gap"

    assert synth_out.model == "deterministic_fallback"
    report = (job.root / "report.md").read_text(encoding="utf-8")
    assert "## Artifacts" in report
    assert "[CSV](artifacts/candidates.csv)" in report
    assert "## Confirmed Gaps" in report
    assert "Maryland SBE fixture" in report
