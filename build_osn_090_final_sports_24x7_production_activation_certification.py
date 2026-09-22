
from pathlib import Path
import json,hashlib
ROOT=Path.cwd()
TARGET=ROOT/"qseries_v2/oracle_source_network/certification/final_sports_24x7_activation.py"
STATE=ROOT/"qseries_v2/oracle_source_network/state/osn090_final_sports_24x7_activation.json"
TEST=ROOT/"test_osn_090_final_sports_24x7_production_activation_certification.py"
MODULE="""from pathlib import Path
import json,hashlib
def certify(root=None):
    base=Path(root or Path.cwd()).resolve()
    s86=json.loads((base/'qseries_v2/oracle_source_network/state/osn086_production_launcher_contract.json').read_text())
    s88=json.loads((base/'qseries_v2/oracle_source_network/state/osn088_extension_supervisor.json').read_text())
    s89=json.loads((base/'qseries_v2/oracle_source_network/state/osn089_bounded_dual_runtime_physical_gate.json').read_text())
    unchanged=hashlib.sha256((base/s86['launcher_path']).read_bytes()).hexdigest()==s86['launcher_sha256']
    ready=bool(unchanged and (base/s88['launcher']).exists() and s89.get('base_launcher_boot_alive') and s89.get('sports_cycle_completed'))
    return {'admitted':['NFL','NCAAF','NBA','NHL','MLS','EPL'],'held':['NCAAB','MLB_CANONICAL_EVENT_EXTRACTION_CERT_REQUIRED'],'blocked':['UCL'],'base_launcher_unchanged':unchanged,'production_extension_launcher':s88['launcher'],'bounded_dual_runtime_certified':bool(s89.get('base_launcher_boot_alive') and s89.get('sports_cycle_completed')),'activation_ready':ready,'terminal_dependency':'NONE','execution_authority':False}
"""
def main():
    print("="*120); print(" OSN-090 FINAL SPORTS 24x7 PRODUCTION ACTIVATION CERTIFICATION"); print("="*120)
    for rel in (
        "qseries_v2/oracle_source_network/state/osn085_durable_runtime_cycle.json",
        "qseries_v2/oracle_source_network/state/osn086_production_launcher_contract.json",
        "qseries_v2/oracle_source_network/state/osn087_sports_supervised_child.json",
        "qseries_v2/oracle_source_network/state/osn088_extension_supervisor.json",
        "qseries_v2/oracle_source_network/state/osn089_bounded_dual_runtime_physical_gate.json"):
        p=ROOT/rel
        if not p.exists(): raise SystemExit("[FAIL] missing dependency: "+rel)
        print("[PASS] dependency verified:",rel)
    TARGET.parent.mkdir(parents=True,exist_ok=True); TARGET.write_text(MODULE,encoding="utf-8"); compile(MODULE,str(TARGET),"exec")
    TEST.write_text("""from pathlib import Path
import json
from qseries_v2.oracle_source_network.certification.final_sports_24x7_activation import certify
r=certify(Path.cwd()); print('[FINAL]',r)
assert r['activation_ready'] is True
assert r['base_launcher_unchanged'] is True
assert r['bounded_dual_runtime_certified'] is True
assert r['execution_authority'] is False
p=Path.cwd()/'qseries_v2/oracle_source_network/state/osn090_final_sports_24x7_activation.json'
p.write_text(json.dumps(r,indent=2),encoding='utf-8')
print('[STATE]',p)
print('[PASS] sports 24x7 production activation path certified')
print('[PASS] use run_oracle_live_WITH_OSN_SPORTS.py for combined Oracle + sports runtime')
print('[PASS] execution_authority=FALSE')
""",encoding="utf-8")
    print("[WRITE]",TARGET.relative_to(ROOT)); print("[WRITE]",TEST.name); print("[PASS] execution_authority=FALSE")
if __name__=="__main__": main()
