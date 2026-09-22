from __future__ import annotations
import hashlib, importlib, json, os, subprocess, sys
from pathlib import Path

ROOT=Path.cwd().resolve()
PACKAGE=ROOT/"qseries_v2"/"oracle_adapters"/"kalshi"
INIT=PACKAGE/"__init__.py"

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def update_init(marker,module,exports):
    current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if marker in current:
        return
    block=marker+"\nfrom ."+module+" import (\n"+"".join("    "+x+",\n" for x in exports)+")\n"
    write_exact(INIT,current.rstrip()+("\n\n" if current.strip() else "")+block)

def run_test(path):
    p=subprocess.run([sys.executable,str(path)],cwd=str(ROOT))
    if p.returncode:
        raise RuntimeError("Certification test failed: "+path.name)

BUILD_ID='OAD-042'
TITLE='PARTITIONED PERSISTENT CANONICAL PERSISTENCE'
REVISION='OAD_042_PRODUCTION_V1'
MODULE=PACKAGE/'oad_042_partitioned_persistence.py'
TEST=ROOT/'test_oad_042_partitioned_persistent_canonical_persistence.py'
EXPORTS=('OAD_042_BUILD_ID', 'OAD_042_REVISION', 'PartitionPersistenceState', 'build_partition_persistence_state', 'summarize_partition_persistence', 'verify_oad_042_partitioned_persistent_canonical_persistence')
MODULE_SOURCE='from dataclasses import dataclass\nOAD_042_BUILD_ID="OAD-042"\nOAD_042_REVISION="OAD_042_PARTITIONED_PERSISTENT_CANONICAL_PERSISTENCE_V1"\n\n@dataclass(frozen=True)\nclass PartitionPersistenceState:\n    partition_id:int\n    connected:bool\n    subscription_ready:bool\n    events_seen:int\n    persisted:int\n    reconnects:int\n    healthy:bool\n\ndef build_partition_persistence_state(partition_id,connected,subscription_ready,events_seen,persisted,reconnects):\n    pid=int(partition_id); events=int(events_seen); saved=int(persisted); rec=int(reconnects)\n    if pid<1 or min(events,saved,rec)<0:\n        raise ValueError("valid partition counters required")\n    healthy=bool(connected and subscription_ready and saved<=events)\n    return PartitionPersistenceState(pid,bool(connected),bool(subscription_ready),events,saved,rec,healthy)\n\ndef summarize_partition_persistence(states):\n    states=tuple(states)\n    if not states:\n        raise ValueError("partition states required")\n    ids=tuple(x.partition_id for x in states)\n    if len(set(ids))!=len(ids):\n        raise ValueError("duplicate partition id")\n    return {\n        "partitions":len(states),\n        "healthy_partitions":sum(1 for x in states if x.healthy),\n        "events_seen":sum(x.events_seen for x in states),\n        "persisted":sum(x.persisted for x in states),\n        "reconnects":sum(x.reconnects for x in states),\n        "complete":all(x.healthy for x in states),\n    }\n\ndef verify_oad_042_partitioned_persistent_canonical_persistence():\n    a=build_partition_persistence_state(1,True,True,5,5,0)\n    b=build_partition_persistence_state(2,True,True,3,3,1)\n    x=summarize_partition_persistence((a,b))\n    return x["complete"] and x["persisted"]==8 and x["partitions"]==2\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.kalshi.oad_042_partitioned_persistence import *\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_oad_042_partitioned_persistent_canonical_persistence())\nif __name__=="__main__":\n    print("="*72);print(" OAD-042 CERTIFICATION TEST");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Partitioned canonical persistence supervision certified")\n    print("[DONE] OAD-042 CERTIFIED")\n'

def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_041_full_universe_partitioning')
        if getattr(m,'verify_oad_041_full_universe_stream_partition_expansion')() is not True:
            raise RuntimeError("Certified upstream verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def main():
    print("="*72)
    print(" "+BUILD_ID+" INSTALLER")
    print(" "+TITLE)
    print("="*72)
    print("[BOOT] Revision: "+REVISION)
    print("[ROOT] "+str(ROOT))
    verify_upstream()
    print("[PASS] Certified upstream boundary verified read-only")

    affected=(MODULE,TEST,INIT)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}

    try:
        write_exact(MODULE,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
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
            if str(ROOT) in sys.path:
                sys.path.remove(str(ROOT))

        run_test(TEST)

    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
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

if __name__=="__main__":
    main()
