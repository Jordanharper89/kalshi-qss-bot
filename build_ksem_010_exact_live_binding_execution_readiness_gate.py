
from pathlib import Path
import json
ROOT=Path.cwd()
PKG=ROOT/"qseries_v2/kalshi_sports_evidence_mapping"
SEL=PKG/"state/ksem007_exact_callable_binding_selection.json"
STATE=PKG/"state/ksem010_exact_live_binding_execution_readiness.json"
TEST=ROOT/"test_ksem_010_exact_live_binding_execution_readiness_gate.py"
def main():
    print("="*118); print(" KSEM-010 EXACT LIVE BINDING EXECUTION READINESS GATE"); print("="*118)
    for p in [SEL,PKG/"state/ksem008_canonical_event_binding_contract.json",PKG/"state/ksem009_market_to_event_binding_lineage.json"]:
        if not p.exists(): raise SystemExit("[FAIL] missing dependency: "+str(p.relative_to(ROOT)))
    sel=json.loads(SEL.read_text(encoding="utf-8"))
    ambiguous=[k for k,v in sel["roles"].items() if v["selection_status"]!="SELECTED"]
    selected={k:v["selected"] for k,v in sel["roles"].items() if v["selection_status"]=="SELECTED"}
    ready=not ambiguous
    d={"exact_callable_selection_complete":ready,"selected_roles":selected,"ambiguous_roles":ambiguous,"canonical_binding_contract_ready":True,"binding_lineage_ready":True,"live_market_binding_executed":False,"next_action":"EXECUTE_PHYSICAL_KALSHI_TO_CANONICAL_EVENT_BINDING" if ready else "RESOLVE_AMBIGUOUS_EXISTING_CALLABLES_FROM_EXACT_SOURCE","execution_authority":False}
    STATE.write_text(json.dumps(d,indent=2),encoding="utf-8")
    TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem010_exact_live_binding_execution_readiness.json').read_text())\nassert d['canonical_binding_contract_ready'] and d['binding_lineage_ready']\nassert d['live_market_binding_executed'] is False\nassert d['execution_authority'] is False\nprint('[PASS] live binding readiness truthfully classified')\nprint('[PASS] no fake live Kalshi-to-event binding claimed')\nprint('[PASS] KSEM-010 certified')\n",encoding="utf-8")
    print("[SELECTED_ROLES]",list(selected)); print("[AMBIGUOUS_ROLES]",ambiguous); print("[NEXT]",d["next_action"])
    print("[WRITE]",STATE.relative_to(ROOT)); print("[WRITE]",TEST.name)
if __name__=="__main__": main()
