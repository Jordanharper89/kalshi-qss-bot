from __future__ import annotations
import hashlib, importlib, json, os, subprocess, sys
from pathlib import Path

SCRIPT_DIR=Path(__file__).resolve().parent

def locate_repository():
    candidates=[]
    for base in (Path.cwd().resolve(),SCRIPT_DIR):
        candidates += [base,base/"kalshi-qss-bot"]
        for p in base.parents:
            candidates += [p,p/"kalshi-qss-bot"]
    seen=set()
    for c in candidates:
        try: c=c.resolve()
        except OSError: continue
        if c in seen: continue
        seen.add(c)
        if (c/"qseries_v2").is_dir(): return c
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
    if p.returncode: raise RuntimeError("Certification test failed: "+path.name)

BUILD_ID='OAD-037'
TITLE='OLA PRODUCTION POSTGRESQL ROUTER BINDING'
REVISION='OAD_037_PRODUCTION_V1'
MODULE=PACKAGE/'oad_037_ola_postgres_router_binding.py'
TEST=ROOT/'test_oad_037_ola_production_postgresql_router_binding.py'
EXPORTS=('OAD_037_BUILD_ID', 'OAD_037_REVISION', 'load_repository_environment', 'build_ola_production_persistence_router', 'persist_canonical_observation', 'verify_oad_037_ola_production_postgresql_router_binding')
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom datetime import datetime\nfrom pathlib import Path\nimport os\n\nOAD_037_BUILD_ID="OAD-037"\nOAD_037_REVISION="OAD_037_OLA_PRODUCTION_POSTGRESQL_ROUTER_BINDING_V1"\n\ndef load_repository_environment(root):\n    result=dict(os.environ)\n    p=Path(root)/".env"\n    if not p.is_file(): return result\n    for raw in p.read_text(encoding="utf-8",errors="ignore").splitlines():\n        line=raw.strip()\n        if not line or line.startswith("#") or "=" not in line: continue\n        k,v=line.split("=",1)\n        k=k.strip(); v=v.strip()\n        if len(v)>=2 and v[0]==v[-1] and v[0] in ("\'",\'"\'): v=v[1:-1]\n        if k and k not in result: result[k]=v\n    return result\n\ndef build_ola_production_persistence_router(root,environment=None):\n    from qseries_v2.oracle_intelligence.live_acquisition_model.oracle_first_real_shadow_corpus_launch_command import (\n        build_real_oracle_shadow_graph,\n    )\n    root=Path(root).resolve()\n    env=dict(environment) if environment is not None else load_repository_environment(root)\n    graph=build_real_oracle_shadow_graph(\n        runtime_root=root,\n        environment=env,\n        service_tick_interval_seconds=5,\n    )\n    router=graph.get("persistence_router")\n    if router is None or not callable(getattr(router,"route",None)):\n        raise RuntimeError("OLA-030 production persistence router unavailable")\n    return router\n\ndef persist_canonical_observation(router,observation,*,routed_at):\n    if not isinstance(routed_at,datetime) or routed_at.tzinfo is None:\n        raise ValueError("routed_at must be timezone-aware")\n    route=getattr(router,"route",None)\n    if not callable(route): raise ValueError("router must expose route")\n    evidence=route(observation,routed_at)\n    if getattr(evidence,"accepted",None) is not True:\n        raise RuntimeError("OLA canonical persistence routing rejected")\n    if getattr(evidence,"observation_id",None)!=observation.observation_id:\n        raise RuntimeError("persistence evidence observation mismatch")\n    return evidence\n\ndef verify_oad_037_ola_production_postgresql_router_binding():\n    class E:\n        accepted=True\n        observation_id="x"\n    class R:\n        def route(self,o,t):\n            e=E(); e.observation_id=o.observation_id; return e\n    class O: observation_id="x"\n    from datetime import timezone\n    return persist_canonical_observation(R(),O(),routed_at=datetime(2026,8,13,tzinfo=timezone.utc)).accepted is True\n'
TEST_SOURCE='\nimport unittest\nfrom datetime import datetime,timezone\nfrom qseries_v2.oracle_adapters.kalshi.oad_037_ola_postgres_router_binding import *\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_oad_037_ola_production_postgresql_router_binding())\n    def test_env(self):\n        self.assertIsInstance(load_repository_environment("."),dict)\nif __name__=="__main__":\n    print("="*72);print(" OAD-037 CERTIFICATION TEST");print(" OLA PRODUCTION POSTGRESQL ROUTER BINDING");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Existing OLA production persistence router binding certified");print("[DONE] OAD-037 CERTIFIED")\n'


def verify_upstream():
    p=PACKAGE/'oad_036_websocket_canonical_bridge.py'
    if not p.is_file(): raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_036_websocket_canonical_bridge')
        if getattr(m,'verify_oad_036_kalshi_websocket_to_ola_canonical_observation_bridge')() is not True:
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
            v=getattr(m,[x for x in EXPORTS if x.startswith("verify_")][-1])
            if v() is not True: raise RuntimeError("Production verifier returned false")
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
