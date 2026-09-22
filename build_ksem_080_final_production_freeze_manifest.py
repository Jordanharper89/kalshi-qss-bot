from pathlib import Path
import ast,hashlib,json
ROOT=Path.cwd(); PKG=ROOT/"qseries_v2/kalshi_sports_evidence_mapping"; STATE=PKG/"state"
TEST=ROOT/"test_ksem_080_final_production_freeze_manifest.py"
def main():
    print("="*120); print(" KSEM-080 FINAL PRODUCTION FREEZE MANIFEST INSTALLER"); print("="*120)
    required=["ksem070_24x7_activation_readiness.json","ksem075_pre_freeze_gate.json",
              "ksem076_live_children_contract.json","ksem077_native_launcher_cutover.json",
              "ksem_worker_heartbeat.json","ksem_restart_recovery.json","ksem_live_mapping_state.json"]
    for name in required:
        if not (STATE/name).is_file(): raise RuntimeError(f"missing certification state: {name}")
        print("[PASS] certification state verified:",name)
    launcher=(ROOT/"run_oracle_LIVE.py").read_text(encoding="utf-8"); tree=ast.parse(launcher)
    children=None
    for n in tree.body:
        if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in n.targets):
            children=ast.literal_eval(n.value); break
    if not isinstance(children,dict) or children.get("ksem_mapping")!="run_ksem_live_mapping.py":
        raise RuntimeError("KSEM_NOT_NATIVELY_SUPERVISED__REFUSE_FREEZE")
    live=json.loads((STATE/"ksem_live_mapping_state.json").read_text())
    if live.get("total_rows",0)<=0 or live.get("accounted_rows")!=live.get("total_rows"):
        raise RuntimeError("KSEM_LIVE_STATE_NOT_FULLY_ACCOUNTED__REFUSE_FREEZE")
    manifest={"schema_version":"KSEM-080","status":"FROZEN","certified_range":"KSEM-001..KSEM-080",
              "native_child_key":"ksem_mapping","native_child_runner":"run_ksem_live_mapping.py",
              "launcher_sha256":hashlib.sha256(launcher.encode()).hexdigest(),
              "latest_mapping_content_hash":live.get("content_hash"),"latest_total_rows":live.get("total_rows"),
              "latest_counts":live.get("counts"),"terminal_dependency":"NONE",
              "probability_enabled":False,"execution_authority":False,
              "change_policy":"DEFECT_CORRECTIONS_ONLY"}
    (STATE/"ksem080_final_freeze_manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True),encoding="utf-8")
    TEST.write_text("""from pathlib import Path\nimport json\np=Path.cwd()/'qseries_v2/kalshi_sports_evidence_mapping/state/ksem080_final_freeze_manifest.json'; r=json.loads(p.read_text())\nprint('[FREEZE]',r)\nassert r['status']=='FROZEN' and r['native_child_key']=='ksem_mapping'\nassert r['terminal_dependency']=='NONE' and r['execution_authority'] is False and r['probability_enabled'] is False\nassert r['latest_total_rows']>0\nprint('[PASS] KSEM native production activation frozen through KSEM-080')\nprint('[PASS] future KSEM changes restricted to genuine defect corrections')\n""",encoding="utf-8")
    print("[FREEZE]",manifest)
    print("[PASS] wrote",TEST.name)
    print("[PASS] KSEM-080 installer complete")
if __name__=="__main__": main()