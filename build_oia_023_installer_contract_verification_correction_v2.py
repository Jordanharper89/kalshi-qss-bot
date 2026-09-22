from __future__ import annotations

import ast
from pathlib import Path


TARGET_INSTALLER = (
    "build_oia_023_oracle_qualified_research_"
    "worker_session_manifest_builder.py"
)


def main() -> int:
    root = Path.cwd()
    installer_path = root / TARGET_INSTALLER

    print("========================================")
    print(" OIA-023 INSTALLER CORRECTION V2")
    print(" ACTUAL OIA-022 ACTIVATION HASH")
    print(" CONTRACT VERIFICATION REPAIR")
    print("========================================")

    if not installer_path.exists():
        raise SystemExit(
            "[FAIL] OIA-023 installer is missing: "
            f"{installer_path.resolve()}"
        )

    original = installer_path.read_text(
        encoding="utf-8"
    )

    incorrect_block = '''        "activation_sequence",
        "source_activation_hash",
        "source_claim_hash",
'''

    corrected_block = '''        "activation_sequence",
        "source_claim_hash",
'''

    if incorrect_block not in original:
        if corrected_block in original:
            print(
                "[OK] Incorrect source_activation_hash "
                "verification is already absent"
            )

            ast.parse(
                original,
                filename=str(installer_path),
            )

            print(
                "[OK] Existing OIA-023 installer "
                "syntax verified"
            )

            print(
                "[DONE] OIA-023 installer contract "
                "verification already corrected"
            )

            return 0

        raise SystemExit(
            "[FAIL] Expected OIA-023 verification "
            "block was not found. No changes written."
        )

    corrected = original.replace(
        incorrect_block,
        corrected_block,
        1,
    )

    if corrected == original:
        raise SystemExit(
            "[FAIL] OIA-023 installer correction "
            "did not modify the file."
        )

    if '"source_activation_hash",' in corrected:
        raise SystemExit(
            "[FAIL] Incorrect source_activation_hash "
            "verification remains after correction."
        )

    ast.parse(
        corrected,
        filename=str(installer_path),
    )

    installer_path.write_text(
        corrected,
        encoding="utf-8",
        newline="\n",
    )

    print(
        "[OK] FULL REPLACEMENT: "
        f"{installer_path.resolve()}"
    )

    print(
        "[OK] Invalid source_activation_hash "
        "verification removed"
    )

    print(
        "[OK] Actual OIA-022 activation_hash "
        "contract retained"
    )

    print(
        "[OK] Corrected OIA-023 installer "
        "syntax verified"
    )

    print(
        "[DONE] OIA-023 installer contract "
        "verification corrected"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )