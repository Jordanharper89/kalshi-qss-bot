import argparse
from pathlib import Path
from .engine import run

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--interval",type=float,default=1.0)
    ap.add_argument("--max-cycles",type=int,default=0)
    a=ap.parse_args()
    print("[QSB-039] MRIYA-STYLE MULTI-DEX HOTGRAPH HUNTER",flush=True)
    print("[DEX] PumpSwap | Meteora DLMM | Meteora DAMM V2 | Raydium CLMM | Raydium CPMM | Orca",flush=True)
    print("[ARCH] one shared live router -> local cross-venue graph -> only fresh spreads surfaced",flush=True)
    print("[NO-SPAM] no per-size HTTP quote loop in this hunter",flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)
    try:
        run(Path.cwd(),a.interval,a.max_cycles)
    except KeyboardInterrupt:
        print("[STOP] user interrupted",flush=True)

if __name__=="__main__":main()
