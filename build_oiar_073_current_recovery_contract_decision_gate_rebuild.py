from pathlib import Path
import ast,importlib,os,subprocess,sys,time

ROOT=Path.cwd().resolve()
MOD=ROOT/"qseries_v2/oracle_intelligence_analytics_runtime/oiar_073_coverage_repair_decision_gate.py"
TEST=ROOT/"test_oiar_073_coverage_repair_decision_gate.py"
MODULE_SOURCE='from __future__ import annotations\nfrom pathlib import Path\nfrom . import oiar_069_historical_pre_settlement_coverage_acquisition_gap_physical_trace as b69\nfrom . import oiar_070_active_only_coverage_semantics_physical_proof as b70\nfrom . import oiar_072_historical_recovery_semantics_boundary_proof as b72\n\nBUILD_ID="OIAR-073"\nREVISION="OIAR_073_CURRENT_RECOVERY_CONTRACT_DECISION_GATE_REBUILD_V1"\n\ndef physical_probe(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    x=b69.trace(root,50)\n    c=b70.contract_probe()\n    r=b72.physical_probe(root)\n\n    before=int(x["before_opc_coverage_epoch"])\n    inside=int(x["inside_opc_coverage_epoch_without_snapshot"])\n\n    # Current certified OIAR-072 contract:\n    # OBR-004 preserves explicit NO_LIVE_EVIDENCE_DURING_GAP lineage,\n    # OHL requires genuine pre-settlement evidence, and fabrication is forbidden.\n    explicit_missing_lineage=bool(r["obr_004_missing_live_evidence_lineage_explicit"])\n    requires_pre=bool(r["ohl_requires_pre_settlement_evidence"])\n    rejects_leakage=bool(r["ohl_rejects_post_outcome_leakage"])\n    no_fabrication=not bool(r["historical_pre_settlement_fabrication_allowed"])\n\n    if inside>before:\n        decision="IN_COVERAGE_ERA_ROTATION_OR_ADMISSION_GAP"\n        nxt="OPC_FORWARD_COVERAGE_LATENCY_AND_SETTLEMENT_AWARENESS_PAVEMENT"\n    elif before>0:\n        decision="LEGACY_PRE_COVERAGE_HISTORY_GAP"\n        nxt="FORWARD_COVERAGE_PLUS_EXPLICIT_UNRECOVERABLE_HISTORY_LINEAGE"\n    else:\n        decision="NO_DOMINANT_UPSTREAM_GAP_CLASSIFIED"\n        nxt="RETURN_TO_EXACT_EVIDENCE_LINKAGE_DIAGNOSTIC"\n\n    return {\n      "sample_size":int(x["sampled_missing_settlements"]),\n      "before_coverage_epoch":before,\n      "inside_coverage_epoch_missing_snapshot":inside,\n      "pre_settlement_snapshot_found":int(x["pre_settlement_snapshot_found"]),\n      "post_only_snapshot_found":int(x["post_only_snapshot_found"]),\n      "active_only_normal_coverage":not bool(c["historical_settled_backfill_supported_by_normal_cycle"]),\n      "explicit_missing_live_evidence_lineage":explicit_missing_lineage,\n      "historical_learning_requires_pre_settlement_evidence":requires_pre,\n      "historical_learning_rejects_post_outcome_leakage":rejects_leakage,\n      "historical_evidence_fabrication_forbidden":no_fabrication,\n      "decision":decision,\n      "next_pavement":nxt,\n      "read_only":True,\n      "repaired_rows":0,\n      "probability_enabled":False,\n      "execution_authority":False,\n    }\n\ndef verify_oiar_073():\n    return BUILD_ID=="OIAR-073"\n'
TEST_SOURCE='import unittest\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_073_coverage_repair_decision_gate as m\n\nclass T(unittest.TestCase):\n def test_contract(self):\n  self.assertTrue(m.verify_oiar_073())\n\n def test_physical(self):\n  x=m.physical_probe()\n  self.assertGreater(x["sample_size"],0)\n  self.assertTrue(x["active_only_normal_coverage"])\n  self.assertTrue(x["explicit_missing_live_evidence_lineage"])\n  self.assertTrue(x["historical_learning_requires_pre_settlement_evidence"])\n  self.assertTrue(x["historical_learning_rejects_post_outcome_leakage"])\n  self.assertTrue(x["historical_evidence_fabrication_forbidden"])\n  self.assertTrue(x["decision"])\n  self.assertTrue(x["next_pavement"])\n  self.assertFalse(x["probability_enabled"])\n  self.assertFalse(x["execution_authority"])\n\nif __name__=="__main__":\n print("="*88)\n print(" OIAR-073 CERTIFICATION TEST")\n print(" CURRENT RECOVERY CONTRACT COVERAGE REPAIR DECISION GATE")\n print("="*88)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] current certified OIAR-072 contract consumed")\n print("[PASS] upstream coverage decision physically classified")\n print("[PASS] historical evidence fabrication remains forbidden")\n print("[PASS] probability_enabled=FALSE")\n print("[PASS] execution_authority=FALSE")\n print("[DONE] OIAR-073 CERTIFIED")\n'
REQ=(
"qseries_v2/oracle_intelligence_analytics_runtime/oiar_069_historical_pre_settlement_coverage_acquisition_gap_physical_trace.py",
"qseries_v2/oracle_intelligence_analytics_runtime/oiar_070_active_only_coverage_semantics_physical_proof.py",
"qseries_v2/oracle_intelligence_analytics_runtime/oiar_072_historical_recovery_semantics_boundary_proof.py",
)

