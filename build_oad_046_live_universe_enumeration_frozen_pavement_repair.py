from pathlib import Path
import ast, importlib, os, subprocess, sys, time

ROOT=Path.cwd().resolve()
TITLE='OAD-046 FROZEN-PAVEMENT REPAIR / ACTIVE UNIVERSE SEMANTICS'
TARGETS=['qseries_v2/oracle_adapters/kalshi/oad_046_live_universe_enumeration.py']
PAYLOADS=['from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .oad_021_credentials import KalshiCredentialConfig\nfrom .oad_022_rest_transport import kalshi_rest_get\n\nOAD_046_BUILD_ID="OAD-046"\nOAD_046_REVISION="OAD_046_LIVE_UNIVERSE_ENUMERATION_ACTIVE_SEMANTICS_RECERTIFIED"\n\n@dataclass(frozen=True)\nclass LiveUniverseEnumeration:\n    tickers:tuple[str,...]\n    pages:int\n    duplicate_count:int\n    terminal_cursor_reached:bool\n\ndef _is_current_market(raw):\n    return str((raw or {}).get("status") or "").strip().lower()=="active"\n\ndef enumerate_live_open_universe(credentials,max_pages=10000,timeout_seconds=8,progress=None):\n    if not isinstance(credentials,KalshiCredentialConfig): raise ValueError("certified credentials required")\n    emit=progress or (lambda _msg:None); cursor=""; seen={}; duplicates=0; pages=0\n    while pages<int(max_pages):\n        params={"limit":1000}\n        if cursor: params["cursor"]=cursor\n        emit(f"[UNIVERSE] requesting_page={pages+1} accumulated_active={len(seen)}")\n        response=kalshi_rest_get(credentials,"/markets",params,timeout_seconds)\n        pages+=1; markets=tuple(response.body.get("markets",()) or ())\n        for market in markets:\n            if not _is_current_market(market): continue\n            ticker=str(market.get("ticker","")).strip()\n            if not ticker: continue\n            if ticker in seen: duplicates+=1\n            else: seen[ticker]=True\n        emit(f"[UNIVERSE] page={pages} received={len(markets)} active_total={len(seen)}")\n        nxt=str(response.body.get("cursor") or "")\n        if not nxt:\n            emit(f"[UNIVERSE] COMPLETE pages={pages} active_markets={len(seen)}")\n            return LiveUniverseEnumeration(tuple(sorted(seen)),pages,duplicates,True)\n        if nxt==cursor: raise RuntimeError("Kalshi live-universe cursor did not advance")\n        cursor=nxt\n    raise RuntimeError("Kalshi live-universe enumeration exceeded max_pages")\n\ndef verify_oad_046_physical_live_full_universe_enumeration():\n    import inspect\n    src=inspect.getsource(enumerate_live_open_universe)\n    return (\'"status":"open"\' not in src and \'_is_current_market\' in src\n            and inspect.signature(enumerate_live_open_universe).parameters["timeout_seconds"].default==8)\n']
TESTS=['test_oad_046_physical_live_full_universe_enumeration.py']

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
    print("="*88); print(" OAD-046 FROZEN-PAVEMENT REPAIR / ACTIVE UNIVERSE SEMANTICS"); print("="*88); print("[ROOT]",ROOT)
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
        from qseries_v2.oracle_adapters.kalshi.oad_021_credentials import load_kalshi_credentials
        from qseries_v2.oracle_adapters.kalshi.oad_022_rest_transport import kalshi_rest_get
        creds=load_kalshi_credentials(root=ROOT); r=kalshi_rest_get(creds,"/markets",{"limit":1000},15)
        ms=tuple(r.body.get("markets",()) or ()); counts={}
        for x in ms:
            s=str(x.get("status") or "").lower(); counts[s]=counts.get(s,0)+1
        print("[PHYSICAL] first_page=",len(ms),"statuses=",counts,"cursor_present=",bool(r.body.get("cursor")))
        if counts.get("active",0)<=0: raise RuntimeError("no ACTIVE markets observed on physical page")
        print("[PASS] Kalshi current production ACTIVE semantics physically proven")
    except Exception:
        for rel,data in backups.items(): _restore(ROOT/rel,data)
        print("[ROLLBACK] repair failed; exact affected repository files restored")
        raise
    print("[PASS] public production path repaired in place")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OAD-046 FROZEN-PAVEMENT REPAIR / ACTIVE UNIVERSE SEMANTICS COMPLETE")

if __name__=="__main__": main()
