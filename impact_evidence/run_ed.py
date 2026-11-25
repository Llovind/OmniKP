"""Measure the ED backend path with a fresh DB and an in-process synthetic model.

No credentials are loaded. The model transport cannot make a network request.
The UI attended phases and the real provider are not part of this measurement.
"""
import csv
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from decimal import Decimal
import os
import socket
import sys
from threading import Thread
from time import perf_counter_ns, sleep
from uuid import uuid4

import httpx
from fastapi.testclient import TestClient
from openai import AsyncOpenAI
import uvicorn


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "impact_evidence"
FIXTURE_DIR = ROOT / "frontend/public/demo/divisions"
WORKBOOK = FIXTURE_DIR / "ed.xlsx"
EXPECTED = FIXTURE_DIR / "expected-readings.json"
COMMAND = [sys.executable, "impact_evidence/run_ed.py"]
MODEL = "synthetic-offline-mock"
MACHINE = "mesin"
HUMAN = "menunggu_keputusan_manusia"
TIME_COLUMNS = ("langkah", "mulai", "selesai", "durasi_detik", "jenis")
FIELDS = ("actual_value", "target_value", "location_name", "source_row")
RUNBOOK = "VantageNet/ED_DEMO_RUNBOOK.md"


def now():
    return datetime.now(timezone.utc).isoformat()


def duration(start):
    return str(Decimal(perf_counter_ns() - start) / Decimal(1_000_000_000))


def save_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def save_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def file_hash(path):
    return sha256(path.read_bytes()).hexdigest()


@contextmanager
def backend_client(app, provenance):
    """Prefer loopback HTTP on a fresh port. Preserve ASGI evidence if binding fails."""
    sock = socket.socket()
    server = thread = None
    try:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning", access_log=False)
        server = uvicorn.Server(config)
        thread = Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
        thread.start()
        deadline = perf_counter_ns() + 5_000_000_000
        while thread.is_alive() and not server.started and perf_counter_ns() < deadline:
            sleep(0.025)
        if not server.started:
            raise RuntimeError("Uvicorn did not reach the started state on the fresh loopback socket.")
        origin = f"http://127.0.0.1:{port}"
        with httpx.Client(base_url=origin, timeout=5, trust_env=False) as probe:
            probe.get("/api/v1/health").raise_for_status()
    except (OSError, RuntimeError, httpx.HTTPError) as error:
        provenance["loopback_failure"] = str(error)
        print(str(error), file=sys.stderr)
        if server:
            server.should_exit = True
        if thread:
            thread.join(6)
            if thread.is_alive():
                raise RuntimeError("Could not stop the loopback backend before fallback.") from error
        sock.close()
        provenance["transport"] = "FastAPI TestClient (ASGI in-process)"
        with TestClient(app) as client:
            yield client
    else:
        provenance["transport"] = "Uvicorn loopback HTTP on a fresh port"
        provenance["origin"] = origin
        try:
            with httpx.Client(base_url=origin, timeout=30, trust_env=False) as client:
                yield client
        finally:
            server.should_exit = True
            thread.join(6)
            sock.close()


