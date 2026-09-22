
from dataclasses import dataclass
from pathlib import Path
import ast, importlib.util, inspect, sys

ADMITTED=("NFL","NCAAF","NBA","NHL","MLS","EPL")
PROMOTED={
 "NHL":"qseries_v2/oracle_source_network/providers/production_surfaces/nhl_proven_surface.py",
 "MLS":"qseries_v2/oracle_source_network/providers/production_surfaces/mls_proven_surface.py",
 "EPL":"qseries_v2/oracle_source_network/providers/production_surfaces/epl_proven_surface.py",
}

@dataclass(frozen=True)
class CanonicalProviderResult:
    league:str
    events:tuple
    event_count:int
    authority:str
    callable_name:str
    execution_authority:bool=False

def _is_event(x):
    try:
        from qseries_v2.oracle_source_network.canonical.sports_event_v2 import CanonicalSportsEvent
        return isinstance(x,CanonicalSportsEvent)
    except Exception:
        return False

def _collect(value,depth=0):
    if depth>8 or value is None: return ()
    if _is_event(value): return (value,)
    if isinstance(value,(list,tuple,set)):
        out=[]
        for x in value: out.extend(_collect(x,depth+1))
        return tuple(out)
    if isinstance(value,dict):
        out=[]
        for x in value.values(): out.extend(_collect(x,depth+1))
        return tuple(out)
    for attr in ("events","games","fixtures","matches","rows","data","result","schedule"):
        if hasattr(value,attr):
            got=_collect(getattr(value,attr),depth+1)
            if got: return got
    return ()

def _body(raw):
    if isinstance(raw,(str,bytes,bytearray)): return raw
    if isinstance(raw,dict):
        for k in ("body","raw","html","text","content","payload"):
            if isinstance(raw.get(k),(str,bytes,bytearray)): return raw[k]
    for k in ("body","raw","html","text","content","payload"):
        if hasattr(raw,k) and isinstance(getattr(raw,k),(str,bytes,bytearray)): return getattr(raw,k)
    raise RuntimeError("acquisition return has no exact text body")

def _legacy(league,timeout):
    if league=="NFL":
        from qseries_v2.oracle_source_network.acquisition.nfl_official_live import acquire_nfl_scores
        from qseries_v2.oracle_source_network.mapping.nfl_live_escaped_state_extractor import extract_nfl_live_events
        v=extract_nfl_live_events(_body(acquire_nfl_scores(timeout=timeout)))
        name="acquire_nfl_scores -> extract_nfl_live_events"
    elif league=="NCAAF":
        from qseries_v2.oracle_source_network.acquisition.ncaa_football_official_live import acquire_ncaa_fbs_scoreboard
        from qseries_v2.oracle_source_network.mapping.ncaaf_exact_scoreboard_extractor import extract_ncaaf_live_events
        v=extract_ncaaf_live_events(_body(acquire_ncaa_fbs_scoreboard(timeout=timeout)))
        name="acquire_ncaa_fbs_scoreboard -> extract_ncaaf_live_events"
    elif league=="NBA":
        from qseries_v2.oracle_source_network.acquisition.nba_official_live import acquire_nba_games
        from qseries_v2.oracle_source_network.mapping.basketball_event_extractor import extract_basketball_events
        v=extract_basketball_events(_body(acquire_nba_games(timeout=timeout)),"NBA","nba_official")
        name="acquire_nba_games -> extract_basketball_events"
    else: raise RuntimeError(league)
    ev=_collect(v)
    if not ev: raise RuntimeError(f"{league} direct chain returned zero canonical events")
    return CanonicalProviderResult(league,ev,len(ev),"EXACT_DIRECT_SOURCE_EXTRACTOR",name)

def _functions_with_constructor(path):
    tree=ast.parse(path.read_text(encoding="utf-8"),filename=str(path))
    parents={}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child]=node
    direct=set()
    defs={}
    for n in ast.walk(tree):
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
            defs[n.name]=n
    for n in ast.walk(tree):
        if not isinstance(n,ast.Call): continue
        f=n.func
        is_ctor=(isinstance(f,ast.Name) and f.id=="CanonicalSportsEvent") or (isinstance(f,ast.Attribute) and f.attr=="CanonicalSportsEvent")
        if not is_ctor: continue
        cur=n
        while cur in parents:
            cur=parents[cur]
            if isinstance(cur,(ast.FunctionDef,ast.AsyncFunctionDef)):
                direct.add(cur.name); break
    # Include zero-arg/optional-only functions that call a constructor-bearing helper.
    changed=True
    related=set(direct)
    while changed:
        changed=False
        for name,node in defs.items():
            if name in related: continue
            called=set()
            for c in ast.walk(node):
                if isinstance(c,ast.Call) and isinstance(c.func,ast.Name):
                    called.add(c.func.id)
            if called & related:
                related.add(name); changed=True
    return related

