from pathlib import Path
from .core import ensure_meteora_math
from .crosslisted import scan

def main():
    print("[QSB-038D] CROSS-LISTED LIVE ATOMIC ARB SCANNER",flush=True)
    print("[ORDER] live PumpSwap activity FIRST -> exact Pump identities -> Meteora intersection -> quote both directions",flush=True)
    print("[NO FISHING] does not scan random/high-TVL Meteora tokens",flush=True)
    print("[SIZE_GRID] 0.03,0.05,0.10,0.20,0.35,0.50,0.75,1.00 SOL",flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)
    dep=ensure_meteora_math();print("[PYTHON_QUOTE_MATH]",dep,flush=True)
    if not dep.get("ok"):return
    r=scan(Path.cwd())
    b=r.get("best")
    if b:
        print("[BEST] token=%s dir=%s pump_pool=%s meteora_pool=%s start=%.6f end=%.9f net=%+.9f bps=%+.2f fresh=%s PAPER_TRADE=%s"%(
          b["token"],b["direction"],b.get("pump_pool"),b["pool"],b["start_sol"],b["end_sol"],
          b["net_sol"],b["net_bps"],b["fresh"],"YES" if b["paper_trade"] else "NO"),flush=True)
    else:
        print("[BEST] NONE",flush=True)
    print("[SUMMARY] crosslisted=%d quotes=%d execution_authority=FALSE"%(
      len(r["crosslisted_pairs"]),len(r["quotes"])),flush=True)

if __name__=="__main__":main()
