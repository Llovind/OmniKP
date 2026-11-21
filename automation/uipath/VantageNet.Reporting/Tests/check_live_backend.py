"""Exercise the ED fixture against the live AI provider on a temporary database.

This checks the backend contract only. The mapping decision is a test input.
Run from any directory with the backend requirements and local credentials.
"""

import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

from dotenv import load_dotenv
from fastapi.testclient import TestClient


def checked(response, label):
    if response.is_error:
        raise SystemExit(f"{label} failed (HTTP {response.status_code}). Check local provider/backend logs.")
    return response.json()


def main():
    root = Path(__file__).resolve().parents[4]
    backend = root / "backend"
    load_dotenv(backend / ".env")
    if not os.environ.get("OPENROUTER_API_KEY"):
        raise SystemExit("Configure OPENROUTER_API_KEY locally before running this live check.")
    with TemporaryDirectory(prefix="vantagenet-ed-") as directory:
        os.environ["DATABASE_URL"] = f"sqlite:///{(Path(directory) / 'disposable.db').as_posix()}"
        os.environ["VANTAGENET_DISPOSABLE"] = "1"
        os.environ["VANTAGENET_DISPOSABLE_INSTANCE_ID"] = "ed-contract-smoke"
        sys.path.insert(0, str(backend))
        from database import DimDomain, SessionLocal, engine, init_db
        from main import app

        try:
            init_db()
            with SessionLocal.begin() as db:
                db.add(DimDomain(domain_id=1, domain_name="Telecommunications", domain_code="digital_infra"))
            base = "/api/v1/domains/1"
            with TestClient(app) as client:
                workbook = root / "frontend/public/demo/divisions/ed.xlsx"
                preview = checked(client.post(f"{base}/submissions/preview",
                    files={"file": (workbook.name, workbook.read_bytes())},
                    data={"division": "ED", "report_date": "2026-06-30", "sheet_name": "Report",
                          "header_row": 4, "header_depth": 1}), "Live mapping preview")
                mapping = {column: item["target"] for column, item in preview["column_mapping"].items()}
                submission = f"{base}/submissions/{preview['submission_id']}"
                review = checked(client.post(f"{submission}/review", json={"mapping": mapping}), "Mapping validation")
                if not review["can_confirm"] or review["valid_readings"] != 26:
                    raise SystemExit("Live mapping did not validate to 26 ED readings.")
                checked(client.post(f"{submission}/confirm", json={"mapping": mapping}), "Test import")
                detail = checked(client.get(submission), "Confirmed submission")
                selected = next(reading for reading in detail["readings"] if reading["status"] == "RED")
                report = checked(client.post(f"{base}/report-bundles", json={
                    "submission_id": preview["submission_id"], "fact_id": selected["fact_id"],
                    "bundle_id": "ed-live-backend-smoke", "revision": "v1",
                }), "Report export")
                print(json.dumps({
                    "confirmed_readings": len(detail["readings"]), "schema": report["schema_version"],
                    "fact_id": report["scope"]["fact_id"], "source_row": selected["source_row"],
                    "feedback_origin": report["snapshot"]["feedback"]["origin"],
                    "evidence_status": report["evidence_status"], "ai_invoked": report["ai_invoked"],
                    "citation_verified": report["snapshot"]["narrative"]["grounding"]["citation_verified"],
                }, indent=2))
                if report["evidence_status"] != "draft_ready":
                    raise SystemExit("Live report export did not produce a reviewable draft.")
        finally:
            engine.dispose()


if __name__ == "__main__":
    main()
