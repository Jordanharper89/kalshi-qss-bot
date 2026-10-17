"""ORACLE-147 full installer: replace 146 native-prewarm component with public-identity recovery.
No wallet secret reads, writes, or prompts. Never signs or sends transactions.
"""
from pathlib import Path
import ast
import os
import subprocess
import sys
import tempfile

ROOT = Path.cwd()
BASE = ROOT / 'qseries_v2/oracle_execution/solana_atomic_executor/oracle105_sdk_worker'
TARGET = BASE / 'oracle146_native_template_preparation.py'
Q25 = ROOT / 'qseries_v2/oracle_execution/oracle_025_single_hydration_exact_live_reuse.py'
NATIVE = ROOT / 'qseries_v2/oracle_execution/solana_atomic_executor/runtime.py'
MODULE = r'''"""ORACLE-147: recover configured public wallet; prewarm existing Q25 inventory.
No secret reads, signing, simulation or broadcasting.
"""
import argparse
import json
import os
import threading
from pathlib import Path

OUT = Path('runtime_state/oracle/oracle_live_execution/ORACLE_147_WALLET_TEMPLATE_REPORT.json')
LEGACY = Path('runtime_state/oracle/oracle_live_execution/ORACLE_146_NATIVE_TEMPLATES.json')
MRIYA = 'MriyaNN8TMp6qRWjfr723PK7xgQK7yCt7Kg2v2PQu7X'
_LOCK = threading.Lock()
_STARTED = False

# Explicit configuration metadata, never research-wallet lists or key material.
SOURCES = (
    'runtime_state/oracle/oracle_live_execution/solana_wallet_identity.json',
    'runtime_state/oracle/oracle_live_execution/wallet_identity.json',
    'runtime_state/oracle/solana_wallet_identity.json',
    'runtime_state/oracle/wallet_identity.json',
    'runtime_state/oracle/oracle_live_execution/solana_executor_wallet.json',
)
FIELDS = ('signer_pubkey', 'executor_wallet', 'wallet_address', 'public_key', 'wallet_pubkey')

def valid_public(value):
    if not isinstance(value, str) or not value.strip() or value.strip() == MRIYA:
        return None
    try:
        from solders.pubkey import Pubkey
        pub = Pubkey.from_string(value.strip())
        return str(pub) if pub.is_on_curve() else None
    except Exception:
        return None

def resolve_wallet(root=Path('.'), environment=None):
    env = os.environ if environment is None else environment
    explicit = valid_public(env.get('QSB_SOLANA_WALLET', ''))
    if explicit:
        return explicit, 'QSB_SOLANA_WALLET', []
    hits = []
    for rel in SOURCES:
        path = root / rel
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
        except (ValueError, OSError):
            continue
        if not isinstance(data, dict):
            continue
        for field in FIELDS:
            val = valid_public(data.get(field))
            if val:
                hits.append((val, str(rel) + ':' + field))
    unique = {x[0] for x in hits}
    if len(unique) == 1:
        return next(iter(unique)), 'configured_public_metadata', []
    if len(unique) > 1:
        return None, 'NONE', ['HOLD_AMBIGUOUS_CONFIGURED_WALLET_IDENTITIES']
    return None, 'NONE', ['HOLD_PUBLIC_WALLET_IDENTITY_NOT_CONFIGURED']

def prepare(state, warmed, native=None, wallet=None):
    pairs = list(state.get('pairs') or [])
    record = {'build': 'ORACLE147', 'pair_count': len(pairs), 'ready_tokens': [],
              'ready_count': 0, 'holds': [], 'execution_authority': False,
              'signed': False, 'simulated': False, 'broadcast': False}
    if not valid_public(wallet):
        record['holds'].append('HOLD_UNVERIFIED_PUBLIC_WALLET')
        return record
    if native is None:
        from qseries_v2.oracle_execution.solana_atomic_executor import runtime as native
    if not callable(getattr(native, 'prebuild_templates', None)) or not callable(getattr(native, 'prebuild_meteora_templates', None)):
        record['holds'].append('HOLD_NATIVE_TEMPLATE_APIS_UNAVAILABLE')
        return record
    try:
        native.prebuild_templates(state, wallet)
    except Exception as exc:
        record['holds'].append('HOLD_PUMP_TEMPLATE_' + type(exc).__name__)
        return record
    try:
        native.prebuild_meteora_templates(state, wallet, warmed)
    except Exception as exc:
        record['holds'].append('HOLD_METEORA_TEMPLATE_' + type(exc).__name__)
    pumps = getattr(native, 'TEMPLATES', {})
    meteoras = getattr(native, 'METEORA_TEMPLATES', {})
    ready = set(getattr(native, 'READY_TOKENS', set()))
    for pair in pairs:
        token = str(pair.token)
        pt = pumps.get(token)
        mt = meteoras.get(token)
        if token not in ready:
            record['holds'].append('HOLD_NOT_READY_' + token[:12])
        elif not isinstance(pt, dict) or pt.get('pump_pool') != str(pair.pump_pool):
            record['holds'].append('HOLD_PUMP_POOL_MISMATCH_' + token[:12])
        elif not isinstance(mt, dict):
            record['holds'].append('HOLD_METEORA_TEMPLATE_MISSING_' + token[:12])
        else:
            record['ready_tokens'].append(token[:12])
    record['ready_count'] = len(record['ready_tokens'])
    if not record['ready_count']:
        record['holds'].append('HOLD_NO_COMPLETE_NATIVE_TEMPLATES')
    return record

def save(record, path=OUT):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(record, indent=2, sort_keys=True), encoding='utf-8')
    os.replace(tmp, path)

def _worker(state, warmed):
    wallet, source, holds = resolve_wallet()
    if wallet is None:
        report = {'build': 'ORACLE147', 'ready_count': 0,
                  'pair_count': len(state.get('pairs') or []), 'holds': holds,
                  'signed': False, 'simulated': False, 'broadcast': False}
    else:
        try:
            report = prepare(state, warmed, wallet=wallet)
        except Exception as exc:
            report = {'build': 'ORACLE147', 'ready_count': 0,
                      'holds': ['HOLD_NATIVE_PREPARE_' + type(exc).__name__],
                      'signed': False, 'simulated': False, 'broadcast': False}
    report['wallet_source'] = source
    report['public_wallet_configured'] = wallet is not None
    save(report)
    save(report, LEGACY)
    print('[ORACLE147_NATIVE_TEMPLATES] ready=%s pairs=%s holds=%s report=%s' % (
        report.get('ready_count', 0), report.get('pair_count', 0), report.get('holds', []), OUT), flush=True)

def start(state, warmed):
    global _STARTED
    with _LOCK:
        if _STARTED:
            return
        _STARTED = True
    threading.Thread(target=_worker, args=(state, warmed), daemon=True,
                     name='oracle147-identity-native-template').start()
    print('[ORACLE147] identity-resolved Q25 native template prewarm; broadcast disabled', flush=True)

def test():
    from types import SimpleNamespace
    from solders.keypair import Keypair
    from tempfile import TemporaryDirectory
    pub = str(Keypair().pubkey())
    assert valid_public(pub) == pub
    assert valid_public(MRIYA) is None
    with TemporaryDirectory() as d:
        root = Path(d)
        a, source, holds = resolve_wallet(root, {'QSB_SOLANA_WALLET': pub})
        assert a == pub and not holds and source == 'QSB_SOLANA_WALLET'
        assert resolve_wallet(root, {})[0] is None
        p = root / SOURCES[0]
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({'wallet_pubkey': pub}), encoding='utf-8')
        assert resolve_wallet(root, {})[0] == pub
        p.write_text(json.dumps({'wallet_pubkey': MRIYA}), encoding='utf-8')
        assert resolve_wallet(root, {})[0] is None
    class Native:
        TEMPLATES = {}
        METEORA_TEMPLATES = {}
        READY_TOKENS = set()
        @classmethod
        def prebuild_templates(cls, state, wallet):
            cls.TEMPLATES = {'T': {'pump_pool': 'P'}}
            cls.READY_TOKENS = {'T'}
        @classmethod
        def prebuild_meteora_templates(cls, state, wallet, warmed):
            cls.METEORA_TEMPLATES = {'T': {'pool': 'M'}}
    state = {'pairs': [SimpleNamespace(token='T', pump_pool='P')]}
    assert 'HOLD_UNVERIFIED_PUBLIC_WALLET' in prepare(state, [], Native, None)['holds']
    result = prepare(state, [], Native, pub)
    assert result['ready_count'] == 1 and not result['holds'], result
    assert result['broadcast'] is False and result['signed'] is False
    print('[TEST PASS] ORACLE147 wallet resolution, Mriya rejection, native bindings, no signing/broadcast')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true')
    args = parser.parse_args()
    test()
    if not args.test:
        print('[MODE] Embedded in Q25. Start with oracle120_credentials.py --run')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
'''