def prepare_environment(run_dir, instance):
    for key in list(os.environ):
        if key.upper() in {"HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "OPENAI_API_KEY"}:
            os.environ.pop(key)
    os.environ.update(
        PYTHON_DOTENV_DISABLED="1", OPENROUTER_API_KEY="synthetic-placeholder",
        OPENROUTER_BASE_URL="http://127.0.0.1:1/v1", LLM_MODEL=MODEL,
        DATABASE_URL=f"sqlite:///{(run_dir / 'disposable.db').as_posix()}",
        DEMO_DATABASE_URL=f"sqlite:///{(run_dir / 'disposable-demo.db').as_posix()}",
        VANTAGENET_DISPOSABLE="1", VANTAGENET_DISPOSABLE_INSTANCE_ID=instance,
    )
    sys.path.insert(0, str(ROOT / "backend"))


def configure_mock(harvester, feedback_rca, run_dir, calls):
    async def respond(request):
        started, clock = now(), perf_counter_ns()
        payload = json.loads(request.content)
        context = json.loads(payload["messages"][1]["content"])
        if isinstance(context, list):
            step = "preview_mapping"
            content = {column["header"]: column["suggestion"] for column in context}
        else:
            step = "rca"
            feedback = context["feedback"][0]
            ref = feedback["feedback_id"]
            content = dict(root_cause=f"{feedback['explanation']} [F{ref}]",
                           prescriptive_action=f"{feedback['corrective_action']} [F{ref}]",
                           cited_feedback_ids=[ref])
        completion = json.dumps(content, ensure_ascii=False, separators=(",", ":"))
        response = httpx.Response(200, json=dict(
            id="synthetic-completion", object="chat.completion", model=MODEL,
            choices=[dict(index=0, message=dict(role="assistant", content=completion), finish_reason="stop")],
        ))
        elapsed, finished = duration(clock), now()
        evidence = run_dir / f"mock_{step}_{len(calls) + 1}.json"
        measured_input = len(json.dumps(payload["messages"], ensure_ascii=False,
                                        separators=(",", ":")).encode("utf-8"))
        measured_output = len(completion.encode("utf-8"))
        record = dict(
            langkah=step, model=payload["model"], mulai=started, selesai=finished,
            durasi_detik=elapsed, jenis="transport mock, bukan latensi inferensi",
            input_bytes=measured_input, output_bytes=measured_output,
            usage_input=None, usage_output=None,
            estimasi_input=(measured_input + 3) // 4, estimasi_output=(measured_output + 3) // 4,
            evidence=evidence.relative_to(OUT).as_posix(),
        )
        save_json(evidence, dict(command=COMMAND, record=record, payload=payload,
                                 completion_content=completion))
        calls.append(record)
        return response

    client = AsyncOpenAI(api_key="synthetic-placeholder", base_url="http://127.0.0.1:1/v1",
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(respond), trust_env=False),
        max_retries=0)
    harvester._client = feedback_rca._client = client
    return client


def compare_ledger(ledger, run_dir, mode):
    expected = [row for row in json.loads(EXPECTED.read_text(encoding="utf-8"))
                if row["division"] == "ED" and row["source_file"] == WORKBOOK.name]
    observed = list(ledger["readings"])
    counts = {field: dict(cocok=0, tidak_cocok=0, tidak_ada=0) for field in FIELDS}
    details = []
    remaining = observed.copy()
    for row in expected:
        candidates = [actual for actual in remaining if all(
            row[field] == actual.get(field) for field in ("division", "kpi_name", "date", "source_file")
        )]
        matches = [item for item in candidates if item.get("source_row") == row["source_row"]]
        if not matches:
            matches = [item for item in candidates if item.get("location_name") == row["location_name"]]
        actual = matches[0] if len(matches) == 1 else None
        if actual is not None:
            remaining.remove(actual)
        for field, counter in counts.items():
            other = actual.get(field) if actual is not None else None
            status = "tidak_ada" if actual is None else "cocok" if row[field] == other else "tidak_cocok"
            counter[status] += 1
            if status != "cocok":
                details.append(dict(kpi=row["kpi_name"], expected_row=row["source_row"],
                                    field=field, expected=row[field], observed=other, status=status))
    save_json(OUT / "ledger_diff.json", dict(
        command=COMMAND, timestamp_utc=now(), mode=mode,
        expected_path=EXPECTED.relative_to(ROOT).as_posix(), expected_sha256=file_hash(EXPECTED),
        ledger= (run_dir / "backend-ledger.json").relative_to(OUT).as_posix(),
        ledger_sha256=file_hash(run_dir / "backend-ledger.json"),
        join="division, kpi_name, date, source_file; source_row first, unique location fallback",
        expected_readings=len(expected), observed_readings=len(observed),
        count_matches=len(expected) == len(observed), missing_rows=counts["source_row"]["tidak_ada"],
        unmatched_observed=remaining, fields=counts, differences=details,
    ))


