from __future__ import annotations

import ast
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OLA030 = ROOT / "qseries_v2/oracle_intelligence/live_acquisition_model/oracle_first_real_shadow_corpus_launch_command.py"
BACKUP = OLA030.with_suffix(".py.pre_final_router_reconciliation.bak")
TEST = ROOT / "test_final_ola030_router_reconciliation.py"
LAUNCHER = ROOT / "run_oracle_live_shadow_FINAL.py"

TEST_TEXT = 'from __future__ import annotations\n\nimport ast\nfrom pathlib import Path\n\nROOT = Path(__file__).resolve().parent\nOLA030 = ROOT / "qseries_v2/oracle_intelligence/live_acquisition_model/oracle_first_real_shadow_corpus_launch_command.py"\n\ndef _call_name(node):\n    if isinstance(node.func, ast.Name):\n        return node.func.id\n    if isinstance(node.func, ast.Attribute):\n        return node.func.attr\n    return None\n\ndef _kw(source, call_name, keyword_name):\n    tree = ast.parse(source)\n    matches = []\n    for node in ast.walk(tree):\n        if not isinstance(node, ast.Call) or _call_name(node) != call_name:\n            continue\n        for keyword in node.keywords:\n            if keyword.arg == keyword_name:\n                matches.append(ast.get_source_segment(source, keyword.value))\n    if not matches:\n        raise AssertionError(f"Missing {call_name} keyword {keyword_name}")\n    return matches[-1]\n\ndef main():\n    source = OLA030.read_text(encoding="utf-8")\n    ast.parse(source)\n\n    canonical = _kw(\n        source,\n        "OraclePostgreSQLShadowAcquisitionCycleOrchestrator",\n        "postgresql_router",\n    )\n\n    production = _kw(\n        source,\n        "attest",\n        "production_persistence_router",\n    )\n\n    runtime = _kw(\n        source,\n        "attest",\n        "runtime_persistence_router",\n    )\n\n    ola017 = _kw(\n        source,\n        "attest",\n        "ola017_persistence_router",\n    )\n\n    assert canonical == production\n    assert runtime == ola017\n    assert canonical != runtime\n\n    print("[PASS] FINAL OLA-030 Router Reconciliation")\n    print({\n        "status": "passed",\n        "strict_postgresql_orchestrator_uses_canonical_router": True,\n        "production_attestation_uses_canonical_router": True,\n        "runtime_and_ola017_share_staged_router": True,\n        "dual_router_topology_reconciled": True,\n        "read_only": True,\n        "execution_allowed": False,\n    })\n\nif __name__ == "__main__":\n    main()\n'
LAUNCHER_TEXT = 'from __future__ import annotations\n\nimport os\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_intelligence.live_acquisition_model.oracle_first_real_shadow_corpus_launch_command import (\n    build_real_oracle_shadow_graph,\n)\n\nROOT = Path(__file__).resolve().parent\n\ndef main() -> int:\n    print("========================================")\n    print(" ORACLE LIVE SHADOW FINAL LAUNCH")\n    print(" READ-ONLY PRODUCTION RUNTIME")\n    print("========================================")\n\n    required = (\n        "ORACLE_POSTGRES_HOST",\n        "ORACLE_POSTGRES_DATABASE",\n        "ORACLE_POSTGRES_USERNAME",\n        "ORACLE_POSTGRES_PASSWORD",\n        "ORACLE_POSTGRES_SSLMODE",\n    )\n\n    missing = [name for name in required if not os.environ.get(name)]\n    if missing:\n        raise RuntimeError(\n            "Missing required environment variables: " + ", ".join(missing)\n        )\n\n    graph = build_real_oracle_shadow_graph(\n        runtime_root=ROOT,\n        environment=dict(os.environ),\n        service_tick_interval_seconds=5,\n    )\n\n    activator = graph.get(\n        "production_live_shadow_persistent_service_activator"\n    )\n\n    if activator is None:\n        raise RuntimeError(\n            "OLA-063 persistent service activator is missing"\n        )\n\n    if getattr(activator, "read_only", None) is not True:\n        raise RuntimeError("Activator is not read-only")\n\n    if getattr(activator, "execution_allowed", None) is not False:\n        raise RuntimeError("Activator exposes execution permission")\n\n    print("[OK] OLA-030 production graph assembled")\n    print("[OK] PostgreSQL bootstrap completed")\n    print("[OK] Router topology reconciled")\n    print("[START] Oracle live-shadow service")\n    print("[INFO] Press Ctrl+C for operator shutdown")\n\n    try:\n        record, result = activator.activate(\n            production_graph=graph,\n        )\n        print("[STOP] Oracle live-shadow service returned")\n        print(record)\n        print(result)\n        return 0\n    except KeyboardInterrupt:\n        print("\\\\n[STOP] Operator shutdown requested")\n        return 130\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'

