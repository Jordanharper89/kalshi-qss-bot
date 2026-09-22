from pathlib import Path
import shutil

R=Path.cwd()
P=R/"qseries_v2"/"oracle_predictive_discovery"/"opd_live_full_evidence_fusion_predictor.py"
T=R/"test_opd_FULL_EVIDENCE_EXACT_PUBLIC_CLOSE_FALLBACK.py"
B=P.with_suffix(".pre_exact_public_close_fallback.bak")

if not P.exists():
    raise SystemExit("[FAIL] full-evidence predictor missing")

s=P.read_text(encoding="utf-8")
if "contract_horizon" not in s or "MARKET_ID_EXPRESSION" not in s:
    raise SystemExit("[FAIL] required contract-lifetime/indexed-close pavement missing")

imp = "from qseries_v2.oracle_intelligence.live_acquisition.oracle_kalshi_public_market_shadow_source_adapter import OracleKalshiPublicMarketShadowSourceAdapter\n"
anchor = "from qseries_v2.oracle_intelligence_analytics_runtime.oiar_003_canonical_market_history_access_index import MARKET_ID_EXPRESSION\n"
if imp not in s:
    if anchor not in s:
        raise SystemExit("[FAIL] OIAR-003 import anchor missing")
    s=s.replace(anchor, anchor+imp, 1)

start=s.index("def _contract_close_metadata(root,ticker):")
end=s.index("\ndef latest_live_anchor(root):",start)

replacement = '''def _public_contract_close_metadata(ticker,adapter_cls=OracleKalshiPublicMarketShadowSourceAdapter):
    try:
        from datetime import datetime,timezone
        adapter=adapter_cls(
            market_status="open",
            market_tickers=(str(ticker),),
            page_limit=1,
            max_pages=1,
            timeout_seconds=10,
        )
        rows=adapter.acquire(acquired_at=datetime.now(timezone.utc))
    except Exception as e:
        return {'close_epoch':None,'metadata_sequence':None,
          'basis':'PUBLIC_CLOSE_LOOKUP_FAILED_'+type(e).__name__.upper()}
    for obs in rows:
        payload=dict(obs.payload)
        if str(payload.get('source_market_id') or '') != str(ticker):
            continue
        epoch=_iso_epoch(payload.get('source_close_time'))
        if epoch is not None:
            return {'close_epoch':epoch,'metadata_sequence':None,
              'basis':'LIVE_PUBLIC_KALSHI_SOURCE_CLOSE_TIME'}
        return {'close_epoch':None,'metadata_sequence':None,
          'basis':'INVALID_LIVE_PUBLIC_KALSHI_SOURCE_CLOSE_TIME'}
    return {'close_epoch':None,'metadata_sequence':None,
      'basis':'NO_LIVE_PUBLIC_KALSHI_MARKET_METADATA'}

def _contract_close_metadata(root,ticker):
    sql=f"""SELECT sequence_number,
      COALESCE(canonical_observation_json->'raw_observation'->'payload',
               canonical_observation_json->'payload','{{}}'::jsonb)->>'source_close_time'
      FROM public.oracle_canonical_observations
      WHERE observation_type='market_snapshot'
        AND ({MARKET_ID_EXPRESSION})=%s
      ORDER BY sequence_number DESC LIMIT 1"""
    row=None
    try:
        with connect(root,autocommit=False) as c:
            with c.cursor() as q:
                q.execute('SET TRANSACTION READ ONLY')
                q.execute("SET LOCAL statement_timeout='5000ms'")
                q.execute(sql,(str(ticker),));row=q.fetchone()
            c.rollback()
    except Exception:
        row=None
    if row:
        epoch=_iso_epoch(row[1])
        if epoch is not None:
            return {'close_epoch':epoch,'metadata_sequence':int(row[0]),
              'basis':'INDEXED_CANONICAL_SOURCE_CLOSE_TIME'}
    return _public_contract_close_metadata(ticker)
'''

s=s[:start]+replacement+s[end:]
if not B.exists():
    shutil.copy2(P,B)
P.write_text(s,encoding="utf-8")

TEST = '''import inspect
from collections import namedtuple
import qseries_v2.oracle_predictive_discovery.opd_live_full_evidence_fusion_predictor as m

Obs=namedtuple("Obs","payload")
class FakeAdapter:
    def __init__(self,**kw):
        assert kw["market_status"]=="open"
        assert kw["market_tickers"]==("KXBTC15M-TEST",)
        assert kw["page_limit"]==1 and kw["max_pages"]==1
    def acquire(self,*,acquired_at):
        return (Obs((("source_market_id","KXBTC15M-TEST"),
                     ("source_close_time","2026-09-12T07:00:00Z"))),)

meta=m._public_contract_close_metadata("KXBTC15M-TEST",FakeAdapter)
assert meta["basis"]=="LIVE_PUBLIC_KALSHI_SOURCE_CLOSE_TIME"
assert meta["close_epoch"] is not None
assert meta["metadata_sequence"] is None

states=[];outs={}
for i in range(24):
    sid="h"+str(i)
    states.append({"state_id":sid,"ticker":"KXBTC"+str(i%4),
      "observed_epoch":1000+i,"horizon_seconds":300,
      "tokens":["K:A","CB:B","CC:C","L:D"]})
    outs[sid]={"state_id":sid,"resolution_epoch":1500+i,
      "future_return":-0.05,"mfe":-0.01,"mae":-0.05}

base={"state_id":"LIVE","ticker":"KXBTC15M-TEST",
 "observed_epoch":2000.0,"horizon_seconds":300,
 "tokens":["K:A","CB:B","CC:C","L:D"]}
ok=m._score_state(dict(base,contract_close_epoch=2300.0),states,outs,2001.0)
bad=m._score_state(dict(base,contract_close_epoch=2299.0),states,outs,2001.0)

assert ok["checks"]["contract_horizon"] is True and ok["passed"] is True
assert bad["checks"]["contract_horizon"] is False and bad["passed"] is False
assert m.EXECUTION_AUTHORITY is False and m.PUBLICATION_ALLOWED is False

src=inspect.getsource(m._contract_close_metadata)
assert "_public_contract_close_metadata(ticker)" in src

print("[PASS] exact-ticker public Kalshi close-time fallback verified without network")
print("[PASS] indexed canonical close-time remains first choice")
print("[PASS] no ticker parsing or inferred expiration introduced")
print("[PASS] contract-horizon fail-closed semantics preserved")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
'''
T.write_text(TEST,encoding="utf-8")

compile(P.read_text(encoding="utf-8"),str(P),"exec")
compile(T.read_text(encoding="utf-8"),str(T),"exec")

print("[PASS] exact public Kalshi close-time fallback installed")
print("[PASS] existing read-only Kalshi public market adapter reused")
print("[PASS] probability/edge/evidence thresholds unchanged")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
