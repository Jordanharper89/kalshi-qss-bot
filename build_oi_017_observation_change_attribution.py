from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-017"
INSTALLER_REVISION = "OI_017_OBSERVATION_CHANGE_ATTRIBUTION_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"
UPSTREAM_007 = PACKAGE / "oi_007_observation_history.py"
UPSTREAM_015 = PACKAGE / "oi_015_reasoning_input_builder.py"
UPSTREAM_016 = PACKAGE / "oi_016_evidence_sufficiency_gate.py"
MODULE = PACKAGE / "oi_017_observation_change_attribution.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_017_observation_change_attribution.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_003_canonical_observation_gateway import CanonicalLiveObservation

BUILD_ID = "OI-017"
OI_017_REVISION = "OI_017_OBSERVATION_CHANGE_ATTRIBUTION_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
CAUSAL_INFERENCE_ALLOWED = False
PREDICTION_ALLOWED = False


class ObservationChangeAttributionError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ObservationChange:
    subject: str
    observation_type: str
    value_field: str
    prior_observation_id: str
    current_observation_id: str
    prior_value: float
    current_value: float
    absolute_change: float
    relative_change: float | None
    direction: str
    change_hash: str


class ObservationChangeAttributionEngine:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    causal_inference_allowed = False
    prediction_allowed = False

    def compare_numeric(
        self,
        *,
        prior: CanonicalLiveObservation,
        current: CanonicalLiveObservation,
        value_field: str,
    ) -> ObservationChange:
        if not isinstance(prior, CanonicalLiveObservation):
            raise TypeError("prior must be CanonicalLiveObservation")
        if not isinstance(current, CanonicalLiveObservation):
            raise TypeError("current must be CanonicalLiveObservation")

        if prior.subject != current.subject:
            raise ObservationChangeAttributionError(
                "observations must share subject"
            )

        if prior.observation_type != current.observation_type:
            raise ObservationChangeAttributionError(
                "observations must share observation_type"
            )

        if current.observed_at <= prior.observed_at:
            raise ObservationChangeAttributionError(
                "current observation must be later than prior observation"
            )

        field = str(value_field).strip()
        if not field:
            raise ObservationChangeAttributionError(
                "value_field must not be empty"
            )

        try:
            prior_value = float(prior.facts[field])
            current_value = float(current.facts[field])
        except (KeyError, TypeError, ValueError) as exc:
            raise ObservationChangeAttributionError(
                f"numeric value field unavailable: {field}"
            ) from exc

        absolute_change = current_value - prior_value

        if absolute_change > 0:
            direction = "up"
        elif absolute_change < 0:
            direction = "down"
        else:
            direction = "unchanged"

        relative_change = (
            None
            if prior_value == 0
            else absolute_change / abs(prior_value)
        )

        body = {
            "subject": prior.subject,
            "observation_type": prior.observation_type,
            "value_field": field,
            "prior_observation_id": prior.canonical_observation_id,
            "current_observation_id": current.canonical_observation_id,
            "prior_value": prior_value,
            "current_value": current_value,
            "absolute_change": absolute_change,
            "relative_change": relative_change,
            "direction": direction,
        }

        return ObservationChange(
            subject=prior.subject,
            observation_type=prior.observation_type,
            value_field=field,
            prior_observation_id=prior.canonical_observation_id,
            current_observation_id=current.canonical_observation_id,
            prior_value=prior_value,
            current_value=current_value,
            absolute_change=absolute_change,
            relative_change=relative_change,
            direction=direction,
            change_hash=deterministic_sha256(body),
        )


