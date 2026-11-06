"""Record provider mapping suggestions for the seven demo workbooks.

The output is replayed as a clearly labelled fallback when no provider key is configured.
Only headers and up to three sample values per column leave this machine, exactly like intake.
"""
import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'frontend/public/demo/divisions'
OUTPUT = ROOT / 'backend/evidence/recorded-ai-mappings.json'


def demo_reports():
    manifest = json.loads((FIXTURES / 'manifest.json').read_text(encoding='utf-8'))
    for entry in manifest:
        path = FIXTURES / entry['filename']
        yield entry, path.read_bytes()


async def run():
    from agents.harvester import LLM_MODEL, OPENROUTER_API_KEY, OPENROUTER_BASE_URL
    from services.intake import ai_mapping, read_report, signature, suggest_mapping

    if not OPENROUTER_API_KEY:
        raise SystemExit('OPENROUTER_API_KEY is required to record provider suggestions.')

    mappings = {}
    for entry, content in demo_reports():
        report = read_report(content, entry['filename'], entry['sheet'], entry['header_row'], entry['header_depth'])
        rules = suggest_mapping(report['columns'])
        mapping, message, trace = await ai_mapping(report, rules)
        if trace['mode'] != 'live':
            print(f"skip {entry['filename']}: {trace['mode']} — {message}")
            continue
        key = signature(report)
        slot = mappings.setdefault(key, {'columns': {}, 'files': [], 'conflicts': []})
        slot['files'].append({'filename': entry['filename'], 'division': entry['division'],
                              'sheet': entry['sheet'], 'header_row': entry['header_row'],
                              'header_depth': entry['header_depth']})
        for column, suggestion in mapping.items():
            if suggestion.get('method') != 'llm':
                continue
            target = suggestion['target']
            existing = slot['columns'].get(column)
            if existing and existing['target'] != target:
                slot['conflicts'].append({'column': column, 'kept': existing['target'],
                                          'rejected': target, 'file': entry['filename']})
                continue
            slot['columns'].setdefault(column, {
                'target': target, 'reason': suggestion.get('reason', ''),
                'rules_target': rules[column]['target']})
        print(f"{entry['filename']}: {len(report['columns'])} columns; signature {key[:12]}")
        print(f"  {message}")

    payload = {
        'provenance': {
            'model': LLM_MODEL,
            'provider': OPENROUTER_BASE_URL,
            'recorded_at': datetime.now(timezone.utc).date().isoformat(),
            'samples_per_column': 3,
            'script': 'backend/record_ai_mappings.py',
            'note': ('Recorded provider output for exact ordered header signatures. Replayed only when no '
                     'provider key is configured, and labelled as recorded in the interface.'),
        },
        'mappings': mappings,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'Results: {OUTPUT}')


if __name__ == '__main__':
    asyncio.run(run())