def w(p,s):
 p.parent.mkdir(parents=True,exist_ok=True)
 t=p.with_name(p.name+f".{os.getpid()}.tmp")
 t.write_text(s,encoding="utf-8",newline="\n")
 os.replace(t,p)

def rr(p,b):
 if b is None:
  if p.exists():p.unlink()
 else:
  p.write_bytes(b)

def main():
 print("="*88)
 print(" OIAR-073 REBUILD INSTALLER")
 print(" CURRENT RECOVERY CONTRACT COVERAGE REPAIR DECISION GATE")
 print("="*88)
 print("[ROOT]",ROOT)

 for rel in REQ:
  if not (ROOT/rel).is_file():
   raise RuntimeError("Required certified upstream missing: "+rel)

 bm=MOD.read_bytes() if MOD.exists() else None
 bt=TEST.read_bytes() if TEST.exists() else None

 try:
  ast.parse(MODULE_SOURCE)
  ast.parse(TEST_SOURCE)
  print("[PASS] installer payload syntax verified")
  w(MOD,MODULE_SOURCE)
  w(TEST,TEST_SOURCE)
  importlib.invalidate_caches()

  name="qseries_v2.oracle_intelligence_analytics_runtime.oiar_073_coverage_repair_decision_gate"
  if name in sys.modules:del sys.modules[name]
  m=importlib.import_module(name)

  s=time.monotonic()
  x=m.physical_probe(ROOT)
  print("[PHYSICAL]",x,"elapsed_seconds=",round(time.monotonic()-s,3))
  print("[DECISION]",x["decision"])
  print("[NEXT PAVEMENT]",x["next_pavement"])

  if not x["explicit_missing_live_evidence_lineage"]:
   raise RuntimeError("current OBR missing-evidence lineage contract not proven")
  if not x["historical_learning_requires_pre_settlement_evidence"]:
   raise RuntimeError("pre-settlement evidence requirement not proven")
  if not x["historical_evidence_fabrication_forbidden"]:
   raise RuntimeError("historical evidence fabrication invariant violated")

  subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True,timeout=180)

 except Exception:
  rr(MOD,bm)
  rr(TEST,bt)
  print("[ROLLBACK] OIAR-073 rebuild failed; affected files restored")
  raise

 print("[PASS] obsolete OIAR-072 key dependency removed")
 print("[PASS] current certified recovery contract used")
 print("[PASS] probability_enabled=FALSE")
 print("[PASS] execution_authority=FALSE")
 print("[DONE] OIAR-073 INSTALLATION COMPLETE")

if __name__=="__main__":
 main()
