from pathlib import Path
from .bridge import build
def main():
    print("[QSB-040] CERTIFIED ECONOMIC TAPE BRIDGE",flush=True)
    print("[FIX] router activity is materialized through certified venue economic producers before price logic",flush=True)
    print("[TARGET] PumpSwap | Meteora DLMM/DAMM V2 | Raydium CLMM/CPMM | Orca",flush=True)
    print("[MODE] READ_ONLY=True execution_authority=FALSE",flush=True)
    d=build(Path.cwd())
    if d["fresh_economic_rows"]:
        for x in d["fresh_economic_rows"][:12]:
            print("[ECON] venue=%s in=%s %.9g out=%s %.9g slot_age=%s pool=%s"%(
              x["venue"],x["input_mint"],x["input_amount"],x["output_mint"],x["output_amount"],
              x["slot_age"],x.get("pool")),flush=True)
    else:
        print("[HOLD] no fresh certified economic rows; do not fabricate spread signals",flush=True)
if __name__=="__main__":main()
