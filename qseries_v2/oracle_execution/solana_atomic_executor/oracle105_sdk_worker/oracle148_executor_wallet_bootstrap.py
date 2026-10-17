"""ORACLE-148: bind a public execution wallet to ORACLE-147 template preparation.
No private-key access, signer creation, simulation or broadcast.
"""
import argparse
import json
import os
from pathlib import Path

REPORT = Path('runtime_state/oracle/oracle_live_execution/solana_wallet_identity.json')
MRIYA = 'MriyaNN8TMp6qRWjfr723PK7xgQK7yCt7Kg2v2PQu7X'

def validate_wallet(value):
    if not isinstance(value, str) or not value.strip() or value.strip() == MRIYA:
        raise ValueError('INVALID_OR_TRACKED_MRIYA_WALLET')
    from solders.pubkey import Pubkey
    pub = Pubkey.from_string(value.strip())
    if str(pub) != value.strip() or not pub.is_on_curve():
        raise ValueError('INVALID_EXECUTION_PUBLIC_WALLET')
    return str(pub)

def configure(wallet, root=Path('.')):
    pub = validate_wallet(wallet)
    from qseries_v2.oracle_execution.solana_atomic_executor.oracle105_sdk_worker import oracle146_native_template_preparation as stage
    path = root / REPORT
    # Never overwrite a different previously configured identity automatically.
    if path.exists():
        old = json.loads(path.read_text(encoding='utf-8'))
        previous = old.get('wallet_pubkey') if isinstance(old, dict) else None
        if previous and previous != pub:
            raise RuntimeError('HOLD_EXISTING_WALLET_IDENTITY_DIFFERS')
    # Check every public identity location used by ORACLE-147 for conflicts.
    existing, source, holds = stage.resolve_wallet(root, {'QSB_SOLANA_WALLET': ''})
    if 'HOLD_AMBIGUOUS_CONFIGURED_WALLET_IDENTITIES' in holds or (existing and existing != pub):
        raise RuntimeError('HOLD_CONFLICTING_EXISTING_PUBLIC_WALLET')
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps({'wallet_pubkey': pub, 'purpose': 'oracle_execution',
                                'build': 'ORACLE148', 'contains_private_key': False}, indent=2), encoding='utf-8')
    os.replace(temp, path)
    found, source, holds = stage.resolve_wallet(root, {'QSB_SOLANA_WALLET': ''})
    if found != pub or holds:
        raise RuntimeError('HOLD_WALLET_READBACK_FAILED')
    print('[ORACLE148_CONFIG_PASS] public wallet identity verified; source=%s' % source)
    print('[REPORT] %s' % path)
    print('[GUARD] no private-key access; signing=FALSE broadcast=FALSE')

def test():
    from tempfile import TemporaryDirectory
    from solders.keypair import Keypair
    a = str(Keypair().pubkey())
    b = str(Keypair().pubkey())
    with TemporaryDirectory() as d:
        root = Path(d)
        configure(a, root)
        configure(a, root)
        try:
            configure(b, root)
        except RuntimeError as exc:
            assert 'DIFFERS' in str(exc)
        else:
            raise AssertionError('wallet identity mutation accepted')
        payload = json.loads((root / REPORT).read_text(encoding='utf-8'))
        assert payload['wallet_pubkey'] == a and payload['contains_private_key'] is False
    try:
        validate_wallet(MRIYA)
    except ValueError:
        pass
    else:
        raise AssertionError('tracked wallet accepted')
    print('[TEST PASS] ORACLE148 public identity setup/readback, mismatch rejection, no secrets')

def main():
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--test', action='store_true')
    g.add_argument('--configure', action='store_true')
    args = p.parse_args()
    if args.test:
        test()
    else:
        print('[PUBLIC ADDRESS ONLY] Enter YOUR executor wallet address, never seed phrase or private key.')
        address = input('Execution wallet PUBLIC address: ').strip()
        configure(address)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
