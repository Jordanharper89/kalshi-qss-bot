from pathlib import Path
import json

root=Path.cwd()
p=root/"runtime"/"predictive_data"/"opd_035_prospective_edge_evaluation_registry.json"

rows=json.loads(p.read_text(encoding="utf-8"))

print("="*92)
print("ALL FROZEN PROSPECTIVE CANDIDATES")
print("="*92)

for i,x in enumerate(rows,1):
    print(f"CANDIDATE_{i}")
    for k in (
        "family_id","target","direction","horizon_seconds",
        "baseline_n","trigger_n","trigger_tickers",
        "prospective_lift","q_value",
        "net_expected_after_hurdle",
        "favorable_excursion","reward_risk_proxy",
        "sign_preserved","certified_edge"
    ):
        print(k.upper(),"=",x.get(k))

    checks=x.get("prospective_checks",{})
    print("PASSED_CHECKS=",sum(bool(v) for v in checks.values()),"/",len(checks))
    print("FAILED_CHECKS=",",".join(k for k,v in checks.items() if not v) or "NONE")
    print("-"*92)

print("EXECUTION_AUTHORITY=FALSE")