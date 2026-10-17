from __future__ import annotations
import json,time,traceback
from datetime import datetime,timezone
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_012_live_event_normalization_and_intake import run as intake_run
import threading
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_083_persistent_event_driven_runtime import run_forever as run_suls_forever

ROOT=Path(__file__).resolve().parent
STATUS=ROOT/"runtime_state/solana_intelligence/osi_live_child_status.json"
STOP=ROOT/"runtime_state/solana_intelligence/STOP_OSI_LIVE"
INTERVAL=1.0
EXECUTION_AUTHORITY=False

def now_iso():
 return datetime.now(timezone.utc).isoformat()

def write_status(**kw):
 STATUS.parent.mkdir(parents=True,exist_ok=True)
 payload={"execution_authority":False,"read_only":True,"child":"run_osi_solana_intelligence_live.py",**kw}
 STATUS.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")

def one_cycle():
 result=intake_run(ROOT,now_iso())
 fresh=result.get("fresh_opportunities",[])
 return {"fresh_opportunities":len(fresh),"normalized_event_count":result.get("normalized_event_count",0)}

def main():
 # SULS-084B indentation-safe existing OSI child binding
 _suls_thread=threading.Thread(target=run_suls_forever,args=(ROOT,),name="OSI-SULS-EventDriven",daemon=True)
 _suls_thread.start()
 cycle=0
 while not STOP.exists():
  cycle+=1
  try:
   r=one_cycle()
   write_status(state="LIVE_CYCLE_COMPLETE",cycle_count=cycle,updated_at=now_iso(),error=None,**r)
  except Exception as exc:
   write_status(state="LIVE_CYCLE_ERROR",cycle_count=cycle,updated_at=now_iso(),error=str(exc),traceback=traceback.format_exc()[-4000:])
  time.sleep(INTERVAL)

if __name__=="__main__":
 main()
