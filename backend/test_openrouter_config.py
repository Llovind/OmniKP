"""Offline tests for OpenRouter configuration and the acceptance request shapes."""
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import AsyncMock, patch

import httpx

from agents import feedback_rca, harvester, openrouter_config
from services import intake


FREE_MODEL = "google/gemma-4-31b-it:free"
OPENROUTER_URL = "https://openrouter.ai/api/v1"
MOCK_KEY = "test-only-key"


class OpenRouterConfiguration(unittest.TestCase):
    def configured_clients(self, model, key, retries):
        env = dict(os.environ, LLM_MODEL=model, OPENROUTER_API_KEY=key,
                   OPENROUTER_BASE_URL=OPENROUTER_URL, DATABASE_URL="sqlite://")
        env.pop("OPENROUTER_MAX_RETRIES", None)
        if retries is not None:
            env["OPENROUTER_MAX_RETRIES"] = retries
        output = subprocess.check_output(
            [sys.executable, "-B", "-c", """
import json
from unittest.mock import AsyncMock, patch

with patch("dotenv.load_dotenv"):
    from agents import feedback_rca
    from routers.ai import ai_status

    status = ai_status()
    print(json.dumps({
        "configured": status["configured"],
        "mode": status["mode"],
        "mapping_model": status["model"],
        "mapping_provider": status["provider"],
        "mapping_retries": status["max_retries"],
        "rca_model": feedback_rca.LLM_MODEL,
        "rca_endpoint": str(feedback_rca._client.base_url).rstrip("/"),
        "rca_retries": feedback_rca._client.max_retries,
    }))
"""],
            cwd=Path(__file__).resolve().parent,
            env=env,
            text=True,
        )
        self.assertNotIn(MOCK_KEY, output)
        return json.loads(output)

    def test_free_model_and_retry_override_reach_both_clients(self):
        self.assertEqual(self.configured_clients(FREE_MODEL, MOCK_KEY, "0"), {
            "configured": True, "mode": "live",
            "mapping_model": FREE_MODEL, "mapping_provider": OPENROUTER_URL,
            "mapping_retries": 0, "rca_model": FREE_MODEL,
            "rca_endpoint": OPENROUTER_URL, "rca_retries": 0,
        })

    def test_paid_model_keeps_sdk_retry_default(self):
        model = "baidu/ernie-5.5-flash-preview"
        status = self.configured_clients(model, MOCK_KEY, None)
        self.assertEqual((status["mapping_model"], status["rca_model"]), (model, model))
        self.assertEqual((status["mapping_retries"], status["rca_retries"]), (2, 2))

    def test_missing_credential_does_not_report_live_mode(self):
        status = self.configured_clients(FREE_MODEL, "", "0")
        self.assertFalse(status["configured"])
        self.assertEqual(status["mode"], "unavailable")
        self.assertEqual(status["mapping_model"], FREE_MODEL)

    def test_invalid_retry_configuration_is_rejected(self):
        for retries in ("-1", "bad", ""):
            with self.subTest(retries=retries), patch.dict(os.environ, {"OPENROUTER_MAX_RETRIES": retries}):
                with self.assertRaisesRegex(ValueError, "nonnegative integer"):
                    openrouter_config.create_openrouter_client()

    def test_local_ollama_configuration_and_secret_isolation(self):
        local_url = "http://127.0.0.1:11434/v1"
        local_model = "qwen3.5:9b"
        real_secret = "sk-or-v1-secret-must-not-reach-local"
        env = dict(os.environ, LLM_MODEL=local_model, OPENROUTER_API_KEY=real_secret,
                   OPENROUTER_BASE_URL=local_url, OPENROUTER_MAX_RETRIES="0", DATABASE_URL="sqlite://")
        output = subprocess.check_output(
            [sys.executable, "-B", "-c", """
import json
from unittest.mock import patch

with patch("dotenv.load_dotenv"):
    from agents import feedback_rca, openrouter_config
    from routers.ai import ai_status

    status = ai_status()
    print(json.dumps({
        "configured": status["configured"],
        "mode": status["mode"],
        "mapping_model": status["model"],
        "mapping_provider": status["provider"],
        "rca_model": feedback_rca.LLM_MODEL,
        "rca_endpoint": str(feedback_rca._client.base_url).rstrip("/"),
        "rca_retries": feedback_rca._client.max_retries,
        "rca_key": feedback_rca.OPENROUTER_API_KEY,
        "client_key": feedback_rca._client.api_key,
    }))
"""],
            cwd=Path(__file__).resolve().parent,
            env=env,
            text=True,
        )
        self.assertNotIn(real_secret, output)
        parsed = json.loads(output)
        self.assertEqual(parsed, {
            "configured": True,
            "mode": "live",
            "mapping_model": local_model,
            "mapping_provider": local_url,
            "rca_model": local_model,
            "rca_endpoint": local_url,
            "rca_retries": 0,
            "rca_key": openrouter_config.LOCAL_PROVIDER_DUMMY_KEY,
            "client_key": openrouter_config.LOCAL_PROVIDER_DUMMY_KEY,
        })


