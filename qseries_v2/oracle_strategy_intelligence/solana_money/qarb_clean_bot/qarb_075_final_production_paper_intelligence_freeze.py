from __future__ import annotations
import hashlib,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_070_persistent_active_profitable_set as q70
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_071_continuous_mriya_replenishment as q71
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_072_promotion_aging_retirement as q72
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_073_opportunity_lineage_learning as q73
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_074_restart_continuity_gap_recovery as q74
STATE=Path("runtime_state/qseries/qarb_clean_bot/qarb_075_final_freeze.json")
EXECUTION_AUTHORITY=False;PAPER_ONLY=True;REQ={2.0,5.0,15.0,30.0,60.0,90.0}
def _load(p):
 try:return json.loads(Path(p).read_text(encoding="utf-8"))
 except Exception:return {}
def _sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def certify(root,strict_files=True):
 root=Path(root);a=q70._load(root);r=_load(root/q71.STATE);l=_load(root/q72.STATE);x=_load(root/q73.STATE);c=_load(root/q74.STATE)
 active=sum(v.get("status")=="ACTIVE" for v in a.get("tokens",{}).values());coverage={float(v) for v in x.get("horizon_coverage",[])}
 checks={"q070_active_nonempty":active>0,"q071_active_replenishment":int(r.get("active_count",0))>0 and int(r.get("merged_count",0))>0,"q072_lifecycle_nonempty":int((l.get("counts") or {}).get("ACTIVE",0))+int((l.get("counts") or {}).get("RECHECK",0))>0,"q073_lineage_nonempty":int(x.get("token_count",0))>0 and bool(x.get("content_hash")) and bool(x.get("outcome_journal_exists")),"q073_full_horizon_coverage":REQ.issubset(coverage),"q074_continuity_ok":bool(c.get("continuity_ok")) and int(c.get("token_count",0))>0,"execution_authority_false":all(not getattr(m,"EXECUTION_AUTHORITY",True) for m in (q70,q71,q72,q73,q74))}
 hashes={}
 if strict_files:
  for m in (q70,q71,q72,q73,q74):hashes[Path(m.__file__).name]=_sha(m.__file__)
  for rel in (q70.STATE,q71.STATE,q72.STATE,q73.STATE,q73.JOURNAL,q74.STATE,q74.CHECKPOINT):
   p=root/rel;checks["exists:"+str(rel)]=p.is_file()
   if p.is_file():hashes[str(rel)]=_sha(p)
 ok=all(checks.values());out={"revision":"QARB_075","paper_intelligence_certified":ok,"frozen":ok,"checks":checks,"hashes":hashes,"execution_authority":False,"real_money_moved":False}
 p=root/STATE;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8");return out
def main():
 x=certify(Path.cwd());print("[QARB-075] FINAL PRODUCTION PAPER-INTELLIGENCE CERTIFICATION + FREEZE");print("[CERTIFIED] %s [FROZEN] %s"%(x["paper_intelligence_certified"],x["frozen"]));print("[CHECKS] "+json.dumps(x["checks"],sort_keys=True));print("[MODE] PAPER_ONLY=True execution_authority=FALSE real_money_moved=FALSE");raise SystemExit(0 if x["paper_intelligence_certified"] else 2)
if __name__=="__main__":main()
