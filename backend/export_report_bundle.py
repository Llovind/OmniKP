r"""Export one consistent single-reading VantageNet report bundle JSON file.

Usage (from backend/):
    ..\.venv\Scripts\python.exe export_report_bundle.py --submission-id <id> --fact-id <id> --output bundle.json
"""
import argparse
import asyncio
import json
import os
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Export a single-reading VantageNet report bundle JSON.")
    parser.add_argument("--submission-id", required=True, help="Confirmed submission UUID.")
    parser.add_argument("--fact-id", required=True, type=int, help="Exact fact_id belonging to that submission.")
    parser.add_argument("--output", required=True, help="Destination JSON file path.")
    parser.add_argument("--bundle-id", default="backend-bundle", help="Bundle ID ([A-Za-z0-9_-]{1,48}).")
    parser.add_argument("--revision", default="v1", help="Bundle revision (v1, v2, ...).")
    parser.add_argument("--domain-id", default=1, type=int, help="Domain ID (default: 1).")
    parser.add_argument("--db", default="", help="Optional SQLite file path (overrides DATABASE_URL).")
    args = parser.parse_args()

    if args.db:
        db_path = Path(args.db).resolve()
        os.environ["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"

    from dotenv import load_dotenv

    load_dotenv()

    from database import SessionLocal, init_db
    from services.report_bundle import build_report_bundle

    init_db()
    with SessionLocal() as db:
        bundle = asyncio.run(
            build_report_bundle(
                db=db,
                domain_id=args.domain_id,
                submission_id=args.submission_id,
                fact_id=args.fact_id,
                bundle_id=args.bundle_id,
                revision=args.revision,
            )
        )

    out_path = Path(args.output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(bundle, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp_path, out_path)

    print(
        json.dumps(
            {
                "output": out_path.as_posix(),
                "contract": bundle["contract"],
                "schema_version": bundle["schema_version"],
                "bundle_id": bundle["bundle_id"],
                "revision": bundle["revision"],
                "evidence_status": bundle["evidence_status"],
                "ai_invoked": bundle["ai_invoked"],
                "fact_id": bundle["scope"]["fact_id"],
                "reading_sha256": bundle["producer"]["reading_sha256"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
