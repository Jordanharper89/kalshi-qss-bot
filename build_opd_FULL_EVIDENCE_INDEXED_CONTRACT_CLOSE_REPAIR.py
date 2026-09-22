from pathlib import Path
import shutil

R=Path.cwd()
P=R/"qseries_v2"/"oracle_predictive_discovery"/"opd_live_full_evidence_fusion_predictor.py"
T=R/"test_opd_FULL_EVIDENCE_INDEXED_CONTRACT_CLOSE_REPAIR.py"
B=P.with_suffix(".pre_indexed_contract_close_repair.bak")

if not P.exists():
    raise SystemExit("[FAIL] full-evidence predictor missing")
s=P.read_text(encoding="utf-8")
if "contract_horizon" not in s:
    raise SystemExit("[FAIL] contract-lifetime gate is not installed")
if "MARKET_ID_EXPRESSION" not in s:
    s=s.replace(
        "from qseries_v2.oracle_predictive_discovery.opd_041_exact_live_token_materializer import materialize_exact_live_tokens\n",
        "from qseries_v2.oracle_predictive_discovery.opd_041_exact_live_token_materializer import materialize_exact_live_tokens\n"
        "from qseries_v2.oracle_intelligence_analytics_runtime.oiar_003_canonical_market_history_access_index import MARKET_ID_EXPRESSION\n",
        1,
    )

start=s.index("def _contract_close_metadata(root,ticker):")
end=s.index("\ndef latest_live_anchor(root):",start)
replacement = '''def _contract_close_metadata(root,ticker):
    sql=f"""SELECT sequence_number,
      COALESCE(canonical_observation_json->'raw_observation'->'payload',
               canonical_observation_json->'payload','{{}}'::jsonb)->>'source_close_time'
      FROM public.oracle_canonical_observations
      WHERE observation_type='market_snapshot'
        AND ({MARKET_ID_EXPRESSION})=%s
      ORDER BY sequence_number DESC LIMIT 1"""
    try:
        with connect(root,autocommit=False) as c:
            with c.cursor() as q:
                q.execute('SET TRANSACTION READ ONLY')
                q.execute("SET LOCAL statement_timeout='5000ms'")
                q.execute(sql,(str(ticker),));row=q.fetchone()
            c.rollback()
    except Exception as e:
        return {'close_epoch':None,'metadata_sequence':None,
          'basis':'INDEXED_CLOSE_LOOKUP_FAILED_'+type(e).__name__.upper()}
    if not row:return {'close_epoch':None,'metadata_sequence':None,'basis':'NO_INDEXED_CANONICAL_CLOSE_TIME'}
    epoch=_iso_epoch(row[1])
    return {'close_epoch':epoch,'metadata_sequence':int(row[0]),
      'basis':'INDEXED_CANONICAL_SOURCE_CLOSE_TIME' if epoch is not None else 'INVALID_INDEXED_CANONICAL_CLOSE_TIME'}
'''
s=s[:start]+replacement+s[end:]

if not B.exists(): shutil.copy2(P,B)
P.write_text(s,encoding="utf-8")

TEST = '''import inspect
import qseries_v2.oracle_predictive_discovery.opd_live_full_evidence_fusion_predictor as m

src=inspect.getsource(m._contract_close_metadata)
assert "MARKET_ID_EXPRESSION" in src
assert "observation_type='market_snapshot'" in src
assert "statement_timeout='5000ms'" in src
assert "except Exception as e" in src

states=[];outs={}
for i in range(24):
    sid='h'+str(i)
    states.append({'state_id':sid,'ticker':'KXBTC'+str(i%4),'observed_epoch':1000+i,
      'horizon_seconds':300,'tokens':['K:A','CB:B','CC:C','L:D']})
    outs[sid]={'state_id':sid,'resolution_epoch':1500+i,'future_return':-0.05,'mfe':-0.01,'mae':-0.05}

base={'state_id':'LIVE','ticker':'KXBTC15M-TEST','observed_epoch':2000.0,
  'horizon_seconds':300,'tokens':['K:A','CB:B','CC:C','L:D']}
ok=m._score_state(dict(base,contract_close_epoch=2300.0),states,outs,2001.0)
bad=m._score_state(dict(base,contract_close_epoch=2299.0),states,outs,2001.0)
missing=m._score_state(dict(base,contract_close_epoch=None),states,outs,2001.0)

assert ok['checks']['contract_horizon'] is True and ok['passed'] is True
assert bad['checks']['contract_horizon'] is False and bad['passed'] is False
assert missing['checks']['contract_horizon'] is False and missing['passed'] is False
assert m.EXECUTION_AUTHORITY is False and m.PUBLICATION_ALLOWED is False

print('[PASS] contract-close lookup now uses certified OIAR-003 exact market index expression')
print('[PASS] canonical-table JSON scan removed from lifetime metadata lookup')
print('[PASS] lookup timeout/error fails closed instead of crashing predictor')
print('[PASS] contract-horizon semantics preserved')
print('[EXECUTION/PUBLICATION] FALSE/FALSE')
'''
T.write_text(TEST,encoding="utf-8")
compile(P.read_text(encoding="utf-8"),str(P),"exec")
compile(T.read_text(encoding="utf-8"),str(T),"exec")

print("[PASS] indexed contract-close lookup repair installed")
print("[PASS] OIAR-003 exact market-snapshot index pavement reused")
print("[PASS] probability/edge/evidence thresholds unchanged")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
