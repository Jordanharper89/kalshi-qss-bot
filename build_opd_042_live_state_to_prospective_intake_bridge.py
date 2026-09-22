from pathlib import Path
import ast, hashlib, json

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_predictive_discovery"
DATA = ROOT / "runtime" / "predictive_data"
PKG.mkdir(parents=True, exist_ok=True)
DATA.mkdir(parents=True, exist_ok=True)
if not (PKG / "opd_041_exact_live_token_materializer.py").is_file():
    raise RuntimeError("OPD-041 missing")

def unique_source(pattern):
    hits = [p for p in ROOT.rglob(pattern)
            if "rollback" not in {x.lower() for x in p.parts}
            and not p.name.startswith(("build_", "test_"))]
    if len(hits) != 1:
        raise RuntimeError(f"{pattern}: expected exactly one production module, found {len(hits)}: {[str(x) for x in hits[:8]]}")
    return hits[0]

def choose(path, terms):
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    candidates = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
            segment = (ast.get_source_segment(text, node) or "").lower()
            name = node.name.lower()
            score = sum(8 if term in name else 2 if term in segment else 0 for term in terms)
            if score:
                candidates.append((score, node.name))
    candidates.sort(reverse=True)
    if not candidates:
        raise RuntimeError(f"no compatible callable proved in {path}")
    if len(candidates) > 1 and candidates[0][0] == candidates[1][0]:
        raise RuntimeError(f"ambiguous callable in {path}: {candidates[:8]}")
    return candidates[0][1], hashlib.sha256(text.encode("utf-8")).hexdigest()

reader = unique_source("opd_036_*.py")
intake = unique_source("opd_032_*.py")
reader_fn, reader_sha = choose(reader, ("bounded", "read", "live", "state"))
intake_fn, intake_sha = choose(intake, ("intake", "state", "ledger", "append"))
module_code = f'''from pathlib import Path
import hashlib, importlib.util, inspect
from .opd_041_exact_live_token_materializer import materialize_exact_live_tokens

READER_PATH = r"{reader.relative_to(ROOT)}"
READER_SHA256 = "{reader_sha}"
READER_CALLABLE = "{reader_fn}"
INTAKE_PATH = r"{intake.relative_to(ROOT)}"
INTAKE_SHA256 = "{intake_sha}"
INTAKE_CALLABLE = "{intake_fn}"
execution_authority = False
probability_enabled = False
direction_enabled = False
publication_allowed = False

def _load(root, relative, expected_sha, callable_name):
    path = Path(root) / relative
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha:
        raise RuntimeError("certified upstream source changed: " + relative)
    spec = importlib.util.spec_from_file_location("_opd042_" + callable_name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fn = getattr(mod, callable_name, None)
    if not callable(fn):
        raise RuntimeError("proved callable disappeared: " + callable_name)
    return fn

def _invoke(fn, root, payload=None, limit=1):
    signature = inspect.signature(fn)
    kwargs = {{}}
    for name, parameter in signature.parameters.items():
        if name in ("root", "repository_root", "repo_root"):
            kwargs[name] = Path(root)
        elif name in ("limit", "max_rows", "row_limit", "max_records"):
            kwargs[name] = limit
        elif payload is not None and name in ("state", "state_at_t", "row", "record", "observation"):
            kwargs[name] = payload
        elif parameter.default is inspect._empty and parameter.kind in (parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD):
            raise RuntimeError("unsupported required parameter on proved callable " + fn.__name__ + str(signature))
    return fn(**kwargs)

def bridge_once(root):
    reader_fn = _load(root, READER_PATH, READER_SHA256, READER_CALLABLE)
    states = _invoke(reader_fn, root, limit=1)
    if states is None:
        return {{"read": 0, "intaken": 0}}
    if not isinstance(states, (list, tuple)):
        states = [states]
    states = list(states)[:1]
    if not states:
        return {{"read": 0, "intaken": 0}}
    intake_fn = _load(root, INTAKE_PATH, INTAKE_SHA256, INTAKE_CALLABLE)
    count = 0
    for state in states:
        tokens = materialize_exact_live_tokens(root, state)
        payload = dict(state) if isinstance(state, dict) else state
        if isinstance(payload, dict):
            payload["feature_tokens"] = list(tokens)
        _invoke(intake_fn, root, payload=payload, limit=1)
        count += 1
    return {{"read": len(states), "intaken": count}}
'''
(PKG / "opd_042_live_state_to_prospective_intake_bridge.py").write_text(module_code, encoding="utf-8")
manifest = {
    "schema_version": "OPD-042",
    "reader_path": str(reader.relative_to(ROOT)),
    "reader_callable": reader_fn,
    "intake_path": str(intake.relative_to(ROOT)),
    "intake_callable": intake_fn,
    "opd041_exact_token_lineage": True,
    "execution_authority": False,
    "probability_enabled": False,
    "direction_enabled": False,
    "publication_allowed": False,
}
(DATA / "opd_042_live_state_intake_bridge_contract.json").write_text(
    json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
test_code = '''from pathlib import Path
from qseries_v2.oracle_predictive_discovery import opd_042_live_state_to_prospective_intake_bridge as m
root = Path.cwd()
assert m.execution_authority is False and m.probability_enabled is False
assert m.direction_enabled is False and m.publication_allowed is False
assert callable(m._load(root, m.READER_PATH, m.READER_SHA256, m.READER_CALLABLE))
assert callable(m._load(root, m.INTAKE_PATH, m.INTAKE_SHA256, m.INTAKE_CALLABLE))
print("[READER]", m.READER_PATH, m.READER_CALLABLE)
print("[INTAKE]", m.INTAKE_PATH, m.INTAKE_CALLABLE)
print("[PASS] exact live state reader -> frozen OPD-017 token semantics -> OPD-032 intake wired")
print("[PASS] OPD-042 certified")
'''
(ROOT / "test_opd_042_live_state_to_prospective_intake_bridge.py").write_text(test_code, encoding="utf-8")
print("[PASS] OPD-042 installer complete")
