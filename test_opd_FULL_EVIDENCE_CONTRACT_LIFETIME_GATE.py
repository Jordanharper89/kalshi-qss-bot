import qseries_v2.oracle_predictive_discovery.opd_live_full_evidence_fusion_predictor as m

assert m._iso_epoch('2026-09-12T01:15:00Z') is not None
states=[];outs={}
for i in range(24):
    sid='h'+str(i)
    states.append({'state_id':sid,'ticker':'KXBTC'+str(i%4),'observed_epoch':1000+i,'horizon_seconds':300,'tokens':['K:A','CB:B','CC:C','L:D']})
    outs[sid]={'state_id':sid,'resolution_epoch':1500+i,'future_return':-0.05,'mfe':-0.01,'mae':-0.05}
base={'state_id':'LIVE','ticker':'KXBTC15M-TEST','observed_epoch':2000.0,'horizon_seconds':300,'tokens':['K:A','CB:B','CC:C','L:D']}
eligible=dict(base,contract_close_epoch=2300.0)
z=m._score_state(eligible,states,outs,2001.0)
assert z['horizon_eligible'] is True and z['checks']['contract_horizon'] is True and z['passed'] is True and z['direction']=='DOWN'
expired=dict(base,contract_close_epoch=2299.0)
z2=m._score_state(expired,states,outs,2001.0)
assert z2['horizon_eligible'] is False and z2['checks']['contract_horizon'] is False and z2['passed'] is False
unknown=dict(base,contract_close_epoch=None)
z3=m._score_state(unknown,states,outs,2001.0)
assert z3['horizon_eligible'] is False and z3['checks']['contract_horizon'] is False and z3['passed'] is False
assert m.EXECUTION_AUTHORITY is False and m.PUBLICATION_ALLOWED is False
print('[PASS] exact close boundary allows horizon ending exactly at contract close')
print('[PASS] horizon extending one second past close is forced to ABSTAIN')
print('[PASS] missing close metadata fails closed instead of producing actionable prediction')
print('[EXECUTION/PUBLICATION] FALSE/FALSE')
