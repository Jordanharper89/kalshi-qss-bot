"""ORACLE-094: full fail-closed public account metadata capture installer.
Works against the confirmed ORACLE-092 v0 compiler. No key access or RPC at install.
"""
import argparse
import ast
import tempfile
from pathlib import Path

TARGET = Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle_074_native_v0_compiler.py')
MARKER = '# ORACLE094_PUBLIC_ROUTE_CAPTURE'
ANCHOR = "        if gate != 'ADMITTED':\n            result['attempts'].append({'candidate': name, 'error': gate})\n            continue\n"
HELPER = '''# ORACLE094_PUBLIC_ROUTE_CAPTURE
_ORACLE094_CAPTURED = set()

def _oracle094_capture_public(root, user, token, name, ixs):
    """Persist public keys/flags only. No instruction data, URL, secrets, or wallet loading."""
    if not isinstance(token, str) or not token or not token.isalnum() or len(token) > 60:
        return
    if not isinstance(user, str) or not (32 <= len(user) <= 44):
        return
    if not isinstance(ixs, list) or not (1 <= len(ixs) <= 64):
        return
    key = (token, name)
    if key in _ORACLE094_CAPTURED:
        return
    public = []
    try:
        for ix in ixs:
            if not isinstance(ix, dict) or not isinstance(ix.get('accounts'), list):
                return
            if len(ix['accounts']) > 128:
                return
            program = ix.get('programId')
            if not isinstance(program, str) or not (32 <= len(program) <= 44):
                return
            accounts = []
            for a in ix['accounts']:
                pk = a.get('pubkey') if isinstance(a, dict) else None
                if not isinstance(pk, str) or not (32 <= len(pk) <= 44):
                    return
                accounts.append({'pubkey': pk, 'isSigner': a.get('isSigner') is True,
                                 'isWritable': a.get('isWritable') is True})
            public.append({'programId': program, 'accounts': accounts})
        doc = {'user': user, 'token': token,
               'candidates': [{'name': name, 'instructions': public}],
               'capture_scope': 'PUBLIC_ACCOUNT_KEYS_ONLY', 'data_included': False,
               'signing': False, 'broadcast': False}
        folder = Path(root) / 'runtime_state/oracle/solana_atomic_executor/alt_public_capture'
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / ('oracle094_' + token + '_' + name + '.json')
        raw = json.dumps(doc, sort_keys=True, indent=2)
        if not target.exists() or target.read_text(encoding='utf-8') != raw:
            temp = target.with_suffix('.tmp')
            temp.write_text(raw, encoding='utf-8')
            temp.replace(target)
        _ORACLE094_CAPTURED.add(key)
        print('[ORACLE094_PUBLIC_ROUTE_CAPTURE] token=%s candidate=%s account_rows=%d path=%s' %
              (token[:10], name, sum(len(x['accounts']) for x in public), target), flush=True)
    except (OSError, TypeError, ValueError):
        print('[ORACLE094_CAPTURE_HOLD] local_public_metadata_unavailable', flush=True)
'''

def transform(s):
    if MARKER in s:
        return s
    if s.count('def compile_existing_alt(') != 1 or s.count(ANCHOR) != 1:
        raise RuntimeError('ORACLE094_EXPECTED_ORACLE092_SOURCE_NOT_FOUND_NO_CHANGES')
    s = s.replace('def compile_existing_alt(', HELPER + '\ndef compile_existing_alt(', 1)
    s = s.replace(ANCHOR, ANCHOR + "        if name == 'FULL':\n            _oracle094_capture_public(root, user, token, name, ixs)\n", 1)
    ast.parse(s)
    return s

def tests():
    with tempfile.TemporaryDirectory() as d:
        original = '''import json\nfrom pathlib import Path\ndef compile_existing_alt(user, route, core, q87, root):\n    result = {'attempts': []}\n    token = route['token']\n    for cand in q87.repaired_candidates(route):\n        name = str(cand.get('name', 'UNKNOWN'))\n        ixs = cand['instructions']\n        gate = 'ADMITTED'\n        if gate != 'ADMITTED':\n            result['attempts'].append({'candidate': name, 'error': gate})\n            continue\n    return result\n'''
        ns = {}
        exec(compile(transform(original), '<oracle094_fixture>', 'exec'), ns)
        address = '11111111111111111111111111111111'
        ix = {'programId': address, 'accounts': [
            {'pubkey': '22222222222222222222222222222222', 'isSigner': False, 'isWritable': True},
            {'pubkey': '33333333333333333333333333333333', 'isSigner': True, 'isWritable': False}]}
        class Q:
            def repaired_candidates(self, route):
                return [{'name': 'FULL', 'instructions': [ix]}]
        ns['compile_existing_alt'](address, {'token': 'TOKEN123'}, None, Q(), d)
        out = Path(d) / 'runtime_state/oracle/solana_atomic_executor/alt_public_capture/oracle094_TOKEN123_FULL.json'
        doc = __import__('json').loads(out.read_text(encoding='utf-8'))
        assert doc['candidates'][0]['instructions'][0]['accounts'][1]['isSigner']
        assert 'data' not in out.read_text(encoding='utf-8').replace('data_included', '')
        assert doc['signing'] is False and doc['broadcast'] is False
        assert transform(transform(original)) == transform(original)
    print('[PASS] ORACLE094_PUBLIC_ONLY_CAPTURE_IDEMPOTENCE_AND_SOURCE_TESTS')
    print('[BOUNDARY] INSTALL_NO_RPC NO_PRIVATE_KEY NO_SIGNING NO_BROADCAST NO_SCANNER_CHANGE')

def install():
    tests()
    if not TARGET.is_file():
        raise RuntimeError('ORACLE094_COMPILER_NOT_FOUND')
    existing = TARGET.read_text(encoding='utf-8')
    updated = transform(existing)
    if existing == updated:
        print('[PASS] ORACLE094_ALREADY_INSTALLED')
        return
    backup = TARGET.with_name(TARGET.stem + '.before_oracle094.py')
    if backup.exists():
        raise RuntimeError('ORACLE094_BACKUP_EXISTS_STOPPING')
    ast.parse(updated)
    backup.write_text(existing, encoding='utf-8')
    temp = TARGET.with_suffix('.oracle094.tmp')
    try:
        temp.write_text(updated, encoding='utf-8')
        ast.parse(temp.read_text(encoding='utf-8'))
        temp.replace(TARGET)
    except Exception:
        temp.unlink(missing_ok=True)
        TARGET.write_text(existing, encoding='utf-8')
        raise
    print('[PASS] ORACLE094_PUBLIC_ROUTE_CAPTURE_INSTALLED')
    print('[NEXT] Next existing native compile attempt captures FULL public instruction keys; no scanner changes')

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--test', action='store_true')
    args = ap.parse_args()
    tests() if args.test else install()
