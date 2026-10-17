from __future__ import annotations
import argparse, ast, hashlib, json, os, time
from pathlib import Path

BASE = Path('qseries_v2/oracle_execution/solana_atomic_executor')
TARGET = BASE / 'oracle_524_verified_execution_shadow.py'
SCANNER = BASE / 'boss_scanner_live.py'
STAGE = Path('runtime_state/oracle/final_boss_dual/staged_discovery.json')
Q521 = Path('runtime_state/oracle/oracle_live_execution/oracle_521/quote_coverage.json')
Q523 = Path('runtime_state/oracle/oracle_live_execution/oracle_523/inventory_handoff.json')
REGISTRY = Path('runtime_state/oracle/solana_atomic_executor/multi_dlmm_pair_registry.json')
ROOT = Path('runtime_state/oracle/oracle_live_execution/oracle_524')
SHADOW = ROOT / 'verified_candidate_registry.json'
REPORT = ROOT / 'handoff_report.json'
REVISION = 'CHECKPOINT11_MULTI_POOL_REGISTRY_V1'
B58 = set('123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz')
class Hold(RuntimeError): pass

def valid(s):
    return isinstance(s,str) and 32 <= len(s) <= 44 and set(s) <= B58

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def read(p):
    if not Path(p).is_file(): raise Hold('MISSING_'+Path(p).name)
    obj = json.loads(Path(p).read_text(encoding='utf-8'))
    if not isinstance(obj,dict): raise Hold('INVALID_JSON_'+Path(p).name)
    return obj

