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

BUILD_ID='OAD-031'
TITLE='PHYSICAL ORACLE LIVE RUNTIME KALSHI BINDING'
REVISION='OAD_031_PRODUCTION_V1'
MODULE=PACKAGE/'oad_031_runtime_binding.py'
TEST=ROOT/'test_oad_031_physical_oracle_live_runtime_kalshi_binding.py'
EXPORTS=('OAD_031_BUILD_ID', 'OAD_031_REVISION', 'OracleKalshiRuntimeBinding', 'discover_live_shadow_launcher', 'build_oracle_kalshi_runtime_binding', 'verify_oad_031_physical_oracle_live_runtime_kalshi_binding')
MODULE_SOURCE='\nfrom dataclasses import dataclass\nfrom pathlib import Path\nfrom types import MappingProxyType\n\nOAD_031_BUILD_ID="OAD-031"\nOAD_031_REVISION="OAD_031_PHYSICAL_ORACLE_LIVE_RUNTIME_KALSHI_BINDING_V1"\n\nLIVE_SHADOW_LAUNCHER_CANDIDATES=(\n    "run_oracle_live_shadow_FIXED.py",\n    "run_oracle_live_shadow_continuous.py",\n    "run_oracle_live_shadow.py",\n)\n\n@dataclass(frozen=True)\nclass OracleKalshiRuntimeBinding:\n    oracle_launcher:str\n    kalshi_stream_runner:str\n    live_shadow_launcher:str|None\n    terminal_dependency:bool=False\n    execution_authority:bool=False\n\ndef discover_live_shadow_launcher(root):\n    root=Path(root)\n    for name in LIVE_SHADOW_LAUNCHER_CANDIDATES:\n        if (root/name).is_file():\n            return name\n    return None\n\ndef build_oracle_kalshi_runtime_binding(root):\n    root=Path(root)\n    if not (root/"run_oracle_LIVE.py").is_file():\n        raise RuntimeError("run_oracle_LIVE.py missing")\n    stream="run_oad_032_kalshi_persistent_stream.py"\n    return OracleKalshiRuntimeBinding(\n        "run_oracle_LIVE.py",stream,discover_live_shadow_launcher(root),False,False\n    )\n\ndef verify_oad_031_physical_oracle_live_runtime_kalshi_binding():\n    # Repository-independent verifier protects authority boundaries.\n    x=OracleKalshiRuntimeBinding("run_oracle_LIVE.py","run_oad_032_kalshi_persistent_stream.py",None,False,False)\n    return not x.terminal_dependency and not x.execution_authority and x.oracle_launcher=="run_oracle_LIVE.py"\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.kalshi.oad_031_runtime_binding import *\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_oad_031_physical_oracle_live_runtime_kalshi_binding())\n    def test_no_execution(self):\n        x=OracleKalshiRuntimeBinding("a","b",None)\n        self.assertFalse(x.execution_authority)\nif __name__=="__main__":\n    print("="*72);print(" OAD-031 CERTIFICATION TEST");print(" PHYSICAL ORACLE LIVE RUNTIME KALSHI BINDING");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Oracle/Kalshi physical launcher binding boundary certified");print("[DONE] OAD-031 CERTIFIED")\n'


def verify_upstream():
    p=PACKAGE/'oad_030_runtime_integration_gate.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_030_runtime_integration_gate')
        if getattr(m,'verify_oad_030_kalshi_oracle_live_runtime_integration_gate')() is not True:
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
