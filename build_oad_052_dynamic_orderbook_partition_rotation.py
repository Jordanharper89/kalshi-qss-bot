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

BUILD_ID='OAD-052'
TITLE='DYNAMIC ORDERBOOK PARTITION ROTATION'
REVISION='OAD_052_PRODUCTION_V1'
MODULE=PACKAGE/'oad_052_dynamic_orderbook_rotation.py'
TEST=ROOT/'test_oad_052_dynamic_orderbook_partition_rotation.py'
EXPORTS=('OAD_052_BUILD_ID', 'OAD_052_REVISION', 'SubscriptionRotation', 'compute_subscription_rotation', 'build_update_subscription_command', 'build_rotation_commands', 'verify_oad_052_dynamic_orderbook_partition_rotation')
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\n\nOAD_052_BUILD_ID="OAD-052"\nOAD_052_REVISION="OAD_052_DYNAMIC_ORDERBOOK_PARTITION_ROTATION_V1"\n\n@dataclass(frozen=True)\nclass SubscriptionRotation:\n    add_markets:tuple[str,...]\n    delete_markets:tuple[str,...]\n    unchanged_markets:tuple[str,...]\n\ndef compute_subscription_rotation(current_markets,target_markets):\n    current=set(str(x) for x in current_markets if str(x))\n    target=set(str(x) for x in target_markets if str(x))\n    return SubscriptionRotation(\n        tuple(sorted(target-current)),\n        tuple(sorted(current-target)),\n        tuple(sorted(current & target)),\n    )\n\ndef build_update_subscription_command(command_id,sids,market_tickers,action):\n    action=str(action)\n    if action not in ("add_markets","delete_markets"):\n        raise ValueError("action must be add_markets or delete_markets")\n    sids=tuple(int(x) for x in sids)\n    markets=tuple(str(x) for x in market_tickers if str(x))\n    if not sids or not markets:\n        raise ValueError("sids and market_tickers required")\n    return {\n        "id":int(command_id),\n        "cmd":"update_subscription",\n        "params":{\n            "sids":list(sids),\n            "market_tickers":list(markets),\n            "action":action,\n        },\n    }\n\ndef build_rotation_commands(rotation,sids,start_command_id=1000):\n    commands=[]\n    cid=int(start_command_id)\n    if rotation.add_markets:\n        commands.append(build_update_subscription_command(cid,sids,rotation.add_markets,"add_markets"))\n        cid+=1\n    if rotation.delete_markets:\n        commands.append(build_update_subscription_command(cid,sids,rotation.delete_markets,"delete_markets"))\n    return tuple(commands)\n\ndef verify_oad_052_dynamic_orderbook_partition_rotation():\n    r=compute_subscription_rotation(("A","B"),("B","C"))\n    cmds=build_rotation_commands(r,(7,))\n    return r.add_markets==("C",) and r.delete_markets==("A",) and len(cmds)==2 and cmds[0]["cmd"]=="update_subscription"\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.kalshi.oad_052_dynamic_orderbook_rotation import *\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_oad_052_dynamic_orderbook_partition_rotation())\n    def test_no_reconnect_command(self):\n        r=compute_subscription_rotation(("A",),("B",))\n        self.assertTrue(all(x["cmd"]=="update_subscription" for x in build_rotation_commands(r,(1,))))\nif __name__=="__main__":\n    print("="*72);print(" OAD-052 CERTIFICATION TEST");print(" DYNAMIC ORDERBOOK PARTITION ROTATION");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] In-place WebSocket orderbook market rotation certified")\n    print("[DONE] OAD-052 CERTIFIED")\n'


def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_051_adaptive_orderbook_tier_scheduler')
        if getattr(m,'verify_oad_051_adaptive_orderbook_tier_scheduler')() is not True:
            raise RuntimeError("Certified upstream verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def main():
    print("="*72);print(" "+BUILD_ID+" INSTALLER");print(" "+TITLE);print("="*72)
    print("[BOOT] Revision: "+REVISION);print("[ROOT] "+str(ROOT))
    verify_upstream();print("[PASS] Certified upstream boundary verified read-only")
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
                if p.exists(): p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] "+BUILD_ID+" installation failed; affected files restored")
        raise
    print("[PASS] Wrote: "+str(MODULE.relative_to(ROOT)))
    print("[PASS] Updated: "+str(INIT.relative_to(ROOT)))
    print("[PASS] Wrote: "+TEST.name)
    print("[DONE] "+BUILD_ID+" INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":
    main()
