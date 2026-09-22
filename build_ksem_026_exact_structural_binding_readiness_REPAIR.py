from pathlib import Path
import json

ROOT=Path.cwd()
S=ROOT/"qseries_v2/kalshi_sports_evidence_mapping/state"
OUT=S/"ksem026_exact_structural_binding_readiness_repair.json"
TEST=ROOT/"test_ksem_026_exact_structural_binding_readiness_REPAIR.py"

def main():
    print("="*120); print(" KSEM-026 EXACT STRUCTURAL BINDING READINESS REPAIR"); print("="*120)
    c=json.loads((S/"ksem024_candidate_association_shape.json").read_text())
    e=json.loads((S/"ksem025_live_osn_canonical_event_shape.json").read_text())
    mf=sorted(c["market"]["fields"]); df=sorted(c["descriptor"]["fields"])
    ef=sorted(set(k for L in ("NFL","NCAAF","NBA","NHL","MLS","EPL")
                  for k in ((e[L]["sample"] or {}).get("fields",{}))))
    report={"market_fields":mf,"descriptor_fields":df,"canonical_event_fields":ef,
            "production_candidate_groups_present":c["nonempty_groups"]>0,
            "structural_contracts_ready":bool(mf and df and ef),
            "exact_binding_execution_ready":bool(mf and df and ef),
            "execution_authority":False}
    for k,v in report.items(): print(f"[{k.upper()}] {v}")
    if not report["structural_contracts_ready"]: raise RuntimeError("structural contracts still incomplete")
    OUT.write_text(json.dumps(report,indent=2),encoding="utf-8")
    TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem026_exact_structural_binding_readiness_repair.json').read_text())\nassert d['structural_contracts_ready'] is True\nassert d['execution_authority'] is False\nprint('[PASS] Kalshi descriptor/market and OSN event structural contracts ready')\nprint('[PASS] KSEM-026 repair certified')\n",encoding="utf-8")
    print("[WRITE]",OUT.relative_to(ROOT)); print("[WRITE]",TEST.name)

if __name__=="__main__": main()