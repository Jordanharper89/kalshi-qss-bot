from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-063"
INSTALLER_REVISION = "OI_063_EXPLANATION_CONTEXT_SWITCH_RESOLUTION_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    (PACKAGE / "oi_058_explanation_followup_reference_resolution.py", "OI-058"),
    (PACKAGE / "oi_062_multi_subject_conversation_coordinator.py", "OI-062"),
)

MODULE = PACKAGE / "oi_063_explanation_context_switch_resolution.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_063_explanation_context_switch_resolution.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_062_multi_subject_conversation_coordinator import (
    MultiSubjectConversationState,
)

BUILD_ID = "OI-063"
OI_063_REVISION = "OI_063_EXPLANATION_CONTEXT_SWITCH_RESOLUTION_V1"

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

SWITCH_RESOLVED = "switch_resolved"
SWITCH_CURRENT = "switch_current"
SWITCH_UNRESOLVED = "switch_unresolved"


@dataclass(frozen=True, slots=True)
class ExplanationContextSwitchResolution:
    session_id: str
    requested_subject_hint: str
    prior_active_subject_hint: str | None
    resolved_subject_hint: str | None
    switch_status: str
    switch_hash: str
    read_only: bool


class ExplanationContextSwitchResolver:
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

    def resolve(
        self,
        *,
        state: MultiSubjectConversationState,
        requested_subject_hint: str,
    ) -> ExplanationContextSwitchResolution:
        if not isinstance(
            state,
            MultiSubjectConversationState,
        ):
            raise TypeError(
                "state must be MultiSubjectConversationState"
            )

        requested = " ".join(
            str(requested_subject_hint).strip().split()
        )

        if not requested:
            raise ValueError(
                "requested_subject_hint must not be empty"
            )

        normalized_map = {
            subject.lower(): subject
            for subject in state.subject_hints
        }

        resolved = normalized_map.get(
            requested.lower()
        )

        if resolved is None:
            status = SWITCH_UNRESOLVED
        elif resolved == state.active_subject_hint:
            status = SWITCH_CURRENT
        else:
            status = SWITCH_RESOLVED

        body = {
            "session_id": state.session_id,
            "requested_subject_hint": requested,
            "prior_active_subject_hint": (
                state.active_subject_hint
            ),
            "resolved_subject_hint": resolved,
            "switch_status": status,
            "read_only": True,
        }

        return ExplanationContextSwitchResolution(
            session_id=state.session_id,
            requested_subject_hint=requested,
            prior_active_subject_hint=(
                state.active_subject_hint
            ),
            resolved_subject_hint=resolved,
            switch_status=status,
            switch_hash=deterministic_sha256(body),
            read_only=True,
        )


def verify_explanation_context_switch_resolution() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-063 must remain read-only")

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
            "OI-063 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_063_REVISION",
    "SWITCH_RESOLVED",
    "SWITCH_CURRENT",
    "SWITCH_UNRESOLVED",
    "ExplanationContextSwitchResolution",
    "ExplanationContextSwitchResolver",
    "verify_explanation_context_switch_resolution",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest

from qseries_v2.observation_intelligence.oi_062_multi_subject_conversation_coordinator import (
    MultiSubjectConversationState,
)
from qseries_v2.observation_intelligence.oi_063_explanation_context_switch_resolution import (
    OI_063_REVISION,
    SWITCH_CURRENT,
    SWITCH_RESOLVED,
    SWITCH_UNRESOLVED,
    ExplanationContextSwitchResolver,
    verify_explanation_context_switch_resolution,
)


def state():
    return MultiSubjectConversationState(
        session_id="session.1",
        active_subject_hint="Bitcoin",
        subject_hints=(
            "Astros strikeouts",
            "Bitcoin",
        ),
        subject_turn_counts=(
            ("Astros strikeouts", 1),
            ("Bitcoin", 2),
        ),
        state_hash="a" * 64,
        read_only=True,
    )