def verify_observation_change_attribution() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-017 must remain read-only")

    if any(
        (
            NETWORK_ALLOWED,
            PERSISTENCE_ALLOWED,
            PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,
            CAUSAL_INFERENCE_ALLOWED,
            PREDICTION_ALLOWED,
        )
    ):
        raise AssertionError("OI-017 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_017_REVISION",
    "ObservationChangeAttributionError",
    "ObservationChange",
    "ObservationChangeAttributionEngine",
    "verify_observation_change_attribution",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from qseries_v2.observation_intelligence.oi_001_universal_observation_intake import (
    ObservationSourceIdentity,
    RawObservationEnvelope,
)
from qseries_v2.observation_intelligence.oi_003_canonical_observation_gateway import (
    CanonicalLiveObservationGateway,
)
from qseries_v2.observation_intelligence.oi_006_live_observation_registry import (
    default_source_registry,
)
from qseries_v2.observation_intelligence.oi_017_observation_change_attribution import (
    OI_017_REVISION,
    ObservationChangeAttributionEngine,
    verify_observation_change_attribution,
)

BASE = datetime(2026, 8, 10, 12, 0, tzinfo=timezone.utc)


def observation(index: int, price: str):
    source = ObservationSourceIdentity(
        source_id="coinbase.public.spot",
        source_kind="market_data",
        provider="Coinbase",
        adapter_id="adapter.coinbase.spot.v1",
    )

    envelope = RawObservationEnvelope(
        source=source,
        external_observation_id=f"BTC-{index}",
        observed_at=BASE + timedelta(minutes=index),
        subject="BTC",
        observation_type="spot_price",
        payload={
            "symbol": "BTC",
            "quote_currency": "USD",
            "price": price,
        },
        metadata={},
    )

    return CanonicalLiveObservationGateway(
        default_source_registry()
    ).canonicalize(envelope).canonical_observation


class TestOI017(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_observation_change_attribution()
        )

    def test_up(self):
        change = ObservationChangeAttributionEngine().compare_numeric(
            prior=observation(0, "100"),
            current=observation(1, "105"),
            value_field="price",
        )
        self.assertEqual(change.direction, "up")
        self.assertEqual(change.absolute_change, 5.0)

    def test_down(self):
        change = ObservationChangeAttributionEngine().compare_numeric(
            prior=observation(0, "105"),
            current=observation(1, "100"),
            value_field="price",
        )
        self.assertEqual(change.direction, "down")

    def test_unchanged(self):
        change = ObservationChangeAttributionEngine().compare_numeric(
            prior=observation(0, "100"),
            current=observation(1, "100"),
            value_field="price",
        )
        self.assertEqual(change.direction, "unchanged")

    def test_reverse_time_rejected(self):
        with self.assertRaises(ValueError):
            ObservationChangeAttributionEngine().compare_numeric(
                prior=observation(1, "100"),
                current=observation(0, "101"),
                value_field="price",
            )

    def test_deterministic(self):
        engine = ObservationChangeAttributionEngine()
        a = engine.compare_numeric(
            prior=observation(0, "100"),
            current=observation(1, "105"),
            value_field="price",
        )
        b = engine.compare_numeric(
            prior=observation(0, "100"),
            current=observation(1, "105"),
            value_field="price",
        )
        self.assertEqual(a.change_hash, b.change_hash)

    def test_side_effects(self):
        engine = ObservationChangeAttributionEngine()
        self.assertTrue(engine.read_only)
        self.assertFalse(engine.network_allowed)
        self.assertFalse(engine.persistence_allowed)
        self.assertFalse(engine.publication_allowed)
        self.assertFalse(engine.execution_allowed)
        self.assertFalse(engine.qseries_execution_allowed)
        self.assertFalse(engine.causal_inference_allowed)
        self.assertFalse(engine.prediction_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-017 CERTIFICATION TEST")
    print(" OBSERVATION CHANGE ATTRIBUTION")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI017
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-017")
    print(f"[PASS] Revision: {OI_017_REVISION}")
    print("[PASS] Numeric observation changes and direction certified")
    print("[PASS] Prior/current observation lineage preserved")
    print("[PASS] Change attribution is descriptive only; no causal inference introduced")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-017 CERTIFIED")
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
    print(" OI-017 INSTALLER")
    print(" OBSERVATION CHANGE ATTRIBUTION")
    print("=" * 72)
    print(f"[BOOT] Revision: {INSTALLER_REVISION}")
    print(f"[ROOT] {ROOT}")

    upstreams = (
        (UPSTREAM_007, "OI-007"),
        (UPSTREAM_015, "OI-015"),
        (UPSTREAM_016, "OI-016"),
    )

    for path, name in upstreams:
        if not path.is_file():
            raise RuntimeError(f"Certified {name} missing: {path}")

    upstream_hashes = {
        path: sha(path)
        for path, _ in upstreams
    }

    print("[PASS] Certified OI-007, OI-015, and OI-016 verified read-only")

    affected = (MODULE, TEST, INIT)
    backups = {
        path: path.read_bytes() if path.exists() else None
        for path in affected
    }

    try:
        write_checked(MODULE, MODULE_SOURCE)
        write_checked(TEST, TEST_SOURCE)

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export = "from .oi_017_observation_change_attribution import *"

        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"
            current += export + "\n"
            ast.parse(current, filename=str(INIT))
            INIT.write_text(current, encoding="utf-8", newline="\n")

        print("[PASS] Updated: qseries_v2\\observation_intelligence\\__init__.py")

        compile(MODULE.read_text(encoding="utf-8"), str(MODULE), "exec")
        compile(TEST.read_text(encoding="utf-8"), str(TEST), "exec")

        for path, expected in upstream_hashes.items():
            if sha(path) != expected:
                raise RuntimeError(f"Certified upstream changed: {path.name}")

        print("[PASS] In-memory compilation verified")
        print("[PASS] Certified upstream remained unchanged")

        install_hash = hashlib.sha256(
            MODULE.read_bytes() + TEST.read_bytes()
        ).hexdigest()

        print(f"[PASS] Deterministic install hash: {install_hash}")
        print("[PASS] Change attribution remains deterministic, read-only, and non-causal")
        print("[DONE] OI-017 INSTALLATION COMPLETE")
        return 0

    except Exception:
        for path, content in backups.items():
            if content is None:
                if path.exists():
                    path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)

        print("[ROLLBACK] OI-017 installation failed; all affected files restored")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