def atomic_write(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('wb', dir=path.parent, delete=False) as out:
        out.write(raw)
        temporary = Path(out.name)
    os.replace(temporary, path)

def main():
    if not (TARGET.is_file() and Q25.is_file() and NATIVE.is_file()):
        raise SystemExit('[HOLD] ORACLE146, Q25, or native executor missing; no files changed')
    q25 = Q25.read_text(encoding='utf-8')
    old = TARGET.read_bytes()
    if q25.count('o146.start(state,warmed)') != 1:
        raise SystemExit('[HOLD] Q25 native prewarm hook absent or duplicated; no changes')
    for src in (MODULE, q25):
        ast.parse(src)
    if 'def prebuild_templates(' not in NATIVE.read_text(encoding='utf-8'):
        raise SystemExit('[HOLD] native template API unavailable; no changes')
    try:
        atomic_write(TARGET, MODULE.encode('utf-8'))
        proc = subprocess.run([sys.executable, '-m',
            'qseries_v2.oracle_execution.solana_atomic_executor.oracle105_sdk_worker.oracle146_native_template_preparation',
            '--test'], cwd=ROOT, capture_output=True, text=True, timeout=40)
        if proc.returncode != 0:
            raise RuntimeError((proc.stdout + proc.stderr)[-1200:])
        print(proc.stdout.strip())
    except BaseException as exc:
        atomic_write(TARGET, old)
        raise SystemExit('[HOLD] ORACLE147 rolled back: ' + str(exc))
    print('[INSTALL PASS] ORACLE147 wallet identity + native template recovery; existing scanner unchanged')
    print('[RUN] python oracle120_credentials.py --run')

if __name__ == '__main__':
    main()
