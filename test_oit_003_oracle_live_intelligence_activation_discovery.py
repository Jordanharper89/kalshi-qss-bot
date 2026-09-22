from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from qseries_v2.oracle_terminal.oracle_live_intelligence_activation_discovery import *


def reject(function) -> None:
    try:
        function()
        raise AssertionError("unsafe activation discovery accepted")
    except OracleLiveIntelligenceActivationDiscoveryInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OIT-003 TEST")
    print(" LIVE INTELLIGENCE ACTIVATION DISCOVERY")
    print("=" * 40)

    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        analytics = root / "qseries_v2" / "oracle_intelligence" / "analytics"
        live = (
            root / "qseries_v2" / "oracle_intelligence"
            / "live_acquisition_model"
        )
        analytics.mkdir(parents=True)
        live.mkdir(parents=True)
        (analytics / "__init__.py").write_text("", encoding="utf-8")
        (live / "__init__.py").write_text("", encoding="utf-8")
        (live / "oracle_live_observation_contract.py").write_text(
            "class OracleLiveObservation: pass\n",
            encoding="utf-8",
        )
        (analytics / "oracle_production_analytics_pipeline.py").write_text(
            "from qseries_v2.oracle_intelligence.live_acquisition_model."
            "oracle_live_observation_contract import OracleLiveObservation\n"
            "TARGET = r'runtime\\oracle_intelligence\\production_analytics'\n"
            "def activate_production_analytics("
            "observation: OracleLiveObservation, evaluation_policy: str):\n"
            "    return observation, evaluation_policy\n",
            encoding="utf-8",
        )
        (root / "runtime" / "oracle_live_shadow").mkdir(parents=True)

        before = sorted(
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
        )
        receipt = discover_live_intelligence_activation(
            repository_root=root
        )
        after = sorted(
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
        )

        assert before == after
        assert verify_activation_discovery(receipt)
        assert receipt.analytics_package_present
        assert receipt.analytics_python_file_count == 2
        assert receipt.canonical_entry_module == (
            "qseries_v2.oracle_intelligence.analytics."
            "oracle_production_analytics_pipeline"
        )
        assert receipt.canonical_entry_callable == (
            "activate_production_analytics"
        )
        assert any("observation" in item for item in receipt.required_inputs)
        assert receipt.live_acquisition_dependency_present
        assert receipt.canonical_persistence_target == (
            "runtime/oracle_intelligence/production_analytics"
        )
        assert receipt.static_chain_executable
        assert receipt.activation_readiness == "ready_for_bounded_activation"
        assert receipt.live_execution_status == (
            "live_acquisition_available_analytics_not_persisting"
        )
        assert not (root / "runtime" / "oracle_intelligence").exists()
        assert not receipt.analytics_execution_performed
        assert not receipt.runtime_artifact_created
        assert not receipt.database_access_performed
        assert not receipt.module_import_execution_performed
        assert receipt.read_only
        assert not receipt.execution_allowed
        assert not receipt.publication_allowed
        assert not receipt.qseries_mutation_allowed

        lines = execute_activation_discovery_command(
            repository_root=root
        )
        rendered = "\n".join(lines)
        assert "analytics_entry_point:" in rendered
        assert "required_inputs:" in rendered
        assert "dependency_chain:" in rendered
        assert "persistence_target:" in rendered
        assert "activation_readiness: ready_for_bounded_activation" in rendered
        assert "live_execution_status:" in rendered
        assert "OIT-004 bounded activation remains disabled." in rendered

        reject(lambda: verify_activation_discovery(
            replace(receipt, analytics_execution_performed=True)
        ))
        reject(lambda: verify_activation_discovery(
            replace(receipt, runtime_artifact_created=True)
        ))
        reject(lambda: verify_activation_discovery(
            replace(receipt, execution_allowed=True)
        ))
        reject(lambda: verify_activation_discovery(
            replace(receipt, receipt_hash="0" * 64)
        ))

    print("[PASS] Actual OIT-002 discovery contract consumed")
    print("[PASS] Canonical analytics entry point discovered statically")
    print("[PASS] Required input contract extracted without invocation")
    print("[PASS] Minimum live-acquisition-to-analytics graph traced")
    print("[PASS] Canonical runtime/oracle_intelligence target discovered")
    print("[PASS] Static executability checked without importing analytics")
    print("[PASS] Activation terminal command reports complete readiness")
    print("[PASS] No runtime artifact, database access, or analytics execution occurred")
    print("[PASS] Read-only, publication, and Q Series boundaries preserved")
    print("[DONE] OIT-003 LIVE INTELLIGENCE ACTIVATION DISCOVERY PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
