from __future__ import annotations

import hashlib
from pathlib import Path

from qseries_v2.oracle_terminal.oracle_temporal_intelligence_timeline_reconstruction import (
    build_temporal_intelligence_report,
    temporal_intelligence_lines,
)
from qseries_v2.oracle_terminal.oracle_adversarial_perspective_debate_and_challenge import (
    adversarial_debate_lines,
    build_adversarial_debate_report,
    debate_perspective_lines,
    select_debate_perspective,
)
from qseries_v2.oracle_terminal.oracle_contradiction_and_uncertainty_inspection import (
    build_contradiction_and_uncertainty_report,
    contradiction_and_uncertainty_lines,
)
from qseries_v2.oracle_terminal.oracle_evidence_inspection_and_answer_explainability import (
    answer_explainability_lines,
    build_answer_explainability_report,
    evidence_inspection_lines,
    select_evidence_inspection,
)
from qseries_v2.oracle_terminal.oracle_grounded_intelligence_answer_composition import (
    compose_grounded_intelligence_answer,
    grounded_answer_lines,
)
from qseries_v2.oracle_terminal.oracle_natural_language_query_planning_and_execution import (
    build_natural_language_query_plan,
    execute_natural_language_query,
    natural_language_query_plan_lines,
    natural_language_query_result_lines,
)
from qseries_v2.oracle_terminal.oracle_queryable_intelligence_read_model import (
    build_queryable_intelligence_read_model,
    queryable_intelligence_status_lines,
    queryable_record_inventory_lines,
    queryable_record_lines,
    queryable_schema_lines,
    search_queryable_records,
    select_queryable_record,
)
from qseries_v2.oracle_terminal.oracle_genuine_intelligence_read_only_consumption import (
    consume_admitted_intelligence,
    intelligence_artifact_lines,
    intelligence_consumption_status_lines,
    intelligence_inventory_lines,
    select_intelligence_artifact,
)
from qseries_v2.oracle_terminal.oracle_genuine_intelligence_artifact_admission import (
    discover_and_admit_intelligence_artifacts,
    intelligence_admission_lines,
)
from qseries_v2.oracle_terminal.oracle_bounded_live_intelligence_activation import (
    activate_once,
    bounded_activation_lines,
    inspect_bounded_activation,
)
from qseries_v2.oracle_terminal.oracle_live_intelligence_activation_discovery import (
    execute_activation_discovery_command,
)
from qseries_v2.oracle_terminal.oracle_live_intelligence_runtime_discovery_and_binding import (
    execute_bound_terminal_command,
)
from qseries_v2.oracle_terminal.oracle_open_intelligence_terminal_foundation import (
    TERMINAL_PROMPT,
    build_dependency_receipt,
    format_terminal_response,
    parse_terminal_input,
    terminal_banner,
)

ROOT = Path(__file__).resolve().parent
OOR_013 = (
    ROOT / "qseries_v2" / "oracle_operator_runtime"
    / "oracle_operator_runtime_final_completion_and_freeze_gate.py"
)


