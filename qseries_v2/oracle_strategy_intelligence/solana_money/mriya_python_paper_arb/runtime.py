from pathlib import Path
from .core import *
def main():
    root=Path.cwd()
    print("[QSB-038] PYTHON-ONLY LIVE MRIYA PAPER ARB",flush=True)
    print("[NO NODE] no node, no npm, no JS bridge",flush=True)
    print("[ROUTE] WSOL -> Meteora DLMM -> CbyTNf...pump -> PumpSwap -> WSOL",flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)
    dep=ensure_meteora_math();print("[PYTHON_QUOTE_MATH]",dep,flush=True)
    if not dep.get("ok"):return
    sizes=clean_sizes(root)
    if len(sizes)<2:
        print("[FAIL] clean QSB-035 Mriya sizes missing",flush=True);return
    probes=[sizes[0],sum(sizes)/len(sizes),sizes[-1]]
    yes=0
    for s in probes:
        try:
            x=one_quote(root,s)
            print("[LIVE] start=%.9f pool=%s meteora_token_out=%.6f pump_sol_out=%.9f slots=%d->%d spread=%d"%(
              s,x["pool"],x["meteora"]["out_ui"],x["pump"]["sol_out"],x["slot_start"],x["slot_end"],x["slot_spread"]),flush=True)
            print("[PAPER_PNL] start=%.9f end=%.9f cost=%.9f net=%+.9f net_bps=%+.2f fresh=%s PAPER_TRADE=%s"%(
              x["start_sol"],x["gross_end_sol"],x["tx_cost_sol"],x["net_sol"],x["net_bps"],x["fresh"],
              "YES" if x["paper_trade"] else "NO"),flush=True)
            yes+=int(x["paper_trade"])
        except Exception as e:
            print("[QUOTE_ERROR] size=%.9f %s: %s"%(s,type(e).__name__,e),flush=True)
    print("[SUMMARY] tested=%d positive_fresh_paper=%d execution_authority=FALSE"%(len(probes),yes),flush=True)
if __name__=="__main__":main()
