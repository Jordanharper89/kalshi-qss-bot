"""ORACLE-168: read-only signed-size-equivalent v0 packet certification.
No runtime import, wallet key, RPC, transaction signature or broadcast.
Requires a saved canonical route JSON with full candidate instructions and ALT entries.
"""
import argparse
import base64
import json
from pathlib import Path

OUT = Path('runtime_state/oracle/oracle_live_execution/ORACLE168_NATIVE_PACKET_CERTIFICATION.json')
ATA = 'ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL'
PUMP = 'pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA'
MAX = 1232
AMOUNT = 50_000_000


def hold(reason):
    raise RuntimeError('HOLD_ORACLE168_' + reason)


def pub(s):
    from solders.pubkey import Pubkey
    if not isinstance(s, str) or not s:
        hold('INVALID_PUBLIC_KEY')
    try:
        return Pubkey.from_string(s)
    except Exception:
        hold('INVALID_PUBLIC_KEY')


def parse_ix(d):
    from solders.instruction import AccountMeta, Instruction
    if not isinstance(d, dict) or not isinstance(d.get('accounts'), list):
        hold('INVALID_INSTRUCTION')
    raw = d.get('data')
    if not isinstance(raw, str):
        hold('MISSING_INSTRUCTION_DATA')
    try:
        data = base64.b64decode(raw, validate=True)
    except Exception:
        hold('INVALID_INSTRUCTION_DATA')
    metas = []
    for a in d['accounts']:
        if not isinstance(a, dict) or 'pubkey' not in a:
            hold('INVALID_ACCOUNT_META')
        signer = a.get('isSigner', a.get('is_signer'))
        writable = a.get('isWritable', a.get('is_writable'))
        if type(signer) is not bool or type(writable) is not bool:
            hold('ACCOUNT_META_PERMISSIONS_MISSING')
        metas.append(AccountMeta(pub(a['pubkey']), signer, writable))
    return Instruction(pub(d['programId']), data, metas)


def find_routes(src):
    """Accept only explicit route records, not arbitrary startup reports."""
    records = src if isinstance(src, list) else [src]
    return [r for r in records if isinstance(r, dict) and
            isinstance(r.get('original_candidates'), list) and
            type(r.get('start_lamports')) is int]


