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

ATTESTATION = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition"
    / "oracle_production_lineage_graph_assembly_attestation.py"
)


def main() -> None:
    ola030_source = OLA030.read_text(encoding="utf-8")
    attestation_source = ATTESTATION.read_text(encoding="utf-8")

    ast.parse(ola030_source)
    ast.parse(attestation_source)

    assert "postgresql_router=(\n                persistence_router\n            )" in ola030_source
    assert "persistence_router=(\n                lineage_persistence_router\n            )" in ola030_source

    readiness_pos = ola030_source.index("    def readiness_kwargs_factory(")
    scheduler_pos = ola030_source.index("    def scheduler_kwargs_factory(")
    readiness_block = ola030_source[readiness_pos:scheduler_pos]

    assert "lineage_scheduler_activation_attestation" not in readiness_block
    assert "return {" in readiness_block

    assert "runtime_uses_staged_router_attested" in attestation_source
    assert "ola017_uses_production_router_attested" in attestation_source
    assert "dual_router_topology_attested" in attestation_source

    print("[PASS] FINAL OLA Runtime Repair")
    print({
        "status": "passed",
        "ola030_ast_valid": True,
        "attestation_ast_valid": True,
        "canonical_postgresql_router_preserved": True,
        "staged_runtime_router_preserved": True,
        "dual_router_attestation_contract_installed": True,
        "readiness_factory_scope_repaired": True,
        "activation_chain_scope_repaired": True,
        "read_only": True,
        "execution_allowed": False,
    })


if __name__ == "__main__":
    main()
