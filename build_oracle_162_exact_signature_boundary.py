"""ORACLE-162: complete installer for v0 single-wallet signature verification.
Run on Windows CMD in the existing venv. No broadcast, no scanner modifications.
"""
from __future__ import annotations
import argparse
import ast
import json
from pathlib import Path

ROOT = Path('qseries_v2/oracle_execution/solana_atomic_executor')
RUNTIME = ROOT/'runtime.py'
HELPER = ROOT/'oracle105_sdk_worker/oracle162_exact_signature_boundary.py'
REPORT = Path('runtime_state/oracle/oracle_live_execution/ORACLE162_SIGNATURE_CONTRACT.json')
ANCHOR = "    return built\n# ORACLE161_COMPILE_CONTRACT_END"
REPLACEMENT = "    return _oracle162_verify_and_sign(built,user)\n# ORACLE161_COMPILE_CONTRACT_END"
IMPORT = "from qseries_v2.oracle_execution.solana_atomic_executor.oracle105_sdk_worker.oracle162_exact_signature_boundary import verify_and_sign as _oracle162_verify_and_sign\n"
HELPER_SOURCE = '''"""Sign only an already-compiled v0 Solana transaction, simulation-only.
No network operations, no logging of private key, no sending transactions.
"""
from __future__ import annotations


def verify_and_sign(built, expected_wallet):
    from solders.transaction import VersionedTransaction
    from solders.message import to_bytes_versioned
    from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core

    if not isinstance(built, dict) or not built.get('ok'):
        raise RuntimeError('ORACLE162_INVALID_COMPILER_RESULT')
    raw = built.get('raw')
    if not isinstance(raw, (bytes, bytearray)) or not (100 <= len(raw) <= 1232):
        raise RuntimeError('ORACLE162_INVALID_RAW_PACKET')
    try:
        tx = VersionedTransaction.from_bytes(bytes(raw))
    except Exception:
        raise RuntimeError('ORACLE162_NOT_PARSEABLE_VERSIONED_TX') from None
    msg = tx.message
    if not hasattr(msg, 'address_table_lookups'):
        raise RuntimeError('ORACLE162_NOT_V0_TRANSACTION')
    header = msg.header
    n = int(header.num_required_signatures)
    if n != 1 or len(tx.signatures) != n:
        raise RuntimeError('ORACLE162_UNEXPECTED_SIGNER_COUNT:%d' % n)
    # The first static key is the payer and sole authorized signer.
    if str(msg.account_keys[0]) != str(expected_wallet):
        raise RuntimeError('ORACLE162_MESSAGE_PAYER_MISMATCH')
    signing_keypair = core.keypair()
    if str(signing_keypair.pubkey()) != str(expected_wallet):
        raise RuntimeError('ORACLE162_CREDENTIAL_SIGNER_MISMATCH')
    message_bytes = to_bytes_versioned(msg)
    # Never mutate the message, including instruction accounts, amounts or ALT indices.
    signature = signing_keypair.sign_message(message_bytes)
    signed = VersionedTransaction.populate(msg, [signature])
    verified = signed.verify_with_results()
    if len(verified) != 1 or verified[0] is not True:
        raise RuntimeError('ORACLE162_SIGNATURE_VERIFY_FAILED')
    out = bytes(signed)
    if len(out) > 1232 or len(out) < 100:
        raise RuntimeError('ORACLE162_SIGNED_PACKET_SIZE_INVALID')
    # A newly populated packet must serialize the exact same v0 message.
    if to_bytes_versioned(VersionedTransaction.from_bytes(out).message) != message_bytes:
        raise RuntimeError('ORACLE162_MESSAGE_MUTATED')
    import hashlib
    print('[ORACLE162_SIGNATURE_VALID] signers=1 verified=True bytes=%d message_sha256=%s broadcast=FALSE' %
        (len(out),hashlib.sha256(message_bytes).hexdigest()[:16]),flush=True)
    result = dict(built)
    result['raw'] = out
    result['bytes'] = len(out)
    result['oracle162_signature_verified'] = True
    return result
'''


