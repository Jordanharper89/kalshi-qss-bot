"""ORACLE-085: install exact DLMM output ATA preparation into active reverse route.
No RPC, signing, broadcast, or scanner changes. Fails closed on identity drift.
"""
from pathlib import Path
import ast
import argparse

P = Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle_054_reverse_native_handoff.py')
START = '# ORACLE085_REVERSE_EXACT_ATA_CUTOVER_BEGIN'
END = '# ORACLE085_REVERSE_EXACT_ATA_CUTOVER_END'
BLOCK = '''
# ORACLE085_REVERSE_EXACT_ATA_CUTOVER_BEGIN
_ORACLE085_UNBOUND_REVERSE_ROUTE = native_reverse_route

def native_reverse_route(snap, row, templates, rt, q18, fee_bps=20, reserve=100000):
    """Prepare the exact DLMM output ATA before the swap, without changing Q25/Q20/Q18."""
    from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint26_dlmm_output_ata_readiness as readiness
    route = _ORACLE085_UNBOUND_REVERSE_ROUTE(snap, row, templates, rt, q18, fee_bps, reserve)
    if route.get('direction') != 'METEORA_TO_PUMP':
        raise RuntimeError('ORACLE085_REVERSE_DIRECTION_DRIFT')
    if str(route.get('token')) != str(snap.get('token')):
        raise RuntimeError('ORACLE085_TOKEN_IDENTITY_DRIFT')
    pump = str(rt.q87.c.PUMP)
    signers = set()
    for _, instructions in route.get('original_candidates') or []:
        for ix in instructions:
            if str(ix.get('programId')) == pump:
                for account in ix.get('accounts') or []:
                    if account.get('isSigner') is True and account.get('pubkey'):
                        signers.add(str(account['pubkey']))
    if len(signers) != 1:
        raise RuntimeError('ORACLE085_EXACT_USER_SIGNER_UNRESOLVED:'+str(len(signers)))
    user = next(iter(signers))
    result = readiness._bind_exact_output_ata(
        user, snap, {'direction': 'METEORA_TO_PUMP'}, route
    )
    proof = result.get('checkpoint26_output_ata') or {}
    if (proof.get('before_dlmm') is not True or
        proof.get('create_idempotent') is not True or
        proof.get('direction') != 'METEORA_TO_PUMP'):
        raise RuntimeError('ORACLE085_OUTPUT_ATA_PROOF_MISSING')
    return result
# ORACLE085_REVERSE_EXACT_ATA_CUTOVER_END
'''

def test():
    tree = ast.parse(BLOCK)
    fn = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == 'native_reverse_route')
    assert fn.args.args[0].arg == 'snap'
    assert 'readiness._bind_exact_output_ata' in BLOCK
    assert 'ORACLE085_EXACT_USER_SIGNER_UNRESOLVED' in BLOCK
    assert 'ORACLE085_OUTPUT_ATA_PROOF_MISSING' in BLOCK
    assert P.is_file(), 'Expected existing reverse builder missing'
    content = P.read_text(encoding='utf-8')
    assert 'def native_reverse_route(' in content
    assert 'def meteora_buy_ix(' in content
    assert 'def rewrite_sell(' in content
    assert 'def warm_reverse_templates(' in content
    if START in content:
        assert content.count(START) == 1 and content.count(END) == 1
    print('[PASS] ORACLE085_STATIC_INTEGRATION_CONTRACT')
    print('[BOUNDARY] NO_RPC NO_PRIVATE_KEY NO_SIGNING NO_BROADCAST')

def install():
    test()
    original = P.read_text(encoding='utf-8')
    if START in original:
        print('[PASS] ORACLE085_ALREADY_INSTALLED')
        return
    if 'native_reverse_route =' in original or '_ORACLE085_UNBOUND_REVERSE_ROUTE' in original:
        raise RuntimeError('ORACLE085_UNEXPECTED_EXISTING_OVERRIDE')
    updated = original.rstrip() + '\n\n' + BLOCK
    ast.parse(updated, filename=str(P))
    backup = P.with_name(P.stem + '.before_oracle085.py')
    if backup.exists():
        raise RuntimeError('ORACLE085_BACKUP_ALREADY_EXISTS_WITHOUT_MARKER')
    backup.write_text(original, encoding='utf-8')
    temp = P.with_suffix('.oracle085.tmp')
    temp.write_text(updated, encoding='utf-8')
    temp.replace(P)
    print('[PASS] ORACLE085_REVERSE_NATIVE_ATA_CUTOVER_INSTALLED')
    print('[BACKUP]', backup)
    print('[TARGET]', P)
    print('[BOUNDARY] REVERSE_ATA_ONLY; WSOL_FUNDING_UNCHANGED; SIGNING_FALSE; BROADCAST_FALSE')

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--test', action='store_true')
    args = ap.parse_args()
    test() if args.test else install()
