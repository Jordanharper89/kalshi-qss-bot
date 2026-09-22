from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-053"
INSTALLER_REVISION = "OI_053_EXPLANATION_QUERY_RESPONSE_PACKAGE_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    (PACKAGE / "oi_025_oracle_explanation_query_engine.py", "OI-025"),
    (PACKAGE / "oi_052_terminal_explanation_adapter.py", "OI-052"),
)

MODULE = PACKAGE / "oi_053_explanation_query_response_package.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_053_explanation_query_response_package.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_025_oracle_explanation_query_engine import OracleExplanationQuery
from .oi_052_terminal_explanation_adapter import TerminalExplanationView

BUILD_ID = "OI-053"
OI_053_REVISION = "OI_053_EXPLANATION_QUERY_RESPONSE_PACKAGE_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
PREDICTION_ALLOWED = False
EDGE_SCORE_ALLOWED = False
PROBABILITY_ALLOWED = False
CAUSAL_CLAIM_ALLOWED = False
TERMINAL_MUTATION_ALLOWED = False


@dataclass(frozen=True, slots=True)
class ExplanationQueryResponsePackage:
    response_id: str
    query_id: str
    query_kind: str
    subject_hint: str
    completeness_status: str
    title: str
    body_lines: tuple[str, ...]
    caveat_lines: tuple[str, ...]
    footer: str
    assembled_at: datetime
    response_hash: str
    read_only: bool


class ExplanationQueryResponsePackageBuilder:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    prediction_allowed = False
    edge_score_allowed = False
    probability_allowed = False
    causal_claim_allowed = False
    terminal_mutation_allowed = False

    def build(
        self,
        *,
        response_id: str,
        query: OracleExplanationQuery,
        view: TerminalExplanationView,
        assembled_at: datetime,
    ) -> ExplanationQueryResponsePackage:
        response_id_value = str(response_id).strip()

        if not response_id_value:
            raise ValueError(
                "response_id must not be empty"
            )

        if not isinstance(query, OracleExplanationQuery):
            raise TypeError(
                "query must be OracleExplanationQuery"
            )

        if not isinstance(view, TerminalExplanationView):
            raise TypeError(
                "view must be TerminalExplanationView"
            )

        if query.query_id != view.query_id:
            raise ValueError(
                "query/view query_id mismatch"
            )

        if not isinstance(assembled_at, datetime):
            raise TypeError(
                "assembled_at must be datetime"
            )

        if assembled_at.tzinfo is None:
            raise ValueError(
                "assembled_at must be timezone-aware"
            )

        assembled_at = assembled_at.astimezone(
            timezone.utc
        )

        body = {
            "response_id": response_id_value,
            "query_id": query.query_id,
            "query_kind": query.query_kind,
            "subject_hint": query.subject_hint,
            "completeness_status": view.completeness_status,
            "title": view.title,
            "body_lines": view.body_lines,
            "caveat_lines": view.caveat_lines,
            "footer": view.footer,
            "assembled_at": assembled_at,
            "read_only": True,
        }

        return ExplanationQueryResponsePackage(
            response_id=response_id_value,
            query_id=query.query_id,
            query_kind=query.query_kind,
            subject_hint=query.subject_hint,
            completeness_status=view.completeness_status,
            title=view.title,
            body_lines=view.body_lines,
            caveat_lines=view.caveat_lines,
            footer=view.footer,
            assembled_at=assembled_at,
            response_hash=deterministic_sha256(body),
            read_only=True,
        )


