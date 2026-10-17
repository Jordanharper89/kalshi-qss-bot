"""ORACLE-257: one-run Mriya-to-hydration-to-gross-pricing audit; no execution."""
import argparse
import json
import os
import re
from collections import Counter
from pathlib import Path

ROOT = Path('runtime_state/oracle/oracle_live_execution')
RAW = ROOT / 'ORACLE257_CANONICAL_RAW.json'
OUT = ROOT / 'ORACLE257_MRIYA_PRICING_GATE.json'
SIZES = (0.010, 0.015, 0.030, 0.060)
DIRECTIONS = {'PUMP_TO_METEORA', 'METEORA_TO_PUMP'}
B58 = re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')


def token(row):
    if isinstance(row, str) and B58.fullmatch(row):
        return row
    if isinstance(row, dict):
        for name in ('token', 'mint', 'token_mint', 'base_mint'):
            v = row.get(name)
            if isinstance(v, str) and B58.fullmatch(v):
                return v
    v = getattr(row, 'token', None)
    return str(v) if v is not None and B58.fullmatch(str(v)) else None


def tokens(rows):
    return {v for row in rows if (v := token(row))}


def classify(source, stages):
    if source.get('build') != 'ORACLE241' or any(
        source.get(k) is not False for k in ('signing', 'broadcast', 'execution_admission')
    ):
        raise ValueError('UNTRUSTED_ORACLE241_REPORT')
    hot = stages['hot']
    rows = []
    for mint in sorted(hot):
        matches = [o for o in source.get('observations', []) if o.get('mint') == mint]
        best = None
        holds = Counter()
        valid = 0
        for o in matches:
            if o.get('status') != 'FULL_FILL_GROSS_MEASURED':
                holds[str(o.get('status', 'UNKNOWN'))[:64]] += 1
                continue
            size = o.get('size_sol')
            if type(size) not in (float, int) or not any(abs(size - s) < 1e-9 for s in SIZES):
                holds['INVALID_SIZE'] += 1
                continue
            start = round(size * 1_000_000_000)
            qs = o.get('directions')
            if not isinstance(qs, list) or len(qs) != 2 or any(not isinstance(q, dict) for q in qs) or {q.get('direction') for q in qs} != DIRECTIONS or any(
                type(q.get('start_lamports')) is not int or q['start_lamports'] != start or
                type(q.get('end_lamports')) is not int or q['end_lamports'] <= 0 or
                type(q.get('gross_lamports')) is not int or q['gross_lamports'] != q['end_lamports'] - start
                for q in qs
            ):
                holds['INVALID_FULL_FILL_ACCOUNTING'] += 1
                continue
            valid += 1
            for q in qs:
                candidate = {'direction': q['direction'], 'size_sol': size,
                             'gross_lamports': q['gross_lamports'],
                             'gross_bps': round(q['gross_lamports'] * 10000 / start, 4)}
                if best is None or candidate['gross_lamports'] > best['gross_lamports']:
                    best = candidate
        rows.append({'token': mint, 'in_raw': mint in stages['raw'],
                     'in_exact': mint in stages['exact'],
                     'hydrated': mint in stages['hydrated'],
                     'sample_attempts': len(matches), 'valid_full_fill_samples': valid,
                     'holds': dict(holds), 'best': best,
                     'positive_gross': best is not None and best['gross_lamports'] > 0,
                     'eligible_for_execution': False})
    return rows


def test():
    a = 'A' * 32
    q = lambda d, end: {'direction': d, 'start_lamports': 10_000_000,
                         'end_lamports': end, 'gross_lamports': end - 10_000_000}
    s = {'build': 'ORACLE241', 'signing': False, 'broadcast': False,
         'execution_admission': False, 'observations': [{'mint': a, 'size_sol': .01,
         'status': 'FULL_FILL_GROSS_MEASURED', 'directions': [
         q('PUMP_TO_METEORA', 10_001_000), q('METEORA_TO_PUMP', 9_999_000)]}]}
    stages = dict.fromkeys(('hot', 'raw', 'exact', 'hydrated'), {a})
    assert classify(s, stages)[0]['positive_gross']
    assert classify(s, stages)[0]['valid_full_fill_samples'] == 1
    s['observations'][0]['directions'][0]['gross_lamports'] = 999
    assert classify(s, stages)[0]['valid_full_fill_samples'] == 0
    s['signing'] = True
    try:
        classify(s, stages)
    except ValueError:
        pass
    else:
        raise AssertionError('UNSAFE_REPORT_ADMITTED')
    print('[ORACLE257_TEST_PASS] lineage=TRUE full_fill=TRUE accounting=TRUE fail_closed=TRUE')


