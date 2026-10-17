"""ORACLE-274: validate verified WS bytes on receipt; zero REST, no trading."""
import argparse
import json
import os
import time
from collections import Counter
from pathlib import Path

import build_oracle_269_persistent_token_lifecycle as life
import build_oracle_270_verified_pool_ws_lifecycle as bridge
import build_oracle_272_ws_account_state_capture as capture
import build_oracle_273_canonical_ws_hydration_gate as gate

OUT = Path('runtime_state/oracle/oracle_live_execution/ORACLE274_INLINE_FRESH_WS_GATE.json')
GRID = [round(.010 + .005*i, 3) for i in range(19)]


def monitor(inventory, max_age=120):
    counts = Counter()
    seen = set()
    last = {'verified_pair_candidates': 0, 'candidates': []}
    original = capture.accept

    def hooked(state, item):
        result = original(state, item)
        counts[result] += 1
        if result == 'CAPTURED_NEW_ACCOUNT_STATE':
            now = time.time()
            label = gate.check_account(item['address'], item, inventory, now, max_age)
            counts['INLINE_'+label] += 1
            if label == 'VALID_CAPTURED_BYTES':
                review = gate.evaluate(state, inventory, now, max_age=max_age)
                last.update(review)
                for row in review['candidates']:
                    identity = (row['token'], row['pump_pool']['slot'], row['meteora_pool']['slot'])
                    if identity not in seen:
                        seen.add(identity)
                        counts['FRESH_TWO_VENUE_PAIR_OBSERVED'] += 1
        return result
    return hooked, original, counts, seen, last


def check_report(report):
    if report.get('build') != 'ORACLE274' or report.get('size_grid') != GRID:
        raise RuntimeError('GRID_OR_BUILD_MISMATCH')
    for key in ('signing', 'broadcast', 'execution_admission', 'canonical_full_hydration', 'local_pricing_connected'):
        if report.get(key) is not False:
            raise RuntimeError('FAIL_CLOSED_'+key)
    if report.get('rpc_poll_calls') != 0:
        raise RuntimeError('RPC_POLLING_NOT_ZERO')
    return True


def test():
    import base64, hashlib
    mint, pa, ma, owner = ('A'*32, 'B'*32, 'C'*32, 'D'*32)
    inv = {pa:[(mint,'PUMPSWAP_WS')], ma:[(mint,'METEORA_WS')]}
    hook, original, counts, seen, last = monitor(inv)
    now = time.time()
    def make(addr, venue, slot):
        raw = (addr+venue).encode()
        return {'address':addr, 'slot':slot, 'owner':owner, 'received_epoch':now,
                'data_b64':base64.b64encode(raw).decode(), 'fingerprint':hashlib.sha256(raw).hexdigest(),
                'byte_count':len(raw), 'refs':[[mint,venue]]}
    state = capture.empty()
    assert hook(state,make(pa,'PUMPSWAP_WS',100)) == 'CAPTURED_NEW_ACCOUNT_STATE'
    assert hook(state,make(ma,'METEORA_WS',102)) == 'CAPTURED_NEW_ACCOUNT_STATE'
    assert counts['FRESH_TWO_VENUE_PAIR_OBSERVED'] == 1
    assert hook(state,make(pa,'PUMPSWAP_WS',100)) == 'DUPLICATE'
    assert counts['FRESH_TWO_VENUE_PAIR_OBSERVED'] == 1
    stale=make(pa,'PUMPSWAP_WS',103);stale['received_epoch']-=200
    assert hook(state,stale) == 'CAPTURED_NEW_ACCOUNT_STATE'
    assert counts['INLINE_STALE_ACCOUNT'] == 1
    assert capture.accept is original
    assert check_report({'build':'ORACLE274','size_grid':GRID,'signing':False,'broadcast':False,
                         'execution_admission':False,'canonical_full_hydration':False,
                         'local_pricing_connected':False,'rpc_poll_calls':0})
    print('[ORACLE274_TEST_PASS] inline_freshness=TRUE duplicate=TRUE 19_sizes=TRUE no_orders=TRUE')


def run(seconds, maximum):
    if os.getenv('QSB_SOLANA_PRIVATE_KEY') or os.getenv('QSB_LIVE_ARM','NO').upper() != 'NO':
        raise RuntimeError('DISARMED_CHILD_REQUIRED')
    db = life.load(life.DB)
    inventory_all = bridge.inventory(bridge.INPUTS, set(db['tokens']))
    inventory = dict(list(inventory_all.items())[:maximum])
    if not inventory: raise RuntimeError('CANONICAL_POOL_INVENTORY_MISSING')
    hooked, original, counts, seen, last = monitor(inventory)
    capture.accept = hooked
    start = time.time()
    try:
        capture.run(seconds, maximum)
    finally:
        capture.accept = original
    # Capture may have finished with some accounts expired; distinguish peak vs final.
    state = capture.load(capture.STATE)
    final = gate.evaluate(state, inventory, time.time(), max_age=120)
    report = {'build':'ORACLE274', 'size_grid':GRID, 'watched_accounts':len(inventory),
              'event_counts':dict(counts),'unique_fresh_pair_state_combinations':len(seen),
              'last_inline_candidates':last['verified_pair_candidates'],
              'final_fresh_pair_candidates':final['verified_pair_candidates'],
              'final_account_checks':final['account_checks'],
              'elapsed_seconds':round(time.time()-start,2),
              'rpc_poll_calls':0, 'canonical_full_hydration':False,
              'local_pricing_connected':False,'execution_admission':False,
              'signing':False,'broadcast':False,
              'status':'POOL_BYTES_VERIFIED_MISSING_VAULT_AND_BIN_ACCOUNTS' if seen else 'HOLD_NO_FRESH_TWO_VENUE_PAIR'}
    check_report(report)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    capture.save(OUT,report)
    print('[ORACLE274_RESULT]',json.dumps(report,sort_keys=True))
    print('[REPORT]',OUT)


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--test',action='store_true');p.add_argument('--run',action='store_true')
    p.add_argument('--seconds',type=int,default=90);p.add_argument('--max-accounts',type=int,default=30)
    a=p.parse_args()
    if not(a.test or a.run):p.error('Specify --test or --run')
    if a.test:test()
    if a.run:run(max(15,min(a.seconds,180)),max(1,min(a.max_accounts,64)))
