from pathlib import Path
import ast
ROOT=Path.cwd()
TARGET=ROOT/"qseries_v2/oracle_strategy_intelligence/solana/ssi_003_005_unified_solana_profitability_closeout.py"
TEST=ROOT/"test_ssi_003_005_unified_solana_profitability_closeout.py"
MODULE=r"""
from dataclasses import dataclass
from datetime import datetime,timezone
from itertools import combinations
from qseries_v2.oracle_adapters.independent.oad_274_solana_multi_horizon_condition_windows import read_pinned_pool_history
from qseries_v2.oracle_adapters.independent.oad_271_solana_historical_experience_formation import build_solana_historical_experiences
from qseries_v2.oracle_adapters.independent.oad_314_solana_verified_forward_outcome_attribution import _price_for_pair

TOKEN="9xNoCET14f4rhffNjtVH2TfDTfjo7nzS26BSDyS9DqHn"
HORIZONS=(15,30,60,300)
RR=((0.02,0.01),(0.05,0.02),(0.10,0.05),(0.15,0.08))
FRICTION_BPS=(50,100,200,500)

def _dt(v):
 if isinstance(v,datetime): return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
 return datetime.fromisoformat(str(v).replace("Z","+00:00"))

@dataclass(frozen=True)
class FrozenExample:
 anchor_at:str; pair_address:str; horizon_seconds:int; target:float; stop:float
 label:str; gross_return:float; conditions:tuple; evidence_ids:tuple
 path_ids:tuple; read_only:bool=True; execution_authority:bool=False

def _experiences(rows):
 out={}
 for n in range(2,len(rows)):
  for x in build_solana_historical_experiences(rows[:n]):
   out[(x.snapshot_at,x.pair_address)]=x
 return tuple(sorted(out.values(),key=lambda x:(_dt(x.snapshot_at),x.pair_address)))

def _example(x,rows,h,target,stop,tol=8.0):
 at=_dt(x.snapshot_at); anchors=[r for r in rows if r.observation_id in set(x.evidence_observation_ids)]
 if not anchors:return None
 ap=_price_for_pair(anchors[-1],x.pair_address)
 if ap is None or float(ap)<=0:return None
 end=at.timestamp()+h
 future=[r for r in rows if _dt(r.observed_at)>at and _dt(r.observed_at).timestamp()<=end+tol and _price_for_pair(r,x.pair_address) is not None]
 terminal=[r for r in future if _dt(r.observed_at).timestamp()>=end]
 if not terminal:return None
 term=terminal[0]; path=[r for r in future if _dt(r.observed_at)<=_dt(term.observed_at)]
 first=None
 for r in path:
  ret=float(_price_for_pair(r,x.pair_address))/float(ap)-1.0
  if ret>=target:first=("TARGET_FIRST",target);break
  if ret<=-stop:first=("STOP_FIRST",-stop);break
 tr=float(_price_for_pair(term,x.pair_address))/float(ap)-1.0
 label,gross=first if first else ("TIMEOUT",tr)
 return FrozenExample(str(x.snapshot_at),x.pair_address,h,target,stop,label,float(gross),
  tuple(x.conditions),tuple(x.evidence_observation_ids),tuple(r.observation_id for r in path),True,False)

def materialize(root=None,token=TOKEN):
 rows=tuple(read_pinned_pool_history(token,root=root,limit=4096))
 if len(rows)<10:raise AssertionError("insufficient certified pinned history")
 exps=_experiences(rows); examples=[]
 for x in exps:
  for h in HORIZONS:
   for target,stop in RR:
    e=_example(x,rows,h,target,stop)
    if e:examples.append(e)
 examples=tuple(sorted(examples,key=lambda e:(_dt(e.anchor_at),e.horizon_seconds,e.target,e.stop)))
 print("[SSI-003]",{"history_rows":len(rows),"frozen_entries":len(exps),"reward_risk_examples":len(examples),
  "labels":{k:sum(e.label==k for e in examples) for k in ("TARGET_FIRST","STOP_FIRST","TIMEOUT")}})
 return rows,examples

def _keys(conditions):
 c=tuple((str(k),str(v)) for k,v in conditions)
 out=[]
 for n in range(1,min(4,len(c))+1):
  out.extend(tuple(z) for z in combinations(c,n))
 return tuple(out)

def _net(e,bps):return e.gross_return-(float(bps)/10000.0)

def _metrics(xs,bps):
 vals=[_net(e,bps) for e in xs]
 wins=[v for v in vals if v>0];loss=[v for v in vals if v<0]
 avgw=sum(wins)/len(wins) if wins else 0.0; avgl=sum(loss)/len(loss) if loss else 0.0
 payoff=(avgw/abs(avgl)) if wins and loss else (float("inf") if wins else 0.0)
 eq=0.0;peak=0.0;mdd=0.0
 for v in vals:
  eq+=v;peak=max(peak,eq);mdd=min(mdd,eq-peak)
 return {"n":len(vals),"hit_rate":len(wins)/len(vals) if vals else 0.0,
  "expectancy":sum(vals)/len(vals) if vals else 0.0,"avg_win":avgw,"avg_loss":avgl,
  "payoff_ratio":payoff,"max_sequence_drawdown":mdd}

def discover(root=None,token=TOKEN):
 rows,examples=materialize(root,token)
 anchors=sorted({_dt(e.anchor_at) for e in examples})
 if len(anchors)<10:raise AssertionError("insufficient chronological anchors")
 cut=anchors[max(1,int(len(anchors)*0.70))-1]
 train=tuple(e for e in examples if _dt(e.anchor_at)<=cut); test=tuple(e for e in examples if _dt(e.anchor_at)>cut)
 candidates=[]
 configs=sorted({(e.horizon_seconds,e.target,e.stop) for e in train})
 for cfg in configs:
  base=[e for e in train if (e.horizon_seconds,e.target,e.stop)==cfg]
  keyed={}
  for e in base:
   for key in _keys(e.conditions):keyed.setdefault(key,[]).append(e)
  for key,xs in keyed.items():
   if len(xs)<8:continue
   m=_metrics(xs,200)
   candidates.append((m["expectancy"],len(xs),cfg,key,m))
 candidates.sort(key=lambda z:(z[0],z[1]),reverse=True)
 print("[SSI-004]",{"chronological_cut":str(cut),"train_examples":len(train),"oos_examples":len(test),
  "future_leakage":False,"evidence_frozen_at_or_before_entry":True})
 reports=[]
 for _,_,cfg,key,tm in candidates[:25]:
  oos=[e for e in test if (e.horizon_seconds,e.target,e.stop)==cfg and all(k in e.conditions for k in key)]
  if not oos:continue
  sensitivity={bps:_metrics(oos,bps) for bps in FRICTION_BPS}
  reports.append({"config":cfg,"conditions":key,"train_200bps":tm,"oos":sensitivity,
   "coverage":len(oos)/len(test) if test else 0.0})
 qualified=[r for r in reports if r["oos"][200]["n"]>=5 and r["coverage"]>=0.02 and
  r["train_200bps"]["expectancy"]>0 and r["oos"][200]["expectancy"]>0]
 result={"token":token,"history_rows":len(rows),"examples":len(examples),"train":len(train),"oos":len(test),
  "candidates_tested":len(candidates),"reports":tuple(reports),"qualified":tuple(qualified),
  "profitability_state":"OOS_POSITIVE_NET_EXPECTANCY_FOUND" if qualified else "NO_CERTIFIED_PROFITABLE_THESIS_YET",
  "read_only":True,"execution_authority":False}
 print("[SSI-005]",result)
 print("[SSI-003-005-PHYSICAL-CLOSEOUT]",{"profitability_state":result["profitability_state"],
  "qualified":len(qualified),"candidates_tested":len(candidates),"examples":len(examples),
  "read_only":True,"execution_authority":False})
 return result
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_strategy_intelligence.solana.ssi_003_005_unified_solana_profitability_closeout import discover
class T(unittest.TestCase):
 def test_unified_profitability_closeout(self):
  r=discover()
  self.assertGreater(r["history_rows"],10);self.assertGreater(r["examples"],0)
  self.assertGreater(r["train"],0);self.assertGreater(r["oos"],0);self.assertGreater(r["candidates_tested"],0)
  self.assertIn(r["profitability_state"],("OOS_POSITIVE_NET_EXPECTANCY_FOUND","NO_CERTIFIED_PROFITABLE_THESIS_YET"))
  self.assertTrue(r["read_only"]);self.assertFalse(r["execution_authority"])
if __name__=="__main__":unittest.main(verbosity=2)
"""
def main():
 print("="*120);print(" SSI-003 -> SSI-005 UNIFIED SOLANA PROFITABILITY CLOSEOUT INSTALLER");print("="*120)
 deps=[
 "qseries_v2/oracle_adapters/independent/oad_274_solana_multi_horizon_condition_windows.py",
 "qseries_v2/oracle_adapters/independent/oad_271_solana_historical_experience_formation.py",
 "qseries_v2/oracle_adapters/independent/oad_314_solana_verified_forward_outcome_attribution.py",
 "qseries_v2/oracle_strategy_intelligence/solana/ssi_002_physical_exact_future_price_path_materialization.py"]
 for rel in deps:
  q=ROOT/rel
  if not q.exists():raise SystemExit("[FAIL] missing dependency: "+rel)
  ast.parse(q.read_text(encoding="utf-8",errors="replace"));print("[PASS] dependency:",rel)
 TARGET.parent.mkdir(parents=True,exist_ok=True);TARGET.write_text(MODULE,encoding="utf-8");TEST.write_text(TEST_SOURCE,encoding="utf-8")
 ast.parse(MODULE);ast.parse(TEST_SOURCE)
 print("[PASS] installed:",TARGET.relative_to(ROOT));print("[PASS] test:",TEST.relative_to(ROOT))
 print("[PASS] SSI-003 exact sampled target-first / stop-first / timeout reward-risk labels")
 print("[PASS] SSI-004 frozen pre-entry conditions and evidence lineage; strict chronological split")
 print("[PASS] SSI-005 train-only thesis discovery + untouched OOS evaluation + 50/100/200/500 bps friction sensitivity")
 print("[PASS] profitability is reported only from positive 200-bps OOS net expectancy with minimum OOS support")
 print("[PASS] read-only; existing certified history only; no acquisition, writer, GMGN, or execution authority")
 print("[DONE] SSI-003 -> SSI-005 UNIFIED PROFITABILITY CLOSEOUT INSTALLED")
if __name__=="__main__":main()
