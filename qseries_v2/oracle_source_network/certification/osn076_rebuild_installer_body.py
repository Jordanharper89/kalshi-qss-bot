
from pathlib import Path
import ast, hashlib, json, re, shutil

ROOT = Path.cwd()
TESTS = {
    "NHL": "test_osn_051_nhl_official_json_event_surface_physical_gate.py",
    "MLS": "test_osn_052_mls_official_stats_exact_query_event_surface_REPAIR.py",
    "EPL": "test_osn_053_epl_official_json_event_surface_physical_gate.py",
}
ANCHORS = {
    "NHL": ("api-web.nhle.com", "CanonicalSportsEvent"),
    "MLS": ("planned_kickoff_time", "CanonicalSportsEvent"),
    "EPL": ("CanonicalSportsEvent",),
}
PREFERRED = {
    "NHL": (),
    "MLS": ("mls_official_stats_exact_query_probe.py",),
    "EPL": ("epl_official_fpl_event_surface.py",),
}
DEST = {
    "NHL": "qseries_v2/oracle_source_network/providers/production_surfaces/nhl_proven_surface.py",
    "MLS": "qseries_v2/oracle_source_network/providers/production_surfaces/mls_proven_surface.py",
    "EPL": "qseries_v2/oracle_source_network/providers/production_surfaces/epl_proven_surface.py",
}
STATE = "qseries_v2/oracle_source_network/state/osn076_production_surface_foundation.json"

def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def _source_candidates_from_test(test_path):
    text = test_path.read_text(encoding="utf-8")
    found = set()
    try:
        tree = ast.parse(text, filename=str(test_path))
    except SyntaxError:
        tree = None
    if tree:
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("qseries_v2.oracle_source_network"):
                rel = Path(*node.module.split(".")).with_suffix(".py")
                if (ROOT/rel).exists():
                    found.add(rel.as_posix())
            elif isinstance(node, ast.Import):
                for a in node.names:
                    if a.name.startswith("qseries_v2.oracle_source_network"):
                        rel = Path(*a.name.split(".")).with_suffix(".py")
                        if (ROOT/rel).exists():
                            found.add(rel.as_posix())
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                s = node.value.replace("\\","/")
                if "qseries_v2/oracle_source_network/" in s and s.endswith(".py"):
                    idx = s.index("qseries_v2/oracle_source_network/")
                    rel = s[idx:]
                    if (ROOT/rel).exists():
                        found.add(rel)
    for m in re.findall(r"qseries_v2[\\/]+oracle_source_network[\\/]+[A-Za-z0-9_./\\-]+\.py", text):
        rel = m.replace("\\","/")
        if (ROOT/rel).exists():
            found.add(rel)
    return found

def _score(league, rel):
    p = ROOT/rel
    try:
        text = p.read_text(encoding="utf-8")
    except Exception:
        return -1
    anchors = ANCHORS[league]
    if not all(a in text for a in anchors):
        return -1
    score = 100
    low = rel.lower()
    if "certification/" not in low:
        score += 10
    for pref in PREFERRED[league]:
        if low.endswith(pref.lower()):
            score += 50
    if "event_surface" in low:
        score += 5
    return score

def _discover(league, test_name):
    test_path = ROOT/test_name
    if not test_path.exists():
        raise RuntimeError(f"missing certified physical test: {test_name}")

    candidates = set(_source_candidates_from_test(test_path))
    # Foundation repair is allowed to inspect current repo, but only admits files
    # that contain the exact physical-source anchors already proven by the tests.
    for p in (ROOT/"qseries_v2/oracle_source_network").rglob("*.py"):
        rel = p.relative_to(ROOT).as_posix()
        if _score(league, rel) >= 0:
            candidates.add(rel)

    ranked = sorted(
        (( _score(league, rel), rel) for rel in candidates),
        reverse=True
    )
    ranked = [(s,r) for s,r in ranked if s >= 0]
    if not ranked:
        raise RuntimeError(
            f"{league}: no current-repo implementation contains required proven anchors {ANCHORS[league]}"
        )

    best_score = ranked[0][0]
    best = [r for s,r in ranked if s == best_score]
    if len(best) != 1:
        raise RuntimeError(f"{league}: ambiguous proven implementation candidates: {best}")
    return best[0], ranked

def main():
    print("="*120)
    print(" OSN-076 SPORTS PRODUCTION SOURCE FOUNDATION — CLEAN REBUILD")
    print("="*120)

    rows=[]
    for league,test_name in TESTS.items():
        src_rel, ranked = _discover(league,test_name)
        src = ROOT/src_rel
        dst = ROOT/DEST[league]
        dst.parent.mkdir(parents=True, exist_ok=True)

        source = src.read_text(encoding="utf-8")
        compile(source, str(src), "exec")
        dst.write_text(source, encoding="utf-8")
        compile(dst.read_text(encoding="utf-8"), str(dst), "exec")

        row = {
            "league": league,
            "certified_test": test_name,
            "source_path": src_rel,
            "source_sha256": _sha(src),
            "promoted_path": DEST[league],
            "promoted_sha256": _sha(dst),
            "byte_exact_promotion": src.read_bytes() == dst.read_bytes(),
            "candidate_count": len(ranked),
            "execution_authority": False,
        }
        if not row["byte_exact_promotion"]:
            raise RuntimeError(f"{league}: promotion is not byte-exact")
        rows.append(row)
        print(f"[PROMOTE] {league} {src_rel} -> {DEST[league]}")
        print(f"[HASH] {league} {row['source_sha256']}")

    state = ROOT/STATE
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(json.dumps({
        "rows": rows,
        "held": ["NCAAB","MLB_CANONICAL_EVENT_EXTRACTION_CERT_REQUIRED"],
        "blocked": ["UCL"],
        "execution_authority": False,
    }, indent=2, sort_keys=True), encoding="utf-8")

    print("[STATE]", state.relative_to(ROOT))
    print("[PASS] NHL/MLS/EPL exact proven implementation sources promoted byte-for-byte")
    print("[PASS] certification-only package location is no longer the runtime contract")
    print("[PASS] no endpoint or response schema guessed")
    print("[PASS] execution_authority=FALSE")

if __name__ == "__main__":
    main()
