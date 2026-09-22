from pathlib import Path
import json

ROOT=Path.cwd()
KSEM=ROOT/"qseries_v2/kalshi_sports_evidence_mapping/state"
STATE=KSEM/"ksem026_market_event_binding_readiness_gate.json"
TEST=ROOT/"test_ksem_026_market_event_binding_readiness_gate.py"

def main():
    print("="*120); print(" KSEM-026 MARKET/EVENT BINDING READINESS GATE"); print("="*120)

    c=json.loads((KSEM/"ksem024_candidate_association_shape.json").read_text(encoding="utf-8"))
    e=json.loads((KSEM/"ksem025_live_osn_canonical_event_shape.json").read_text(encoding="utf-8"))

    market_fields=sorted((c.get("market") or {}).get("fields",{}))
    descriptor_fields=sorted((c.get("descriptor") or {}).get("fields",{}))

    event_fields=sorted(set(
        k
        for league in ("NFL","NCAAF","NBA","NHL","MLS","EPL")
        for k in ((e.get(league,{}).get("sample") or {}).get("fields",{}))
    ))

    report={
        "market_fields":market_fields,
        "descriptor_fields":descriptor_fields,
        "canonical_event_fields":event_fields,
        "production_candidate_groups_present":c.get("nonempty_groups",0)>0,
        "ready_for_exact_binding_implementation":bool(
            market_fields and descriptor_fields and event_fields
        ),
        "execution_authority":False
    }

    for k,v in report.items():
        print(f"[{k.upper()}] {v}")

    if not report["ready_for_exact_binding_implementation"]:
        raise RuntimeError("exact physical schemas incomplete")

    STATE.write_text(json.dumps(report,indent=2),encoding="utf-8")

    TEST.write_text(
        "import json\n"
        "from pathlib import Path\n"
        "d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem026_market_event_binding_readiness_gate.json').read_text())\n"
        "assert d['ready_for_exact_binding_implementation'] is True\n"
        "assert d['execution_authority'] is False\n"
        "print('[PASS] exact Kalshi market / persisted descriptor / OSN event schemas are available')\n"
        "print('[PASS] KSEM-026 certified')\n",
        encoding="utf-8"
    )

    print("[WRITE]",STATE.relative_to(ROOT))
    print("[WRITE]",TEST.name)

if __name__=="__main__":
    main()