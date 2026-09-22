from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID="OAD-061"; REVISION="OAD_061_PRODUCTION_INSTALLER_V1"
def find_root():
 for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
  for p in (b,*b.parents):
   if (p/"qseries_v2").is_dir(): return p
 raise SystemExit("[ERROR] Q Series repository not found")
ROOT=find_root(); PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"; MODULE=PKG/"oad_061_independent_to_canonical_bridge.py"; TEST=ROOT/"test_oad_061_independent_to_existing_canonical_bridge.py"; INIT=PKG/"__init__.py"
MODULE_SOURCE='\nfrom datetime import datetime,timezone\nfrom qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import RawSourceObservation,CanonicalObservation\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\ndef _dt(v):\n    d=datetime.fromisoformat(str(v).replace("Z","+00:00"))\n    return (d if d.tzinfo else d.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)\ndef canonicalize_independent_observation(x,acquisition_batch_id):\n    if x.source_class not in ("authoritative_real_world","independent_information"): raise ValueError("independent source required")\n    raw=RawSourceObservation.create(source_observation_id="independent."+x.source_id+"."+x.provenance_hash,\n      observed_at=_dt(x.observed_at),observation_type=x.observation_type,\n      payload={"subject":x.subject,"source_url":x.source_url,"source_class":x.source_class,"independent_evidence":True,\n               "provenance_hash":x.provenance_hash,"source_payload":dict(x.payload)},\n      provenance={"source_id":"source.independent."+x.source_id,"upstream_source_id":x.source_id,"source_class":x.source_class,\n                  "source_url":x.source_url,"provenance_hash":x.provenance_hash,"read_only":True,"execution_authority":False})\n    return CanonicalObservation.create(source_id="source.independent."+x.source_id,raw_observation=raw,\n      acquired_at=datetime.now(timezone.utc),acquisition_batch_id=str(acquisition_batch_id))\ndef canonicalize_independent_bundle(report,acquisition_batch_id):\n    return tuple(canonicalize_independent_observation(x,acquisition_batch_id) for x in report.observations)\n'; TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_060_independent_source_bundle import acquire_independent_production_bundle\nfrom qseries_v2.oracle_adapters.independent.oad_061_independent_to_canonical_bridge import *\nclass T(unittest.TestCase):\n def test_physical(self):\n  r=acquire_independent_production_bundle(2); c=canonicalize_independent_bundle(r,"oad061.physical")\n  print("[PHYSICAL] acquired=",len(r.observations),"canonicalized=",len(c))\n  self.assertGreater(len(c),0); self.assertEqual(len(c),len(r.observations))\n  self.assertTrue(all(dict(x.payload).get("independent_evidence") is True for x in c))\nif __name__=="__main__":\n print("="*80); print(" OAD-061 PHYSICAL CERTIFICATION TEST"); print("="*80)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful(): raise SystemExit(1)\n print("[PASS] Existing OLA canonical contract accepted real independent observations"); print("[DONE] OAD-061 CERTIFIED")\n'
def write(p,s):
 s=textwrap.dedent(s).lstrip(); ast.parse(s,filename=str(p)); p.parent.mkdir(parents=True,exist_ok=True)
 t=p.with_suffix(p.suffix+".tmp"); t.write_text(s,encoding="utf-8",newline="\n"); os.replace(t,p)
def main():
 print("="*80); print(" OAD-061 INSTALLER"); print(" INDEPENDENT OBSERVATION TO EXISTING OLA CANONICAL BRIDGE"); print("="*80); print("[BOOT] Revision:",REVISION); print("[ROOT]",ROOT)
 freeze=ROOT/"qseries_v2"/"oracle_adapters"/"kalshi"/"oad_055_kalshi_production_freeze.py"
 if not freeze.is_file(): raise RuntimeError("Frozen Kalshi OAD-055 boundary missing")
 if not (PKG/"oad_060_independent_source_bundle.py").is_file(): raise RuntimeError("Certified OAD-060 dependency missing")
 h=hashlib.sha256(freeze.read_bytes()).hexdigest(); affected=(MODULE,TEST,INIT); backup={p:(p.read_bytes() if p.exists() else None) for p in affected}
 try:
  write(MODULE,MODULE_SOURCE); write(TEST,TEST_SOURCE)
  lines=INIT.read_text(encoding="utf-8").splitlines() if INIT.exists() else []; exp="from ."+MODULE.stem+" import *"
  if exp not in lines: lines.append(exp)
  write(INIT,"\n".join(x for x in lines if x.strip())+"\n")
  if hashlib.sha256(freeze.read_bytes()).hexdigest()!=h: raise RuntimeError("Frozen Kalshi OAD-055 changed")
  print("[PASS] OAD-060 dependency verified"); print("[PASS] Frozen Kalshi OAD-055 unchanged"); print("[PASS] Wrote:",MODULE.relative_to(ROOT)); print("[PASS] Wrote:",TEST.name); print("[PASS] execution_authority=FALSE"); print("[DONE] OAD-061 INSTALLATION COMPLETE")
 except Exception:
  for p,v in backup.items():
   if v is None:
    if p.exists(): p.unlink()
   else: p.write_bytes(v)
  print("[ROLLBACK] affected files restored"); raise
if __name__=="__main__": main()