def _load(path,league):
    name=f"_osn_prod_{league.lower()}"
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec)
    sys.modules[name]=mod
    spec.loader.exec_module(mod)
    return mod

def _invoke_candidate(fn,timeout):
    sig=inspect.signature(fn)
    kwargs={}
    for p in sig.parameters.values():
        if p.kind in (p.VAR_POSITIONAL,p.VAR_KEYWORD): continue
        if p.default is inspect._empty:
            # We do not guess required business parameters.
            return None
        if p.name=="timeout": kwargs[p.name]=timeout
    return fn(**kwargs)

def _promoted(league,timeout,root):
    base=Path(root or Path.cwd())
    path=base/PROMOTED[league]
    if not path.exists(): raise RuntimeError(f"{league} promoted module missing: {path}")
    related=_functions_with_constructor(path)
    mod=_load(path,league)
    candidates=[]
    for name in related:
        fn=getattr(mod,name,None)
        if not callable(fn): continue
        sig=inspect.signature(fn)
        required=[p.name for p in sig.parameters.values()
                  if p.kind not in (p.VAR_POSITIONAL,p.VAR_KEYWORD)
                  and p.default is inspect._empty]
        if required: continue
        # Prefer explicit acquisition/extraction/run functions over main.
        score=0
        low=name.lower()
        if any(x in low for x in ("acquire","fetch","extract","events","schedule","fixtures","run")): score+=20
        if low=="main": score-=10
        candidates.append((score,name,fn))
    candidates.sort(key=lambda x:(x[0],x[1]),reverse=True)
    diagnostics=[]
    for _,name,fn in candidates:
        try:
            value=_invoke_candidate(fn,timeout)
            ev=_collect(value)
            diagnostics.append((name,len(ev),"RETURN"))
            if ev:
                return CanonicalProviderResult(
                    league,ev,len(ev),
                    "PROMOTED_EXECUTABLE_CANONICAL_ENTRYPOINT",name
                )
        except Exception as exc:
            diagnostics.append((name,0,f"{type(exc).__name__}:{exc}"))

    # Some proven surfaces build canonical events internally and return report objects.
    # Capture only the canonical constructor while calling an actual promoted function.
    canonical_mod=sys.modules.get("qseries_v2.oracle_source_network.canonical.sports_event_v2")
    if canonical_mod is None:
        import qseries_v2.oracle_source_network.canonical.sports_event_v2 as canonical_mod
    original=canonical_mod.CanonicalSportsEvent
    for _,name,fn in candidates:
        captured=[]
        def capture(*a,**kw):
            ev=original(*a,**kw); captured.append(ev); return ev
        canonical_mod.CanonicalSportsEvent=capture
        # Also patch imported class reference in the promoted module if present.
        had=hasattr(mod,"CanonicalSportsEvent")
        prior=getattr(mod,"CanonicalSportsEvent",None)
        if had: setattr(mod,"CanonicalSportsEvent",capture)
        try:
            _invoke_candidate(fn,timeout)
        except Exception as exc:
            diagnostics.append((name,len(captured),f"CAPTURE:{type(exc).__name__}:{exc}"))
        finally:
            canonical_mod.CanonicalSportsEvent=original
            if had: setattr(mod,"CanonicalSportsEvent",prior)
        if captured:
            # dedupe provider identity
            out=[]; seen=set()
            for ev in captured:
                key=getattr(ev,"canonical_event_id",None) or getattr(ev,"provider_event_id",None) or repr(ev)
                if key in seen: continue
                seen.add(key); out.append(ev)
            return CanonicalProviderResult(
                league,tuple(out),len(out),
                "PROMOTED_EXECUTABLE_CANONICAL_ENTRYPOINT_CAPTURE",name
            )
    raise RuntimeError(f"{league} no executable promoted function produced canonical events; diagnostics={diagnostics}")

def acquire_canonical_events(league,timeout=15,root=None):
    league=str(league).upper()
    if league not in ADMITTED: raise RuntimeError(f"league not admitted: {league}")
    if league in ("NFL","NCAAF","NBA"): return _legacy(league,timeout)
    return _promoted(league,timeout,root)
