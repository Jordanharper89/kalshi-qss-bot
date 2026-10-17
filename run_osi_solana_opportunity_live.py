from pathlib import Path
import time
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_027_lean_solana_opportunity_child_runtime import registered_sources,health
ROOT=Path(__file__).resolve().parent
STOP=ROOT/"runtime_state/solana_opportunities/STOP_OSI_SOLANA_OPPORTUNITY"
def main():
 cycle=0
 while not STOP.exists():
  cycle+=1
  try:
   r=registered_sources(ROOT)
   native=len(r.get("primary",{}).get("native_solana",[]));gmgn=len(r.get("primary",{}).get("gmgn",[]))
   health(ROOT,cycle,"LIVE_CYCLE_COMPLETE",None)
  except Exception as e:
   health(ROOT,cycle,"LIVE_CYCLE_ERROR",repr(e))
  time.sleep(1.0)
if __name__=="__main__":main()
