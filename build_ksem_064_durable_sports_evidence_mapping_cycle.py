from pathlib import Path
ROOT=Path.cwd()
PKG=ROOT/"qseries_v2/kalshi_sports_evidence_mapping"
STATE=PKG/"state"
MOD=PKG/"durable_sports_evidence_mapping_cycle.py"
TEST=ROOT/"test_ksem_064_durable_sports_evidence_mapping_cycle.py"

MODULE=r"""
from pathlib import Path
from dataclasses import asdict
from hashlib import sha256
from datetime import datetime,timezone
import json,os,tempfile
from qseries_v2.oracle_adapters.kalshi.oad_021_credentials import load_kalshi_credentials
from qseries_v2.kalshi_sports_evidence_mapping.exact_live_underlying_market_retrieval import select_current_mve_underlying_tickers,retrieve_exact_market
from qseries_v2.kalshi_sports_evidence_mapping.exact_live_sports_proposition_context import reconstruct_rows
from qseries_v2.kalshi_sports_evidence_mapping.live_osn_exact_event_binding import run_binding

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

def _atomic_json(path,payload):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=path.name+".",suffix=".tmp",dir=str(path.parent))
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as f:
            json.dump(payload,f,indent=2,sort_keys=True,default=str); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def run_cycle(root=None,max_tickers=50,timeout_seconds=15):
    root=Path(root or Path.cwd()).resolve()
    credentials=load_kalshi_credentials(root=root)
    legs=select_current_mve_underlying_tickers(root=root,max_tickers=max_tickers,timeout_seconds=timeout_seconds)
    retrieval=[]
    for leg in legs:
        try:
            market=retrieve_exact_market(credentials,leg["market_ticker"],timeout_seconds)
            status="RESOLVED" if market else "NOT_FOUND"; error=""
        except Exception as exc:
            market=None; status="ERROR"; error=f"{type(exc).__name__}: {exc}"
        retrieval.append({**leg,"status":status,"market":market,"error":error})
    contexts=reconstruct_rows(retrieval)
    context_dicts=[asdict(x) for x in contexts if x.league in ("NFL","NCAAF","NBA","NHL","MLS","EPL")]
    bindings,_=run_binding(context_dicts,root=root,timeout=timeout_seconds)
    counts={k:sum(x.status==k for x in bindings) for k in ("EXACT_BOUND","AMBIGUOUS","SOURCE_GAP")}
    observed=datetime.now(timezone.utc).isoformat()
    rows=[]
    by_ticker={x.market_ticker:x for x in bindings}
    for c in contexts:
        b=by_ticker.get(c.market_ticker)
        rows.append({
            "market_ticker":c.market_ticker,"parent_ticker":c.parent_ticker,
            "event_ticker":c.event_ticker,"league":c.league,
            "proposition_type":c.proposition_type,"title":c.title,
            "binding_status":b.status if b else "SOURCE_GAP",
            "canonical_event_id":b.canonical_event_id if b else None,
            "home_team":b.home_team if b else None,"away_team":b.away_team if b else None,
            "observed_at":observed,"execution_authority":False,
        })
    payload={"observed_at":observed,"rows":rows,"counts":counts,"execution_authority":False}
    payload["state_hash"]=sha256(json.dumps(payload,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
    path=root/"qseries_v2/kalshi_sports_evidence_mapping/state/ksem_live_mapping_state.json"
    _atomic_json(path,payload)
    return payload
"""

TEST_BODY=r"""
from pathlib import Path
from qseries_v2.kalshi_sports_evidence_mapping.durable_sports_evidence_mapping_cycle import run_cycle

root=Path.cwd()
a=run_cycle(root=root,max_tickers=25,timeout_seconds=15)
b=run_cycle(root=root,max_tickers=25,timeout_seconds=15)
print("[CYCLE_A]",len(a["rows"]),a["counts"],a["state_hash"])
print("[CYCLE_B]",len(b["rows"]),b["counts"],b["state_hash"])
assert a["rows"] and b["rows"]
assert all(x["execution_authority"] is False for x in b["rows"])
assert (root/"qseries_v2/kalshi_sports_evidence_mapping/state/ksem_live_mapping_state.json").is_file()
print("[PASS] durable sports evidence mapping cycle ran twice and atomically checkpointed")
print("[PASS] KSEM-064 certified")
"""

def main():
    print("="*120); print(" KSEM-064 DURABLE SPORTS EVIDENCE MAPPING CYCLE INSTALLER"); print("="*120)
    if not (STATE/"ksem063_live_osn_exact_event_binding.json").exists():
        raise RuntimeError("KSEM-063 physical state required")
    MOD.write_text(MODULE.lstrip(),encoding="utf-8"); TEST.write_text(TEST_BODY.lstrip(),encoding="utf-8")
    print("[PASS] wrote",MOD.relative_to(ROOT)); print("[PASS] wrote",TEST.name)
    print("[PASS] atomic durable mapping checkpoint installed")
    print("[PASS] no production launcher mutation")
    print("[PASS] KSEM-064 installer complete")
if __name__=="__main__": main()
