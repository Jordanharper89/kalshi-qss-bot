
import json
from pathlib import Path
from qseries_v2.oracle_source_network.certification.sports_event_production_admission_gate_v3_REPAIR import admission
from qseries_v2.oracle_source_network.certification.ncaab_dynamic_activation_gate import activate
from qseries_v2.oracle_source_network.certification.mlb_unified_boundary_reconciliation import reconcile

REPORT=Path("qseries_v2/oracle_source_network/certification/osn_059_universal_sports_event_report.json")

def certify():
    if not REPORT.exists():
        raise RuntimeError("OSN-059 universal physical report missing")
    physical=json.loads(REPORT.read_text(encoding="utf-8"))
    base=admission()
    ncaab=activate()
    mlb=reconcile()

    admitted=list(base["admitted"])
    if ncaab.admitted and "NCAAB" not in admitted: admitted.append("NCAAB")
    # MLB reconciliation locates reusable pavement; it does NOT promote event extraction
    # without a current canonical MLB extraction certification.
    held=[]
    if not ncaab.admitted: held.append("NCAAB")
    if mlb.admitted_boundary: held.append("MLB_CANONICAL_EVENT_EXTRACTION_CERT_REQUIRED")
    else: held.append("MLB_RECONCILIATION_REQUIRED")

    physically_rerun=tuple(x["league"] for x in physical["physical_reruns"] if x.get("passed"))
    foundation_ok=bool(base["passed"] and physical.get("passed"))

    return {
        "passed":foundation_ok,
        "physically_rerun":physically_rerun,
        "nba_certified_admission":bool(physical.get("nba_certified_admission")),
        "admitted":tuple(admitted),
        "held":tuple(held),
        "blocked":("UCL",),
        "persistence_ready":foundation_ok,
        "execution_authority":False,
    }
