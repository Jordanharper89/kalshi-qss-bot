from __future__ import annotations
import json,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_070_persistent_active_profitable_set as q70
STATE=Path("runtime_state/qseries/qarb_clean_bot/qarb_072_lifecycle.json")
EXECUTION_AUTHORITY=False;PAPER_ONLY=True
RECHECK_SECONDS=600.0;RETIRE_MIN_SAMPLES=6;RETIRE_MAX_WIN_RATE=.34
def classify(x,now=None):
 now=time.time() if now is None else now;n=int(x.get("samples",0));w=int(x.get("wins",0));p=float(x.get("pnl_sol",0))
 wr=w/n if n else 0.;age=now-float(x.get("last_profitable_unix",now))
 if n>=RETIRE_MIN_SAMPLES and p<=0 and wr<=RETIRE_MAX_WIN_RATE:return "RETIRED"
 if x.get("status")=="ACTIVE" and age>RECHECK_SECONDS:return "RECHECK"
 if x.get("status")=="ACTIVE":return "ACTIVE"
 return "OBSERVE"
def run(root):
 root=Path(root);src=q70._load(root);rows={}
 for t,x in src.get("tokens",{}).items():
  y=dict(x);y["lifecycle"]=classify(x);rows[t]=y
 out={"tokens":rows,"counts":{k:sum(v["lifecycle"]==k for v in rows.values()) for k in ("ACTIVE","RECHECK","OBSERVE","RETIRED")},"execution_authority":False}
 p=root/STATE;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8");return out
def main():
 r=run(Path.cwd());print("[QARB-072] PROMOTION / AGING / RETIREMENT");print("[LIFECYCLE] "+json.dumps(r["counts"],sort_keys=True));print("[POLICY] age alone cannot retire a profitable token");print("[MODE] PAPER_ONLY=True execution_authority=FALSE")
if __name__=="__main__":main()
