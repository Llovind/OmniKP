"""Run the synthetic ED backend flow with the configured provider and log usage."""
import json
import os
from time import perf_counter_ns
from urllib.parse import urlsplit
from uuid import uuid4

from dotenv import dotenv_values
import httpx
from openai import AsyncOpenAI

import run_ed


def main():
    settings = dotenv_values(run_ed.ROOT / "backend" / ".env")

    def config(name, default=""):
        return os.environ.get(name) or settings.get(name) or default

    key = config("OPENROUTER_API_KEY")
    base_url = config("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    model = config("LLM_MODEL", "meta-llama/llama-3.1-70b-instruct")
    endpoint = urlsplit(base_url)
    output = run_ed.ROOT / "output" / "impact-ed-live" / uuid4().hex
    output.mkdir(parents=True)
    summary = dict(timestamp_utc=run_ed.now(), provider=endpoint.hostname,
                   requested_model=model, data="synthetic ED", calls=[])

    def prepare(run_dir, instance):
        run_ed.prepare_environment(run_dir, instance)
        os.environ.update(OPENROUTER_API_KEY=key, OPENROUTER_BASE_URL=base_url, LLM_MODEL=model)

    def configure(harvester, feedback_rca, run_dir, calls):
        async def started(request):
            context = json.loads(json.loads(request.content)["messages"][1]["content"])
            request.extensions["impact_clock"] = perf_counter_ns()
            request.extensions["impact_start_utc"] = run_ed.now()
            request.extensions["impact_step"] = "preview_mapping" if isinstance(context, list) else "rca"

        async def finished(response):
            await response.aread()
            request = response.request
            try:
                body = response.json()
            except ValueError:
                body = {}
            usage = body.get("usage") or {}
            record = dict(langkah=request.extensions["impact_step"],
                          model=body.get("model"), mulai=request.extensions["impact_start_utc"],
                          selesai=run_ed.now(), durasi_detik=run_ed.duration(
                              request.extensions["impact_clock"]),
                          jenis="live provider HTTP", status_http=response.status_code,
                          usage_input=usage.get("prompt_tokens"),
                          usage_output=usage.get("completion_tokens"),
                          usage_total=usage.get("total_tokens"))
            summary["calls"].append(record)
            calls.append({name: value for name, value in record.items()
                          if name not in ("status_http", "usage_total")})

        client = AsyncOpenAI(api_key=key, base_url=base_url, max_retries=0,
                             http_client=httpx.AsyncClient(
                                 trust_env=False, event_hooks={"request": [started],
                                                               "response": [finished]}))
        harvester._client = feedback_rca._client = client
        return client

    try:
        if not key:
            summary["status"] = "tidak ada key"
            return
        if endpoint.scheme != "https" or not endpoint.hostname or endpoint.username or endpoint.password:
            summary["status"] = "endpoint provider HTTPS tidak valid"
            return
        run_ed.OUT = output
        run_ed.COMMAND = ["python", "impact_evidence/run_ed_live.py"]
        run_ed.main(prepare, configure, "backend_with_live_provider", "backend_ledger_live")
        summary["status"] = "backend flow completed"
        ledger = json.loads((output / "ledger_diff.json").read_text(encoding="utf-8"))
        summary["ledger"] = {key: ledger[key] for key in
                             ("expected_readings", "observed_readings", "fields")}
    except Exception as error:
        summary["status"] = "backend flow failed"
        summary["error_type"] = type(error).__name__
        raise SystemExit(1) from None
    finally:
        summary["finished_utc"] = run_ed.now()
        run_ed.save_json(output / "provider-run.json", summary)
        print(output / "provider-run.json")


if __name__ == "__main__":
    main()
