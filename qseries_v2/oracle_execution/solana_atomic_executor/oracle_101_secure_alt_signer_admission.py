"""Hidden credential admission for existing ALT; never signs or broadcasts."""
import getpass, json, os
from pathlib import Path
from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r

ROOT = Path('runtime_state/oracle/solana_atomic_executor')

def main():
    p = ROOT / 'oracle100_unsigned_extension_packet.json'
    report = json.loads(p.read_text(encoding='utf-8'))
    plan = json.loads((ROOT / 'canonical_alt_plan.json').read_text(encoding='utf-8'))
    reg = json.loads((ROOT / 'canonical_alt.json').read_text(encoding='utf-8'))
    authority = 'DshvULBw4foHgiqLksn8H6vHWredDT6mrJBmKLTFJih6'
    table = 'HSEM6g4Txajd6EHPav7GBanr4eXc5zzSs4cmySthg97r'
    if report.get('status') != 'UNSIGNED_PACKET_PREFLIGHT_ONLY' or report.get('signing') is not False or report.get('broadcast') is not False:
        raise RuntimeError('ORACLE100_REPORT_NOT_SAFE')
    if report.get('table') != table or reg.get('address') != table or report.get('authority') != authority or plan.get('public_payer') != authority:
        raise RuntimeError('CANONICAL_ALT_IDENTITY_MISMATCH')
    missing = report.get('missing')
    if not isinstance(missing,list) or len(missing) != 5 or len(set(missing)) != 5 or report.get('missing_count') != 5:
        raise RuntimeError('EXTENSION_ADDRESS_SET_MISMATCH')
    if not set(missing).issubset(set(plan.get('selected_addresses', []))):
        raise RuntimeError('UNAUTHORIZED_EXTENSION_ADDRESS')
    if int(report.get('estimated_total_lamports', -1)) > 1000000:
        raise RuntimeError('PREFLIGHT_COST_EXCEEDS_1000000_LAMPORT_CAP')
    if os.environ.get('QSB_SOLANA_PRIVATE_KEY'):
        raise RuntimeError('KEY_ALREADY_IN_ENV_REFUSE_TO_OVERRIDE')
    print('[ORACLE101] Five-address extension signer admission; NO SIGNING OR BROADCAST')
    secret = getpass.getpass('Solana signing key (hidden, local only): ').strip()
    if not secret:
        raise RuntimeError('KEY_REQUIRED')
    try:
        os.environ['QSB_SOLANA_PRIVATE_KEY'] = secret
        del secret
        signer, pubkey = r.q87.c.sim_identity()
        if signer is None or str(pubkey) != authority or str(signer.pubkey()) != authority:
            raise RuntimeError('SIGNER_NOT_ALT_AUTHORITY')
        print('[PASS] ORACLE101_SIGNER_MATCHES_EXISTING_ALT_AUTHORITY')
        print('[PASS] ORACLE101_APPROVED_MISSING_ADDRESSES=5')
        print('[PASS] ORACLE101_ESTIMATED_COST_UNDER_1000000_LAMPORT_CAP')
        print('[HOLD] NO_TRANSACTION_SIGNED_OR_SENT; KEY_NOT_PERSISTED')
    finally:
        os.environ.pop('QSB_SOLANA_PRIVATE_KEY', None)

if __name__ == '__main__': main()
