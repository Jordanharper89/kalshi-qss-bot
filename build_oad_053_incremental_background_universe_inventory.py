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

BUILD_ID='OAD-053'
TITLE='INCREMENTAL BACKGROUND UNIVERSE INVENTORY'
REVISION='OAD_053_PRODUCTION_V1'
MODULE=PACKAGE/'oad_053_background_universe_inventory.py'
TEST=ROOT/'test_oad_053_incremental_background_universe_inventory.py'
EXPORTS=('OAD_053_BUILD_ID', 'OAD_053_REVISION', 'UniverseInventoryCheckpoint', 'load_inventory_checkpoint', 'save_inventory_checkpoint', 'run_inventory_slice', 'verify_oad_053_incremental_background_universe_inventory')
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\nimport json,os,time\n\nfrom .oad_021_credentials import load_kalshi_credentials\nfrom .oad_022_rest_transport import kalshi_rest_get\n\nOAD_053_BUILD_ID="OAD-053"\nOAD_053_REVISION="OAD_053_INCREMENTAL_BACKGROUND_UNIVERSE_INVENTORY_V1"\n\n@dataclass(frozen=True)\nclass UniverseInventoryCheckpoint:\n    cursor:str\n    pages_completed:int\n    markets_seen:int\n    cycles_completed:int\n\ndef load_inventory_checkpoint(path):\n    p=Path(path)\n    if not p.is_file():\n        return UniverseInventoryCheckpoint("",0,0,0)\n    d=json.loads(p.read_text(encoding="utf-8"))\n    return UniverseInventoryCheckpoint(\n        str(d.get("cursor") or ""),\n        int(d.get("pages_completed",0)),\n        int(d.get("markets_seen",0)),\n        int(d.get("cycles_completed",0)),\n    )\n\ndef save_inventory_checkpoint(path,checkpoint):\n    p=Path(path)\n    p.parent.mkdir(parents=True,exist_ok=True)\n    tmp=p.with_suffix(p.suffix+".tmp")\n    tmp.write_text(json.dumps({\n        "cursor":checkpoint.cursor,\n        "pages_completed":checkpoint.pages_completed,\n        "markets_seen":checkpoint.markets_seen,\n        "cycles_completed":checkpoint.cycles_completed,\n    },sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\\n")\n    os.replace(tmp,p)\n\ndef run_inventory_slice(root=None,pages_per_slice=5,timeout_seconds=8,checkpoint_path=None,progress=print):\n    root=Path(root or Path.cwd()).resolve()\n    cp_path=Path(checkpoint_path or root/"runtime_state"/"kalshi_universe_inventory_checkpoint.json")\n    cp=load_inventory_checkpoint(cp_path)\n    credentials=load_kalshi_credentials(root=root)\n    cursor=cp.cursor\n    pages=cp.pages_completed\n    seen=cp.markets_seen\n    terminal=False\n\n    for _ in range(int(pages_per_slice)):\n        params={"limit":1000,"status":"open"}\n        if cursor:\n            params["cursor"]=cursor\n        progress(f"[INVENTORY] requesting_page={pages+1} markets_seen={seen}")\n        r=kalshi_rest_get(credentials,"/markets",params,timeout_seconds)\n        markets=tuple(r.body.get("markets",()))\n        seen+=len(markets)\n        pages+=1\n        nxt=str(r.body.get("cursor") or "")\n        progress(f"[INVENTORY] page={pages} received={len(markets)} markets_seen={seen}")\n        if not nxt:\n            cursor=""\n            terminal=True\n            break\n        cursor=nxt\n\n    cycles=cp.cycles_completed+(1 if terminal else 0)\n    new_cp=UniverseInventoryCheckpoint(cursor,pages,seen,cycles)\n    save_inventory_checkpoint(cp_path,new_cp)\n    return new_cp,terminal\n\ndef verify_oad_053_incremental_background_universe_inventory():\n    import tempfile\n    from pathlib import Path\n    with tempfile.TemporaryDirectory() as d:\n        p=Path(d)/"cp.json"\n        c=UniverseInventoryCheckpoint("abc",2,2000,0)\n        save_inventory_checkpoint(p,c)\n        return load_inventory_checkpoint(p)==c\n'
TEST_SOURCE='import tempfile,unittest\nfrom pathlib import Path\nfrom qseries_v2.oracle_adapters.kalshi.oad_053_background_universe_inventory import *\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_oad_053_incremental_background_universe_inventory())\n    def test_empty_checkpoint(self):\n        with tempfile.TemporaryDirectory() as d:\n            self.assertEqual(load_inventory_checkpoint(Path(d)/"none.json").markets_seen,0)\nif __name__=="__main__":\n    print("="*72);print(" OAD-053 CERTIFICATION TEST");print(" INCREMENTAL BACKGROUND UNIVERSE INVENTORY");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Checkpoint/resume background universe inventory certified")\n    print("[DONE] OAD-053 CERTIFIED")\n'
EXTRA_1='from pathlib import Path\nimport argparse,time\nfrom qseries_v2.oracle_adapters.kalshi.oad_053_background_universe_inventory import run_inventory_slice\n\ndef main():\n    p=argparse.ArgumentParser()\n    p.add_argument("--pages-per-slice",type=int,default=5)\n    p.add_argument("--sleep-seconds",type=float,default=5.0)\n    p.add_argument("--once",action="store_true")\n    a=p.parse_args()\n    root=Path.cwd()\n    print("="*72,flush=True);print(" OAD-053 BACKGROUND KALSHI UNIVERSE INVENTORY",flush=True);print("="*72,flush=True)\n    try:\n        while True:\n            cp,terminal=run_inventory_slice(root,pages_per_slice=a.pages_per_slice,progress=lambda x:print(x,flush=True))\n            print("[CHECKPOINT]",cp,flush=True)\n            if a.once:\n                return 0\n            time.sleep(a.sleep_seconds)\n    except KeyboardInterrupt:\n        print("\\n[STOP] Background universe inventory stopped by operator.",flush=True)\n        return 0\n\nif __name__=="__main__":\n    raise SystemExit(main())\n'


def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_052_dynamic_orderbook_rotation')
        if getattr(m,'verify_oad_052_dynamic_orderbook_partition_rotation')() is not True:
            raise RuntimeError("Certified upstream verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def main():
    print("="*72);print(" "+BUILD_ID+" INSTALLER");print(" "+TITLE);print("="*72)
    print("[BOOT] Revision: "+REVISION);print("[ROOT] "+str(ROOT))
    verify_upstream();print("[PASS] Certified upstream boundary verified read-only")
    affected=(MODULE,TEST,INIT,ROOT/'run_oad_053_background_universe_inventory.py')
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        write_exact(ROOT/'run_oad_053_background_universe_inventory.py',EXTRA_1)

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
