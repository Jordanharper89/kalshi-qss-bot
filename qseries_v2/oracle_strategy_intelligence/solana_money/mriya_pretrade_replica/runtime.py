from __future__ import annotations
from pathlib import Path
from .core import load_report,learned_templates,reject_decimal_anomaly
from .providers import pretrade_quote_capability

def main():
    root=Path.cwd();report=load_report(root);templates=learned_templates(report)
    print("[QSB-036] MRIYA PRE-TRADE REPLICA GATE",flush=True)
    print("[SOURCE] QSB-035 clean realized route fingerprints only",flush=True)
    print("[FILTER] closed+contiguous, 0<gross_bps<=500; absurd decimal route excluded",flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)
    if not templates:
        print("[HOLD] NO_REPEATABLE_CLEAN_ROUTE_TEMPLATE",flush=True);return
    for i,t in enumerate(templates,1):
        print("[TEMPLATE %d] venues=%s path=%s wins=%d size=[%s,%s] avg_gross_bps=%.2f"%(
          i,t["venues"],t["mint_path"],t["wins"],t["observed_size_min"],t["observed_size_max"],
          t["observed_avg_gross_bps"]),flush=True)
        cap=pretrade_quote_capability(root,t)
        print("[QUOTE_CAPABILITY]",cap,flush=True)
        if cap["ready"]:
            print("[READY] exact fresh pre-trade quote path is bound",flush=True)
        else:
            print("[HOLD_EXACT_QUOTE] "+",".join(cap["missing"]),flush=True)
    print("[NEXT_BOUNDARY] bind official fresh pool-state quote math; do not substitute historical execution prices",flush=True)

if __name__=="__main__":main()
