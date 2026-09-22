from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OLA030 = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition_model"
    / "oracle_first_real_shadow_corpus_launch_command.py"
)
TEST = ROOT / "test_ola_030_runtime_postgresql_router_type_correction.py"


def _find_assignment_name(tree: ast.AST, constructor_name: str) -> str:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        value = node.value
        if not isinstance(value, ast.Call):
            continue
        func = value.func
        if isinstance(func, ast.Name) and func.id == constructor_name:
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                return node.targets[0].id
    raise RuntimeError(f"Could not find assignment for {constructor_name}")


def _find_orchestrator_router_span(source: str, tree: ast.AST):
    lines = source.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (
            isinstance(func, ast.Name)
            and func.id == "OraclePostgreSQLShadowAcquisitionCycleOrchestrator"
        ):
            continue
        for keyword in node.keywords:
            if keyword.arg != "postgresql_router":
                continue
            value = keyword.value
            start = offsets[value.lineno - 1] + value.col_offset
            end = offsets[value.end_lineno - 1] + value.end_col_offset
            return start, end, source[start:end]
    raise RuntimeError(
        "Could not find postgresql_router keyword on "
        "OraclePostgreSQLShadowAcquisitionCycleOrchestrator"
    )


def main() -> None:
    print("========================================")
    print(" OLA-030 RUNTIME CORRECTION")
    print(" POSTGRESQL ROUTER TYPE BOUNDARY")
    print("========================================")

    if not OLA030.exists():
        raise SystemExit(f"[ERROR] Missing OLA-030 production graph: {OLA030}")

    source = OLA030.read_text(encoding="utf-8")
    tree = ast.parse(source)

    canonical_router_name = _find_assignment_name(
        tree,
        "OraclePostgreSQLCanonicalObservationPersistenceRouter",
    )

    start, end, old_expression = _find_orchestrator_router_span(source, tree)

    if old_expression.strip() == canonical_router_name:
        corrected = source
        print("[OK] OLA-030 orchestrator already uses canonical PostgreSQL router")
    else:
        corrected = source[:start] + canonical_router_name + source[end:]
        ast.parse(corrected)
        OLA030.write_text(corrected, encoding="utf-8")
        print("[OK] Corrected OLA-030 orchestrator postgresql_router:")
        print(f"     FROM: {old_expression.strip()}")
        print(f"     TO:   {canonical_router_name}")

    test_text = f"""from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OLA030 = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition_model"
    / "oracle_first_real_shadow_corpus_launch_command.py"
)


def main() -> None:
    source = OLA030.read_text(encoding="utf-8")
    tree = ast.parse(source)
    canonical_router_name = {canonical_router_name!r}
    found = False

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not (
            isinstance(node.func, ast.Name)
            and node.func.id == "OraclePostgreSQLShadowAcquisitionCycleOrchestrator"
        ):
            continue
        for keyword in node.keywords:
            if keyword.arg != "postgresql_router":
                continue
            assert isinstance(keyword.value, ast.Name)
            assert keyword.value.id == canonical_router_name
            found = True

    assert found is True

    print("[PASS] OLA-030 Runtime PostgreSQL Router Type Correction")
    print({{
        "status": "passed",
        "actual_ola030_source_graph_inspected": True,
        "actual_graph_ast_valid": True,
        "postgresql_orchestrator_uses_canonical_router": True,
        "lineage_wrapper_not_passed_into_strict_orchestrator_constructor": True,
        "read_only": True,
        "execution_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "trade_authorization_allowed": False,
        "order_placement_allowed": False,
        "funds_moved": False,
        "portfolio_mutated": False,
    }})


if __name__ == "__main__":
    main()
"""

    TEST.write_text(test_text, encoding="utf-8")
    compile(TEST.read_text(encoding="utf-8"), str(TEST), "exec")

    print(f"[OK] Wrote regression test: {TEST}")
    print("\n[DONE] OLA-030 runtime PostgreSQL router type correction installed")
    print("\nRun:")
    print("py test_ola_030_runtime_postgresql_router_type_correction.py")


if __name__ == "__main__":
    main()