def certify(source):
    routes = find_routes(source)
    if len(routes) != 1:
        hold('NEED_EXACTLY_ONE_SAVED_ROUTE')
    route = routes[0]
    if route['start_lamports'] != AMOUNT:
        hold('AMOUNT_NOT_050_SOL')
    if not isinstance(route.get('user') or route.get('payer'), str):
        hold('PAYER_PUBLIC_KEY_REQUIRED')
    payer = pub(route.get('user') or route.get('payer'))
    blockhash = route.get('blockhash')
    # A deterministic public blockhash is enough for size measurement only.
    # Never claim this packet was current or valid for chain execution.
    dummy_blockhash = Hash.default() if not blockhash else Hash.from_string(blockhash)
    alt_input = route.get('lookup_tables')
    if not isinstance(alt_input, list) or not alt_input:
        hold('LOOKUP_TABLE_CONTENTS_REQUIRED')
    from solders.hash import Hash
    from solders.message import MessageV0
    from solders.address_lookup_table_account import AddressLookupTableAccount
    from solders.signature import Signature
    from solders.transaction import VersionedTransaction
    alts = []
    for a in alt_input:
        if not isinstance(a, dict) or not isinstance(a.get('addresses'), list):
            hold('INVALID_LOOKUP_TABLE_CONTENTS')
        alts.append(AddressLookupTableAccount(pub(a.get('key') or a.get('address')),
                                               [pub(p) for p in a['addresses']]))
    expected_meteora = route.get('meteora_program_id')
    if not expected_meteora and isinstance(route.get('meteora_ix'), dict):
        expected_meteora = route['meteora_ix'].get('programId')
    if not expected_meteora or expected_meteora in (PUMP, ATA):
        hold('METEORA_PROGRAM_ID_UNCERTIFIED')
    candidates = []
    for candidate in route['original_candidates']:
        if not isinstance(candidate, (list, tuple)) or len(candidate) != 2:
            hold('BAD_CANDIDATE_SHAPE')
        name, raw_ixs = candidate
        if not isinstance(raw_ixs, list) or len(raw_ixs) < 4:
            hold('CANDIDATE_MISSING_INSTRUCTIONS')
        programs = [r.get('programId') for r in raw_ixs if isinstance(r, dict)]
        if len(programs) != len(raw_ixs) or programs[:2] != [ATA, ATA]:
            hold('ATA_PREFIX_MISSING')
        if programs.count(PUMP) != 1 or programs.count(expected_meteora) != 1:
            hold('BOTH_SWAP_LEGS_REQUIRED')
        if programs.index(PUMP) < 2 or programs.index(expected_meteora) < 2:
            hold('SWAP_PRECEDES_ATA')
        if route.get('direction') == 'PUMP_TO_METEORA' and programs.index(PUMP) > programs.index(expected_meteora):
            hold('FORWARD_LEG_ORDER')
        if route.get('direction') == 'METEORA_TO_PUMP' and programs.index(expected_meteora) > programs.index(PUMP):
            hold('REVERSE_LEG_ORDER')
        instructions = [parse_ix(x) for x in raw_ixs]
        message = MessageV0.try_compile(payer, instructions, alts, dummy_blockhash)
        if message.header.num_required_signatures != 1:
            hold('MULTI_SIGNER_NOT_CERTIFIED')
        # Populate with a 64-byte *empty signature*. Packet length is exact,
        # but packet IS NOT signed, valid, broadcastable, or simulated.
        packet = VersionedTransaction.populate(message, [Signature.default()])
        length = len(bytes(packet))
        candidates.append({'candidate': str(name)[:80], 'serialized_bytes': length,
                           'fits_1232': length <= MAX, 'instructions': len(raw_ixs),
                           'lookup_tables': len(message.address_table_lookups),
                           'required_signatures': message.header.num_required_signatures,
                           'direction': route.get('direction')})
    if not candidates:
        hold('NO_CANDIDATES')
    best = min(candidates, key=lambda r:r['serialized_bytes'])
    return {'build': 'ORACLE168', 'status': 'OFFLINE_NATIVE_SIZE_PASS' if best['fits_1232'] else 'HOLD_PACKET_TOO_LARGE',
            'real_saved_route_input': True, 'wallet_signing': False,
            'broadcast': False, 'on_chain_simulation': False, 'profit_certified': False,
            'blockhash_freshness_certified': False, 'candidate_results': candidates,
            'smallest_serialized_bytes': best['serialized_bytes']}


def test():
    # Deterministic negative checks that must HOLD before any Solana SDK invocation.
    for src in ({}, {'start_lamports':AMOUNT,'original_candidates':[]},
                {'start_lamports':10_000_000,'original_candidates':[]}):
        try:
            certify(src)
            raise AssertionError('Expected explicit HOLD')
        except RuntimeError as e:
            assert str(e).startswith('HOLD_ORACLE168_'), str(e)
    print('[TEST PASS] ORACLE168 missing-route and amount fail-closed')


def run(route_file):
    if not route_file:
        hold('SAVED_ROUTE_JSON_REQUIRED_NO_LIVE_CAPTURE_INVENTED')
    path = Path(route_file)
    if not path.is_file():
        hold('SAVED_ROUTE_FILE_NOT_FOUND')
    obj = json.loads(path.read_text(encoding='utf-8'))
    result = certify(obj)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('[ORACLE168_PACKET] smallest_bytes=%s max=1232 status=%s' %
          (result['smallest_serialized_bytes'],result['status']))
    print('[ORACLE168_SCOPE] placeholder_signature=TRUE rpc=FALSE signing=FALSE broadcast=FALSE')
    print('[REPORT]', OUT)
    if result['status'] != 'OFFLINE_NATIVE_SIZE_PASS':
        hold('PACKET_EXCEEDS_MAX')


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--test',action='store_true')
    p.add_argument('--route-json',default=None)
    args=p.parse_args()
    test() if args.test else run(args.route_json)