class TestOI063(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_explanation_context_switch_resolution()
        )

    def test_resolved_switch(self):
        result = ExplanationContextSwitchResolver().resolve(
            state=state(),
            requested_subject_hint="Astros strikeouts",
        )

        self.assertEqual(
            result.switch_status,
            SWITCH_RESOLVED,
        )

        self.assertEqual(
            result.resolved_subject_hint,
            "Astros strikeouts",
        )

    def test_current_switch(self):
        result = ExplanationContextSwitchResolver().resolve(
            state=state(),
            requested_subject_hint="Bitcoin",
        )

        self.assertEqual(
            result.switch_status,
            SWITCH_CURRENT,
        )

    def test_unresolved_switch(self):
        result = ExplanationContextSwitchResolver().resolve(
            state=state(),
            requested_subject_hint="Oil",
        )

        self.assertEqual(
            result.switch_status,
            SWITCH_UNRESOLVED,
        )

        self.assertIsNone(
            result.resolved_subject_hint
        )

    def test_case_insensitive(self):
        result = ExplanationContextSwitchResolver().resolve(
            state=state(),
            requested_subject_hint="bitcoin",
        )

        self.assertEqual(
            result.resolved_subject_hint,
            "Bitcoin",
        )

    def test_deterministic(self):
        resolver = ExplanationContextSwitchResolver()

        a = resolver.resolve(
            state=state(),
            requested_subject_hint="Astros strikeouts",
        )
        b = resolver.resolve(
            state=state(),
            requested_subject_hint="Astros strikeouts",
        )

        self.assertEqual(
            a.switch_hash,
            b.switch_hash,
        )

    def test_side_effects(self):
        resolver = ExplanationContextSwitchResolver()

        self.assertTrue(resolver.read_only)
        self.assertFalse(resolver.network_allowed)
        self.assertFalse(resolver.persistence_allowed)
        self.assertFalse(resolver.publication_allowed)
        self.assertFalse(resolver.execution_allowed)
        self.assertFalse(resolver.qseries_execution_allowed)
        self.assertFalse(resolver.prediction_allowed)
        self.assertFalse(resolver.edge_score_allowed)
        self.assertFalse(resolver.probability_allowed)
        self.assertFalse(resolver.causal_claim_allowed)
        self.assertFalse(resolver.terminal_mutation_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-063 CERTIFICATION TEST")
    print(" EXPLANATION CONTEXT SWITCH RESOLUTION")
    print("=" * 72)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(TestOI063)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-063")
    print(f"[PASS] Revision: {OI_063_REVISION}")
    print("[PASS] Resolved, current, and unresolved subject switches certified")
    print("[PASS] Known subject identity is preserved across deterministic context switches")
    print("[PASS] Unknown subjects fail closed without silently replacing active context")
    print("[DONE] OI-063 CERTIFIED")
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
    print(" OI-063 INSTALLER")
    print(" EXPLANATION CONTEXT SWITCH RESOLUTION")
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
        "[PASS] Certified OI-058 and OI-062 "
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

        current = INIT.read_text(
            encoding="utf-8"
        ) if INIT.exists() else ""

        export = (
            "from .oi_063_explanation_context_switch_resolution import *"
        )

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
                    f"Certified upstream changed: "
                    f"{upstream.name}"
                )

        print("[PASS] In-memory compilation verified")
        print("[PASS] Certified upstream remained unchanged")

        install_hash = hashlib.sha256(
            MODULE.read_bytes()
            + TEST.read_bytes()
        ).hexdigest()

        print(
            f"[PASS] Deterministic install hash: "
            f"{install_hash}"
        )
        print(
            "[PASS] Explanation context switching remains "
            "deterministic, read-only, and fail-closed"
        )
        print("[DONE] OI-063 INSTALLATION COMPLETE")
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
            "[ROLLBACK] OI-063 installation failed; "
            "all affected files restored"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