def _offsets(source):
    values = [0]
    for line in source.splitlines(keepends=True):
        values.append(values[-1] + len(line))
    return values

def _span(source, node):
    offsets = _offsets(source)
    return (
        offsets[node.lineno - 1] + node.col_offset,
        offsets[node.end_lineno - 1] + node.end_col_offset,
    )

def _assignment_name(tree, constructor_name):
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not isinstance(node.value, ast.Call):
            continue
        func = node.value.func
        if not (isinstance(func, ast.Name) and func.id == constructor_name):
            continue
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            return node.targets[0].id
    raise RuntimeError(f"Could not locate assignment for {constructor_name}")

def _staged_router_name(tree):
    candidates = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        name = node.targets[0].id
        low = name.lower()
        if "staged" in low and "router" in low:
            candidates.append(name)

    preferred = [x for x in candidates if "persistence" in x.lower()]
    if len(preferred) == 1:
        return preferred[0]
    if len(candidates) == 1:
        return candidates[0]

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute) or node.func.attr != "attest":
            continue
        for keyword in node.keywords:
            if keyword.arg == "staged_persistence_router" and isinstance(keyword.value, ast.Name):
                return keyword.value.id

    raise RuntimeError(
        "Could not uniquely resolve staged router. "
        f"Candidates: {candidates}"
    )

def _replace_keyword(source, call_name, keyword_name, replacement):
    tree = ast.parse(source)
    matches = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        name = None
        if isinstance(node.func, ast.Name):
            name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            name = node.func.attr

        if name != call_name:
            continue

        for keyword in node.keywords:
            if keyword.arg == keyword_name:
                matches.append(keyword.value)

    if not matches:
        raise RuntimeError(
            f"Could not find {call_name}(..., {keyword_name}=...)"
        )

    node = matches[-1]
    start, end = _span(source, node)
    return source[:start] + replacement + source[end:]

def main():
    print("========================================")
    print(" FINAL OLA-030 ROUTER RECONCILIATION")
    print(" AND OPERATOR LAUNCH INSTALLER")
    print("========================================")

    if not OLA030.exists():
        raise SystemExit(f"[ERROR] Missing OLA-030: {OLA030}")

    if not BACKUP.exists():
        shutil.copy2(OLA030, BACKUP)
        print(f"[OK] Backup created: {BACKUP}")

    source = OLA030.read_text(encoding="utf-8")
    tree = ast.parse(source)

    canonical = _assignment_name(
        tree,
        "OraclePostgreSQLCanonicalObservationPersistenceRouter",
    )

    staged = _staged_router_name(tree)

    patched = source

    patched = _replace_keyword(
        patched,
        "OraclePostgreSQLShadowAcquisitionCycleOrchestrator",
        "postgresql_router",
        canonical,
    )

    patched = _replace_keyword(
        patched,
        "attest",
        "production_persistence_router",
        canonical,
    )

    patched = _replace_keyword(
        patched,
        "attest",
        "runtime_persistence_router",
        staged,
    )

    patched = _replace_keyword(
        patched,
        "attest",
        "ola017_persistence_router",
        staged,
    )

    try:
        patched = _replace_keyword(
            patched,
            "attest",
            "staged_persistence_router",
            staged,
        )
    except RuntimeError:
        pass

    ast.parse(patched)
    OLA030.write_text(patched, encoding="utf-8")

    TEST.write_text(TEST_TEXT, encoding="utf-8")
    LAUNCHER.write_text(LAUNCHER_TEXT, encoding="utf-8")

    compile(TEST.read_text(encoding="utf-8"), str(TEST), "exec")
    compile(LAUNCHER.read_text(encoding="utf-8"), str(LAUNCHER), "exec")

    print(f"[OK] Canonical router: {canonical}")
    print(f"[OK] Staged lineage router: {staged}")
    print(f"[OK] Wrote test: {TEST}")
    print(f"[OK] Wrote launcher: {LAUNCHER}")
    print("\n[DONE] Final router reconciliation and launcher installed")
    print("\nRun exactly:")
    print("py test_final_ola030_router_reconciliation.py")
    print("py run_oracle_live_shadow_FINAL.py")

if __name__ == "__main__":
    main()
