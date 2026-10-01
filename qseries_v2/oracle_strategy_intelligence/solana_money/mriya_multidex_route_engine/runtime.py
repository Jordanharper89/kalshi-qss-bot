from pathlib import Path
from .engine import build
def main():
    print("[QSB-041] MRIYA-STYLE 2-LEG + 3-LEG MULTI-DEX ROUTE ENGINE",flush=True)
    print("[DEX] PumpSwap | Meteora DLMM | Meteora DAMM V2 | Raydium CLMM | Raydium CPMM | Orca",flush=True)
    print("[SEARCH] anchor cycles in WSOL / USDC / USDT across distinct venues",flush=True)
    print("[TRUTH] observed certified trade economics only; exact route re-quote + atomic simulation still required",flush=True)
    print("[MODE] READ_ONLY=True execution_authority=FALSE",flush=True)
    d=build(Path.cwd())
    if d["routes"]:
        r=d["routes"][0]
        print("[TOP_ROUTE] legs=%d gross_bps=%+.2f venues=%s slot_spread=%d"%(
          r["legs"],r["gross_bps"]," -> ".join(r["venues"]),r["slot_spread"]),flush=True)
        print("[NEXT] exact route re-quote and atomic simulation",flush=True)
    else:
        print("[NO_ROUTE] no fresh >20 bps 2-leg/3-leg cycle in current certified economic window",flush=True)
if __name__=="__main__":main()
