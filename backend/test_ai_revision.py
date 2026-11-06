"""Live interpretation, provenance, and historical evaluation contracts."""
import asyncio
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch
from types import SimpleNamespace

_TEMP = tempfile.TemporaryDirectory(prefix='omnikpi-ai-tests-')
os.environ['DATABASE_URL'] = 'sqlite:///' + (Path(_TEMP.name) / 'test.db').as_posix()
os.environ['DEMO_DATABASE_URL'] = 'sqlite:///' + (Path(_TEMP.name) / 'demo.db').as_posix()

from agents import harvester  # noqa: E402
from routers import ai as ai_router  # noqa: E402
from services import intake  # noqa: E402

FIXTURES = Path(__file__).resolve().parents[1] / 'frontend/public/demo/divisions'


def demo_report():
    manifest = json.loads((FIXTURES / 'manifest.json').read_text(encoding='utf-8'))
    entry = manifest[0]
    content = (FIXTURES / entry['filename']).read_bytes()
    return intake.read_report(content, entry['filename'], entry['sheet'], entry['header_row'],
                              entry['header_depth'])


class LiveInterpretation(unittest.TestCase):
    def test_recorded_demo_layout_cannot_bypass_missing_provider(self):
        report = demo_report()
        mapping = intake.suggest_mapping(report['columns'])
        with patch.object(harvester, 'OPENROUTER_API_KEY', ''):
            with self.assertRaisesRegex(RuntimeError, 'unavailable'):
                asyncio.run(intake.ai_mapping(report, mapping))

    def test_unknown_layout_without_key_requires_provider(self):
        report = {'columns': ['Totally Unknown Header'], 'rows': [{'values': {'Totally Unknown Header': 'x'}}]}
        with patch.object(harvester, 'OPENROUTER_API_KEY', ''):
            with self.assertRaises(RuntimeError):
                asyncio.run(intake.ai_mapping(report, intake.suggest_mapping(report['columns'])))

    def test_structured_reasons_and_trace_describe_live_call(self):
        report = {'columns': ['Observed result'], 'rows': [{'values': {'Observed result': 97.8}}]}
        response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps({
            'Observed result': {'field': 'actual_value', 'reason': 'Observed measurement: 97.8'}
        })))])
        with patch.object(harvester, 'OPENROUTER_API_KEY', 'test'), patch.object(
                harvester._client.chat.completions, 'create', new=AsyncMock(return_value=response)) as call:
            mapping, message, trace = asyncio.run(intake.ai_mapping(report, intake.suggest_mapping(report['columns'])))
        self.assertEqual(call.await_count, 1)
        self.assertEqual(mapping['Observed result']['reason'], 'Observed measurement: 97.8')
        self.assertEqual(trace['mode'], 'live')
        self.assertEqual(trace['columns'], 1)
        self.assertEqual(trace['fallback_batches'], 0)
        self.assertIn('97.8', call.call_args.kwargs['messages'][1]['content'])

    def test_partial_model_response_is_rejected(self):
        report = {'columns': ['Metric', 'Actual'], 'rows': [{'values': {'Metric': 'KPI', 'Actual': 90}}]}
        response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='{"Metric":"kpi_name"}'))])
        with patch.object(harvester, 'OPENROUTER_API_KEY', 'test'), patch.object(
                harvester._client.chat.completions, 'create', new=AsyncMock(return_value=response)):
            with self.assertRaises(RuntimeError):
                asyncio.run(intake.ai_mapping(report, intake.suggest_mapping(report['columns'])))


class EvidenceEndpoints(unittest.TestCase):
    def test_status_requires_provider_even_with_recordings(self):
        with patch.object(harvester, 'OPENROUTER_API_KEY', ''):
            body = ai_router.ai_status()
        self.assertFalse(body['configured'])
        self.assertEqual(body['mode'], 'unavailable')
        self.assertTrue(body['required'])
        self.assertFalse(body['recorded_replay_enabled'])
        self.assertGreater(body['recorded_suggestions'], 0)
        self.assertTrue(body['recorded_provenance']['model'])

    def test_evaluation_compares_rules_with_provider(self):
        body = ai_router.mapping_evaluation()
        cases = {case['case']: case for case in body['cases']}
        self.assertIn('unfamiliar', cases)
        self.assertEqual(cases['unfamiliar']['rules']['accuracy'], 0)
        self.assertEqual(cases['unfamiliar']['ai']['accuracy'], 1)
        self.assertLess(cases['reordered']['ai']['accuracy'], 1)
        self.assertTrue(body['ai_model'])
        self.assertEqual(body['ai_repeats'], 3)
        self.assertTrue(body['limitations'])


if __name__ == '__main__':
    unittest.main()
