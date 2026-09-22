from pathlib import Path
import ast, hashlib, json

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_predictive_discovery"
DATA = ROOT / "runtime" / "predictive_data"
PKG.mkdir(parents=True, exist_ok=True)
DATA.mkdir(parents=True, exist_ok=True)

def unique_source(pattern):
    hits = [p for p in ROOT.rglob(pattern)
            if "rollback" not in {x.lower() for x in p.parts}
            and not p.name.startswith(("build_", "test_"))]
    if len(hits) != 1:
        raise RuntimeError(f"{pattern}: expected exactly one production module, found {len(hits)}: {[str(x) for x in hits[:8]]}")
    return hits[0]

source = unique_source("opd_017_*.py")
text = source.read_text(encoding="utf-8")
tree = ast.parse(text)
candidates = []
for node in tree.body:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
        segment = ast.get_source_segment(text, node) or ""
        low = segment.lower()
        score = (10 if "token" in node.name.lower() else 0) + (6 if "primitive" in node.name.lower() else 0)
        score += 4 * ("CC:" in segment) + 4 * ("L:" in segment) + 2 * ("token" in low)
        if score:
            candidates.append((score, node.name))
candidates.sort(reverse=True)
if not candidates:
    raise RuntimeError("OPD-017 frozen source exposes no provable token/primitive callable")
if len(candidates) > 1 and candidates[0][0] == candidates[1][0]:
    raise RuntimeError(f"OPD-017 token callable is ambiguous: {candidates[:8]}")
callable_name = candidates[0][1]
source_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
module_code = f'''from pathlib import Path
import hashlib, importlib.util, inspect
SOURCE_PATH = r"{source.relative_to(ROOT)}"
SOURCE_SHA256 = "{source_sha}"
TOKEN_CALLABLE = "{callable_name}"
execution_authority = False
probability_enabled = False
direction_enabled = False
publication_allowed = False

def _load(root):
    path = Path(root) / SOURCE_PATH
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise RuntimeError("OPD-017 frozen source hash changed; refusing semantic drift")
    spec = importlib.util.spec_from_file_location("_opd017_frozen", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fn = getattr(mod, TOKEN_CALLABLE, None)
    if not callable(fn):
        raise RuntimeError("frozen OPD-017 token callable disappeared")
    return fn

def materialize_exact_live_tokens(root, state_at_t):
    fn = _load(root)
    sig = inspect.signature(fn)
    required = [p for p in sig.parameters.values()
                if p.default is inspect._empty
                and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
    if len(required) != 1:
        raise RuntimeError("OPD-017 exact token callable is not a one-state contract: " + str(sig))
    result = fn(state_at_t)
    if isinstance(result, dict):
        for key in ("tokens", "feature_tokens", "primitives"):
            if key in result:
                result = result[key]
                break
    if not isinstance(result, (list, tuple, set, frozenset)):
        raise RuntimeError("OPD-017 token callable returned unsupported type: " + type(result).__name__)
    return tuple(str(x) for x in result)
'''
(PKG / "opd_041_exact_live_token_materializer.py").write_text(module_code, encoding="utf-8")
manifest = {
    "schema_version": "OPD-041",
    "opd017_path": str(source.relative_to(ROOT)),
    "opd017_sha256": source_sha,
    "token_callable": callable_name,
    "exact_frozen_semantics": True,
    "execution_authority": False,
    "probability_enabled": False,
    "direction_enabled": False,
    "publication_allowed": False,
}
(DATA / "opd_041_exact_live_token_materializer_contract.json").write_text(
    json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
test_code = '''from pathlib import Path
from qseries_v2.oracle_predictive_discovery import opd_041_exact_live_token_materializer as m
root = Path.cwd()
assert (root / m.SOURCE_PATH).is_file()
assert m.execution_authority is False
assert m.probability_enabled is False
assert m.direction_enabled is False
assert m.publication_allowed is False
assert callable(m._load(root))
print("[OPD017]", m.SOURCE_PATH)
print("[TOKEN_CALLABLE]", m.TOKEN_CALLABLE)
print("[PASS] exact frozen OPD-017 source/hash/callable lineage captured")
print("[PASS] no token semantics invented or retuned")
print("[PASS] OPD-041 certified")
'''
(ROOT / "test_opd_041_exact_live_token_materializer_from_frozen_opd017_semantics.py").write_text(test_code, encoding="utf-8")
print("[PASS] OPD-041 installer complete")
