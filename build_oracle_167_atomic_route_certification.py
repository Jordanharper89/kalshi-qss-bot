"""ORACLE-167: deterministic, offline certification of installed atomic ATA route.
No credentials, imports of runtime, RPC, signing, or broadcast. Fail closed.
"""
import argparse
import ast
import json
from pathlib import Path
from types import SimpleNamespace

ROOT = Path('qseries_v2/oracle_execution/solana_atomic_executor')
TARGET = ROOT / 'runtime.py'
REPORT = Path('runtime_state/oracle/oracle_live_execution/ORACLE167_ATOMIC_ROUTE_CERTIFICATION.json')
ATA_PROGRAM = 'ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL'
TOKEN_PROGRAM = 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'
TOKEN_2022 = 'TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb'
WSOL = 'So11111111111111111111111111111111111111112'


def fail(reason):
    raise RuntimeError('HOLD_ORACLE167_' + reason)


def get_function(tree, name):
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name]
    if len(nodes) != 1:
        fail('FUNCTION_' + name + '_COUNT_' + str(len(nodes)))
    return nodes[0]


def certify(source):
    tree = ast.parse(source)
    helper = get_function(tree, '_reverse_prepend_ata_readiness')
    profit = get_function(tree, '_fast_010_profit_lock_route')
    helper_source = ast.get_source_segment(source, helper) or ''
    profit_source = ast.get_source_segment(source, profit) or ''
    for term in ('_ata_create_idempotent_ix(', '"original_candidates"', '"reverse_ata_ready"'):
        if term not in helper_source:
            fail('HELPER_CONTRACT_' + term[:25])
    for term in ('ORACLE166C_FORWARD_ATA_READINESS', 'direction in ("PUMP_TO_METEORA", "METEORA_TO_PUMP")',
                 '_mry019_align_meteora_programs(out)', '_reverse_prepend_ata_readiness(',
                 '"ATA_READY_"', '"ORACLE166C_ATA_NOT_CERTIFIED"'):
        if term not in profit_source:
            fail('ROUTE_CONTRACT_' + term[:30])
    if profit_source.index('_mry019_align_meteora_programs(out)') > profit_source.index('ORACLE166C_FORWARD_ATA_READINESS'):
        fail('ATA_BEFORE_PROGRAM_ALIGNMENT')
    if 'ORACLE158_SIMULATION_ONLY_DIRECT_SEND_BLOCKED' not in source:
        fail('SEND_GUARD_ABSENT')
    if 'start != 50_000_000' not in source or 'size>1232' not in source:
        fail('NATIVE_COMPILER_GUARD_ABSENT')
    # Execute ONLY the inspected ATA helper AST in an isolated, restricted namespace.
    # The helper receives deterministic mock instruction constructors and mock templates.
    code = compile(ast.fix_missing_locations(ast.Module(body=[helper], type_ignores=[])), '<oracle167-offline-helper>', 'exec')
    cases = []
    for token_program in (TOKEN_PROGRAM, TOKEN_2022):
        token = 'TEST_TOKEN_MINT'
        user = 'TEST_PUBLIC_WALLET'
        calls = []
        def create(payer, owner, mint, program):
            calls.append((payer, owner, mint, program))
            return {'programId': ATA_PROGRAM, 'data': '02',
                    'accounts': [{'pubkey': owner}, {'pubkey': mint}, {'pubkey': program}]}
        # Real helper reads account index 11 from the Pump instruction and
        # also reads matching Meteora token program from fixed_accounts.
        pump_accounts = [{'pubkey': 'NOT_TOKEN_PROGRAM'} for _ in range(12)]
        pump_accounts[11] = {'pubkey': token_program}
        mock_ix = {'programId': 'PUMP_SWAP', 'accounts': pump_accounts, 'data': 'mock'}
        meteora = {'programId': 'METEORA_DLMM', 'accounts': [], 'data': 'mock'}
        route = {'token': token, 'original_candidates': [
            ('FULL', [mock_ix, meteora]), ('COMPACT', [mock_ix, meteora])]}
        g = {'_ata_create_idempotent_ix': create,
             'METEORA_TEMPLATES': {token: {'token_x': token, 'token_y': WSOL,
                  'fixed_accounts': [(token_program, False, False)] * 13}},
             'TEMPLATES': {token: {'pump_index': 0, 'instructions': [mock_ix]}},
             'q87': SimpleNamespace(c=SimpleNamespace(WSOL=WSOL, TOKEN=TOKEN_PROGRAM))}
        exec(code, g)
        output = g['_reverse_prepend_ata_readiness'](user, token, route)
        if output.get('reverse_ata_ready') is not True:
            fail('READINESS_NOT_TRUE')
        if len(output['original_candidates']) != 2 or len(calls) != 2:
            fail('CANDIDATE_OR_ATA_COUNT')
        if calls[0] != (user, user, WSOL, TOKEN_PROGRAM) or calls[1] != (user, user, token, token_program):
            fail('ATA_MINT_OR_TOKEN_PROGRAM_MISMATCH')
        for label, ixs in output['original_candidates']:
            if not label.startswith('ATA_READY_') or len(ixs) != 4:
                fail('CANDIDATE_LENGTH_OR_LABEL')
            if [ix['programId'] for ix in ixs] != [ATA_PROGRAM, ATA_PROGRAM, 'PUMP_SWAP', 'METEORA_DLMM']:
                fail('ATA_PREFIX_OR_SWAP_LEG_ORDER')
        cases.append({'token_program': token_program, 'ata_count': 2,
                      'candidate_count': 2, 'instruction_order': 'ATA,ATA,PUMP,METEORA', 'result': 'PASS'})
    return {'build': 'ORACLE167', 'status': 'OFFLINE_ROUTE_CONTRACT_PASS',
            'amount_lamports': 50_000_000, 'max_packet_bytes': 1232,
            'cases': cases, 'actual_serialized_packet_bytes': None,
            'actual_signed_simulation_pass': False, 'actual_profit_certified': False,
            'signing': False, 'broadcast': False}


