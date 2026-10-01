from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_python_paper_arb.core import ensure_meteora_math
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_python_paper_arb.scanner import scan

def main():
    print("[QSB-038C] LIVE MARKET DEFICIENCY SCANNER",flush=True)
    print("[PURPOSE] scan current WSOL/Meteora DLMM pools against PumpSwap in BOTH directions",flush=True)
    print("[SIZES] 0.05,0.10,0.25,0.50,0.75,1.00,1.50 SOL",flush=True)
    print("[ADMISSION] fresh <=4 slots and >=15 bps net after 0.0001 SOL paper cost buffer",flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)
    dep=ensure_meteora_math();print("[PYTHON_QUOTE_MATH]",dep,flush=True)
    if not dep.get("ok"):return
    r=scan(Path.cwd())
    b=r.get("best")
    if b:
        print("[BEST] dir=%s token=%s pool=%s start=%.6f end=%.9f net=%+.9f bps=%+.2f fresh=%s PAPER_TRADE=%s"%(
          b["direction"],b["token"],b["pool"],b["start_sol"],b["end_sol"],b["net_sol"],b["net_bps"],b["fresh"],
          "YES" if b["paper_trade"] else "NO"),flush=True)
    print("[SUMMARY] pools=%d quotes=%d positive_fresh=%d execution_authority=FALSE"%(
      r["candidate_pools"],r["quotes"],r["paper_opportunities"]),flush=True)

if __name__=="__main__":main()