def run():
    if os.getenv('QSB_LIVE_ARM', 'NO').upper() != 'NO' or os.getenv('QSB_SOLANA_PRIVATE_KEY'):
        raise RuntimeError('DISARMED_ENV_REQUIRED')
    if not os.getenv('SOLANA_RPC_URL', '').startswith('https://'):
        raise RuntimeError('RPC_REQUIRED')
    import build_oracle_241_live_opportunity_sampler as sampler
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import engine, live_account_stream as pd
    g = pd.prepare_pairs.__globals__
    cap = g.get('MAX_PAIRS')
    if type(cap) is not int or not 1 <= cap <= 100:
        raise RuntimeError('UNVERIFIED_CAP')
    originals = {('engine', name): getattr(engine, name) for name in
                 ('mriya_hot_tokens', 'raw_candidate_universe', 'candidate_universe')}
    originals[('pd', 'prepare_pairs')] = pd.prepare_pairs
    original_sizes, original_out = sampler.SIZES, sampler.OUT
    stages = {key: set() for key in ('hot', 'raw', 'exact', 'hydrated')}
    calls = Counter()

    def watch(key, fn, pair_mode=False):
        def wrapped(*args, **kwargs):
            result = fn(*args, **kwargs)
            items = result[0] if pair_mode else result
            if not isinstance(items, (list, tuple)):
                raise RuntimeError('UNEXPECTED_PRODUCER_RESULT_' + key)
            stages[key].update(tokens(items))
            calls[key] += 1
            return result
        return wrapped

    ROOT.mkdir(parents=True, exist_ok=True)
    if RAW.exists():
        RAW.unlink()
    try:
        g['MAX_PAIRS'] = max(cap, 12)
        for (owner, name), fn in originals.items():
            module = engine if owner == 'engine' else pd
            key = ('hot' if name == 'mriya_hot_tokens' else
                   'raw' if name == 'raw_candidate_universe' else
                   'exact' if name == 'candidate_universe' else 'hydrated')
            setattr(module, name, watch(key, fn, name == 'prepare_pairs'))
        sampler.SIZES, sampler.OUT = SIZES, RAW
        sampler.run(1, 12, 0)
    finally:
        sampler.SIZES, sampler.OUT = original_sizes, original_out
        g['MAX_PAIRS'] = cap
        for (owner, name), fn in originals.items():
            setattr(engine if owner == 'engine' else pd, name, fn)
    if not RAW.is_file():
        raise RuntimeError('MISSING_CANONICAL_REPORT')
    source = json.loads(RAW.read_text(encoding='utf-8'))
    rows = classify(source, stages)
    report = {'build': 'ORACLE257', 'calls': dict(calls), 'hot_count': len(stages['hot']),
              'raw_mriya': len(stages['hot'] & stages['raw']),
              'exact_mriya': len(stages['hot'] & stages['exact']),
              'hydrated_mriya': len(stages['hot'] & stages['hydrated']),
              'quoted_mriya': sum(r['valid_full_fill_samples'] > 0 for r in rows),
              'positive_mriya': sum(r['positive_gross'] for r in rows),
              'rows': rows, 'cap_restored': g['MAX_PAIRS'] == cap,
              'fresh_state_certified': False, 'net_profit_certified': False,
              'execution_admission': False, 'signing': False, 'broadcast': False,
              'status': 'HOLD_NET_FRESHNESS_ATOMIC_CERTIFICATION'}
    OUT.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('[ORACLE257_RESULT]', json.dumps({k: v for k, v in report.items() if k != 'rows'}, sort_keys=True))
    for r in rows:
        print('[ORACLE257_MRIYA]', json.dumps({**r, 'token': r['token'][:12]}, sort_keys=True))
    print('[REPORT]', OUT)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--test', action='store_true')
    ap.add_argument('--run', action='store_true')
    a = ap.parse_args()
    if not (a.test or a.run):
        ap.error('Specify --test or --run')
    if a.test:
        test()
    if a.run:
        run()