def main(prepare=prepare_environment, configure_provider=configure_mock,
         mode="backend_with_mock_provider", ledger_mode="backend_ledger_offline_mock"):
    nonce = str(uuid4())
    raw = OUT / "raw"
    run_dir = raw / ("ed-" + nonce)
    run_dir.mkdir(parents=True)
    provenance = dict(command=COMMAND, cwd=str(ROOT), timestamp_utc=now(), instance_id=nonce,
        scenario="Demo North", selected_source_row=5, mode=mode,
        runbook=RUNBOOK, workbook=WORKBOOK.relative_to(ROOT).as_posix(), workbook_sha256=file_hash(WORKBOOK),
        run_dir=run_dir.relative_to(OUT).as_posix(), operations=[])
    rows = [dict(langkah=step, jenis=MACHINE) for step in
            ("preview", "review", "confirm", "fetch bundle", "adapt", "generate PPTX")]
    rows.extend(dict(langkah=step, jenis=HUMAN) for step in
                ("review keputusan mapping", "otorisasi impor", "persetujuan narasi"))
    calls = []

    def request(client, step, method, route, sources, **kwargs):
        started, clock = now(), perf_counter_ns()
        response = client.request(method, route, **kwargs)
        elapsed, finished = duration(clock), now()
        step_record = dict(langkah=f"backend.{step}", mulai=started, selesai=finished,
                           durasi_detik=elapsed, jenis=MACHINE)
        target = run_dir / ("backend-ledger.json" if step == "get_ledger" else f"{step}.json")
        target.write_text(response.text, encoding="utf-8")
        rows.append(step_record)
        provenance["operations"].append(dict(
            **step_record, method=method, route=route, status_code=response.status_code,
            sources=sources, response=target.relative_to(OUT).as_posix(),
        ))
        response.raise_for_status()
        return response.json()

    prepare(run_dir, nonce)
    try:
        from database import engine
        from agents import feedback_rca, harvester
        from main import app

        provider = configure_provider(harvester, feedback_rca, run_dir, calls)
        backend_lifespan = app.router.lifespan_context

        @asynccontextmanager
        async def measured_lifespan(application):
            async with backend_lifespan(application):
                try:
                    yield
                finally:
                    await provider.close()

        app.router.lifespan_context = measured_lifespan
        try:
            with backend_client(app, provenance) as client:
                base = "/api/v1/domains/1"
                identity = request(client, "instance", "GET", "/_development/instance", ["backend/main.py", RUNBOOK])
                assert identity["disposable"] and identity["instance_id"] == nonce
                preview = request(client, "preview", "POST", f"{base}/submissions/preview",
                    [WORKBOOK.relative_to(ROOT).as_posix(), "backend/services/intake.py", RUNBOOK],
                    files={"file": (WORKBOOK.name, WORKBOOK.read_bytes())},
                    data=dict(division="ED", report_date="2026-06-30", sheet_name="Report",
                              header_row=4, header_depth=1))
                mapping = {"mapping": {key: value["target"] for key, value in preview["column_mapping"].items()}}
                save_json(run_dir / "programmatic-mapping.json", mapping)
                loc = f"{base}/submissions/{preview['submission_id']}"
                review = request(client, "review", "POST", loc + "/review",
                    ["backend/routers/submissions.py", "programmatic-mapping.json", RUNBOOK], json=mapping)
                assert review["can_confirm"] and review["valid_readings"] == 26
                request(client, "confirm", "POST", loc + "/confirm",
                    ["backend/services/intake.py", "programmatic-mapping.json", RUNBOOK], json=mapping)
                ledger = request(client, "get_ledger", "GET", loc, ["backend/routers/submissions.py", RUNBOOK])
                assert ledger["status"] == "confirmed"
                compare_ledger(ledger, run_dir, ledger_mode)
                selected, = [row for row in ledger["readings"] if row["source_row"] == 5
                             and row["location_name"] == "Demo North" and row["status"] == "RED"]
                bundle = request(client, "fetch_bundle", "POST", f"{base}/report-bundles",
                    ["backend/services/report_bundle.py", "backend/agents/feedback_rca.py",
                     "backend-ledger.json", RUNBOOK], json=dict(
                         submission_id=preview["submission_id"], fact_id=selected["fact_id"],
                         bundle_id=f"ed-{preview['submission_id'].replace('-', '')}-{selected['fact_id']}",
                         revision="v1"))
                assert bundle["evidence_status"] == "draft_ready"
                assert bundle["snapshot"]["narrative"]["grounding"]["citation_verified"]
                provenance["completed_backend_flow"] = True
        finally:
            app.router.lifespan_context = backend_lifespan
            engine.dispose()
    except Exception as error:
        provenance["failure"] = str(error)
        raise
    finally:
        provenance["finished_utc"] = now()
        save_json(OUT / "ed_run.json", provenance)
        save_csv(OUT / "timing.csv", TIME_COLUMNS, rows)
        fields = ("langkah", "model", "mulai", "selesai", "durasi_detik", "jenis", "input_bytes",
                  "output_bytes", "usage_input", "usage_output", "estimasi_input", "estimasi_output", "evidence")
        save_csv(OUT / "ai_timing_and_tokens.csv", fields, calls)
    print(f"Demo North completed via {provenance['transport']}; run evidence: {run_dir.relative_to(OUT)}")


if __name__ == "__main__":
    main()