def main() -> int:
    if not OOR_013.is_file():
        print(f"[ERROR] Required OOR-013 module missing: {OOR_013}")
        return 1

    receipt = build_dependency_receipt(
        source_module_sha256=hashlib.sha256(OOR_013.read_bytes()).hexdigest()
    )
    print(terminal_banner())
    print("OIT-013 temporal intelligence timeline reconstruction: active")

    while True:
        try:
            raw = input(TERMINAL_PROMPT)
        except (EOFError, KeyboardInterrupt):
            print("\nOracle terminal closed.")
            return 0

        normalized = raw.strip()
        if not normalized:
            continue

        try:
            lowered = normalized.lower()

            if lowered == "activation":
                print("\n".join(execute_activation_discovery_command(
                    repository_root=ROOT
                )))
                continue
            if lowered in {"activation-readiness", "activate-status"}:
                print("\n".join(bounded_activation_lines(
                    inspect_bounded_activation(repository_root=ROOT)
                )))
                continue
            if lowered == "activate-once":
                print("\n".join(bounded_activation_lines(
                    activate_once(repository_root=ROOT)
                )))
                continue
            if lowered in {"intelligence-status", "artifact-admission"}:
                print("\n".join(intelligence_admission_lines(
                    discover_and_admit_intelligence_artifacts(
                        repository_root=ROOT
                    )
                )))
                continue
            if lowered in {"intelligence-consumption", "consumption-status"}:
                print("\n".join(intelligence_consumption_status_lines(
                    consume_admitted_intelligence(repository_root=ROOT)
                )))
                continue
            if lowered in {"intelligence-list", "intelligence-artifacts"}:
                print("\n".join(intelligence_inventory_lines(
                    consume_admitted_intelligence(repository_root=ROOT)
                )))
                continue
            if lowered.startswith("intelligence-read "):
                selector = normalized.split(maxsplit=1)[1]
                consumption = consume_admitted_intelligence(repository_root=ROOT)
                print("\n".join(intelligence_artifact_lines(
                    select_intelligence_artifact(
                        consumption,
                        selector=selector,
                    )
                )))
                continue
            if lowered in {"query-status", "intelligence-query-status"}:
                print("\n".join(queryable_intelligence_status_lines(
                    build_queryable_intelligence_read_model(
                        repository_root=ROOT
                    )
                )))
                continue
            if lowered in {"intelligence-schema", "query-schema"}:
                print("\n".join(queryable_schema_lines(
                    build_queryable_intelligence_read_model(
                        repository_root=ROOT
                    )
                )))
                continue
            if lowered in {"intelligence-records", "query-records"}:
                model = build_queryable_intelligence_read_model(
                    repository_root=ROOT
                )
                print("\n".join(queryable_record_inventory_lines(model.records)))
                continue
            if lowered.startswith("intelligence-record "):
                selector = normalized.split(maxsplit=1)[1]
                model = build_queryable_intelligence_read_model(
                    repository_root=ROOT
                )
                print("\n".join(queryable_record_lines(
                    select_queryable_record(model, selector=selector)
                )))
                continue
            if lowered.startswith("intelligence-search "):
                query = normalized.split(maxsplit=1)[1]
                model = build_queryable_intelligence_read_model(
                    repository_root=ROOT
                )
                print("\n".join(queryable_record_inventory_lines(
                    search_queryable_records(model, query=query),
                    heading=f"ORACLE INTELLIGENCE SEARCH: {query}",
                )))
                continue
            if lowered.startswith("question-plan "):
                query = normalized.split(maxsplit=1)[1]
                print("\n".join(natural_language_query_plan_lines(
                    build_natural_language_query_plan(query=query)
                )))
                continue
            if lowered.startswith("ask-raw "):
                query = normalized.split(maxsplit=1)[1]
                print("\n".join(natural_language_query_result_lines(
                    execute_natural_language_query(
                        repository_root=ROOT,
                        query=query,
                    )
                )))
                continue
            if lowered.startswith("ask "):
                query = normalized.split(maxsplit=1)[1]
                print("\n".join(grounded_answer_lines(
                    compose_grounded_intelligence_answer(
                        repository_root=ROOT,
                        query=query,
                    )
                )))
                continue
            if lowered.startswith("explain "):
                query = normalized.split(maxsplit=1)[1]
                print("\n".join(answer_explainability_lines(
                    build_answer_explainability_report(
                        repository_root=ROOT,
                        query=query,
                    )
                )))
                continue
            if lowered.startswith("evidence "):
                remainder = normalized.split(maxsplit=1)[1]
                if " -- " not in remainder:
                    raise ValueError("usage: evidence E1 -- <question>")
                selector, query = remainder.split(" -- ", 1)
                report = build_answer_explainability_report(
                    repository_root=ROOT,
                    query=query,
                )
                print("\n".join(evidence_inspection_lines(
                    select_evidence_inspection(report, selector=selector)
                )))
                continue
            if lowered.startswith("uncertainty "):
                query = normalized.split(maxsplit=1)[1]
                print("\n".join(contradiction_and_uncertainty_lines(
                    build_contradiction_and_uncertainty_report(
                        repository_root=ROOT,
                        query=query,
                    )
                )))
                continue
            if lowered.startswith("contradictions "):
                query = normalized.split(maxsplit=1)[1]
                print("\n".join(contradiction_and_uncertainty_lines(
                    build_contradiction_and_uncertainty_report(
                        repository_root=ROOT,
                        query=query,
                    )
                )))
                continue
            if lowered.startswith("debate "):
                query = normalized.split(maxsplit=1)[1]
                print("\n".join(adversarial_debate_lines(
                    build_adversarial_debate_report(
                        repository_root=ROOT,
                        query=query,
                    )
                )))
                continue
            if lowered.startswith("challenge "):
                query = normalized.split(maxsplit=1)[1]
                report = build_adversarial_debate_report(
                    repository_root=ROOT,
                    query=query,
                )
                print("\n".join(debate_perspective_lines(
                    select_debate_perspective(
                        report,
                        selector="challenge",
                    )
                )))
                continue
            if lowered.startswith("perspective "):
                remainder = normalized.split(maxsplit=1)[1]
                if " -- " not in remainder:
                    raise ValueError(
                        "usage: perspective bull|bear|neutral|challenge -- <question>"
                    )
                selector, query = remainder.split(" -- ", 1)
                report = build_adversarial_debate_report(
                    repository_root=ROOT,
                    query=query,
                )
                print("\n".join(debate_perspective_lines(
                    select_debate_perspective(
                        report,
                        selector=selector,
                    )
                )))
                continue
            if lowered.startswith("timeline "):
                query = normalized.split(maxsplit=1)[1]
                print("\n".join(temporal_intelligence_lines(
                    build_temporal_intelligence_report(
                        repository_root=ROOT,
                        query=query,
                    )
                )))
                continue
            if lowered.startswith("chronology "):
                query = normalized.split(maxsplit=1)[1]
                print("\n".join(temporal_intelligence_lines(
                    build_temporal_intelligence_report(
                        repository_root=ROOT,
                        query=query,
                    )
                )))
                continue

            command = parse_terminal_input(raw)
            response = execute_bound_terminal_command(
                command,
                repository_root=ROOT,
                dependency_receipt=receipt,
            )
            if response.status in {"exit", "quit"}:
                print("Oracle terminal closed.")
                return 0
            if response.status == "clear":
                print("\n" * 40)
                continue
            print(format_terminal_response(response))
        except Exception as exc:
            print(f"[ERROR] {exc}")


if __name__ == "__main__":
    raise SystemExit(main())
