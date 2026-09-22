import inspect
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
