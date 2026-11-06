"""Read-only AI status and mapping-evaluation evidence.

Both endpoints report what the deployed build can actually do. Nothing here calls a model.
"""
import json

from fastapi import APIRouter

from services.intake import EVIDENCE_DIR, RECORDED_MAPPING_FILE

router = APIRouter(prefix='/api/v1/ai', tags=['AI'])


def _read(name):
    try:
        return json.loads((EVIDENCE_DIR / name).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def _mean(values):
    values = [value for value in values if value is not None]
    return round(sum(values) / len(values), 3) if values else None


def _case_summary(rows):
    """Average accuracy and latency across repeats for one case and mode."""
    if not rows:
        return None
    columns = rows[0].get('columns') or 0
    accuracy = _mean([row.get('correct', 0) / columns for row in rows]) if columns else None
    return {
        'runs': len(rows),
        'columns': columns,
        'correct': _mean([row.get('correct', 0) for row in rows]),
        'accuracy': accuracy,
        'corrections_required': _mean([row.get('corrections_required', 0) for row in rows]),
        'llm_columns': _mean([row.get('llm_columns', 0) for row in rows]),
        'preview_seconds': _mean([row.get('preview_seconds') for row in rows]),
        'errors': sum(len(row.get('errors') or []) for row in rows),
    }


@router.get('/status')
def ai_status():
    """What the running build will do when a user opts into AI mapping."""
    from agents.harvester import LLM_MODEL, OPENROUTER_API_KEY, OPENROUTER_BASE_URL

    configured = bool(OPENROUTER_API_KEY)
    recorded = _read(RECORDED_MAPPING_FILE.name) or {}
    recorded_count = len(recorded.get('mappings', {}))
    if configured:
        mode = 'live'
    elif recorded_count:
        mode = 'recorded'
    else:
        mode = 'unavailable'
    return {
        'configured': configured,
        'mode': mode,
        'model': LLM_MODEL,
        'provider': OPENROUTER_BASE_URL,
        'samples_per_column': 3,
        'recorded_suggestions': recorded_count,
        'recorded_provenance': recorded.get('provenance'),
        'evaluation_available': (EVIDENCE_DIR / 'mapping-benchmark-live.json').exists(),
    }


@router.get('/evaluation')
def mapping_evaluation():
    """Synthetic mapping benchmark: local rules versus the configured provider."""
    rules = _read('mapping-benchmark.json') or {}
    live = _read('mapping-benchmark-live.json') or {}
    rules_rows = rules.get('results', [])
    live_rows = live.get('results', [])
    cases = []
    for name in dict.fromkeys([row.get('case') for row in rules_rows] + [row.get('case') for row in live_rows]):
        cases.append({
            'case': name,
            'rules': _case_summary([row for row in rules_rows
                                    if row.get('case') == name and row.get('mode') == 'rules']),
            'ai': _case_summary([row for row in live_rows
                                 if row.get('case') == name and row.get('mode') == 'ai']),
        })
    limitations = list(dict.fromkeys(
        (rules.get('limitations') or []) + (live.get('limitations') or []) + [
            'Five author-labelled synthetic layouts; the unfamiliar and reordered cases share vocabulary '
            'and are not independent samples.',
            'No held-out real-report accuracy, analyst review time or production claim is supported.',
            'Recorded suggestions are replayed provider output, not a live call.',
        ]))
    return {
        'synthetic': True,
        'dataset': live.get('dataset') or rules.get('dataset'),
        'rules_model': 'local aliases and fuzzy matching',
        'ai_model': live.get('model'),
        'ai_repeats': (max((row.get('repeat', 0) for row in live_rows), default=-1) + 1) or None,
        'recorded_provenance': (_read(RECORDED_MAPPING_FILE.name) or {}).get('provenance'),
        'cases': cases,
        'limitations': limitations,
    }
