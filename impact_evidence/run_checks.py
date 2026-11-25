"""Run existing regressions on synthetic inputs and retain command provenance."""
import importlib.metadata
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
from time import perf_counter_ns
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "impact_evidence"
RAW = OUT / "raw"
ROBOT = Path("automation/uipath/VantageNet.Reporting")
GIT = ["git", "-c", f"safe.directory={ROOT.as_posix()}"]


def now():
    return datetime.now(timezone.utc).isoformat()


def capture(name, argv, cwd, env, sources):
    started, clock = now(), perf_counter_ns()
    try:
        result = subprocess.run(argv, cwd=cwd, env=env, capture_output=True,
                                text=True, encoding="utf-8", errors="replace", timeout=180)
        rc, stdout, stderr = result.returncode, result.stdout, result.stderr
    except (OSError, subprocess.TimeoutExpired) as error:
        rc = None
        stdout = getattr(error, "stdout", "") or ""
        stderr = getattr(error, "stderr", "") or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", "replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", "replace")
        stderr += str(error) + "\n"
    finished, elapsed = now(), (perf_counter_ns() - clock) / 1_000_000_000
    log = RAW / f"{name}.log"
    log.write_text(
        f"command: {subprocess.list2cmdline(argv)}\ncwd: {cwd}\n"
        f"sources: {', '.join(sources)}\nstart_utc: {started}\nend_utc: {finished}\n"
        f"duration_seconds: {elapsed}\nexit_code: {rc}\n"
        f"\n[stdout]\n{stdout}\n[stderr]\n{stderr}", encoding="utf-8",
    )
    return dict(name=name, command=argv, cwd=str(cwd), sources=sources, start_utc=started,
                end_utc=finished, elapsed_seconds=elapsed, exit_code=rc,
                log=log.relative_to(OUT).as_posix()), stdout, stderr


def main():
    RAW.mkdir(exist_ok=True)
    env = os.environ.copy()
    for key in list(env):
        if key.upper() in {"HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "OPENAI_API_KEY"}:
            env.pop(key)
    env.update(
        PYTHONDONTWRITEBYTECODE="1", PYTHON_DOTENV_DISABLED="1", PYTHONIOENCODING="utf-8",
        OPENROUTER_API_KEY="", OPENROUTER_BASE_URL="http://127.0.0.1:1/v1",
        LLM_MODEL="synthetic-test-model", NO_PROXY="127.0.0.1,localhost", NO_COLOR="1",
        UIPATH_CLI_DISABLE_AUTOINSTALL="true", UIPATH_CLI_DISABLE_VERSION_SYNC="true",
    )
    records = []

    def save(name, argv, cwd, sources):
        metadata, stdout, stderr = capture(name, argv, cwd, env, sources)
        records.append(metadata)
        print(name, metadata["exit_code"], metadata["log"], flush=True)
        return metadata, stdout, stderr

    _, branch, _ = save("branch", [*GIT, "branch", "--show-current"], ROOT, [".git/HEAD"])
    _, commit, _ = save("commit", [*GIT, "rev-parse", "HEAD"], ROOT, [".git/HEAD"])
    save("dotnet_sdks", ["dotnet", "--list-sdks"], ROOT, ["dotnet"])
    save("ollama_lookup", ["where.exe", "ollama"], ROOT, ["PATH"])
    save("ollama_loopback_probe", [sys.executable, "-c",
         "import httpx; r=httpx.get('http://127.0.0.1:11434/api/tags', timeout=2, trust_env=False); "
         "r.raise_for_status(); print([m.get('name') for m in r.json()['models']])"],
         ROOT, ["Ollama loopback /api/tags (probe tanpa input KPI)"])
    _, uip, _ = save("uip_lookup", ["where.exe", "uip"], ROOT, ["PATH"])
    cli = env.get("UIPATH_CLI") or next(iter(uip.splitlines()), None)
    dependencies = {}
    for package in ("fastapi", "sqlalchemy", "openpyxl", "httpx", "openai", "python-dotenv"):
        dependencies[package] = importlib.metadata.version(package)
    save("pptx_import", [sys.executable, "-c",
         "import pptx, pypdfium2, PIL; print('python-pptx', pptx.__version__); print('Pillow', PIL.__version__)"],
         ROOT, ["automation/uipath/VantageNet.Reporting/Tests/requirements-test.txt"])

    with TemporaryDirectory(prefix="check-db-", dir=RAW) as temp:
        directory = Path(temp)
        env.update(TMP=str(directory), TEMP=str(directory),
                   DATABASE_URL=f"sqlite:///{(directory / 'isolated.db').as_posix()}",
                   DEMO_DATABASE_URL=f"sqlite:///{(directory / 'demo.db').as_posix()}",
                   VANTAGENET_DISPOSABLE="1", VANTAGENET_DISPOSABLE_INSTANCE_ID="impact-regressions")
        for name in ("test_product_flow", "test_ai_revision", "test_demo"):
            metadata, stdout, stderr = save(name, [sys.executable, "-m", "unittest", "-v", name],
                ROOT / "backend", [f"backend/{name}.py", "frontend/public/demo/"])
            metadata["test_cases"] = dict(re.findall(
                r"^(test_[a-zA-Z0-9_]+) \([^)]+\) \.\.\. (ok|FAIL|ERROR|skipped[^\n]*)",
                stdout + "\n" + stderr, re.MULTILINE,
            ))
            count = re.search(r"Ran (\d+) tests? in ", stderr)
            metadata["tests_run"] = int(count[1]) if count else None

        # Run robot tests against a clean copy so their generated Output never touches the product tree.
        test_root = directory / "robot-checks"
        _, tracked, _ = save("robot_tracked_paths", [*GIT, "ls-files", "--",
            ROBOT.as_posix(), "frontend/public/demo/divisions/ed.xlsx"], ROOT,
            [ROBOT.as_posix(), "frontend/public/demo/divisions/ed.xlsx"])
        for relative in tracked.splitlines():
            path = Path(relative)
            destination = test_root / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / path, destination)
        if cli:
            env["UIPATH_CLI"] = cli
        for name in ("test_mapping_review", "test_controlled_confirm", "test_report_bundle", "test_narrative_pptx"):
            path = ROBOT / "Tests" / f"{name}.py"
            metadata, stdout, stderr = save(name, [sys.executable, str(path)], test_root, [path.as_posix()])
            metadata["blocked_by_missing_cli"] = "Set UIPATH_CLI to your existing uip executable/launcher" in stderr

    save("product_worktree", [*GIT, "status", "--porcelain=v1", "--",
         "backend", "automation", "frontend/public/demo/divisions"], ROOT,
         ["backend/", "automation/", "frontend/public/demo/divisions/"])
    (OUT / "test_runs.json").write_text(json.dumps(dict(
        command=[sys.executable, str(Path(__file__).relative_to(ROOT))], finished_utc=now(),
        branch=branch.strip(), commit=commit.strip(), scenario="Demo North",
        python=sys.version, dependencies=dependencies, records=records,
    ), indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
