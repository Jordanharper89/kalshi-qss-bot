from pathlib import Path
import ast,importlib,os,subprocess,sys,time
ROOT=Path.cwd().resolve();TARGET=ROOT/'qseries_v2/oracle_intelligence_analytics_runtime/oiar_077_current_abstention_aware_reasoning_state.py';TEST=ROOT/'test_oiar_077_current_abstention_aware_reasoning_state.py'
SOURCE='from pathlib import Path\nfrom decimal import Decimal,InvalidOperation\nfrom datetime import datetime,timezone\ndef _dec(v):\n try:return Decimal(str(v)) if v is not None else None\n except (InvalidOperation,ValueError,TypeError):return None\ndef _dt(v):\n if isinstance(v,datetime):return v if v.tzinfo else v.replace(tzinfo=timezone.utc)\n try:return datetime.fromisoformat(str(v).replace("Z","+00:00"))\n except:return None\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_076_current_directional_evidence_balance import build_directional_evidence_balance\nOIAR_077_BUILD_ID="OIAR-077"\ndef build_reasoning_states(root=None):\n x=build_directional_evidence_balance(root);out=[]\n for m in x["markets"]:\n  if m["evidence_quality"]!="STRONG_TEMPORAL":state="ABSTAIN";direction="NEUTRAL";reason="insufficient_priced_temporal_evidence"\n  elif m["directional_contradiction"]:state="OBSERVE";direction="NEUTRAL";reason="research_temporal_contradiction"\n  elif m["directional_agreement"]:state="READY";direction="BULL" if m["research_direction"]=="bull" else "BEAR";reason="independent_directional_agreement"\n  else:state="OBSERVE";direction="NEUTRAL";reason="no_independent_directional_agreement"\n  out.append({**m,"reasoning_state":state,"direction":direction,"state_reason":reason})\n return {"schema_version":"OIAR-077","market_count":len(out),"markets":out,"probability_enabled":False,"read_only":True,"execution_authority":False}\ndef physical_probe(root=None):\n x=build_reasoning_states(root);return {"markets":x["market_count"],"ready":sum(m["reasoning_state"]=="READY" for m in x["markets"]),"observe":sum(m["reasoning_state"]=="OBSERVE" for m in x["markets"]),"abstain":sum(m["reasoning_state"]=="ABSTAIN" for m in x["markets"]),"probability_enabled":False,"execution_authority":False}\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_intelligence_analytics_runtime import oiar_077_current_abstention_aware_reasoning_state as m\nclass T(unittest.TestCase):\n def test_physical(self):\n  x=m.physical_probe();self.assertEqual(x["markets"],x["ready"]+x["observe"]+x["abstain"]);self.assertFalse(x["probability_enabled"]);self.assertFalse(x["execution_authority"])\nif __name__=="__main__":unittest.main(verbosity=2)\n';REQUIRED=('qseries_v2/oracle_intelligence_analytics_runtime/oiar_076_current_directional_evidence_balance.py',)
def w(p,s):
 p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+f".{os.getpid()}.tmp");t.write_text(s,encoding="utf-8",newline="\n");os.replace(t,p)
def restore(p,b):
 if b is None:
  if p.exists():p.unlink()
 else:p.write_bytes(b)
def main():
 print("="*88);print(' OIAR-077 INSTALLER — CURRENT ABSTENTION-AWARE REASONING STATE');print("="*88);print("[ROOT]",ROOT)
 for rel in REQUIRED:
  if not (ROOT/rel).is_file():raise RuntimeError("Required certified upstream missing: "+rel)
 bm=TARGET.read_bytes() if TARGET.exists() else None;bt=TEST.read_bytes() if TEST.exists() else None
 try:
  ast.parse(SOURCE);ast.parse(TEST_SOURCE);print("[PASS] payload syntax verified");w(TARGET,SOURCE);w(TEST,TEST_SOURCE);importlib.invalidate_caches()
  m=importlib.import_module("qseries_v2.oracle_intelligence_analytics_runtime."+'oiar_077_current_abstention_aware_reasoning_state');s=time.monotonic();x=m.physical_probe(ROOT);print("[PHYSICAL]",x,"elapsed_seconds=",round(time.monotonic()-s,3))
  subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True,timeout=90)
 except Exception:
  restore(TARGET,bm);restore(TEST,bt);print("[ROLLBACK] failed; affected files restored");raise
 print("[PASS] probability_enabled=FALSE");print("[PASS] execution_authority=FALSE");print("[DONE] INSTALLATION COMPLETE")
if __name__=="__main__":main()
