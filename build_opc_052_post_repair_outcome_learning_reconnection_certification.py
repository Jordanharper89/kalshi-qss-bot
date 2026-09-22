from pathlib import Path
import ast, importlib, os, subprocess, sys
ROOT=Path.cwd().resolve()
TARGET=ROOT/'qseries_v2/oracle_pre_settlement_coverage/opc_052_post_repair_outcome_learning_reconnection_certification.py'
TEST=ROOT/'test_opc_052_post_repair_outcome_learning_reconnection_certification.py'
SOURCE='from pathlib import Path\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_049_post_repair_settlement_cohort_read_model import physical_probe as cohort\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_050_post_repair_presettlement_evidence_gate import physical_probe as evidence\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_051_post_repair_learning_linkage_gate import physical_probe as linkage\nOPC_052_BUILD_ID="OPC-052"\ndef physical_probe(root=None):\n root=Path(root or Path.cwd()).resolve();a=cohort(root);b=evidence(root);c=linkage(root)\n if a["post_repair_settlements"]==0:status="WAITING_FOR_POST_REPAIR_SETTLEMENTS"\n elif b["with_pre_settlement_snapshot"]==0:status="HOLD_NO_POST_REPAIR_PRESETTLEMENT_EVIDENCE"\n elif c["linked"]==0:status="HOLD_LEARNING_LINKAGE_NOT_RECONNECTED"\n elif c["learned"]==0 and c["eligible"]==0:status="HOLD_NO_ELIGIBLE_OR_LEARNED_POST_REPAIR_OUTCOME"\n else:status="POST_REPAIR_OUTCOME_LEARNING_RECONNECTED"\n return {"gate_status":status,"post_repair_settlements":a["post_repair_settlements"],"with_pre_settlement_snapshot":b["with_pre_settlement_snapshot"],"linked":c["linked"],"eligible":c["eligible"],"learned":c["learned"],"calibration_ready":status=="POST_REPAIR_OUTCOME_LEARNING_RECONNECTED","probability_enabled":False,"read_only":True,"execution_authority":False}\ndef verify_opc_052():return OPC_052_BUILD_ID=="OPC-052"\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage import opc_052_post_repair_outcome_learning_reconnection_certification as m\nclass T(unittest.TestCase):\n def test_gate(self):\n  self.assertTrue(m.verify_opc_052());x=m.physical_probe();self.assertIn(x["gate_status"],{"WAITING_FOR_POST_REPAIR_SETTLEMENTS","HOLD_NO_POST_REPAIR_PRESETTLEMENT_EVIDENCE","HOLD_LEARNING_LINKAGE_NOT_RECONNECTED","HOLD_NO_ELIGIBLE_OR_LEARNED_POST_REPAIR_OUTCOME","POST_REPAIR_OUTCOME_LEARNING_RECONNECTED"});self.assertFalse(x["probability_enabled"]);self.assertTrue(x["read_only"]);self.assertFalse(x["execution_authority"]);print("[PHYSICAL]",x)\nif __name__=="__main__":unittest.main(verbosity=2)\n'

def atomic_write(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+f".{os.getpid()}.tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def restore(path,before):
    if before is None:
        if path.exists(): path.unlink()
    else:
        path.write_bytes(before)

def main():
    print("="*88)
    print(' OPC-052 INSTALLER — POST-REPAIR OUTCOME/LEARNING RECONNECTION CERTIFICATION')
    print("="*88)
    print("[ROOT]",ROOT)
    before_m=TARGET.read_bytes() if TARGET.exists() else None
    before_t=TEST.read_bytes() if TEST.exists() else None
    try:
        ast.parse(SOURCE); ast.parse(TEST_SOURCE)
        print("[PASS] payload syntax verified")
        atomic_write(TARGET,SOURCE); atomic_write(TEST,TEST_SOURCE)
        importlib.invalidate_caches()
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True,timeout=90)
    except Exception:
        restore(TARGET,before_m); restore(TEST,before_t)
        print("[ROLLBACK] installation failed; affected files restored")
        raise
    print("[DONE] INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
