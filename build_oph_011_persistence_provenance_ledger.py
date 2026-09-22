from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_production_hardening"
MOD=PKG/"oph_011_persistence_provenance_ledger.py";TEST=ROOT/"test_oph_011_persistence_provenance_ledger.py";INIT=PKG/"__init__.py"
MODULE='from __future__ import annotations\nfrom pathlib import Path\nfrom datetime import datetime,timezone\nimport json,os\n\nOPH_011_BUILD_ID="OPH-011"\nOPH_011_REVISION="OPH_011_PERSISTENCE_PROVENANCE_LEDGER_V1"\n\ndef ledger_path(root=None):\n    return Path(root or Path.cwd()).resolve()/"runtime_state"/"oracle_canonical_persistence_provenance.jsonl"\n\ndef append_provenance(kind,root=None,**payload):\n    record={\n        "ts":datetime.now(timezone.utc).isoformat(),\n        "pid":os.getpid(),\n        "kind":str(kind),\n        **payload,\n    }\n    p=ledger_path(root)\n    p.parent.mkdir(parents=True,exist_ok=True)\n    with p.open("a",encoding="utf-8") as f:\n        f.write(json.dumps(record,sort_keys=True,default=str)+"\\n")\n    return record\n\ndef verify_oph_011_persistence_provenance_ledger():\n    import tempfile\n    with tempfile.TemporaryDirectory() as td:\n        r=append_provenance("TEST",td,writer="unit")\n        p=ledger_path(td)\n        return p.exists() and r["kind"]=="TEST" and r["writer"]=="unit"\n';TESTSRC='import unittest\nfrom qseries_v2.oracle_production_hardening.oph_011_persistence_provenance_ledger import verify_oph_011_persistence_provenance_ledger\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_oph_011_persistence_provenance_ledger())\nif __name__=="__main__":\n    print("="*80);print(" OPH-011 CERTIFICATION TEST");print(" PERSISTENCE PROVENANCE LEDGER");print("="*80)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] OPH-011 certified");print("[DONE] OPH-011 CERTIFIED")\n'

def write_exact(p,s):
    p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix(p.suffix+".tmp");t.write_text(s,encoding="utf-8",newline="\n");os.replace(t,p)

def main():
    print("="*80);print(" OPH-011 INSTALLER");print(" PERSISTENCE PROVENANCE LEDGER");print("="*80);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_production_hardening.oph_010_physical_single_writer_production_gate")
    if up.verify_oph_010_physical_single_writer_production_gate() is not True:raise RuntimeError("OPH-010 verification failed")
    print("[PASS] Certified OPH-010 upstream boundary verified")
    affected=(MOD,TEST,INIT);old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE);write_exact(TEST,TESTSRC)
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else "";ex="from .oph_011_persistence_provenance_ledger import *"
        if ex not in cur:write_exact(INIT,cur.rstrip()+"\n"+ex+"\n")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)

    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists():p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] OPH-011 installation failed");raise
    print("[PASS] Wrote:",MOD.relative_to(ROOT));print("[PASS] Wrote:",TEST.name);print("[DONE] OPH-011 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
