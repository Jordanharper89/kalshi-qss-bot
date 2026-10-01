from __future__ import annotations
import argparse,asyncio
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_064b_dynamic_profit_machine as machine
EXECUTION_AUTHORITY=False;PAPER_ONLY=True
def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument("--seconds",type=float,default=None);a=ap.parse_args(argv)
    print("[QARB-064C] ORACLE ARBITRAGE PROFIT RUNTIME",flush=True)
    print("[MISSION] silent Mriya intelligence -> live arbitrage machine -> paper outcomes -> learning evidence",flush=True)
    print("[RUNTIME] unbounded unless --seconds is supplied",flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE real_money_moved=FALSE",flush=True)
    try:return asyncio.run(machine.serve(Path.cwd(),a.seconds))
    except KeyboardInterrupt:print("\n[STOP] operator Ctrl+C",flush=True)
if __name__=="__main__":main()
