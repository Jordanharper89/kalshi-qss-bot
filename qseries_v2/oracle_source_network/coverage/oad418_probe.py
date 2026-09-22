
"""Static, read-only OAD-418 evidence inspection. Never imports or executes OAD-418."""
from pathlib import Path
import ast
import json

def _oad418_file(root: Path):
    matches = list((root/"qseries_v2"/"oracle_adapters"/"independent").glob("oad_418_*.py"))
    if not matches:
        raise FileNotFoundError("OAD-418 module not found")
    return matches[0]

def static_literals(root: Path):
    path = _oad418_file(root)
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    rows = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = []
            value_node = None
            if isinstance(node, ast.Assign):
                targets = node.targets
                value_node = node.value
            else:
                targets = [node.target]
                value_node = node.value
            for target in targets:
                if isinstance(target, ast.Name) and not target.id.startswith("_") and value_node is not None:
                    try:
                        value = ast.literal_eval(value_node)
                    except Exception:
                        continue
                    if isinstance(value, (dict, list, tuple, set, str, int, float, bool, type(None))):
                        rows.append({"name": target.id, "value": value})
    return rows

def report_files(root: Path):
    candidates = []
    for pattern in ("*418*.json", "*gap*priority*.json", "*coverage*gap*.json", "*source*coverage*.json"):
        candidates.extend(root.rglob(pattern))
    out = []
    seen = set()
    for p in candidates:
        rp = p.resolve()
        if rp in seen:
            continue
        seen.add(rp)
        try:
            out.append({
                "path": str(p.relative_to(root)),
                "value": json.loads(p.read_text(encoding="utf-8")),
            })
        except Exception:
            pass
    return out
