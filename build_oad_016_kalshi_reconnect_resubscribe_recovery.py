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

BUILD_ID='OAD-016'
TITLE='KALSHI RECONNECT + RESUBSCRIBE RECOVERY'
REVISION='OAD_016_PRODUCTION_V1'
MODULE=PACKAGE/'oad_016_reconnect_recovery.py'
TEST=ROOT/'test_oad_016_kalshi_reconnect_resubscribe_recovery.py'
EXPORTS=('OAD_016_BUILD_ID', 'OAD_016_REVISION', 'ReconnectRecoveryPlan', 'build_reconnect_recovery_plan', 'build_recovery_subscribe_commands', 'recovery_ready', 'build_oad_016_certification_manifest', 'verify_oad_016_kalshi_reconnect_resubscribe_recovery')
MODULE_SOURCE=r"""
from dataclasses import dataclass
from types import MappingProxyType
from .oad_012_subscription_partitioning import SubscriptionCoveragePlan, build_partition_subscribe_commands

OAD_016_BUILD_ID="OAD-016"
OAD_016_REVISION="OAD_016_KALSHI_RECONNECT_RESUBSCRIBE_RECOVERY_V1"

@dataclass(frozen=True)
class ReconnectRecoveryPlan:
    reconnect_required:bool
    relist_subscriptions_required:bool
    resubscribe_required:bool
    resnapshot_orderbooks_required:bool
    universe_reconcile_required:bool

def build_reconnect_recovery_plan(connection_lost,subscription_state_unknown=True):
    reconnect=bool(connection_lost)
    relist=bool(reconnect or subscription_state_unknown)
    resub=bool(reconnect or subscription_state_unknown)
    snapshot=bool(reconnect or subscription_state_unknown)
    reconcile=bool(reconnect)
    return ReconnectRecoveryPlan(reconnect,relist,resub,snapshot,reconcile)

def build_recovery_subscribe_commands(plan,coverage_plan):
    if not isinstance(plan,ReconnectRecoveryPlan):
        raise ValueError("certified recovery plan required")
    if not isinstance(coverage_plan,SubscriptionCoveragePlan):
        raise ValueError("certified coverage plan required")
    if not plan.resubscribe_required:
        return ()
    return build_partition_subscribe_commands(coverage_plan)

def recovery_ready(connected,subscriptions_restored,snapshots_restored,universe_reconciled):
    return bool(connected and subscriptions_restored and snapshots_restored and universe_reconciled)

def build_oad_016_certification_manifest():
    return MappingProxyType({"build_id":OAD_016_BUILD_ID,"revision":OAD_016_REVISION,
        "reconnect":True,"list_subscriptions_after_reconnect":True,"resubscribe":True,
        "orderbook_resnapshot":True,"universe_reconcile":True,"execution":False})

def verify_oad_016_kalshi_reconnect_resubscribe_recovery():
    from .oad_012_subscription_partitioning import partition_subscriptions
    p=build_reconnect_recovery_plan(True)
    c=partition_subscriptions(("A","B"),partition_size=1)
    cmds=build_recovery_subscribe_commands(p,c)
    return p.reconnect_required and p.resubscribe_required and len(cmds)==2 and recovery_ready(True,True,True,True)
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_adapters.kalshi.oad_012_subscription_partitioning import partition_subscriptions
from qseries_v2.oracle_adapters.kalshi.oad_016_reconnect_recovery import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_016_kalshi_reconnect_resubscribe_recovery())
    def test_connection_loss(self):
        p=build_reconnect_recovery_plan(True)
        self.assertTrue(p.resnapshot_orderbooks_required)
        self.assertTrue(p.universe_reconcile_required)
    def test_recovery_commands(self):
        p=build_reconnect_recovery_plan(True)
        c=partition_subscriptions(("A","B","C"),partition_size=2)
        self.assertEqual(len(build_recovery_subscribe_commands(p,c)),2)
if __name__=="__main__":
    print("="*72);print(" OAD-016 CERTIFICATION TEST");print(" KALSHI RECONNECT + RESUBSCRIBE RECOVERY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Kalshi reconnect/resubscribe/resnapshot recovery certified");print("[DONE] OAD-016 CERTIFIED")
"""

def verify_upstream():
    p=PACKAGE/'oad_015_streaming_gate.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_015_streaming_gate')
        if getattr(m,'verify_oad_015_kalshi_low_latency_streaming_capability_gate')() is not True:
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