def write(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    t = p.with_name(p.name+'.'+str(os.getpid())+'.tmp')
    try:
        t.write_text(json.dumps(obj,sort_keys=True,indent=2),encoding='utf-8')
        os.replace(t,p)
    finally: t.unlink(missing_ok=True)

def safe_field(k):
    return not any(x in str(k).lower() for x in ('secret','private','password','credential','api_key','authorization'))

def shape(c):
    out = {'top_level_fields':sorted(k for k in c if safe_field(k)),'collections':{}}
    for k,v in c.items():
        if not safe_field(k) or not isinstance(v,(list,dict)): continue
        item = next(iter(v.values()),None) if isinstance(v,dict) else next(iter(v),None)
        out['collections'][k] = {'container':type(v).__name__,'length':len(v),
                                  'item_type':type(item).__name__,
                                  'item_fields':sorted(f for f in item if safe_field(f)) if isinstance(item,dict) else []}
    return out

def join(observed,selected,canonical,stage=None):
    if observed.get('status')!='PASS_LIVE_QUOTE_COVERAGE_MEASURED': raise Hold('521_PASS_REQUIRED')
    if canonical.get('revision')!=REVISION: raise Hold('NATIVE_REGISTRY_REVISION_CHANGED')
    evidence=observed.get('pair_results')
    if not isinstance(evidence,list) or not evidence: raise Hold('521_EVIDENCE_MISSING')
    by_quote={}
    for row in evidence:
        if not isinstance(row,dict) or not valid(row.get('token')): raise Hold('521_BAD_TOKEN')
        token=row['token']
        if token in by_quote: raise Hold('521_DUPLICATE_TOKEN')
        state=row.get('result')
        if state not in ('MATCHED_QUOTE_OBSERVED','NO_MATCHED_QUOTE_IN_WINDOW'):
            raise Hold('521_UNKNOWN_QUOTE_STATE')
        by_quote[token] = state=='MATCHED_QUOTE_OBSERVED'
    if observed.get('visible_pairs')!=len(by_quote) or observed.get('matched_quoted_pairs')!=sum(by_quote.values()):
        raise Hold('521_COUNTER_MISMATCH')
    quoted={token for token,yes in by_quote.items() if yes}
    if not isinstance(selected,list): raise Hold('QUALIFIED_ROWS_NOT_LIST')
    stage_map={}; current_rows=[]
    if isinstance(stage,dict) and isinstance(stage.get('rows'),list):
        current_rows=stage['rows']
        for row in current_rows:
            if isinstance(row,dict) and valid(row.get('token')) and valid(row.get('pump_pool')):
                stage_map.setdefault(row['token'],set()).add(row['pump_pool'])
    candidates={}; conflicts=[]
    for q in selected:
        if not isinstance(q,dict): continue
        token,pump,meteora=q.get('token'),q.get('pump_pool'),q.get('meteora_pool')
        if token not in quoted: continue
        if not valid(pump) or not valid(meteora) or pump==meteora:
            conflicts.append(str(token)[:12]+':UNVERIFIED_POOL'); continue
        key=token+'|'+meteora
        old=candidates.get(key)
        if old and old['pump_pool']!=pump:
            conflicts.append(token[:12]+':AMBIGUOUS_PUMP_POOL'); continue
        candidates[key]={'pair_key':key,'token':token,'pump_pool':pump,
                         'meteora_pool':meteora,'quote_observed_in_historical_521_window':True,
                         'current_stage_exact_pump_match':pump in stage_map.get(token,set())}
    if conflicts: raise Hold('CONFLICTING_QUALIFIED_POOL_IDENTITY:'+','.join(conflicts[:4]))
    rows=sorted(candidates.values(),key=lambda r:r['pair_key'])
    shadow={'revision':'ORACLE524_HISTORICAL_QUOTE_CANDIDATES_V3',
            'row_key':'pair_key','rows':rows,'native_executor_compatible':False,
            'production_cutover':False,'live_quote_freshness_certified':False}
    report={'status':('PASS_524_HISTORICAL_QUOTE_PAIRS_JOINED' if rows else 'HOLD_NO_QUALIFIED_HISTORICAL_QUOTE_PAIRS'),
            'historical_521_visible':len(by_quote),'historical_521_quoted':len(quoted),
            'qualified_quote_pair_keys':len(rows),
            'qualified_quote_tokens':len({r['token'] for r in rows}),
            'quoted_tokens_without_selected_qualification':sorted(quoted-{r['token'] for r in rows}),
            'current_stage_rows':len(current_rows),
            'historical_quote_tokens_in_current_stage':len(quoted&set(stage_map)),
            'exact_pump_matches_in_current_stage':sum(r['current_stage_exact_pump_match'] for r in rows),
            'native_registry_shape':shape(canonical),
            'cross_window_quote_evidence_only':True,'native_executor_compatible':False,
            'native_hydration_certified':False,'signed_simulation_certified':False,
            'net_profitability_certified':False,'production_registry_modified':False,
            'execution_authority':False,'signing':False,'broadcast':False}
    return shadow,report

def run():
    protected=(SCANNER,Q521,Q523,REGISTRY)
    digests={str(p):sha(p) for p in protected if p.is_file()}
    if len(digests)!=len(protected): raise Hold('PROTECTED_INPUT_MISSING')
    link,observed,canonical=read(Q523),read(Q521),read(REGISTRY)
    if link.get('status') not in ('HOLD_NO_QUOTED_PAIRS_IN_EXECUTOR_REGISTRY','PASS_QUOTED_INVENTORY_LINKED'):
        raise Hold('ORACLE523_LINEAGE_REQUIRED')
    if (link.get('oracle_521_sha256')!=sha(Q521) or link.get('registry_sha256')!=sha(REGISTRY)
            or link.get('scanner_sha256')!=sha(SCANNER)):
        raise Hold('521_523_OR_PRODUCTION_HASH_CHANGED')
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle_509_exact_pair_qualification as q509,
        oracle_510_warm_pair_preflight as q510)
    qualified,count=q510.selected(q509.load(q510.CHECKS),28)
    stage=read(STAGE) if STAGE.is_file() else None
    stage_hash=sha(STAGE) if STAGE.is_file() else None
    shadow,report=join(observed,qualified,canonical,stage)
    if any(sha(Path(p))!=h for p,h in digests.items()): raise Hold('PROTECTED_SOURCE_CHANGED')
    if stage_hash and sha(STAGE)!=stage_hash: raise Hold('STAGE_CHANGED_DURING_JOIN')
    report.update({'qualified_selected':len(qualified),'qualified_registry_reported':count,
                   'current_stage_hash':stage_hash,'historical_stage_count_from_523':link.get('staged_pairs'),
                   'historical_stage_not_assumed_current':True,'native_registry_hash':sha(REGISTRY),
                   'candidate_shadow_path':str(SHADOW)})
    write(SHADOW,shadow)
    report['candidate_shadow_sha256']=sha(SHADOW)
    write(REPORT,report)
    print('[ORACLE524_FINAL]',json.dumps({k:v for k,v in report.items() if k not in ('native_registry_shape','quoted_tokens_without_selected_qualification')},sort_keys=True),flush=True)
    print('[ORACLE524_NATIVE_SCHEMA]',json.dumps(report['native_registry_shape'],sort_keys=True),flush=True)
    print('[ORACLE524_UNMATCHED_QUOTED]',json.dumps(report['quoted_tokens_without_selected_qualification']),flush=True)
    print('[ORACLE524_SHADOW]',str(SHADOW),flush=True)
    return 0 if report['status'].startswith('PASS_') else 2

