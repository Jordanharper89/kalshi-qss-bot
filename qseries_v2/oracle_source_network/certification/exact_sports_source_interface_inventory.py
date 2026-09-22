from dataclasses import dataclass, asdict
from pathlib import Path
import ast
import json

SOURCE_FILES = {
    "NFL": (
        "qseries_v2/oracle_source_network/acquisition/nfl_official_live.py",
        "qseries_v2/oracle_source_network/mapping/nfl_live_escaped_state_extractor.py",
    ),
    "NCAAF": (
        "qseries_v2/oracle_source_network/acquisition/ncaa_football_official_live.py",
        "qseries_v2/oracle_source_network/mapping/ncaaf_exact_scoreboard_extractor.py",
    ),
    "NBA": (
        "qseries_v2/oracle_source_network/acquisition/nba_official_live.py",
        "qseries_v2/oracle_source_network/mapping/basketball_event_extractor.py",
    ),
    "NHL": (
        "qseries_v2/oracle_source_network/acquisition/nhl_official_live.py",
    ),
    "MLS": (
        "qseries_v2/oracle_source_network/acquisition/mls_official_live.py",
    ),
    "EPL": (
        "qseries_v2/oracle_source_network/acquisition/european_soccer_official_live.py",
    ),
}

MANIFEST = Path("qseries_v2/oracle_source_network/state/exact_sports_source_interfaces.json")

@dataclass(frozen=True)
class FunctionShape:
    name: str
    required_args: tuple
    optional_args: tuple
    async_function: bool
    constructs_canonical_event: bool
    network_markers: tuple

def _shape(node, source):
    args = list(node.args.args)
    defaults = list(node.args.defaults)
    required_count = max(0, len(args) - len(defaults))
    required = tuple(a.arg for a in args[:required_count])
    optional = tuple(a.arg for a in args[required_count:])
    segment = ast.get_source_segment(source, node) or ""
    markers = tuple(
        marker for marker in ("urlopen", "requests.", "httpx.", "urllib.", "_get(", "fetch(", "acquire(")
        if marker in segment
    )
    return FunctionShape(
        name=node.name,
        required_args=required,
        optional_args=optional,
        async_function=isinstance(node, ast.AsyncFunctionDef),
        constructs_canonical_event=("CanonicalSportsEvent(" in segment),
        network_markers=markers,
    )

def capture_interfaces(root=None):
    base = Path(root or Path.cwd()).resolve()
    report = {"execution_authority": False, "leagues": {}}

    for league, rels in SOURCE_FILES.items():
        rows = []
        for rel in rels:
            path = base / rel
            if not path.exists():
                rows.append({"path": rel, "missing": True, "functions": []})
                continue
            source = path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(source)
            funcs = []
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
                    funcs.append(asdict(_shape(node, source)))
            rows.append({"path": rel, "missing": False, "functions": funcs})
        report["leagues"][league] = rows

    out = base / MANIFEST
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return report, out
