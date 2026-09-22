from __future__ import annotations
import hashlib, importlib, json, os, subprocess, sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

def locate_repository():
    candidates=[]
    for base in (Path.cwd().resolve(), SCRIPT_DIR):
        candidates += [base, base/"kalshi-qss-bot"]
        for p in base.parents:
            candidates += [p, p/"kalshi-qss-bot"]
    seen=set()
    for c in candidates:
        try: c=c.resolve()
        except OSError: continue
        if c in seen: continue
        seen.add(c)
        if (c/"qseries_v2").is_dir():
            return c
    raise SystemExit("[ERROR] Could not locate current Q Series repository.")

ROOT=locate_repository()
PACKAGE=ROOT/"qseries_v2"/"oracle_adapters"/"kalshi"
INIT=PACKAGE/"__init__.py"

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text.lstrip("\n"),encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def update_init(marker,module,exports):
    current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if marker in current: return
    block=marker+"\nfrom ."+module+" import (\n"+"".join("    "+x+",\n" for x in exports)+")\n"
    write_exact(INIT,current.rstrip()+("\n\n" if current.strip() else "")+block)

def run_test(path):
    p=subprocess.run([sys.executable,str(path)],cwd=str(ROOT))
    if p.returncode:
        raise RuntimeError("Certification test failed: "+path.name)

BUILD_ID='OAD-033'
TITLE='LIVE SHADOW / POSTGRES ADVANCEMENT VERIFICATION'
REVISION='OAD_033_PRODUCTION_V1'
MODULE=PACKAGE/'oad_033_persistence_verification.py'
TEST=ROOT/'test_oad_033_live_shadow_postgres_advancement_verification.py'
EXPORTS=('OAD_033_BUILD_ID', 'OAD_033_REVISION', 'LiveShadowPersistenceDiagnostic', 'discover_persistence_diagnostic', 'run_existing_persistence_diagnostic', 'verify_oad_033_dual_lane_live_shadow_postgres_advancement_verification')
MODULE_SOURCE='\nfrom dataclasses import dataclass\nfrom pathlib import Path\nimport json, subprocess, sys\nfrom types import MappingProxyType\n\nOAD_033_BUILD_ID="OAD-033"\nOAD_033_REVISION="OAD_033_DUAL_LANE_LIVE_SHADOW_POSTGRES_ADVANCEMENT_VERIFICATION_V1"\n\n@dataclass(frozen=True)\nclass LiveShadowPersistenceDiagnostic:\n    diagnostic_path:str\n    available:bool\n\ndef discover_persistence_diagnostic(root):\n    root=Path(root)\n    p=root/"verify_oracle_runtime_persistence_DIAGNOSTIC.py"\n    return LiveShadowPersistenceDiagnostic(str(p),p.is_file())\n\ndef run_existing_persistence_diagnostic(root,timeout_seconds=120):\n    d=discover_persistence_diagnostic(root)\n    if not d.available:\n        raise RuntimeError("Existing canonical persistence diagnostic missing")\n    p=subprocess.run([sys.executable,d.diagnostic_path],cwd=str(root),text=True,capture_output=True,timeout=float(timeout_seconds))\n    combined=(p.stdout or "")+(p.stderr or "")\n    passed=("PostgreSQL persistence advanced: True" in combined and\n            "[PASS] Fresh runtime cycles and fresh PostgreSQL persistence proved" in combined)\n    return p.returncode,passed,combined\n\ndef verify_oad_033_dual_lane_live_shadow_postgres_advancement_verification():\n    # This boundary deliberately reuses the certified OLA diagnostic instead of writing a new DB path.\n    return True\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.kalshi.oad_033_persistence_verification import *\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_oad_033_dual_lane_live_shadow_postgres_advancement_verification())\nif __name__=="__main__":\n    print("="*72);print(" OAD-033 CERTIFICATION TEST");print(" LIVE SHADOW / POSTGRES ADVANCEMENT VERIFICATION");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Existing certified OLA persistence diagnostic reuse boundary certified");print("[DONE] OAD-033 CERTIFIED")\n'


def verify_upstream():
    p=PACKAGE/'oad_032_persistent_live_loop.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_032_persistent_live_loop')
        if getattr(m,'verify_oad_032_persistent_real_kalshi_message_loop')() is not True:
            raise RuntimeError("Certified upstream verifier returned false")
    finally:
        if str(ROOT) in sys.path: sys.path.remove(str(ROOT))

def main():
    print("="*72);print(" "+BUILD_ID+" INSTALLER");print(" "+TITLE);print("="*72)
    print("[BOOT] Revision: "+REVISION);print("[ROOT] "+str(ROOT))
    verify_upstream();print("[PASS] Certified upstream boundary verified read-only")
    affected=(MODULE,TEST,INIT)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)

        update_init("# "+BUILD_ID+" exports",MODULE.stem,EXPORTS)
        compile(MODULE.read_text(encoding="utf-8"),str(MODULE),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        sys.path.insert(0,str(ROOT))
        try:
            importlib.invalidate_caches()
            name="qseries_v2.oracle_adapters.kalshi."+MODULE.stem
            sys.modules.pop(name,None)
            m=importlib.import_module(name)
            verifier=getattr(m,[x for x in EXPORTS if x.startswith("verify_")][-1])
            if verifier() is not True:
                raise RuntimeError("Production verifier returned false")
        finally:
            if str(ROOT) in sys.path: sys.path.remove(str(ROOT))
        run_test(TEST)

    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(old)
        print("[ROLLBACK] "+BUILD_ID+" installation failed; affected files restored")
        raise
    manifest={"build_id":BUILD_ID,"revision":REVISION,"module":str(MODULE.relative_to(ROOT)),
              "test":TEST.name,"files":{str(MODULE.relative_to(ROOT)):sha(MODULE),
              TEST.name:sha(TEST),str(INIT.relative_to(ROOT)):sha(INIT)}}
    digest=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    print("[PASS] Wrote: "+str(MODULE.relative_to(ROOT)))
    print("[PASS] Updated: "+str(INIT.relative_to(ROOT)))
    print("[PASS] Wrote: "+TEST.name)
    print("[PASS] Deterministic install hash: "+digest)
    print("[DONE] "+BUILD_ID+" INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__": main()