class OpenRouterRequestShapes(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.requests = []
        self.report = {"columns": ["Realisasi", "Lokasi"],
                       "rows": [{"values": {"Realisasi": 91.7, "Lokasi": "North"}}]}
        self.reading = dict(fact_id=5, kpi_name="Availability", location_name="North",
                            date="2026-06-30", division="ED", actual_value=91.7,
                            target_value=99.0, higher_is_better=True, unit="%")
        self.evidence = [dict(feedback_id=17, explanation="The division reports a power interruption.",
                              corrective_action="Inspect the power feed.", origin="operator-api")]
        with patch.dict(os.environ, {"OPENROUTER_MAX_RETRIES": "0"}), patch.multiple(
                openrouter_config, OPENROUTER_BASE_URL=OPENROUTER_URL, OPENROUTER_API_KEY=MOCK_KEY):
            gateway = openrouter_config.create_openrouter_client()
        self.addAsyncCleanup(gateway.close)
        self.client = gateway.with_options(
            http_client=httpx.AsyncClient(transport=httpx.MockTransport(self.handle_request)),
        )
        self.addAsyncCleanup(self.client.close)
        for module in (harvester, feedback_rca):
            self.enterContext(patch.multiple(module, _client=self.client, LLM_MODEL=FREE_MODEL,
                                             OPENROUTER_API_KEY=MOCK_KEY))
        self.enterContext(patch.object(harvester, "OPENROUTER_BASE_URL", OPENROUTER_URL))
        self.rate_limited = False
        self.reasoning_only = False

    def handle_request(self, request):
        self.assertEqual(str(request.url), OPENROUTER_URL + "/chat/completions")
        body = json.loads(request.content)
        self.requests.append(body)
        self.assertEqual(body["model"], FREE_MODEL)
        self.assertEqual(body["temperature"], 0)
        for option in ("response_format", "reasoning", "models"):
            self.assertNotIn(option, body)
        if self.rate_limited:
            return httpx.Response(429, json={"error": {"message": "mock rate limit"}})

        self.assertEqual(body["max_tokens"], 6000)
        if "Map telco report headers" in body["messages"][0]["content"]:
            result = {"Realisasi": {"field": "actual_value", "reason": "Measured value"},
                      "Lokasi": {"field": "location_name", "reason": "Location name"}}
        else:
            result = {"root_cause": "The division reports a power interruption [F17].",
                      "prescriptive_action": "Inspect the power feed [F17].",
                      "cited_feedback_ids": [17], "insufficient_evidence": False}
        return httpx.Response(200, json={
            "id": "mock-completion", "object": "chat.completion", "created": 1, "model": FREE_MODEL,
            "choices": [{"index": 0, "finish_reason": "stop", "message": {
                "role": "assistant", "content": None if self.reasoning_only else json.dumps(result),
                "reasoning": "Separate reasoning is not final JSON.",
                "reasoning_details": [{"type": "reasoning.text", "text": "Separate reasoning"}],
            }}],
        })

    async def test_mapping_and_rca_validate_final_content(self):
        mapping, _, trace = await intake.ai_mapping(self.report, intake.suggest_mapping(self.report["columns"]))
        self.assertEqual(intake.plain_mapping(mapping), {"Realisasi": "actual_value", "Lokasi": "location_name"})
        self.assertEqual((trace["model"], trace["provider"], trace["mode"]), (FREE_MODEL, OPENROUTER_URL, "live"))
        rca = await feedback_rca.draft_from_evidence(self.reading, self.evidence)
        self.assertEqual(rca["llm_model"], FREE_MODEL)
        self.assertTrue(rca["ai_invoked"])
        self.assertEqual(rca["provider_status"], "response_accepted")
        self.assertTrue(rca["grounding"]["citation_verified"])
        self.assertEqual(rca["cited_feedback_ids"], [17])
        self.assertEqual(len(self.requests), 2)

    async def test_rate_limit_does_not_retry_mapping_or_rca(self):
        self.rate_limited = True
        with self.assertRaises(RuntimeError):
            await intake.ai_mapping(self.report, intake.suggest_mapping(self.report["columns"]))
        self.assertEqual(len(self.requests), 1)
        with self.assertRaises(feedback_rca.RCAProviderError) as error:
            await feedback_rca.draft_from_evidence(self.reading, self.evidence)
        self.assertEqual(error.exception.provider_status, "attempted_unconfirmed")
        self.assertEqual(error.exception.error_code, "request_failed")
        self.assertEqual(len(self.requests), 2)

    async def test_reasoning_without_final_content_is_rejected(self):
        self.reasoning_only = True
        with self.assertRaises(RuntimeError):
            await intake.ai_mapping(self.report, intake.suggest_mapping(self.report["columns"]))
        with self.assertRaises(feedback_rca.RCAProviderError) as error:
            await feedback_rca.draft_from_evidence(self.reading, self.evidence)
        self.assertEqual(error.exception.provider_status, "response_rejected")
        self.assertEqual(error.exception.error_code, "invalid_response")
        self.assertEqual(error.exception.diagnostics["parser_failure_category"], "empty_content")
        self.assertFalse(error.exception.diagnostics["content_present"])
        self.assertEqual(error.exception.diagnostics["response_model"], FREE_MODEL)
        self.assertEqual(error.exception.diagnostics["finish_reason"], "stop")
        self.assertNotIn("Separate reasoning", json.dumps(error.exception.diagnostics))
        self.assertEqual(len(self.requests), 2)

    async def test_gemma_free_synthetic_acceptance_request_and_response(self):
        syn_evidence = [dict(
            feedback_id=6,
            explanation="SYNTHETIC ACCEPTANCE SCENARIO — hypothetical test input.",
            corrective_action="Coordinate revised execution schedules.",
            origin="operator-api",
        )]
        syn_reply = json.dumps({
            "root_cause": "In this synthetic acceptance scenario, based on the hypothetical assumption in [F6], site-access coordination is pending.",
            "prescriptive_action": "Coordinate revised execution schedules [F6].",
            "cited_feedback_ids": [6],
            "insufficient_evidence": False,
        })
        with patch.object(feedback_rca._client.chat.completions, "create", new=AsyncMock(return_value=type("R", (), {
            "model": FREE_MODEL,
            "choices": [type("C", (), {"finish_reason": "stop", "message": type("M", (), {"content": syn_reply})()})()],
        })())) as mock_call:
            rca = await feedback_rca.draft_from_evidence(self.reading, syn_evidence, allow_synthetic_scenario=True)
        mock_call.assert_awaited_once()
        self.assertEqual(mock_call.call_args.kwargs["model"], FREE_MODEL)
        self.assertEqual(rca["llm_model"], FREE_MODEL)
        self.assertEqual(rca["evidence_status"], "ai_draft")
        self.assertEqual(rca["cited_feedback_ids"], [6])
        self.assertTrue(rca["grounding"]["citation_verified"])

    async def test_local_ollama_request_disables_thinking_and_strips_openrouter_secret(self):
        local_url = "http://127.0.0.1:11434/v1"
        local_model = "qwen3.5:9b"
        real_secret = "sk-or-v1-secret-must-not-be-sent"
        captured = []

        def local_handler(request):
            captured.append((dict(request.headers), json.loads(request.content)))
            reply = json.dumps({
                "root_cause": "In this synthetic acceptance scenario, based on the hypothetical assumption in [F6], planned deployment activities are awaiting site-access coordination.",
                "prescriptive_action": "Review the pending deployment list, identify activities awaiting access approval, and coordinate revised execution schedules with the responsible teams [F6].",
                "cited_feedback_ids": [6],
                "insufficient_evidence": False,
            })
            return httpx.Response(200, json={
                "id": "local-ollama-1",
                "object": "chat.completion",
                "created": 1,
                "model": local_model,
                "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": reply}}],
            })

        with patch.dict(os.environ, {"OPENROUTER_MAX_RETRIES": "0"}), patch.multiple(
            openrouter_config,
            OPENROUTER_BASE_URL=local_url,
            OPENROUTER_API_KEY=openrouter_config.effective_provider_api_key(local_url, real_secret),
        ):
            local_client = openrouter_config.create_openrouter_client()
        self.addAsyncCleanup(local_client.close)
        transport_client = httpx.AsyncClient(
            transport=httpx.MockTransport(local_handler),
            event_hooks=local_client._client.event_hooks,
        )
        local_client = local_client.with_options(http_client=transport_client)
        self.addAsyncCleanup(local_client.close)

        syn_reading = dict(
            fact_id=12, kpi_name="DEP-WHF-Deployment Alpro", location_name="Demo South",
            date="2026-06-30", division="ED", actual_value=546, target_value=600,
            higher_is_better=True, unit="Port",
        )
        syn_evidence = [dict(
            feedback_id=6, reference="F6", fact_id=12, division="ED",
            explanation="SYNTHETIC ACCEPTANCE SCENARIO — hypothetical test input.",
            corrective_action="Review the pending deployment list, identify activities awaiting access approval, and coordinate revised execution schedules with the responsible teams.",
            origin="operator-api",
        )]
        with patch.multiple(
            feedback_rca,
            _client=local_client,
            LLM_MODEL=local_model,
            OPENROUTER_API_KEY=openrouter_config.effective_provider_api_key(local_url, real_secret),
        ):
            rca = await feedback_rca.draft_from_evidence(syn_reading, syn_evidence, allow_synthetic_scenario=True)

        self.assertEqual(len(captured), 1)
        headers, body = captured[0]
        self.assertEqual(headers.get("authorization"), f"Bearer {openrouter_config.LOCAL_PROVIDER_DUMMY_KEY}")
        self.assertNotIn(real_secret, json.dumps(headers))
        self.assertEqual(body["model"], local_model)
        self.assertEqual(body["temperature"], 0)
        self.assertEqual(body["reasoning_effort"], "none")
        self.assertEqual(rca["llm_model"], local_model)
        self.assertEqual(rca["evidence_status"], "ai_draft")
        self.assertEqual(rca["cited_feedback_ids"], [6])
        self.assertTrue(rca["grounding"]["citation_verified"])
        self.assertTrue(rca["root_cause"].startswith(feedback_rca.SYNTHETIC_ROOT_CAUSE_PREFIX))
