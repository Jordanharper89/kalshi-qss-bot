
"""OSN-010 exact static extraction from the certified OAD-418 source file only."""
from pathlib import Path
import ast

def extract_literal_records(path: Path):
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    records = []

    for node in ast.walk(tree):
        value_node = None
        if isinstance(node, ast.Assign):
            value_node = node.value
        elif isinstance(node, ast.AnnAssign):
            value_node = node.value

        if value_node is None:
            continue

        try:
            value = ast.literal_eval(value_node)
        except Exception:
            continue

        if isinstance(value, list):
            records.extend(x for x in value if isinstance(x, dict))
        elif isinstance(value, tuple):
            records.extend(x for x in value if isinstance(x, dict))
        elif isinstance(value, dict):
            # Support common row-container shapes without guessing beyond the exact file.
            for key in ("markets", "rows", "gaps", "priorities", "results", "items"):
                seq = value.get(key)
                if isinstance(seq, (list, tuple)):
                    records.extend(x for x in seq if isinstance(x, dict))

    return tuple(records)
