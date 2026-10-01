from __future__ import annotations
import inspect, json
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money import qsb059_gav_reverse_atomic as q59
from qseries_v2.solana_live_execution import qarb_097_official_meteora_sdk_executor as q97

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False

def _interesting_functions(mod):
    rows=[]
    for name,obj in inspect.getmembers(mod, inspect.isfunction):
        try:
            src=inspect.getsource(obj)
        except Exception:
            src=""
        low=(name+"\n"+src).lower()
        if any(k in low for k in ("lookup","address table","alt","compile_v0","compile_signed","versioned")):
            rows.append({
                "name":name,
                "signature":str(inspect.signature(obj)),
                "mentions_alt":"alt" in low or "lookup" in low,
                "mentions_compile":"compile" in low,
                "mentions_send":"sendtransaction" in low,
                "source_head":"\n".join(src.splitlines()[:30]),
            })
    return rows

def run(root=None):
    root=Path(root or Path.cwd())
    q59_src=inspect.getsource(q59)
    q97_src=inspect.getsource(q97)

    out={
        "oracle_build":"ORACLE-030",
        "q59_has_compile_compact":callable(getattr(q59,"compile_compact",None)),
        "q59_has_recent_alt_lookup":callable(getattr(q59,"recent_mriya_alt_keys",None)),
        "q59_candidate_has_wrap_swap_close":"WRAP_SWAP_CLOSE" in q59_src,
        "q97_functions":_interesting_functions(q97),
        "q97_has_create_lookup_table":"createLookupTable" in q97_src or "create_lookup_table" in q97_src,
        "q97_mentions_existing_alt":"existing" in q97_src.lower() and "alt" in q97_src.lower(),
        "execution_authority":False,
        "paper_only":True,
        "real_money_moved":False,
    }

    p=root/"runtime_state/oracle/oracle_live_execution/oracle_030_existing_alt_reuse_seam_audit.json"
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8")

    print("[ORACLE-030] EXISTING ALT REUSE SEAM AUDIT")
    print("[Q59] compile_compact=%s recent_alt_lookup=%s wrap_swap_close=%s"%(
        out["q59_has_compile_compact"],
        out["q59_has_recent_alt_lookup"],
        out["q59_candidate_has_wrap_swap_close"],
    ))
    print("[Q97] existing_alt=%s create_lookup_table=%s candidates=%d"%(
        out["q97_mentions_existing_alt"],
        out["q97_has_create_lookup_table"],
        len(out["q97_functions"]),
    ))
    for row in out["q97_functions"]:
        print("[Q97_SEAM] name=%s sig=%s alt=%s compile=%s send=%s"%(
            row["name"],row["signature"],row["mentions_alt"],row["mentions_compile"],row["mentions_send"]
        ))
    print("[REPORT] %s"%p)
    print("[BROADCAST] disabled")
    return 0

if __name__=="__main__":
    raise SystemExit(run())
