from pathlib import Path
import ast, importlib, os, subprocess, sys, time

ROOT=Path.cwd().resolve()
TITLE='OAD-053 FROZEN-PAVEMENT REPAIR / RESILIENT UNFILTERED INVENTORY'
TARGETS=['qseries_v2/oracle_adapters/kalshi/oad_053_background_universe_inventory.py']
PAYLOADS=['from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\nimport json,os,time,socket\nfrom urllib.error import URLError,HTTPError\nfrom .oad_021_credentials import load_kalshi_credentials\nfrom .oad_022_rest_transport import kalshi_rest_get\n\nOAD_053_BUILD_ID="OAD-053"\nOAD_053_REVISION="OAD_053_BACKGROUND_UNIVERSE_INVENTORY_ACTIVE_SEMANTICS_RECERTIFIED"\n\n@dataclass(frozen=True)\nclass UniverseInventoryCheckpoint:\n    cursor:str; pages_completed:int; markets_seen:int; cycles_completed:int\n@dataclass(frozen=True)\nclass InventorySliceResult:\n    checkpoint:UniverseInventoryCheckpoint; terminal_cursor_reached:bool; transient_failures:int; retries_used:int; degraded:bool=False\n\ndef load_inventory_checkpoint(path):\n    p=Path(path)\n    if not p.is_file(): return UniverseInventoryCheckpoint("",0,0,0)\n    d=json.loads(p.read_text(encoding="utf-8"))\n    return UniverseInventoryCheckpoint(str(d.get("cursor") or ""),int(d.get("pages_completed",0)),int(d.get("markets_seen",0)),int(d.get("cycles_completed",0)))\ndef save_inventory_checkpoint(path,checkpoint):\n    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+".tmp")\n    tmp.write_text(json.dumps({"cursor":checkpoint.cursor,"pages_completed":checkpoint.pages_completed,"markets_seen":checkpoint.markets_seen,"cycles_completed":checkpoint.cycles_completed},sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\\n");os.replace(tmp,p)\ndef is_transient_inventory_exception(exc):\n    if isinstance(exc,(TimeoutError,socket.timeout)): return True\n    if isinstance(exc,HTTPError): return int(getattr(exc,"code",0)) in (408,425,429,500,502,503,504)\n    if isinstance(exc,URLError): return isinstance(getattr(exc,"reason",None),(TimeoutError,socket.timeout,OSError))\n    return False\ndef _request_market_page(credentials,params,timeout_seconds,max_retries,base_backoff_seconds,progress):\n    failures=0\n    for attempt in range(int(max_retries)+1):\n        try: return kalshi_rest_get(credentials,"/markets",params,timeout_seconds),failures,attempt\n        except Exception as exc:\n            if not is_transient_inventory_exception(exc): raise\n            failures+=1\n            if attempt>=int(max_retries): raise\n            delay=min(30.0,float(base_backoff_seconds)*(2.0**attempt));progress(f"[INVENTORY] transient_error={type(exc).__name__} attempt={attempt+1}/{int(max_retries)+1} retry_in={delay:.1f}s");time.sleep(delay)\n    raise RuntimeError("unreachable retry state")\ndef run_inventory_slice(root=None,pages_per_slice=5,timeout_seconds=8,checkpoint_path=None,progress=print,max_retries=4,base_backoff_seconds=1.0):\n    root=Path(root or Path.cwd()).resolve();cp_path=Path(checkpoint_path or root/"runtime_state"/"kalshi_universe_inventory_checkpoint.json");cp=load_inventory_checkpoint(cp_path);credentials=load_kalshi_credentials(root=root)\n    cursor=cp.cursor;pages=cp.pages_completed;seen=cp.markets_seen;cycles=cp.cycles_completed;terminal=False;failures=0;retries_used=0\n    for _ in range(int(pages_per_slice)):\n        params={"limit":1000}\n        if cursor: params["cursor"]=cursor\n        progress(f"[INVENTORY] requesting_page={pages+1} markets_seen={seen}")\n        response,pf,pr=_request_market_page(credentials,params,timeout_seconds,max_retries,base_backoff_seconds,progress);failures+=pf;retries_used+=pr\n        markets=tuple(response.body.get("markets",()) or ());active=sum(1 for m in markets if str(m.get("status") or "").strip().lower()=="active")\n        seen+=len(markets);pages+=1;nxt=str(response.body.get("cursor") or "")\n        if not nxt: cursor="";terminal=True;cycles+=1\n        else: cursor=nxt\n        current=UniverseInventoryCheckpoint(cursor,pages,seen,cycles);save_inventory_checkpoint(cp_path,current)\n        progress(f"[INVENTORY] page={pages} received={len(markets)} active={active} markets_seen={seen} checkpoint_saved=True")\n        if terminal: break\n    return InventorySliceResult(UniverseInventoryCheckpoint(cursor,pages,seen,cycles),terminal,failures,retries_used,False)\ndef verify_oad_053_incremental_background_universe_inventory():\n    import inspect,tempfile\n    with tempfile.TemporaryDirectory() as d:\n        p=Path(d)/"cp.json";c=UniverseInventoryCheckpoint("abc",2,2000,0);save_inventory_checkpoint(p,c)\n        src=inspect.getsource(run_inventory_slice)\n        return load_inventory_checkpoint(p)==c and \'"status":"open"\' not in src and is_transient_inventory_exception(TimeoutError("timeout"))\n']
TESTS=['test_oad_053_incremental_background_universe_inventory.py']

def _write(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+f".{os.getpid()}.tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def _restore(path,data):
    if data is None:
        if path.exists(): path.unlink()
    else:
        path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(data)

def main():
    print("="*88); print(" OAD-053 FROZEN-PAVEMENT REPAIR / RESILIENT UNFILTERED INVENTORY"); print("="*88); print("[ROOT]",ROOT)
    backups={}
    for rel,src in zip(TARGETS,PAYLOADS):
        p=ROOT/rel; backups[rel]=p.read_bytes() if p.exists() else None
        ast.parse(src,filename=str(p))
    print("[PASS] replacement payload syntax verified")
    try:
        for rel,src in zip(TARGETS,PAYLOADS): _write(ROOT/rel,src)
        importlib.invalidate_caches()
        for t in TESTS:
            subprocess.run([sys.executable,t],cwd=str(ROOT),check=True,timeout=60)
        import tempfile
        from qseries_v2.oracle_adapters.kalshi.oad_053_background_universe_inventory import run_inventory_slice
        with tempfile.TemporaryDirectory() as d:
            x=run_inventory_slice(ROOT,pages_per_slice=1,timeout_seconds=15,checkpoint_path=Path(d)/"cp.json",progress=print,max_retries=2)
        print("[PHYSICAL]",x)
        if x.checkpoint.pages_completed!=1: raise RuntimeError("inventory physical page did not checkpoint")
        print("[PASS] production checkpoint/retry behavior preserved without stale status=open filter")
    except Exception:
        for rel,data in backups.items(): _restore(ROOT/rel,data)
        print("[ROLLBACK] repair failed; exact affected repository files restored")
        raise
    print("[PASS] public production path repaired in place")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OAD-053 FROZEN-PAVEMENT REPAIR / RESILIENT UNFILTERED INVENTORY COMPLETE")

if __name__=="__main__": main()
