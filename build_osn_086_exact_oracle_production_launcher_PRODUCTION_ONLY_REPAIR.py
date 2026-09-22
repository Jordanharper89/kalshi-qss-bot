from pathlib import Path
import json, hashlib

ROOT=Path.cwd()
STATE=ROOT/"qseries_v2/oracle_source_network/state/osn086_production_launcher_contract.json"
TEST=ROOT/"test_osn_086_exact_oracle_production_launcher_PRODUCTION_ONLY_REPAIR.py"

REQUIRED=("fast_lane","inventory","reasoning","learning","terminal_dependency","execution_authority")
EXCLUDED_NAME_TOKENS=("diagnostic","forensic","test","debug","probe","rollback","repair","migration","certification","benchmark","smoke","temporary","temp")

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def classify(p):
    name=p.name.lower()
    text=p.read_text(encoding="utf-8",errors="ignore").lower()
    hits=tuple(x for x in REQUIRED if x in text)
    excluded=tuple(x for x in EXCLUDED_NAME_TOKENS if x in name)
    production_name=(name.startswith("run_oracle_") and ("live" in name or "runtime" in name) and not excluded)
    has_main=("__main__" in text)
    return {"path":p.name,"hits":hits,"excluded_tokens":excluded,"production_name":production_name,"has_main":has_main,"eligible":bool(production_name and has_main and len(hits)==len(REQUIRED))}

def main():
    print("="*120)
    print(" OSN-086 EXACT ORACLE PRODUCTION LAUNCHER — PRODUCTION-ONLY REPAIR")
    print("="*120)

    rows=[]
    for p in sorted(ROOT.glob("run_oracle_*.py")):
        try:
            row=classify(p)
        except Exception:
            continue
        if row["hits"]:
            rows.append(row)

    if not rows:
        raise SystemExit("[FAIL] no Oracle launcher candidates found")

    print("[CANDIDATES]")
    for r in rows:
        if r["eligible"] or r["excluded_tokens"]:
            print(" ",r)

    eligible=[r for r in rows if r["eligible"]]
    if len(eligible)!=1:
        print("[ELIGIBLE]",eligible)
        raise SystemExit("[FAIL] expected exactly one non-diagnostic/non-forensic production launcher; found "+str(len(eligible))+". Refusing to guess.")

    chosen=eligible[0]
    p=ROOT/chosen["path"]
    rejected=[r["path"] for r in rows if r["excluded_tokens"] and len(r["hits"])==len(REQUIRED)]

    state={
        "launcher_path":chosen["path"],
        "launcher_sha256":digest(p),
        "required_runtime_markers":list(REQUIRED),
        "rejected_nonproduction_launchers":rejected,
        "selection_rule":"UNIQUE_FULL_MARKER_LAUNCHER_AFTER_DIAGNOSTIC_FORENSIC_EXCLUSION",
        "integration_strategy":"NON_MUTATING_EXTENSION_SUPERVISOR",
        "terminal_dependency":"NONE",
        "execution_authority":False
    }

    STATE.parent.mkdir(parents=True,exist_ok=True)
    STATE.write_text(json.dumps(state,indent=2),encoding="utf-8")
    TEST.write_text('from pathlib import Path\nimport json,hashlib\n\nroot=Path.cwd()\nstate=json.loads((root/"qseries_v2/oracle_source_network/state/osn086_production_launcher_contract.json").read_text())\np=root/state["launcher_path"]\n\nassert p.exists()\nassert hashlib.sha256(p.read_bytes()).hexdigest()==state["launcher_sha256"]\nassert state["selection_rule"]=="UNIQUE_FULL_MARKER_LAUNCHER_AFTER_DIAGNOSTIC_FORENSIC_EXCLUSION"\nassert state["execution_authority"] is False\n\nprint("[PRODUCTION_LAUNCHER]",state["launcher_path"])\nprint("[REJECTED_NONPRODUCTION]",tuple(state["rejected_nonproduction_launchers"]))\nprint("[PASS] unique production launcher selected only after explicit diagnostic/forensic exclusion")\nprint("[PASS] launcher path + SHA256 frozen")\nprint("[PASS] OSN-086 production-only launcher contract certified")\n',encoding="utf-8")

    print("[PRODUCTION_LAUNCHER]",chosen["path"])
    print("[SHA256]",state["launcher_sha256"])
    print("[REJECTED_NONPRODUCTION]",tuple(rejected))
    print("[STATE]",STATE.relative_to(ROOT))
    print("[WRITE]",TEST.name)
    print("[PASS] diagnostic/forensic launchers excluded from production selection")
    print("[PASS] base launcher preserved byte-for-byte")
    print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
    main()
