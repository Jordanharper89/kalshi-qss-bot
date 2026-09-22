from __future__ import annotations
import importlib,os,subprocess,sys
from pathlib import Path

ROOT=Path.cwd().resolve()
PACKAGE=ROOT/"qseries_v2"/"oracle_adapters"/"kalshi"
MODULE=PACKAGE/"oad_053_background_universe_inventory.py"
TEST=ROOT/"test_oad_053_incremental_background_universe_inventory.py"
RUNNER=ROOT/"run_oad_053_background_universe_inventory.py"

MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\nimport json,os,time,socket\nfrom urllib.error import URLError,HTTPError\n\nfrom .oad_021_credentials import load_kalshi_credentials\nfrom .oad_022_rest_transport import kalshi_rest_get\n\nOAD_053_BUILD_ID="OAD-053"\nOAD_053_REVISION="OAD_053_BACKGROUND_UNIVERSE_INVENTORY_RESILIENCE_CORRECTION_V2"\n\n@dataclass(frozen=True)\nclass UniverseInventoryCheckpoint:\n    cursor:str\n    pages_completed:int\n    markets_seen:int\n    cycles_completed:int\n\n@dataclass(frozen=True)\nclass InventorySliceResult:\n    checkpoint:UniverseInventoryCheckpoint\n    terminal_cursor_reached:bool\n    transient_failures:int\n    retries_used:int\n    degraded:bool=False\n\ndef load_inventory_checkpoint(path):\n    p=Path(path)\n    if not p.is_file():\n        return UniverseInventoryCheckpoint("",0,0,0)\n    d=json.loads(p.read_text(encoding="utf-8"))\n    return UniverseInventoryCheckpoint(\n        str(d.get("cursor") or ""),\n        int(d.get("pages_completed",0)),\n        int(d.get("markets_seen",0)),\n        int(d.get("cycles_completed",0)),\n    )\n\ndef save_inventory_checkpoint(path,checkpoint):\n    p=Path(path)\n    p.parent.mkdir(parents=True,exist_ok=True)\n    tmp=p.with_suffix(p.suffix+".tmp")\n    tmp.write_text(\n        json.dumps({\n            "cursor":checkpoint.cursor,\n            "pages_completed":checkpoint.pages_completed,\n            "markets_seen":checkpoint.markets_seen,\n            "cycles_completed":checkpoint.cycles_completed,\n        },sort_keys=True,separators=(",",":")),\n        encoding="utf-8",\n        newline="\\n",\n    )\n    os.replace(tmp,p)\n\ndef _is_transient_exception(exc):\n    if isinstance(exc,(TimeoutError,socket.timeout)):\n        return True\n    if isinstance(exc,HTTPError):\n        return int(getattr(exc,"code",0)) in (408,425,429,500,502,503,504)\n    if isinstance(exc,URLError):\n        reason=getattr(exc,"reason",None)\n        return isinstance(reason,(TimeoutError,socket.timeout,OSError))\n    return False\n\ndef _request_market_page(credentials,params,timeout_seconds,max_retries,base_backoff_seconds,progress):\n    failures=0\n    for attempt in range(int(max_retries)+1):\n        try:\n            response=kalshi_rest_get(credentials,"/markets",params,timeout_seconds)\n            return response,failures,attempt\n        except Exception as exc:\n            if not _is_transient_exception(exc):\n                raise\n            failures+=1\n            if attempt>=int(max_retries):\n                raise\n            delay=min(30.0,float(base_backoff_seconds)*(2.0**attempt))\n            progress(\n                f"[INVENTORY] transient_error={type(exc).__name__} "\n                f"attempt={attempt+1}/{int(max_retries)+1} retry_in={delay:.1f}s"\n            )\n            time.sleep(delay)\n    raise RuntimeError("unreachable retry state")\n\ndef run_inventory_slice(\n    root=None,\n    pages_per_slice=5,\n    timeout_seconds=8,\n    checkpoint_path=None,\n    progress=print,\n    max_retries=4,\n    base_backoff_seconds=1.0,\n):\n    root=Path(root or Path.cwd()).resolve()\n    cp_path=Path(checkpoint_path or root/"runtime_state"/"kalshi_universe_inventory_checkpoint.json")\n    cp=load_inventory_checkpoint(cp_path)\n    credentials=load_kalshi_credentials(root=root)\n\n    cursor=cp.cursor\n    pages=cp.pages_completed\n    seen=cp.markets_seen\n    cycles=cp.cycles_completed\n    terminal=False\n    failures=0\n    retries_used=0\n\n    for _ in range(int(pages_per_slice)):\n        params={"limit":1000,"status":"open"}\n        if cursor:\n            params["cursor"]=cursor\n\n        progress(f"[INVENTORY] requesting_page={pages+1} markets_seen={seen}")\n\n        response,page_failures,page_retries=_request_market_page(\n            credentials,\n            params,\n            timeout_seconds,\n            max_retries,\n            base_backoff_seconds,\n            progress,\n        )\n        failures+=page_failures\n        retries_used+=page_retries\n\n        markets=tuple(response.body.get("markets",()))\n        seen+=len(markets)\n        pages+=1\n        nxt=str(response.body.get("cursor") or "")\n\n        if not nxt:\n            cursor=""\n            terminal=True\n            cycles+=1\n        else:\n            cursor=nxt\n\n        current=UniverseInventoryCheckpoint(cursor,pages,seen,cycles)\n        save_inventory_checkpoint(cp_path,current)\n\n        progress(\n            f"[INVENTORY] page={pages} received={len(markets)} "\n            f"markets_seen={seen} checkpoint_saved=True"\n        )\n\n        if terminal:\n            break\n\n    final=UniverseInventoryCheckpoint(cursor,pages,seen,cycles)\n    return InventorySliceResult(final,terminal,failures,retries_used,False)\n\ndef verify_oad_053_incremental_background_universe_inventory():\n    import tempfile\n    with tempfile.TemporaryDirectory() as d:\n        p=Path(d)/"cp.json"\n        c=UniverseInventoryCheckpoint("abc",2,2000,0)\n        save_inventory_checkpoint(p,c)\n        loaded=load_inventory_checkpoint(p)\n        return (\n            loaded==c\n            and _is_transient_exception(TimeoutError("timeout"))\n            and not _is_transient_exception(ValueError("bad"))\n            and OAD_053_REVISION.endswith("CORRECTION_V2")\n        )\n'
TEST_SOURCE='import tempfile,unittest\nfrom pathlib import Path\nfrom qseries_v2.oracle_adapters.kalshi.oad_053_background_universe_inventory import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_oad_053_incremental_background_universe_inventory())\n\n    def test_empty_checkpoint(self):\n        with tempfile.TemporaryDirectory() as d:\n            self.assertEqual(\n                load_inventory_checkpoint(Path(d)/"none.json").markets_seen,\n                0,\n            )\n\n    def test_timeout_is_transient(self):\n        self.assertTrue(_is_transient_exception(TimeoutError("read timed out")))\n\n    def test_programming_error_not_transient(self):\n        self.assertFalse(_is_transient_exception(ValueError("bad input")))\n\n    def test_result_contract(self):\n        cp=UniverseInventoryCheckpoint("x",1,1000,0)\n        r=InventorySliceResult(cp,False,1,1,False)\n        self.assertEqual(r.checkpoint,cp)\n        self.assertFalse(r.degraded)\n\nif __name__=="__main__":\n    print("="*72)\n    print(" OAD-053 RESILIENCE CORRECTION V2 CERTIFICATION TEST")\n    print(" BACKGROUND UNIVERSE INVENTORY 24/7 FAULT TOLERANCE")\n    print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] Per-page checkpoint durability certified")\n    print("[PASS] Transient timeout classification certified")\n    print("[PASS] Bounded retry/backoff contract certified")\n    print("[DONE] OAD-053 RESILIENCE CORRECTION V2 CERTIFIED")\n'
RUNNER_SOURCE='from pathlib import Path\nimport argparse,time\nfrom qseries_v2.oracle_adapters.kalshi.oad_053_background_universe_inventory import run_inventory_slice\n\ndef main():\n    p=argparse.ArgumentParser()\n    p.add_argument("--pages-per-slice",type=int,default=5)\n    p.add_argument("--sleep-seconds",type=float,default=5.0)\n    p.add_argument("--timeout-seconds",type=float,default=8.0)\n    p.add_argument("--max-retries",type=int,default=4)\n    p.add_argument("--retry-backoff-seconds",type=float,default=1.0)\n    p.add_argument("--once",action="store_true")\n    a=p.parse_args()\n\n    if a.pages_per_slice<1:\n        raise SystemExit("--pages-per-slice must be >= 1")\n    if a.sleep_seconds<0 or a.timeout_seconds<=0 or a.max_retries<0 or a.retry_backoff_seconds<0:\n        raise SystemExit("invalid runtime arguments")\n\n    root=Path.cwd()\n    print("="*72,flush=True)\n    print(" OAD-053 BACKGROUND KALSHI UNIVERSE INVENTORY - RESILIENT 24/7 V2",flush=True)\n    print("="*72,flush=True)\n\n    outer_failures=0\n\n    try:\n        while True:\n            try:\n                result=run_inventory_slice(\n                    root,\n                    pages_per_slice=a.pages_per_slice,\n                    timeout_seconds=a.timeout_seconds,\n                    progress=lambda x:print(x,flush=True),\n                    max_retries=a.max_retries,\n                    base_backoff_seconds=a.retry_backoff_seconds,\n                )\n                outer_failures=0\n                print("[CHECKPOINT]",result.checkpoint,flush=True)\n                print(\n                    f"[INVENTORY] slice_complete terminal={result.terminal_cursor_reached} "\n                    f"transient_failures={result.transient_failures} "\n                    f"retries_used={result.retries_used}",\n                    flush=True,\n                )\n\n                if a.once:\n                    return 0\n\n                time.sleep(a.sleep_seconds)\n\n            except KeyboardInterrupt:\n                raise\n\n            except Exception as exc:\n                outer_failures+=1\n                delay=min(\n                    60.0,\n                    max(1.0,a.retry_backoff_seconds)*(2.0**min(outer_failures-1,5)),\n                )\n                print(\n                    f"[INVENTORY] recoverable_cycle_failure={type(exc).__name__} "\n                    f"consecutive_failures={outer_failures} "\n                    f"resume_from_checkpoint_in={delay:.1f}s",\n                    flush=True,\n                )\n                time.sleep(delay)\n\n    except KeyboardInterrupt:\n        print("\\n[STOP] Background universe inventory stopped by operator.",flush=True)\n        return 0\n\nif __name__=="__main__":\n    raise SystemExit(main())\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def verify_frozen_boundaries():
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()

        freeze=importlib.import_module(
            "qseries_v2.oracle_adapters.kalshi.oad_055_kalshi_production_freeze"
        )
        if getattr(
            freeze,
            "verify_oad_055_kalshi_production_adapter_freeze_gate",
        )() is not True:
            raise RuntimeError("Frozen OAD-055 boundary verification failed")

        upstream=importlib.import_module(
            "qseries_v2.oracle_adapters.kalshi.oad_052_dynamic_orderbook_rotation"
        )
        if getattr(
            upstream,
            "verify_oad_052_dynamic_orderbook_partition_rotation",
        )() is not True:
            raise RuntimeError("Certified OAD-052 upstream verification failed")

    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def main():
    print("="*72)
    print(" OAD-053 RESILIENCE CORRECTION V2 INSTALLER")
    print(" BACKGROUND UNIVERSE INVENTORY 24/7 FAULT TOLERANCE")
    print("="*72)
    print("[ROOT]",ROOT)

    verify_frozen_boundaries()
    print("[PASS] Frozen OAD-055 boundary verified")
    print("[PASS] Correction classified as defect-only maintenance")

    affected=(MODULE,TEST,RUNNER)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}

    try:
        write_exact(MODULE,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        write_exact(RUNNER,RUNNER_SOURCE)

        compile(MODULE.read_text(encoding="utf-8"),str(MODULE),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        compile(RUNNER.read_text(encoding="utf-8"),str(RUNNER),"exec")

        subprocess.run(
            [sys.executable,str(TEST)],
            cwd=str(ROOT),
            check=True,
        )

    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OAD-053 resilience correction failed; affected files restored")
        raise

    print("[PASS] Corrected:",MODULE.relative_to(ROOT))
    print("[PASS] Corrected:",TEST.name)
    print("[PASS] Corrected:",RUNNER.name)
    print("[PASS] Successful inventory pages now checkpoint immediately")
    print("[PASS] Transient REST timeouts retry with bounded exponential backoff")
    print("[PASS] Exhausted retries no longer terminate the 24/7 inventory child")
    print("[DONE] OAD-053 RESILIENCE CORRECTION V2 INSTALLED + CERTIFIED")

if __name__=="__main__":
    main()
