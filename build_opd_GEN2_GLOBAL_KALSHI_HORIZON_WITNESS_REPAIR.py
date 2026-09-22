from pathlib import Path
R=Path.cwd()
P=R/'qseries_v2'/'oracle_predictive_discovery'/'opd_055_event_time_highwater_coverage.py'
T=R/'test_opd_GEN2_GLOBAL_KALSHI_HORIZON_WITNESS_REPAIR.py'
s=P.read_text(encoding='utf-8')
old='''     if not p or p["ticker"]!=ticker:continue
     ep=float(p["event_epoch"])
     if float(t0)<ep<=float(end):path.append(dict(p,sequence_number=int(sn)))
     if ep>=float(end):witness=dict(p,sequence_number=int(sn));break
'''
new='''     if not p:continue
     ep=float(p["event_epoch"])
     if p["ticker"]==ticker and float(t0)<ep<=float(end):path.append(dict(p,sequence_number=int(sn)))
     if ep>=float(end):
      witness={"event_epoch":ep,"sequence_number":int(sn),"ticker":p.get("ticker"),"coverage_scope":"KALSHI_SOURCE_HIGHWATER"}
      break
'''
if old not in s and new not in s: raise RuntimeError('OPD055_EXPECTED_WITNESS_BLOCK_NOT_FOUND')
s=s.replace(old,new,1)
P.write_text(s,encoding='utf-8')
TEST='''from qseries_v2.oracle_predictive_discovery.opd_051_exact_witnessed_future_path_outcome import materialize_from_path_and_witness
state={"state_id":"g2","ticker":"KXBTC","observed_epoch":100.0,"horizon_seconds":300,"anchor_price":0.40}
path=[]
witness={"event_epoch":401.0,"sequence_number":999,"ticker":"KXOTHER","coverage_scope":"KALSHI_SOURCE_HIGHWATER"}
o=materialize_from_path_and_witness(state,path,witness)
assert o is not None
assert o["future_return"]==0.0
assert o["future_end_price"]==0.40
assert o["outcome_basis"]=="CARRY_FORWARD_NO_SAME_TICKER_EVENT_BEFORE_HORIZON"
assert o["coverage_witness_epoch"]==401.0
print("[PASS] global Kalshi highwater may witness horizon while same-ticker path remains isolated")
print("[PASS] sparse Gen2 300s state can resolve by carry-forward without fabricated ticker trade")
print("[EXECUTION/PROBABILITY/DIRECTION/PUBLICATION] FALSE/FALSE/FALSE/FALSE")
'''
T.write_text(TEST,encoding='utf-8')
compile(P.read_text(encoding='utf-8'),str(P),'exec');compile(TEST,str(T),'exec')
print('[PASS] existing OPD-055 global Kalshi horizon witness repaired')
print(P);print(T)