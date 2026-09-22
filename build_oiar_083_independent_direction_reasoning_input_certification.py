from pathlib import Path
import ast,importlib,os,subprocess,sys,time
ROOT=Path.cwd().resolve();MOD=ROOT/'qseries_v2/oracle_intelligence_analytics_runtime/oiar_083_independent_direction_reasoning_input_certification.py';TEST=ROOT/'test_oiar_083_independent_direction_reasoning_input_certification.py'
SOURCE='from qseries_v2.oracle_intelligence_analytics_runtime.oiar_074_current_repeated_history_temporal_evidence import build_current_temporal_evidence\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_082_independent_research_direction_gate import build_independent_research_direction_gate\nOIAR_083_BUILD_ID="OIAR-083"\ndef certify_directional_reasoning_input(root=None):\n t=build_current_temporal_evidence(root);g=build_independent_research_direction_gate(root);gm={x["market_id"]:x for x in g["markets"]};rows=[]\n for m in t["markets"]:\n  q=gm.get(m["market_id"],{});ind=str(q.get("independent_research_direction") or "neutral").lower();temp="bull" if m["temporal_direction"]=="UP" else "bear" if m["temporal_direction"]=="DOWN" else "neutral";cert=ind in ("bull","bear")\n  rows.append({"market_id":m["market_id"],"temporal_market_direction":temp,"independent_research_direction":ind,"independent_direction_certified":cert,"reasoning_input_ready":cert,"market_direction_may_not_substitute":True})\n ready=sum(x["reasoning_input_ready"] for x in rows)\n status="READY_FOR_INDEPENDENT_DIRECTION_REASONING" if ready else "HOLD_INDEPENDENT_RESEARCH_DIRECTION_UNAVAILABLE"\n return {"schema_version":"OIAR-083","gate_status":status,"market_count":len(rows),"reasoning_input_ready_markets":ready,"markets":rows,"probability_enabled":False,"read_only":True,"execution_authority":False}\ndef physical_probe(root=None):\n x=certify_directional_reasoning_input(root);return {"gate_status":x["gate_status"],"markets":x["market_count"],"reasoning_input_ready_markets":x["reasoning_input_ready_markets"],"probability_enabled":False,"execution_authority":False}\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_intelligence_analytics_runtime import oiar_083_independent_direction_reasoning_input_certification as m\nclass T(unittest.TestCase):\n def test_physical(self):\n  x=m.physical_probe();self.assertGreater(x["markets"],0);self.assertIn(x["gate_status"],("READY_FOR_INDEPENDENT_DIRECTION_REASONING","HOLD_INDEPENDENT_RESEARCH_DIRECTION_UNAVAILABLE"));self.assertFalse(x["probability_enabled"]);self.assertFalse(x["execution_authority"])\nif __name__=="__main__":unittest.main(verbosity=2)\n';REQUIRED=('qseries_v2/oracle_intelligence_analytics_runtime/oiar_074_current_repeated_history_temporal_evidence.py', 'qseries_v2/oracle_intelligence_analytics_runtime/oiar_082_independent_research_direction_gate.py')
def write_exact(p,s):
 p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+f".{os.getpid()}.tmp");t.write_text(s,encoding="utf-8",newline="\n");os.replace(t,p)
def restore(p,b):
 if b is None:
  if p.exists():p.unlink()
 else:p.write_bytes(b)
def main():
 print("="*88);print(' OIAR-083 INSTALLER — INDEPENDENT DIRECTION REASONING INPUT CERTIFICATION');print("="*88);print("[ROOT]",ROOT)
 for rel in REQUIRED:
  if not (ROOT/rel).is_file():raise RuntimeError("Required certified upstream missing: "+rel)
 oldm=MOD.read_bytes() if MOD.exists() else None;oldt=TEST.read_bytes() if TEST.exists() else None
 try:
  ast.parse(SOURCE);ast.parse(TEST_SOURCE);print("[PASS] payload syntax verified");write_exact(MOD,SOURCE);write_exact(TEST,TEST_SOURCE);importlib.invalidate_caches()
  name="qseries_v2.oracle_intelligence_analytics_runtime."+'oiar_083_independent_direction_reasoning_input_certification';sys.modules.pop(name,None);m=importlib.import_module(name)
  s=time.monotonic();x=m.physical_probe(ROOT);print("[PHYSICAL]",x,"elapsed_seconds=",round(time.monotonic()-s,3))
  subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True,timeout=120)
 except Exception:
  restore(MOD,oldm);restore(TEST,oldt);print("[ROLLBACK] failed; affected files restored");raise
 print("[PASS] probability_enabled=FALSE");print("[PASS] execution_authority=FALSE");print("[DONE] INSTALLATION COMPLETE")
if __name__=="__main__":main()
