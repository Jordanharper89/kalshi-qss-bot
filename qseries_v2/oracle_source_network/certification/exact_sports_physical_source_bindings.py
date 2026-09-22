from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class PhysicalSourceBinding:
    league: str
    test_file: str
    source_role: str
    admitted: bool
    execution_authority: bool = False

SPECS = {
    "NFL": {
        "prefix": "test_osn_044_",
        "include": ("extractor",),
        "exclude": ("schema", "probe",),
        "role": "EXACT_CANONICAL_EVENT_EXTRACTION",
    },
    "NCAAF": {
        "prefix": "test_osn_045_",
        "include": ("scoreboard", "extractor"),
        "exclude": ("schema", "probe",),
        "role": "EXACT_CANONICAL_EVENT_EXTRACTION",
    },
    "NBA": {
        "prefix": "test_osn_016_",
        "include": ("nba", "official", "physical", "acquisition"),
        "exclude": (),
        "role": "CERTIFIED_SOURCE_ACQUISITION_POSITIVE_CONTROL",
    },
    "NHL": {
        "prefix": "test_osn_051_",
        "include": ("nhl", "official", "json", "event", "surface"),
        "exclude": (),
        "role": "EXACT_CANONICAL_EVENT_EXTRACTION",
    },
    "MLS": {
        "prefix": "test_osn_052_",
        "include": ("mls", "official", "stats", "exact", "query"),
        "exclude": ("event_surface_physical_probe",),
        "role": "EXACT_CANONICAL_EVENT_EXTRACTION",
    },
    "EPL": {
        "prefix": "test_osn_053_",
        "include": ("epl", "official", "json", "event", "surface"),
        "exclude": (),
        "role": "EXACT_CANONICAL_EVENT_EXTRACTION",
    },
}

def _score(name):
    lower = name.lower()
    score = 0
    if "repair" in lower:
        score += 100
    if "exact" in lower:
        score += 30
    if "extractor" in lower:
        score += 20
    if "physical" in lower:
        score += 10
    if "probe" in lower:
        score -= 40
    return score

def _resolve_one(base, league, spec):
    candidates = []
    for p in base.glob(spec["prefix"] + "*.py"):
        name = p.name.lower()
        if not all(token.lower() in name for token in spec["include"]):
            continue
        if any(token.lower() in name for token in spec["exclude"]):
            continue
        candidates.append(p)

    if not candidates:
        raise RuntimeError(
            f"{league} exact certified test not found using prefix={spec['prefix']} "
            f"include={spec['include']} exclude={spec['exclude']}"
        )

    candidates.sort(key=lambda p: (_score(p.name), p.name), reverse=True)
    chosen = candidates[0]
    return chosen.name, tuple(p.name for p in candidates)

def resolve_bindings(root=None):
    base = Path(root or Path.cwd()).resolve()
    bindings = []
    discovery = {}

    for league, spec in SPECS.items():
        chosen, candidates = _resolve_one(base, league, spec)
        discovery[league] = {"chosen": chosen, "candidates": candidates}
        bindings.append(
            PhysicalSourceBinding(
                league=league,
                test_file=chosen,
                source_role=spec["role"],
                admitted=True,
            )
        )

    return tuple(bindings), discovery

def verify_bindings(root=None):
    bindings, discovery = resolve_bindings(root=root)
    return {
        "admitted": tuple(b.league for b in bindings),
        "held": ("NCAAB", "MLB_CANONICAL_EVENT_EXTRACTION_CERT_REQUIRED"),
        "blocked": ("UCL",),
        "bindings": bindings,
        "discovery": discovery,
        "execution_authority": False,
    }

# Compatibility for downstream OSN-073 while keeping resolution grounded in current repo.
try:
    BINDINGS, _DISCOVERY = resolve_bindings()
except Exception:
    BINDINGS = ()
    _DISCOVERY = {}
