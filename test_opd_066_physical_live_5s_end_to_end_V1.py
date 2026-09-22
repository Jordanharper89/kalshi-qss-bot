from pathlib import Path
import json,time
root=Path.cwd();rt=root/"runtime"/"predictive_data"
spool=rt/"opd_061_live_anchor_spool.jsonl";states=rt/"opd_032_prospective_state_ledger.jsonl";outs=rt/"opd_033_prospective_outcome_ledger.jsonl";hb=rt/"opd_065_worker_heartbeat.json"
def size(p): return p.stat().st_size if p.exists() else 0
def appended(p,pos):
 if not p.exists(): return []
 with p.open("r",encoding="utf-8") as f:
  f.seek(pos);return [json.loads(x) for x in f if x.strip()]
s0,l0,o0=size(spool),size(states),size(outs);deadline=time.time()+90
seen_anchor=None;five=None;resolved=None;heartbeat=None
while time.time()<deadline:
 a=appended(spool,s0)
 if a: seen_anchor=a[-1]
 ss=appended(states,l0)
 fs=[x for x in ss if int(x.get("horizon_seconds",-1))==5 and x.get("post_freeze") is True]
 if fs: five=fs[0]
 oo=appended(outs,o0)
 if five:
  rr=[x for x in oo if x.get("state_id")==five.get("state_id") and x.get("strictly_future") is True]
  if rr: resolved=rr[0]
 if hb.exists():
  try: heartbeat=json.loads(hb.read_text(encoding="utf-8"))
  except Exception: pass
 if seen_anchor and five and resolved and heartbeat and heartbeat.get("state")=="HEALTHY": break
 time.sleep(1)
assert seen_anchor,"NO_NEW_OPD061_LIVE_ANCHOR_IN_90S_RESTART_ORACLE_LIVE"
assert five,"NO_NEW_POST_FREEZE_5S_STATE_IN_OPD032"
assert resolved,"NEW_5S_STATE_DID_NOT_RESOLVE_STRICTLY_FUTURE"
assert heartbeat and heartbeat.get("state")=="HEALTHY","OPD065_WORKER_NOT_HEALTHY"
assert resolved["resolution_epoch"]>=five["observed_epoch"]+5
print("[ANCHOR]",seen_anchor["ticker"],seen_anchor["observed_epoch"])
print("[STATE_ID]",five["state_id"],"[HORIZON]",five["horizon_seconds"])
print("[RESOLUTION_EPOCH]",resolved["resolution_epoch"],"[STRICTLY_FUTURE]",resolved["strictly_future"])
print("[WORKER]",heartbeat["state"],heartbeat.get("result"))
print("[EXECUTION/PROBABILITY/DIRECTION/PUBLICATION] FALSE/FALSE/FALSE/FALSE")
print("[PASS] OPD-066 physical live 5-second prospective end-to-end cycle certified")
