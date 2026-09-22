from __future__ import annotations

import ast
from pathlib import Path


TARGET_INSTALLER = Path(
    "build_oia_020_oracle_qualified_research_dispatch_manifest_builder.py"
)


OLD_WORK_ITEM_TOKEN = '''        (
            'WORK_ITEM_POLICY_ID = '
            '"oracle.qualified-research-work-item-'
            'materialization.v1"'
        ),'''


NEW_WORK_ITEM_TOKENS = '''        "WORK_ITEM_POLICY_ID",
        "oracle.qualified-research-work-item-materialization.v1",'''


OLD_RESEARCH_OBJECTIVE_TOKEN = '''        (
            "RESEARCH_OBJECTIVE = "
            '("evaluate_qualified_component_with_'
        ),'''


NEW_RESEARCH_OBJECTIVE_TOKENS = '''        "RESEARCH_OBJECTIVE",
        "evaluate_qualified_component_with_additional_read_only_evidence",'''


def replace_exactly_once(
    source: str,
    old: str,
    new: str,
    label: str,
) -> str:
    occurrence_count = source.count(old)

    if occurrence_count != 1:
        raise SystemExit(
            f"[FAIL] Expected exactly one {label} block, "
            f"found {occurrence_count}."
        )

    return source.replace(
        old,
        new,
        1,
    )


def main() -> int:
    print("========================================")
    print(" OIA-020 INSTALLER CORRECTION V2")
    print(" ACTUAL OIA-019 MULTILINE CONTRACT")
    print(" VERIFICATION REPAIR")
    print("========================================")

    if not TARGET_INSTALLER.exists():
        raise SystemExit(
            "[FAIL] OIA-020 installer is missing: "
            f"{TARGET_INSTALLER.resolve()}"
        )

    original_source = TARGET_INSTALLER.read_text(
        encoding="utf-8"
    )

    corrected_source = replace_exactly_once(
        original_source,
        OLD_WORK_ITEM_TOKEN,
        NEW_WORK_ITEM_TOKENS,
        "WORK_ITEM_POLICY_ID verification",
    )

    corrected_source = replace_exactly_once(
        corrected_source,
        OLD_RESEARCH_OBJECTIVE_TOKEN,
        NEW_RESEARCH_OBJECTIVE_TOKENS,
        "RESEARCH_OBJECTIVE verification",
    )

    if corrected_source == original_source:
        raise SystemExit(
            "[FAIL] OIA-020 installer correction made no changes."
        )

    ast.parse(
        corrected_source,
        filename=str(TARGET_INSTALLER),
    )

    TARGET_INSTALLER.write_text(
        corrected_source,
        encoding="utf-8",
        newline="\n",
    )

    verification_source = TARGET_INSTALLER.read_text(
        encoding="utf-8"
    )

    ast.parse(
        verification_source,
        filename=str(TARGET_INSTALLER),
    )

    required_corrected_tokens = (
        '"WORK_ITEM_POLICY_ID",',
        (
            '"oracle.qualified-research-work-item-'
            'materialization.v1",'
        ),
        '"RESEARCH_OBJECTIVE",',
        (
            '"evaluate_qualified_component_with_'
            'additional_read_only_evidence",'
        ),
    )

    missing = [
        token
        for token in required_corrected_tokens
        if token not in verification_source
    ]

    if missing:
        raise SystemExit(
            "[FAIL] Corrected OIA-020 installer verification "
            f"tokens are missing: {missing}"
        )

    print(
        "[OK] FULL REPLACEMENT: "
        f"{TARGET_INSTALLER.resolve()}"
    )
    print(
        "[OK] Brittle single-line WORK_ITEM_POLICY_ID "
        "verification removed"
    )
    print(
        "[OK] Brittle single-line RESEARCH_OBJECTIVE "
        "verification removed"
    )
    print(
        "[OK] Actual OIA-019 multiline constant verification installed"
    )
    print(
        "[OK] Corrected OIA-020 installer syntax verified"
    )
    print(
        "[DONE] OIA-020 installer contract verification corrected"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )