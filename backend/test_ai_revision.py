"""Checks for provider suggestions, recorded fallback labelling, and AI evidence endpoints."""
import asyncio
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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


class RecordedFallback(unittest.TestCase):
    def test_recorded_suggestions_are_applied_and_labelled(self):
        report = demo_report()
        mapping = intake.suggest_mapping(report['columns'])
        with patch.object(harvester, 'OPENROUTER_API_KEY', ''):
            mapping, message, trace = asyncio.run(intake.ai_mapping(report, mapping))
        self.assertEqual(trace['mode'], 'recorded')
        self.assertIn('not a live model call', message)
        self.assertTrue(trace['model'])
        recorded = {column: value for column, value in mapping.items() if value['method'] == 'llm_recorded'}
        self.assertTrue(recorded)
        self.assertTrue(all(value.get('reason') for value in recorded.values()))

    def test_unknown_layout_without_key_is_skipped_honestly(self):
        report = {'columns': ['Totally Unknown Header'], 'rows': [{'values': {'Totally Unknown Header': 'x'}}]}
        with patch.object(harvester, 'OPENROUTER_API_KEY', ''):
            mapping, message, trace = asyncio.run(intake.ai_mapping(report, intake.suggest_mapping(report['columns'])))
        self.assertEqual(trace['mode'], 'skipped')
        self.assertIn('no recorded suggestion', message)
        self.assertEqual(mapping['Totally Unknown Header']['target'], 'ignore')


class EvidenceEndpoints(unittest.TestCase):
    def test_status_reports_recorded_mode_without_key(self):
        with patch.object(harvester, 'OPENROUTER_API_KEY', ''):
            body = ai_router.ai_status()
        self.assertFalse(body['configured'])
        self.assertEqual(body['mode'], 'recorded')
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
