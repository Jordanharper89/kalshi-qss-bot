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


def main() -> None:
    source = OLA030.read_text(encoding="utf-8")
    tree = ast.parse(source)
    canonical_router_name = 'persistence_router'
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
    print({
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
    })


if __name__ == "__main__":
    main()
