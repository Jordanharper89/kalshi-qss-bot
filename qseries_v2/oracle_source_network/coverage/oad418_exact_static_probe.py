
"""Static inspection of the exact certified OAD-418 file only."""
from pathlib import Path
import ast

def inspect_exact_oad418(path: Path):
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    names = set()
    dataclass_count = 0
    function_count = 0
    class_count = 0

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            function_count += 1
            names.add(node.name)
        elif isinstance(node, ast.ClassDef):
            class_count += 1
            names.add(node.name)
            for dec in node.decorator_list:
                if isinstance(dec, ast.Name) and dec.id == "dataclass":
                    dataclass_count += 1
                elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name) and dec.func.id == "dataclass":
                    dataclass_count += 1

    return {
        "path": str(path),
        "bytes": len(source.encode("utf-8")),
        "functions": function_count,
        "classes": class_count,
        "dataclasses": dataclass_count,
        "symbols": tuple(sorted(names)),
    }
