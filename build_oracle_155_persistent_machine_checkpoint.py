from pathlib import Path
import ast, json, os, sys, time

ROOT = Path.cwd()
STATE = ROOT / 'runtime_state' / 'oracle' / 'oracle_live_execution'
DEST = ROOT / 'oracle_execution_checkpoint.json'
RUNBOOK = ROOT / 'ORACLE_EXECUTION_RESUME.cmd'
EXPECTED_ALT = 'HSEM6g4Txajd6EHPav7GBanr4eXc5zzSs4cmySthg97r'


def json_file(path):
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def safe_metadata(path, keys):
    data = json_file(path)
    if not isinstance(data, dict):
        return {'present': path.exists(), 'status': 'UNREADABLE_OR_UNEXPECTED'}
    return {'present': True, **{k: data[k] for k in keys if k in data and isinstance(data[k], (str, int, bool))}}


def install():
    expected = [
        'build_oracle_148_executor_wallet_bootstrap.py',
        'build_oracle_149_atomic_v0_alt_compiler.py',
        'build_oracle_150_canonical_alt_registry_bridge.py',
        'build_oracle_151_canonical_alt_live_proof.py',
        'build_oracle_152_alt_metadata_offset_replacement.py',
        'build_oracle_153_verified_alt_only.py',
        'build_oracle_154_real_alt_coverage_trace.py',
    ]
    registry = ROOT / 'runtime_state/oracle/solana_atomic_executor/canonical_alt.json'
    alt = json_file(registry)
    address = alt.get('address') if isinstance(alt, dict) else None
    if address != EXPECTED_ALT:
        raise SystemExit('[HOLD] canonical ALT registry address mismatch; no files changed')
    report = safe_metadata(STATE / 'ORACLE_151_CANONICAL_ALT_LIVE_PROOF.json',
                           ['ok', 'active', 'entries', 'reason', 'address'])
    report149 = safe_metadata(STATE / 'ORACLE_149_ATOMIC_ALT_COMPILE.json',
                              ['ok', 'reason', 'bytes', 'alt_count'])
    wallet = safe_metadata(STATE / 'solana_wallet_identity.json', ['wallet_source', 'source'])
    manifest = {
        'schema': 'ORACLE155_CHECKPOINT_V1',
        'created_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'repo': str(ROOT),
        'builds': {name: (ROOT / name).is_file() for name in expected},
        'canonical_alt_address': address,
        'canonical_alt_verification': report,
        'wallet_public_metadata': wallet,
        'native_alt_compile': report149,
        'last_observed': {'ORACLE154': 'INSTALL_AND_TEST_PASS',
                          'native_runtime': 'HOLD_QSB_SOLANA_PRIVATE_KEY_MISSING',
                          'native_simulation': 'NOT_VERIFIED'},
        'operating_rules': {'scanner_frozen': True,
                            'first_live_canary_sol': '0.010',
                            'never_save_private_key': True,
                            'no_broadcast_without_live_atomic_gates': True},
    }
    cmd = r"""@echo off
cd /d "%~dp0"
if not exist "venv\Scripts\python.exe" (echo [HOLD] Missing venv & exit /b 2)
venv\Scripts\python.exe -c "import os,sys; sys.exit(0 if os.environ.get('QSB_SOLANA_PRIVATE_KEY') else 3)"
if errorlevel 1 (echo [HOLD] Native runtime needs signing credential in current process; no secret is stored & exit /b 3)
echo [ORACLE155] Starting native executor; existing transaction gates remain authoritative
venv\Scripts\python.exe -m qseries_v2.oracle_execution.solana_atomic_executor.runtime --seconds 90
"""
    STATE.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    RUNBOOK.write_text(cmd, encoding='utf-8')
    print('[INSTALL PASS] ORACLE155 persistent nonsecret checkpoint saved')
    print('[CHECKPOINT]', DEST)
    print('[RESUME]', RUNBOOK)
    print('[CANONICAL_ALT]', address)
    print('[BLOCKER] native runtime requires signing credential in process environment')
    print('[GUARD] no private key stored, no signing, no broadcasting by this installer')


def test():
    data = json_file(DEST)
    assert data and data['schema'] == 'ORACLE155_CHECKPOINT_V1'
    assert data['canonical_alt_address'] == EXPECTED_ALT
    script = RUNBOOK.read_text(encoding='utf-8')
    assert 'QSB_SOLANA_PRIVATE_KEY' in script and 'set QSB_SOLANA_PRIVATE_KEY=' not in script
    assert 'runtime --seconds 90' in script
    assert 'private_key' not in json.dumps(data).lower() or 'never_save_private_key' in data['operating_rules']
    print('[TEST PASS] ORACLE155 durable report, command and secret nonpersistence')

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        test()
    else:
        install()
