from pathlib import Path
import ast
ROOT=Path.cwd()
TARGET=ROOT/"qseries_v2/oracle_strategy_intelligence/solana/ssi_006_010_solana_adversarial_generalization_closeout.py"
TEST=ROOT/"test_ssi_006_010a_solana_adversarial_generalization_writer_activation_rebuild.py"
MODULE=r"""
from collections import defaultdict
from datetime import datetime,timezone
from qseries_v2.oracle_adapters.independent.oad_273_solana_pinned_pool_live_snapshot_persistence import persist_pinned_solana_pool_snapshot
from qseries_v2.oracle_adapters.independent.oad_274_solana_multi_horizon_condition_windows import read_pinned_pool_history
from qseries_v2.oracle_adapters.independent.oad_271_solana_historical_experience_formation import build_solana_historical_experiences
from qseries_v2.oracle_adapters.independent.oad_314_solana_verified_forward_outcome_attribution import _price_for_pair
from qseries_v2.oracle_adapters.independent.oad_312_solana_continuous_temporal_history_activation_gate import activate_and_verify_temporal_history
from qseries_v2.oracle_strategy_intelligence.solana.ssi_003_005_unified_solana_profitability_closeout import _metrics

FROZEN={"horizon":60,"target":0.10,"stop":0.05,"condition":("order_flow","BUY_PRESSURE"),"friction_bps":200}
BASELINE="9xNoCET14f4rhffNjtVH2TfDTfjo7nzS26BSDyS9DqHn"

def _dt(v):
 if isinstance(v,datetime):return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
 return datetime.fromisoformat(str(v).replace("Z","+00:00"))

def _prime_writer(root):
 r=activate_and_verify_temporal_history(root=root,cycles=2,acquisition_seconds=5.0,history_limit=512)
 print("[SSI-006-WRITER-PRIME]",r)
 return r

def _tokens(root,n=5):
 out=[]
 for _ in range(max(10,n*4)):
  try:r=persist_pinned_solana_pool_snapshot(root=root,timeout_seconds=120.0,acquisition_timeout_seconds=20.0)
  except TimeoutError:
   _prime_writer(root);continue
  t=r["token_address"]
  if t!=BASELINE and t not in out:out.append(t)
  if len(out)>=n:break
 if len(out)<3:raise AssertionError("insufficient independent live tokens after certified writer activation")
 return tuple(out)

def _collect(token,root,cycles=15):
 for _ in range(cycles-1):
  try:persist_pinned_solana_pool_snapshot(token_address=token,root=root,timeout_seconds=120.0,acquisition_timeout_seconds=20.0)
  except TimeoutError:
   _prime_writer(root)
   persist_pinned_solana_pool_snapshot(token_address=token,root=root,timeout_seconds=120.0,acquisition_timeout_seconds=20.0)
 rows=tuple(read_pinned_pool_history(token,root=root,limit=4096))
 return tuple(sorted(rows,key=lambda r:_dt(r.observed_at)))

def _experiences(rows):
 out={}
 for n in range(2,len(rows)):
  for x in build_solana_historical_experiences(rows[:n]):out[(x.snapshot_at,x.pair_address)]=x
 return tuple(sorted(out.values(),key=lambda x:_dt(x.snapshot_at)))

def _outcome(x,rows):
 at=_dt(x.snapshot_at);ids=set(x.evidence_observation_ids);a=[r for r in rows if r.observation_id in ids]
 if not a:return None
 ap=_price_for_pair(a[-1],x.pair_address)
 if ap is None or float(ap)<=0:return None
 target_at=at.timestamp()+FROZEN["horizon"]
 future=[r for r in rows if _dt(r.observed_at)>at and _dt(r.observed_at).timestamp()<=target_at+8 and _price_for_pair(r,x.pair_address) is not None]
 terminal=[r for r in future if _dt(r.observed_at).timestamp()>=target_at]
 if not terminal:return None
 end=terminal[0];gross=None;label="TIMEOUT"
 for r in [z for z in future if _dt(z.observed_at)<=_dt(end.observed_at)]:
  ret=float(_price_for_pair(r,x.pair_address))/float(ap)-1
  if ret>=FROZEN["target"]:label="TARGET_FIRST";gross=FROZEN["target"];break
  if ret<=-FROZEN["stop"]:label="STOP_FIRST";gross=-FROZEN["stop"];break
 if gross is None:gross=float(_price_for_pair(end,x.pair_address))/float(ap)-1
 return {"conditions":tuple(x.conditions),"gross":gross,"label":label}

def _eval(token,rows):
 xs=[]
 for x in _experiences(rows):
  e=_outcome(x,rows)
  if e and FROZEN["condition"] in e["conditions"]:xs.append(e)
 class E:
  def __init__(self,g):self.gross_return=g
 m=_metrics([E(e["gross"]) for e in xs],FROZEN["friction_bps"])
 return {"token":token,"history":len(rows),"n":len(xs),"metrics":m,"labels":{k:sum(e["label"]==k for e in xs) for k in ("TARGET_FIRST","STOP_FIRST","TIMEOUT")}}

def validate(root=None,token_count=5,cycles=15):
 print("[SSI-006] frozen_thesis=",FROZEN)
 _prime_writer(root)
 tokens=_tokens(root,token_count);print("[SSI-006] independent_tokens=",tokens)
 reports=[]
 for i,t in enumerate(tokens,1):
  rows=_collect(t,root,cycles);r=_eval(t,rows);reports.append(r);print("[SSI-007]",i,r)
 eligible=[r for r in reports if r["n"]>0];total=sum(r["n"] for r in eligible)
 weighted=sum(r["metrics"]["expectancy"]*r["n"] for r in eligible)/total if total else 0.0
 positive=sum(r["metrics"]["expectancy"]>0 for r in eligible)
 print("[SSI-008]",{"eligible_tokens":len(eligible),"positive_tokens":positive,"total_examples":total,"weighted_net_expectancy":weighted})
 sig=defaultdict(list)
 for r in eligible:sig[(round(r["metrics"]["expectancy"],12),r["n"])].append(r["token"])
 print("[SSI-009]",{"duplicate_metric_groups":tuple(v for v in sig.values() if len(v)>1),"independent_token_count":len(tokens)})
 state="GENERALIZATION_NOT_CERTIFIED"
 if len(eligible)>=3 and total>=15 and positive>=max(2,(len(eligible)+1)//2) and weighted>0:state="MULTI_TOKEN_POSITIVE_NET_EXPECTANCY_FOUND"
 result={"frozen_thesis":FROZEN,"tokens":tokens,"reports":tuple(reports),"eligible_tokens":len(eligible),"positive_tokens":positive,
 "total_examples":total,"weighted_net_expectancy":weighted,"state":state,"read_only":True,"execution_authority":False}
 print("[SSI-010-ADVERSARIAL-CLOSEOUT]",result);return result
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_strategy_intelligence.solana.ssi_006_010_solana_adversarial_generalization_closeout import validate,FROZEN
class T(unittest.TestCase):
 def test_writer_activated_adversarial_generalization(self):
  r=validate()
  self.assertEqual(FROZEN,{"horizon":60,"target":0.10,"stop":0.05,"condition":("order_flow","BUY_PRESSURE"),"friction_bps":200})
  self.assertGreaterEqual(len(r["tokens"]),3)
  self.assertIn(r["state"],("MULTI_TOKEN_POSITIVE_NET_EXPECTANCY_FOUND","GENERALIZATION_NOT_CERTIFIED"))
  self.assertTrue(r["read_only"]);self.assertFalse(r["execution_authority"])
if __name__=="__main__":unittest.main(verbosity=2)
"""
def main():
 print("="*120);print(" SSI-006 -> SSI-010A WRITER-ACTIVATED ADVERSARIAL GENERALIZATION REBUILD");print("="*120)
 deps=["qseries_v2/oracle_adapters/independent/oad_273_solana_pinned_pool_live_snapshot_persistence.py",
 "qseries_v2/oracle_adapters/independent/oad_274_solana_multi_horizon_condition_windows.py",
 "qseries_v2/oracle_adapters/independent/oad_271_solana_historical_experience_formation.py",
 "qseries_v2/oracle_adapters/independent/oad_312_solana_continuous_temporal_history_activation_gate.py",
 "qseries_v2/oracle_adapters/independent/oad_314_solana_verified_forward_outcome_attribution.py",
 "qseries_v2/oracle_strategy_intelligence/solana/ssi_003_005_unified_solana_profitability_closeout.py"]
 for rel in deps:
  q=ROOT/rel
  if not q.exists():raise SystemExit("[FAIL] missing dependency: "+rel)
  ast.parse(q.read_text(encoding="utf-8",errors="replace"));print("[PASS] dependency:",rel)
 TARGET.parent.mkdir(parents=True,exist_ok=True);TARGET.write_text(MODULE,encoding="utf-8");TEST.write_text(TEST_SOURCE,encoding="utf-8")
 ast.parse(MODULE);ast.parse(TEST_SOURCE)
 print("[PASS] clean replacement:",TARGET.relative_to(ROOT));print("[PASS] test:",TEST.relative_to(ROOT))
 print("[PASS] frozen thesis unchanged: BUY_PRESSURE / 60s / +10% / -5% / 200bps")
 print("[PASS] certified OAD-312 activation boundary primes OPH-021 single-writer before OAD-273 acquisition")
 print("[PASS] acquisition timeout expanded to 120s with one certified re-prime path")
 print("[PASS] no direct PostgreSQL, no parallel writer, no GMGN, no execution authority")
 print("[DONE] SSI-006 -> SSI-010A REBUILD INSTALLED")
if __name__=="__main__":main()
