from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_multidex_route_engine.engine import build
def main():
    print("[QSB-043] SAME-WINDOW MULTI-DEX HYDRATION + ROUTE ENGINE",flush=True)
    print("[FIX] non-Pump signatures are hydrated from the exact current 046B live window",flush=True)
    print("[SAFETY] only single-venue signatures with exactly one signer token outflow + one inflow are admitted",flush=True)
    print("[MODE] execution_authority=FALSE",flush=True)
    d=build(Path.cwd())
    if d["routes"]:
        r=d["routes"][0]
        print("[TOP_ROUTE] legs=%d gross_bps=%+.2f venues=%s"%(r["legs"],r["gross_bps"]," -> ".join(r["venues"])),flush=True)
    else:print("[NO_ROUTE]",flush=True)
if __name__=="__main__":main()
