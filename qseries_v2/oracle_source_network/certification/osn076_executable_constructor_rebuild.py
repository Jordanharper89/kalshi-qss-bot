
from pathlib import Path
import ast, hashlib, json, shutil

ROOT=Path.cwd()
STATE=ROOT/"qseries_v2/oracle_source_network/state/osn076_production_surface_foundation.json"
DEST={
    "NHL":ROOT/"qseries_v2/oracle_source_network/providers/production_surfaces/nhl_proven_surface.py",
    "MLS":ROOT/"qseries_v2/oracle_source_network/providers/production_surfaces/mls_proven_surface.py",
    "EPL":ROOT/"qseries_v2/oracle_source_network/providers/production_surfaces/epl_proven_surface.py",
}
EXACT={
    "MLS":ROOT/"qseries_v2/oracle_source_network/certification/mls_official_stats_exact_query_probe.py",
    "EPL":ROOT/"qseries_v2/oracle_source_network/acquisition/epl_official_fpl_event_surface.py",
}

def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def _tree(p):
    return ast.parse(p.read_text(encoding="utf-8"), filename=str(p))

def _calls_canonical_constructor(p):
    tree=_tree(p)
    for n in ast.walk(tree):
        if not isinstance(n,ast.Call):
            continue
        f=n.func
        if isinstance(f,ast.Name) and f.id=="CanonicalSportsEvent":
            return True
        if isinstance(f,ast.Attribute) and f.attr=="CanonicalSportsEvent":
            return True
    return False

def _string_literals(p):
    vals=[]
    for n in ast.walk(_tree(p)):
        if isinstance(n,ast.Constant) and isinstance(n.value,str):
            vals.append(n.value)
    return tuple(vals)

def _discover_nhl():
    hits=[]
    root=ROOT/"qseries_v2/oracle_source_network"
    for p in root.rglob("*.py"):
        try:
            if not _calls_canonical_constructor(p):
                continue
            strings=_string_literals(p)
        except Exception:
            continue
        joined="\n".join(strings)
        if "api-web.nhle.com" not in joined:
            continue
        if "/v1/schedule/" not in joined and "/v1/schedule" not in joined:
            continue
        rel=p.relative_to(ROOT).as_posix()
        # Actual event-surface code wins over boundary/forensic files.
        score=0
        low=rel.lower()
        if "event_surface" in low: score+=30
        if "certification/" in low: score+=10
        if "acquisition/" in low: score+=10
        if "boundary" in low: score-=40
        if "forensic" in low or "probe" in low: score-=5
        hits.append((score,rel,p))
    if not hits:
        raise RuntimeError(
            "NHL executable production surface not found: current repo contains no module "
            "with both official api-web.nhle.com schedule endpoint and an actual CanonicalSportsEvent(...) call"
        )
    hits.sort(key=lambda x:(x[0],x[1]),reverse=True)
    best_score=hits[0][0]
    best=[x for x in hits if x[0]==best_score]
    if len(best)!=1:
        raise RuntimeError("NHL executable production surface ambiguous: "+repr([(x[0],x[1]) for x in best]))
    return best[0][2],[(s,r) for s,r,_ in hits]

def _verify_exact(p,league):
    if not p.exists():
        raise RuntimeError(f"{league} exact proven implementation missing: {p}")
    compile(p.read_text(encoding="utf-8"),str(p),"exec")
    if not _calls_canonical_constructor(p):
        raise RuntimeError(f"{league} exact implementation has no executable CanonicalSportsEvent constructor")
    return p

def rebuild():
    nhl,nhl_candidates=_discover_nhl()
    sources={
        "NHL":nhl,
        "MLS":_verify_exact(EXACT["MLS"],"MLS"),
        "EPL":_verify_exact(EXACT["EPL"],"EPL"),
    }
    rows=[]
    for league,src in sources.items():
        _verify_exact(src,league)
        dst=DEST[league]
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(src,dst)
        compile(dst.read_text(encoding="utf-8"),str(dst),"exec")
        if src.read_bytes()!=dst.read_bytes():
            raise RuntimeError(f"{league} byte-exact promotion failed")
        rows.append({
            "league":league,
            "source_path":src.relative_to(ROOT).as_posix(),
            "promoted_path":dst.relative_to(ROOT).as_posix(),
            "sha256":_sha(src),
            "canonical_constructor_present":True,
            "byte_exact_promotion":True,
            "execution_authority":False,
        })
        print(f"[PROMOTE] {league} {src.relative_to(ROOT)} -> {dst.relative_to(ROOT)}")
        print(f"[SHA256] {league} {_sha(src)}")
    STATE.parent.mkdir(parents=True,exist_ok=True)
    STATE.write_text(json.dumps({
        "rows":rows,
        "nhl_candidates":nhl_candidates,
        "selection_rule":"EXECUTABLE_CANONICAL_CONSTRUCTOR_PLUS_PROVEN_OFFICIAL_SURFACE",
        "execution_authority":False,
    },indent=2),encoding="utf-8")
    return rows,STATE

if __name__=="__main__":
    rows,state=rebuild()
    print("[STATE]",state.relative_to(ROOT))
    print("[PASS] promoted modules contain executable CanonicalSportsEvent construction")
    print("[PASS] NHL official schedule implementation selected by executable code, not string mention")
    print("[PASS] MLS exact repaired source retained")
    print("[PASS] EPL exact FPL source retained")
    print("[PASS] execution_authority=FALSE")
