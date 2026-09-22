from pathlib import Path
from dataclasses import dataclass,asdict
import json

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

@dataclass(frozen=True)
class KSEMPreActivationReadiness:
    exact_live_retrieval:bool
    proposition_context:bool
    explicit_osn_binding_status:bool
    durable_cycle:bool
    exact_bound_count:int
    ambiguous_count:int
    source_gap_count:int
    production_launcher_change_allowed:bool
    ready_for_24x7_activation:bool
    execution_authority:bool=False

def evaluate(root=None):
    root=Path(root or Path.cwd()).resolve()
    state=root/"qseries_v2/kalshi_sports_evidence_mapping/state"
    required={
        "retrieval":state/"ksem061_exact_live_underlying_market_retrieval.json",
        "context":state/"ksem062_exact_live_sports_proposition_context.json",
        "binding":state/"ksem063_live_osn_exact_event_binding.json",
        "cycle":state/"ksem_live_mapping_state.json",
    }
    if not all(p.is_file() for p in required.values()):
        missing=[k for k,p in required.items() if not p.is_file()]
        raise RuntimeError("MISSING_KSEM_PHYSICAL_STATE:"+",".join(missing))
    r=json.loads(required["retrieval"].read_text(encoding="utf-8"))
    c=json.loads(required["context"].read_text(encoding="utf-8"))
    b=json.loads(required["binding"].read_text(encoding="utf-8"))
    d=json.loads(required["cycle"].read_text(encoding="utf-8"))
    counts=b.get("counts",{})
    exact=int(counts.get("EXACT_BOUND",0)); amb=int(counts.get("AMBIGUOUS",0)); gap=int(counts.get("SOURCE_GAP",0))
    retrieval_ok=int(r.get("counts",{}).get("RESOLVED",0))>0
    context_ok=int(c.get("supported",0))>0
    explicit=(exact+amb+gap)==len(b.get("rows",[])) and len(b.get("rows",[]))>0
    durable=bool(d.get("rows")) and bool(d.get("state_hash"))
    # Launcher mutation is allowed only after the physical mapping path has at least one real exact bind.
    ready=all((retrieval_ok,context_ok,explicit,durable,exact>0))
    return KSEMPreActivationReadiness(
        retrieval_ok,context_ok,explicit,durable,exact,amb,gap,
        ready,ready,False)