def tests():
    a,b,c,p,m,n='A'*32,'B'*32,'C'*32,'P'*32,'M'*32,'N'*32
    obs={'status':'PASS_LIVE_QUOTE_COVERAGE_MEASURED','visible_pairs':2,'matched_quoted_pairs':2,
         'pair_results':[{'token':a,'result':'MATCHED_QUOTE_OBSERVED'},
                         {'token':b,'result':'MATCHED_QUOTE_OBSERVED'}]}
    qualified=[{'token':a,'pump_pool':p,'meteora_pool':m}]
    native={'revision':REVISION,'rows':[{'pair_key':c+'|'+n,'token':c}]}
    # Stage changed from two historical rows to one newer, different token.
    shadow,r=join(obs,qualified,native,{'rows':[{'token':c,'pump_pool':p}]})
    assert r['current_stage_rows']==1 and r['historical_521_visible']==2
    assert r['qualified_quote_pair_keys']==1 and r['exact_pump_matches_in_current_stage']==0
    assert r['quoted_tokens_without_selected_qualification']==[b]
    assert shadow['rows'][0]['pair_key']==a+'|'+m
    assert not shadow['native_executor_compatible'] and not r['broadcast']
    shadow,r=join(obs,qualified,native,{'rows':[{'token':a,'pump_pool':p}]})
    assert r['exact_pump_matches_in_current_stage']==1
    try:
        join({**obs,'matched_quoted_pairs':3},qualified,native)
        raise AssertionError('BAD_COUNTER_ACCEPTED')
    except Hold: pass
    try:
        join(obs,[{'token':a,'pump_pool':p,'meteora_pool':m},
                  {'token':a,'pump_pool':n,'meteora_pool':m}],native)
        raise AssertionError('AMBIGUOUS_POOL_ACCEPTED')
    except Hold: pass
    print('[PASS] ORACLE524_V3 changed_stage_accepted lineage_preserved exact_pool_join no_execution',flush=True)

def install():
    if not SCANNER.is_file(): raise Hold('FROZEN_SCANNER_MISSING')
    src=Path(__file__).read_text(encoding='utf-8'); ast.parse(src)
    frozen=sha(SCANNER); TARGET.parent.mkdir(parents=True,exist_ok=True)
    t=TARGET.with_name(TARGET.name+'.'+str(os.getpid())+'.tmp')
    try: t.write_text(src,encoding='utf-8'); os.replace(t,TARGET)
    finally: t.unlink(missing_ok=True)
    if sha(SCANNER)!=frozen: raise Hold('SCANNER_CHANGED')
    print('[PASS] ORACLE524_V3_FULL_REPLACEMENT frozen_scanner canonical_registry_unchanged',flush=True)

def main():
    ap=argparse.ArgumentParser(); group=ap.add_mutually_exclusive_group(required=True)
    for cmd in ('install','test','run'): group.add_argument('--'+cmd,action='store_true')
    args=ap.parse_args()
    try:
        if args.install: install(); return 0
        if args.test: tests(); return 0
        return run()
    except Exception as exc:
        print('[ORACLE524_HOLD]',str(exc) if isinstance(exc,Hold) else type(exc).__name__,flush=True)
        return 2
if __name__=='__main__': raise SystemExit(main())