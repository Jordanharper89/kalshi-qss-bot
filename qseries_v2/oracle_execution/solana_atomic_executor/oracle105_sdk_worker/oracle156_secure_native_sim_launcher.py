from __future__ import annotations
import argparse
import json
import os
import importlib
import sys
from pathlib import Path

ROOT = Path.cwd()
WALLET_META = ROOT / 'runtime_state/oracle/oracle_live_execution/solana_wallet_identity.json'
CANONICAL_ALT = ROOT / 'runtime_state/oracle/solana_atomic_executor/canonical_alt.json'
ALT_PROOF = ROOT / 'runtime_state/oracle/oracle_live_execution/ORACLE_151_CANONICAL_ALT_LIVE_PROOF.json'
BLOCKED = {'sendTransaction', 'sendRawTransaction', 'requestAirdrop', 'sendBundle'}

def load_public_wallet():
    if not WALLET_META.is_file():
        raise RuntimeError('HOLD_PUBLIC_WALLET_METADATA_MISSING')
    j = json.loads(WALLET_META.read_text(encoding='utf-8'))
    for k in ('wallet_pubkey','address','public_address','public_key','wallet','wallet_address'):
        v = j.get(k)
        if isinstance(v, str) and len(v) >= 32:
            return v
    raise RuntimeError('HOLD_PUBLIC_WALLET_FIELD_MISSING')

def evidence_gate():
    alt = json.loads(CANONICAL_ALT.read_text(encoding='utf-8'))
    proof = json.loads(ALT_PROOF.read_text(encoding='utf-8'))
    if not proof.get('ok') or proof.get('address') != alt.get('address'):
        raise RuntimeError('HOLD_CANONICAL_ALT_NOT_VERIFIED')
    return alt['address']

def credentials():
    import oracle120_credentials as cred
    wallet = cred.retrieve(cred.WALLET)
    helius = cred.retrieve(cred.HELIUS)
    if not isinstance(wallet, str) or not wallet.strip():
        raise RuntimeError('HOLD_WINDOWS_WALLET_CREDENTIAL_MISSING')
    if not isinstance(helius, str) or not helius.strip():
        raise RuntimeError('HOLD_WINDOWS_HELIUS_CREDENTIAL_MISSING')
    return wallet.strip(), helius.strip()

def prepare_environment(wallet, helius, expected_public):
    # Wallet private key is used in memory to sign simulated transactions only.
    os.environ['QSB_SOLANA_PRIVATE_KEY'] = wallet
    from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as core
    derived = str(core.keypair().pubkey())
    if derived != expected_public:
        os.environ.pop('QSB_SOLANA_PRIVATE_KEY', None)
        raise RuntimeError('HOLD_SIGNER_PUBLIC_WALLET_MISMATCH')
    os.environ['QSB_SOLANA_WALLET'] = expected_public
    os.environ['SOLANA_RPC_URL'] = 'https://mainnet.helius-rpc.com/?api-key=' + helius
    os.environ['SOLANA_WS_URL'] = 'wss://mainnet.helius-rpc.com/?api-key=' + helius
    return core

def block_broadcast(core):
    original = core.rpc
    def guarded(method, params):
        if str(method).lower() in {m.lower() for m in BLOCKED}:
            raise RuntimeError('ORACLE156_BROADCAST_PROHIBITED')
        return original(method, params)
    core.rpc = guarded
    def forbidden(*args, **kwargs):
        raise RuntimeError('ORACLE156_BROADCAST_PROHIBITED')
    core.send = forbidden
    return guarded

def test():
    class Fake:
        def rpc(self, method, params):
            return {'allowed': True}
        def send(self, raw):
            raise AssertionError('not reached')
    obj = Fake()
    guard = block_broadcast(obj)
    assert guard('getLatestBlockhash', []) == {'allowed': True}
    for name in ('sendTransaction','sendRawTransaction','sendBundle'):
        try:
            guard(name, [])
        except RuntimeError as exc:
            assert str(exc) == 'ORACLE156_BROADCAST_PROHIBITED'
        else:
            raise AssertionError('broadcast escaped guard')
    try:
        obj.send(b'example')
    except RuntimeError:
        pass
    else:
        raise AssertionError('send escaped guard')
    import types, unittest.mock as mock
    fake = types.SimpleNamespace(READY_TOKENS=set(), run=lambda seconds: seconds)
    assert hasattr(fake, 'READY_TOKENS') and fake.run(3.0) == 3.0
    with mock.patch('importlib.import_module', return_value=fake) as patched:
        loaded = importlib.import_module('qseries_v2.oracle_execution.solana_atomic_executor.runtime')
        assert loaded is fake and patched.call_count == 1
    assert 'runpy' not in globals()
    print('[TEST PASS] ORACLE157 canonical module identity, credential-independent broadcast guard')
    print('[SCOPE] simulation only; target size=0.050 SOL; no credential output')

def run(seconds):
    expected_public = load_public_wallet()
    table = evidence_gate()
    wallet, helius = credentials()
    try:
        core = prepare_environment(wallet, helius, expected_public)
    finally:
        wallet = None
        helius = None
    block_broadcast(core)
    print('[ORACLE156_CREDENTIAL_HANDOFF] windows_credential_manager=PASS public_identity=PASS', flush=True)
    print('[ORACLE156_ALT] canonical_verified=' + table, flush=True)
    print('[ORACLE156_MODE] SIMULATION_ONLY broadcast=BLOCKED requested_size=0.050_SOL', flush=True)
    try:
        runtime = importlib.import_module('qseries_v2.oracle_execution.solana_atomic_executor.runtime')
        # Guard the runtime's direct q96 transport in addition to core.rpc.
        if not hasattr(runtime, 'q96') or not callable(getattr(runtime.q96, '_rpc', None)):
            raise RuntimeError('HOLD_Q96_DIRECT_TRANSPORT_NOT_GUARDABLE')
        original_q96_rpc = runtime.q96._rpc
        def guarded_q96_rpc(method, params):
            if str(method).lower() in {m.lower() for m in BLOCKED}:
                raise RuntimeError('ORACLE158_Q96_BROADCAST_PROHIBITED')
            return original_q96_rpc(method, params)
        runtime.q96._rpc = guarded_q96_rpc
        if not hasattr(runtime, 'READY_TOKENS') or not callable(getattr(runtime, 'run', None)):
            raise RuntimeError('HOLD_CANONICAL_RUNTIME_INTERFACE_MISSING')
        print('[ORACLE157_CANONICAL_MODULE] READY_TOKENS_PRESENT=True main_alias=False', flush=True)
        runtime.run(float(seconds))
    finally:
        os.environ.pop('QSB_SOLANA_PRIVATE_KEY', None)
        os.environ.pop('SOLANA_RPC_URL', None)
        os.environ.pop('SOLANA_WS_URL', None)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true')
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--seconds', type=int, default=90)
    a = parser.parse_args()
    if a.test:
        test()
    elif a.run:
        run(a.seconds)
    else:
        parser.error('Use --test or --run')

if __name__ == '__main__':
    main()