def test():
    fixture = '''CANARY_TRADE_LAMPORTS=50_000_000
ORACLE158_SIMULATION_ONLY_DIRECT_SEND_BLOCKED=True
# start != 50_000_000 size>1232
''' + '''def _reverse_prepend_ata_readiness(user, token, route):
    create_wsol_ata=_ata_create_idempotent_ix(user,user,q87.c.WSOL,q87.c.TOKEN)
    template=METEORA_TEMPLATES[token]
    fixed=template["fixed_accounts"]
    token_program=fixed[11][0]
    _tpl=TEMPLATES[token]
    _pix=_tpl["instructions"][_tpl["pump_index"]]
    token_program=_pix["accounts"][11]["pubkey"]
    create_token_ata=_ata_create_idempotent_ix(user,user,token,token_program)
    out=dict(route)
    out["original_candidates"]=[("ATA_READY_"+name,[create_token_ata,create_wsol_ata]+list(ixs)) for name,ixs in route["original_candidates"]]
    out["reverse_ata_ready"]=True
    return out

def _fast_010_profit_lock_route(route,direction,required_final_out):
    out=dict(route)
    out=_mry019_align_meteora_programs(out)
    # ORACLE166C_FORWARD_ATA_READINESS
    if direction in ("PUMP_TO_METEORA", "METEORA_TO_PUMP"):
        out=_reverse_prepend_ata_readiness(USER,str(out.get("token") or ""),out)
        if out.get("reverse_ata_ready") is not True:
            raise RuntimeError("ORACLE166C_ATA_NOT_CERTIFIED")
        candidates=out.get("original_candidates")
        for name,ixs in candidates:
            if not str(name).startswith("ATA_READY_"):
                raise RuntimeError("BAD")
    return out,0,0
'''
    certify(fixture)
    for bad in (fixture.replace('ORACLE158_SIMULATION_ONLY_DIRECT_SEND_BLOCKED', 'UNSAFE_SEND'),
                fixture.replace('size>1232', 'size>9999'),
                fixture.replace('"PUMP_TO_METEORA", "METEORA_TO_PUMP"', '"METEORA_TO_PUMP"')):
        try:
            certify(bad)
            raise AssertionError('Should have failed closed')
        except RuntimeError as exc:
            assert str(exc).startswith('HOLD_ORACLE167_')
    print('[TEST PASS] ORACLE167 offline ATA construction, SPL and Token-2022, ordered swap legs, fail closed')


def run():
    if not TARGET.is_file():
        fail('RUNTIME_NOT_FOUND')
    result = certify(TARGET.read_text(encoding='utf-8'))
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('[ORACLE167_PASS] deterministic_ata=TRUE ordered_legs=TRUE broadcast=FALSE')
    print('[ORACLE167_UNCERTIFIED] real_packet_bytes=UNKNOWN signed_sim=FALSE realized_profit=FALSE')
    print('[REPORT]', REPORT)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true')
    args = parser.parse_args()
    test() if args.test else run()
