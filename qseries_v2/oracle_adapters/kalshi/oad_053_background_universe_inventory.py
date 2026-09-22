from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json,os,time,socket
from urllib.error import URLError,HTTPError
from .oad_021_credentials import load_kalshi_credentials
from .oad_022_rest_transport import kalshi_rest_get

OAD_053_BUILD_ID="OAD-053"
OAD_053_REVISION="OAD_053_BACKGROUND_UNIVERSE_INVENTORY_ACTIVE_SEMANTICS_RECERTIFIED"

@dataclass(frozen=True)
class UniverseInventoryCheckpoint:
    cursor:str; pages_completed:int; markets_seen:int; cycles_completed:int
@dataclass(frozen=True)
class InventorySliceResult:
    checkpoint:UniverseInventoryCheckpoint; terminal_cursor_reached:bool; transient_failures:int; retries_used:int; degraded:bool=False

def load_inventory_checkpoint(path):
    p=Path(path)
    if not p.is_file(): return UniverseInventoryCheckpoint("",0,0,0)
    d=json.loads(p.read_text(encoding="utf-8"))
    return UniverseInventoryCheckpoint(str(d.get("cursor") or ""),int(d.get("pages_completed",0)),int(d.get("markets_seen",0)),int(d.get("cycles_completed",0)))
def save_inventory_checkpoint(path,checkpoint):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+".tmp")
    tmp.write_text(json.dumps({"cursor":checkpoint.cursor,"pages_completed":checkpoint.pages_completed,"markets_seen":checkpoint.markets_seen,"cycles_completed":checkpoint.cycles_completed},sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\n");os.replace(tmp,p)
def is_transient_inventory_exception(exc):
    if isinstance(exc,(TimeoutError,socket.timeout)): return True
    if isinstance(exc,HTTPError): return int(getattr(exc,"code",0)) in (408,425,429,500,502,503,504)
    if isinstance(exc,URLError): return isinstance(getattr(exc,"reason",None),(TimeoutError,socket.timeout,OSError))
    return False
def _request_market_page(credentials,params,timeout_seconds,max_retries,base_backoff_seconds,progress):
    failures=0
    for attempt in range(int(max_retries)+1):
        try: return kalshi_rest_get(credentials,"/markets",params,timeout_seconds),failures,attempt
        except Exception as exc:
            if not is_transient_inventory_exception(exc): raise
            failures+=1
            if attempt>=int(max_retries): raise
            delay=min(30.0,float(base_backoff_seconds)*(2.0**attempt));progress(f"[INVENTORY] transient_error={type(exc).__name__} attempt={attempt+1}/{int(max_retries)+1} retry_in={delay:.1f}s");time.sleep(delay)
    raise RuntimeError("unreachable retry state")
def run_inventory_slice(root=None,pages_per_slice=5,timeout_seconds=8,checkpoint_path=None,progress=print,max_retries=4,base_backoff_seconds=1.0):
    root=Path(root or Path.cwd()).resolve();cp_path=Path(checkpoint_path or root/"runtime_state"/"kalshi_universe_inventory_checkpoint.json");cp=load_inventory_checkpoint(cp_path);credentials=load_kalshi_credentials(root=root)
    cursor=cp.cursor;pages=cp.pages_completed;seen=cp.markets_seen;cycles=cp.cycles_completed;terminal=False;failures=0;retries_used=0
    for _ in range(int(pages_per_slice)):
        params={"limit":1000}
        if cursor: params["cursor"]=cursor
        progress(f"[INVENTORY] requesting_page={pages+1} markets_seen={seen}")
        response,pf,pr=_request_market_page(credentials,params,timeout_seconds,max_retries,base_backoff_seconds,progress);failures+=pf;retries_used+=pr
        markets=tuple(response.body.get("markets",()) or ());active=sum(1 for m in markets if str(m.get("status") or "").strip().lower()=="active")
        seen+=len(markets);pages+=1;nxt=str(response.body.get("cursor") or "")
        if not nxt: cursor="";terminal=True;cycles+=1
        else: cursor=nxt
        current=UniverseInventoryCheckpoint(cursor,pages,seen,cycles);save_inventory_checkpoint(cp_path,current)
        progress(f"[INVENTORY] page={pages} received={len(markets)} active={active} markets_seen={seen} checkpoint_saved=True")
        if terminal: break
    return InventorySliceResult(UniverseInventoryCheckpoint(cursor,pages,seen,cycles),terminal,failures,retries_used,False)
def verify_oad_053_incremental_background_universe_inventory():
    import inspect,tempfile
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/"cp.json";c=UniverseInventoryCheckpoint("abc",2,2000,0);save_inventory_checkpoint(p,c)
        src=inspect.getsource(run_inventory_slice)
        return load_inventory_checkpoint(p)==c and '"status":"open"' not in src and is_transient_inventory_exception(TimeoutError("timeout"))
