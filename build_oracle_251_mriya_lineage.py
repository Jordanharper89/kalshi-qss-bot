"""ORACLE-251: offline Mriya-to-pricing lineage audit. Never uses RPC or wallet."""
import argparse
import ast
import json
import re
from pathlib import Path

ROOT = Path('runtime_state/oracle/oracle_live_execution')
OUT = ROOT / 'ORACLE251_MRIYA_LINEAGE.json'
MINT = re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')
SAFE_FIELDS = ('mint', 'token', 'token_mint', 'base_mint', 'address')
SOURCE_NAMES = ('raydium_cpmm_mriya_bridge.py', 'engine.py',
                'merged_live_runtime.py', 'live_account_stream.py')


def addresses(obj, depth=0):
    """Only inspect explicit mint/token identity fields in bounded JSON."""
    result = set()
    if depth > 8:
        return result
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in SAFE_FIELDS and isinstance(value, str) and MINT.fullmatch(value):
                result.add(value)
            elif isinstance(value, (dict, list)):
                result.update(addresses(value, depth + 1))
    elif isinstance(obj, list):
        for value in obj[:2000]:
            result.update(addresses(value, depth + 1))
    return result


def inspect_source(path):
    text = path.read_text(encoding='utf-8', errors='replace')
    tree = ast.parse(text, filename=str(path))
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            segment = ast.get_source_segment(text, node) or ''
            if any(x in segment.lower() for x in ('mriya', 'candidate_universe', 'capture')):
                calls = sorted({ast.unparse(n.func)[:100] for n in ast.walk(node)
                                if isinstance(n, ast.Call)
                                and any(t in ast.unparse(n.func).lower()
                                        for t in ('mriya', 'discover', 'universe', 'capture'))})
                hits.append({'function': node.name, 'line': node.lineno,
                             'calls': calls[:15]})
    return {'file': str(path), 'functions': hits[:40],
            'mentions_mriya': text.lower().count('mriya'),
            'mentions_capture': text.lower().count('capture')}


def audit(base):
    files = sorted(p for p in base.rglob('*.py') if p.name in SOURCE_NAMES)
    source = []
    for p in files[:16]:
        try:
            source.append(inspect_source(p))
        except (SyntaxError, OSError) as e:
            source.append({'file': str(p), 'error': type(e).__name__})
    report_path = ROOT / 'ORACLE250_OPPORTUNITY_SCREEN.json'
    priced = set()
    if report_path.is_file():
        try:
            screening = json.loads(report_path.read_text(encoding='utf-8'))
            if screening.get('build') == 'ORACLE250':
                priced = {r['mint'] for r in screening.get('top_routes', [])
                          if isinstance(r, dict) and MINT.fullmatch(str(r.get('mint', '')))}
        except (OSError, json.JSONDecodeError):
            pass
    artifacts = []
    state = Path('runtime_state')
    if state.exists():
        paths = sorted(p for p in state.rglob('*.json')
                       if 'mriya' in p.name.lower() and p.is_file())
        for p in paths[:50]:
            entry = {'file': str(p), 'classification': 'HISTORICAL_ARTIFACT_ONLY'}
            try:
                if p.stat().st_size > 2_000_000:
                    entry['error'] = 'FILE_TOO_LARGE'
                else:
                    payload = json.loads(p.read_text(encoding='utf-8'))
                    mints = addresses(payload)
                    entry['identity_count'] = len(mints)
                    entry['priced_overlap_count'] = len(priced & mints)
                    entry['priced_overlap_prefixes'] = sorted(x[:12] for x in priced & mints)
            except (OSError, ValueError) as e:
                entry['error'] = type(e).__name__
            artifacts.append(entry)
    return {'build': 'ORACLE251', 'sources': source, 'mriya_artifacts': artifacts,
            'oracle250_priced_identities': len(priced),
            'live_mriya_delivery_certified': False,
            'same_snapshot_lineage_certified': False,
            'execution_admission': False, 'signing': False, 'broadcast': False,
            'status': 'HOLD_LIVE_MRIYA_PROVENANCE_NOT_CERTIFIED'}


def test():
    assert addresses({'mint': 'A'*32, 'private_key': 'B'*32}) == {'A'*32}
    assert not addresses({'pool': 'C'*32})
    assert addresses({'rows': [{'token': 'D'*32}]}) == {'D'*32}
    sample = Path(__file__)
    assert isinstance(inspect_source(sample)['functions'], list)
    print('[ORACLE251_TEST_PASS] explicit_identity=TRUE no_secrets=TRUE static_source=TRUE')


def run():
    result = audit(Path('qseries_v2'))
    ROOT.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print('[ORACLE251_RESULT]', json.dumps({
        'source_modules': len(result['sources']),
        'mriya_artifacts': len(result['mriya_artifacts']),
        'oracle250_priced_identities': result['oracle250_priced_identities'],
        'live_mriya_delivery_certified': False,
        'signing': False, 'broadcast': False}, sort_keys=True))
    for item in result['sources']:
        if item.get('mentions_mriya') or item.get('functions'):
            print('[ORACLE251_SOURCE]', json.dumps(item, sort_keys=True))
    for item in result['mriya_artifacts']:
        print('[ORACLE251_ARTIFACT]', json.dumps(item, sort_keys=True))
    print('[REPORT]', OUT)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true')
    parser.add_argument('--run', action='store_true')
    a = parser.parse_args()
    if not (a.test or a.run):
        parser.error('Specify --test or --run')
    if a.test:
        test()
    if a.run:
        run()