def transform(src):
    if 'ORACLE162_SIGNATURE_BOUNDARY_IMPORT' in src:
        if src.count('ORACLE162_SIGNATURE_BOUNDARY_IMPORT') != 1 or REPLACEMENT not in src:
            raise RuntimeError('HOLD_ORACLE162_EXISTING_BOUNDARY_CORRUPT')
        return src
    if src.count(ANCHOR) != 1 or 'ORACLE161_COMPILE_CONTRACT_BEGIN' not in src:
        raise RuntimeError('HOLD_ORACLE162_EXPECTED_ORACLE161_BOUNDARY_NOT_FOUND')
    if 'ORACLE158_SIMULATION_ONLY_DIRECT_SEND_BLOCKED' not in src:
        raise RuntimeError('HOLD_ORACLE162_BROADCAST_GUARD_NOT_FOUND')
    if 'CANARY_TRADE_LAMPORTS=50_000_000' not in src:
        raise RuntimeError('HOLD_ORACLE162_050_AMOUNT_NOT_FOUND')
    new = src.replace(ANCHOR, REPLACEMENT, 1)
    marker = 'from __future__ import annotations\n'
    if marker in new:
        new = new.replace(marker, marker + '# ORACLE162_SIGNATURE_BOUNDARY_IMPORT\n' + IMPORT, 1)
    else:
        new = '# ORACLE162_SIGNATURE_BOUNDARY_IMPORT\n' + IMPORT + new
    ast.parse(new)
    return new


def test():
    ast.parse(HELPER_SOURCE)
    fixture = ('CANARY_TRADE_LAMPORTS=50_000_000\n'
        'ORACLE158_SIMULATION_ONLY_DIRECT_SEND_BLOCKED=True\n'
        '# ORACLE161_COMPILE_CONTRACT_BEGIN\n'
        'def compile_current(user,route):\n'
        '    built={"ok":True}\n'
        '    return built\n# ORACLE161_COMPILE_CONTRACT_END\n')
    out=transform(fixture)
    assert out == transform(out)
    assert REPLACEMENT in out
    assert 'verify_with_results()' in HELPER_SOURCE
    assert 'to_bytes_versioned' in HELPER_SOURCE
    assert 'ORACLE162_UNEXPECTED_SIGNER_COUNT' in HELPER_SOURCE
    assert 'sendTransaction' not in HELPER_SOURCE
    for bad in (fixture.replace('    return built','    return {}'),
                fixture.replace('ORACLE158_SIMULATION_ONLY_DIRECT_SEND_BLOCKED','GUARD_REMOVED')):
        try: transform(bad)
        except RuntimeError: pass
        else: raise AssertionError('bad source accepted')
    print('[TEST PASS] ORACLE162 fail-closed signature contract, immutable v0 message, idempotent install')


def install():
    source=RUNTIME.read_text(encoding='utf-8')
    updated=transform(source)
    ast.parse(HELPER_SOURCE)
    if updated==source:
        if not HELPER.exists():
            raise RuntimeError('HOLD_ORACLE162_HELPER_MISSING')
        print('[INSTALL PASS] ORACLE162 already installed')
        return
    backup=RUNTIME.with_suffix('.pre_oracle162.bak')
    if backup.exists() or HELPER.exists():
        raise RuntimeError('HOLD_ORACLE162_PREEXISTING_FILES')
    backup.write_text(source,encoding='utf-8')
    try:
        HELPER.parent.mkdir(parents=True,exist_ok=True)
        HELPER.write_text(HELPER_SOURCE,encoding='utf-8')
        RUNTIME.write_text(updated,encoding='utf-8')
        ast.parse(RUNTIME.read_text(encoding='utf-8'))
    except Exception:
        RUNTIME.write_text(source,encoding='utf-8')
        if HELPER.exists(): HELPER.unlink()
        raise
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps({'build':'ORACLE162','target_sol':0.050,
        'stage':'sign_after_native_compile_before_simulation',
        'single_wallet_signer_only':True,'v0_message_immutable':True,
        'real_signed_simulation_pass':False,'broadcast_authorized':False,
        'scanner_changed':False},indent=2)+'\n',encoding='utf-8')
    print('[INSTALL PASS] ORACLE162 native v0 exact signature boundary')
    print('[PROOF]',REPORT)
    print('[GUARD] requires exactly one wallet signer; cryptographically verifies signature; no broadcast')
    print('[NEXT] secure launcher 90s; watch for ORACLE162_SIGNATURE_VALID and simulation result')


def main():
    a=argparse.ArgumentParser()
    a.add_argument('--test',action='store_true')
    ns=a.parse_args()
    test() if ns.test else install()

if __name__=='__main__': main()