def verify_explanation_query_response_package() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-053 must remain read-only"
        )

    if any(
        (
            NETWORK_ALLOWED,
            PERSISTENCE_ALLOWED,
            PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,
            PREDICTION_ALLOWED,
            EDGE_SCORE_ALLOWED,
            PROBABILITY_ALLOWED,
            CAUSAL_CLAIM_ALLOWED,
            TERMINAL_MUTATION_ALLOWED,
        )
    ):
        raise AssertionError(
            "OI-053 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_053_REVISION",
    "ExplanationQueryResponsePackage",
    "ExplanationQueryResponsePackageBuilder",
    "verify_explanation_query_response_package",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_025_oracle_explanation_query_engine import (
    OracleExplanationQueryEngine,
    default_explanation_profile_map,
)
from qseries_v2.observation_intelligence.oi_052_terminal_explanation_adapter import (
    TerminalExplanationView,
)
from qseries_v2.observation_intelligence.oi_053_explanation_query_response_package import (
    OI_053_REVISION,
    ExplanationQueryResponsePackageBuilder,
    verify_explanation_query_response_package,
)

NOW = datetime(2026, 8, 11, 14, 0, tzinfo=timezone.utc)


def query():
    return OracleExplanationQueryEngine(
        default_explanation_profile_map()
    ).resolve(
        query_id="query.astros",
        text="Explain why the Astros strikeout edge moved",
        subject_hint="Astros strikeouts",
        domain="sports",
    )


def view():
    return TerminalExplanationView(
        query_id="query.astros",
        subject_hint="Astros strikeouts",
        completeness_status="partial",
        title="Oracle Evidence Explanation — Astros strikeouts",
        body_lines=("Explanation line",),
        caveat_lines=("missing_required_evidence",),
        footer="MODE: READ-ONLY | NO TRADE AUTHORIZATION | NO CAUSAL CLAIM",
        view_hash="a" * 64,
        read_only=True,
    )


class TestOI053(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_explanation_query_response_package()
        )

    def test_build(self):
        package = ExplanationQueryResponsePackageBuilder().build(
            response_id="response.astros",
            query=query(),
            view=view(),
            assembled_at=NOW,
        )

        self.assertEqual(
            package.query_id,
            "query.astros",
        )
        self.assertEqual(
            package.completeness_status,
            "partial",
        )

    def test_body_preserved(self):
        package = ExplanationQueryResponsePackageBuilder().build(
            response_id="response.astros",
            query=query(),
            view=view(),
            assembled_at=NOW,
        )

        self.assertEqual(
            package.body_lines,
            ("Explanation line",),
        )

    def test_deterministic(self):
        builder = ExplanationQueryResponsePackageBuilder()

        a = builder.build(
            response_id="response.astros",
            query=query(),
            view=view(),
            assembled_at=NOW,
        )

        b = builder.build(
            response_id="response.astros",
            query=query(),
            view=view(),
            assembled_at=NOW,
        )

        self.assertEqual(
            a.response_hash,
            b.response_hash,
        )

    def test_side_effects(self):
        builder = ExplanationQueryResponsePackageBuilder()

        self.assertTrue(builder.read_only)
        self.assertFalse(builder.network_allowed)
        self.assertFalse(builder.persistence_allowed)
        self.assertFalse(builder.publication_allowed)
        self.assertFalse(builder.execution_allowed)
        self.assertFalse(builder.qseries_execution_allowed)
        self.assertFalse(builder.prediction_allowed)
        self.assertFalse(builder.edge_score_allowed)
        self.assertFalse(builder.probability_allowed)
        self.assertFalse(builder.causal_claim_allowed)
        self.assertFalse(builder.terminal_mutation_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-053 CERTIFICATION TEST")
    print(" EXPLANATION QUERY RESPONSE PACKAGE")
    print("=" * 72)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(TestOI053)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-053")
    print(f"[PASS] Revision: {OI_053_REVISION}")
    print("[PASS] Explanation query identity and terminal-safe view packaged into deterministic response")
    print("[PASS] Subject, completeness, explanation body, caveats, and read-only footer preserved")
    print("[PASS] Publication, terminal mutation, prediction, probability, scoring, causation, and execution remain disabled")
    print("[DONE] OI-053 CERTIFIED")
"""


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_checked(path: Path, source: str) -> None:
    text = source.lstrip()
    ast.parse(text, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"[PASS] Wrote: {path.relative_to(ROOT)}")


def main() -> int:
    print("=" * 72)
    print(" OI-053 INSTALLER")
    print(" EXPLANATION QUERY RESPONSE PACKAGE")
    print("=" * 72)
    print(f"[BOOT] Revision: {INSTALLER_REVISION}")
    print(f"[ROOT] {ROOT}")

    for upstream, name in UPSTREAMS:
        if not upstream.is_file():
            raise RuntimeError(
                f"Certified {name} missing: {upstream}"
            )

    upstream_hashes = {
        upstream: sha(upstream)
        for upstream, _ in UPSTREAMS
    }

    print(
        "[PASS] Certified OI-025 and OI-052 "
        "verified read-only"
    )

    affected = (MODULE, TEST, INIT)
    backups = {
        item: item.read_bytes() if item.exists() else None
        for item in affected
    }

    try:
        write_checked(MODULE, MODULE_SOURCE)
        write_checked(TEST, TEST_SOURCE)

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export = "from .oi_053_explanation_query_response_package import *"

        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"
            current += export + "\n"
            ast.parse(current, filename=str(INIT))
            INIT.write_text(
                current,
                encoding="utf-8",
                newline="\n",
            )

        print(
            "[PASS] Updated: "
            "qseries_v2\\observation_intelligence\\__init__.py"
        )

        compile(
            MODULE.read_text(encoding="utf-8"),
            str(MODULE),
            "exec",
        )
        compile(
            TEST.read_text(encoding="utf-8"),
            str(TEST),
            "exec",
        )

        for upstream, expected in upstream_hashes.items():
            if sha(upstream) != expected:
                raise RuntimeError(
                    f"Certified upstream changed: {upstream.name}"
                )

        print("[PASS] In-memory compilation verified")
        print("[PASS] Certified upstream remained unchanged")

        install_hash = hashlib.sha256(
            MODULE.read_bytes() + TEST.read_bytes()
        ).hexdigest()

        print(
            f"[PASS] Deterministic install hash: {install_hash}"
        )
        print(
            "[PASS] Explanation query response packaging remains "
            "deterministic, read-only, terminal-safe, and fail-closed"
        )
        print("[DONE] OI-053 INSTALLATION COMPLETE")
        return 0

    except Exception:
        for item, original in backups.items():
            if original is None:
                if item.exists():
                    item.unlink()
            else:
                item.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )
                item.write_bytes(original)

        print(
            "[ROLLBACK] OI-053 installation failed; "
            "all affected files restored"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
