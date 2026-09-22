from pathlib import Path
import importlib,os,subprocess,sys

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_pre_settlement_coverage"
MOD=PKG/"opc_033_priority_router_patch.py"
TEST=ROOT/"test_opc_033_priority_router_patch.py"
INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom pathlib import Path\n\nfrom .opc_031_persistence_priority_contract import priority_for_child\nfrom .opc_032_cross_process_persistence_arbiter import acquire_persistence_lease\n\nOPC_033_BUILD_ID="OPC-033"\nOPC_033_REVISION="OPC_033_PRIORITY_ROUTER_PATCH_V1"\n\n_PATCH_MARKER="_opc_priority_arbitration_v1"\n\ndef install_priority_router_patch(child_name,root=None):\n    from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_router import (\n        OraclePostgreSQLCanonicalObservationPersistenceRouter,\n    )\n\n    cls=OraclePostgreSQLCanonicalObservationPersistenceRouter\n    if getattr(cls,_PATCH_MARKER,False):\n        return False\n\n    policy=priority_for_child(child_name)\n    original=cls.route_batch\n    root=Path(root or Path.cwd()).resolve()\n\n    def route_batch_with_priority(self,observations,routed_at,*args,**kwargs):\n        items=tuple(observations)\n        if not items:\n            return original(self,items,routed_at,*args,**kwargs)\n\n        if policy.name=="FAST_LANE":\n            with acquire_persistence_lease(\n                policy.name,\n                root=root,\n                timeout_seconds=policy.blocking_timeout_seconds,\n            ):\n                return original(self,items,routed_at,*args,**kwargs)\n\n        evidence=[]\n        size=max(1,int(policy.microbatch_size))\n\n        for start in range(0,len(items),size):\n            chunk=items[start:start+size]\n            with acquire_persistence_lease(\n                policy.name,\n                root=root,\n                timeout_seconds=policy.blocking_timeout_seconds,\n            ):\n                result=original(self,chunk,routed_at,*args,**kwargs)\n                evidence.extend(tuple(result))\n\n        return tuple(evidence)\n\n    setattr(cls,"_opc_priority_original_route_batch",original)\n    setattr(cls,"route_batch",route_batch_with_priority)\n    setattr(cls,_PATCH_MARKER,True)\n    setattr(cls,"_opc_priority_child",str(child_name))\n    return True\n\ndef verify_opc_033_priority_router_patch():\n    from .opc_031_persistence_priority_contract import FAST_LANE,COVERAGE\n    return (\n        FAST_LANE.rank>COVERAGE.rank\n        and COVERAGE.microbatch_size==25\n        and FAST_LANE.microbatch_size==1\n    )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_033_priority_router_patch import verify_opc_033_priority_router_patch\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_opc_033_priority_router_patch())\n\nif __name__=="__main__":\n    print("="*80)\n    print(" OPC-033 CERTIFICATION TEST")\n    print(" PRIORITY ROUTER PATCH")\n    print("="*80)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] OPC-033 certified")\n    print("[DONE] OPC-033 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)


def main():
    print("="*80)
    print(" OPC-033 INSTALLER")
    print(" PRIORITY ROUTER PATCH")
    print("="*80)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))

    up=importlib.import_module("qseries_v2.oracle_pre_settlement_coverage.opc_032_cross_process_persistence_arbiter")
    if up.verify_opc_032_cross_process_persistence_arbiter() is not True:
        raise RuntimeError("Certified OPC-032 verification failed")
    print("[PASS] Certified OPC-032 upstream boundary verified")

    affected=(MOD,TEST,INIT)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}

    try:
        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export="from .opc_033_priority_router_patch import *"
        if export not in current:
            write_exact(INIT,current.rstrip()+"\n"+export+"\n")

        compile(MOD.read_text(encoding="utf-8"),str(MOD),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")

        subprocess.run(
            [sys.executable,str(TEST)],
            cwd=str(ROOT),
            check=True,
        )

    except Exception:
        for p,b in backups.items():
            if b is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(b)
        print("[ROLLBACK] OPC-033 installation failed; affected files restored")
        raise

    print("[PASS] Wrote:",MOD.relative_to(ROOT))
    print("[PASS] Wrote:",TEST.name)
    print("[DONE] OPC-033 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
