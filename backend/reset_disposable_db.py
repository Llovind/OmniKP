r"""Reset and initialize an isolated disposable SQLite test database for VantageNet.

Usage (from backend/):
    ..\.venv\Scripts\python.exe reset_disposable_db.py
"""
import argparse
import json
import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
PROTECTED_DBS = {"omnikpi.db", "omnikpi-demo.db"}


def reset_disposable_db(db_path: Path, instance_id: str) -> dict:
    """Recreate an empty disposable SQLite database containing only domain 1."""
    resolved = db_path.resolve()
    if resolved.name.lower() in PROTECTED_DBS:
        raise SystemExit(
            f"Refusing to reset protected database {resolved.name!r}. "
            "Specify an isolated disposable database path (e.g. disposable_test.db)."
        )

    resolved.parent.mkdir(parents=True, exist_ok=True)
    for suffix in ("", "-wal", "-shm", "-journal"):
        candidate = Path(str(resolved) + suffix)
        if candidate.exists():
            candidate.unlink()

    db_url = f"sqlite:///{resolved.as_posix()}"
    os.environ["DATABASE_URL"] = db_url
    os.environ["VANTAGENET_DISPOSABLE"] = "1"
    os.environ["VANTAGENET_DISPOSABLE_INSTANCE_ID"] = instance_id

    from database import DimDomain, FactKPI, SessionLocal, Submission, engine, init_db

    init_db()
    with SessionLocal() as db:
        if not db.query(DimDomain).filter_by(domain_id=1).first():
            db.add(DimDomain(domain_id=1, domain_name="Telecommunications", domain_code="digital_infra"))
            db.commit()
        submissions_count = db.query(Submission).count()
        readings_count = db.query(FactKPI).count()
    engine.dispose()

    return {
        "disposable": True,
        "instance_id": instance_id,
        "database_path": resolved.as_posix(),
        "database_url": db_url,
        "domain_id": 1,
        "submissions": submissions_count,
        "readings": readings_count,
        "base_url": "http://127.0.0.1:8000",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Reset an isolated disposable VantageNet test database.")
    parser.add_argument(
        "--db",
        default=str(BACKEND_DIR / "disposable_test.db"),
        help="Path to the disposable SQLite file (default: backend/disposable_test.db).",
    )
    parser.add_argument(
        "--instance-id",
        default="disposable-local-test",
        help="Explicit instance_id returned by GET /_development/instance.",
    )
    args = parser.parse_args()

    summary = reset_disposable_db(Path(args.db), args.instance_id.strip() or "disposable-local-test")
    print(json.dumps(summary, indent=2))
    print("\nStart the disposable backend from backend/ with:")
    print(f'$env:DATABASE_URL="{summary["database_url"]}"')
    print('$env:VANTAGENET_DISPOSABLE="1"')
    print(f'$env:VANTAGENET_DISPOSABLE_INSTANCE_ID="{summary["instance_id"]}"')
    print(r"..\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000")


if __name__ == "__main__":
    main()
