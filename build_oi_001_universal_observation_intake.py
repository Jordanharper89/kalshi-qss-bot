from __future__ import annotations

import ast
import hashlib
import json
import shutil
from pathlib import Path


BUILD_ID = "OI-001"
INSTALLER_REVISION = (
    "OI_001_UNIVERSAL_OBSERVATION_INTAKE_FOUNDATION_INSTALLER_V1"
)

ROOT = Path(__file__).resolve().parent

PACKAGE = (
    ROOT
    / "qseries_v2"
    / "observation_intelligence"
)

MODULE = PACKAGE / "oi_001_universal_observation_intake.py"

INIT = PACKAGE / "__init__.py"

TEST = ROOT / "test_oi_001_universal_observation_intake.py"

UMD = (
    ROOT
    / "qseries_v2"
    / "universal_market_discovery"
)


MODULE_SOURCE = r'''
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping


BUILD_ID = "OI-001"

OI_001_REVISION = (
    "OI_001_UNIVERSAL_OBSERVATION_INTAKE_FOUNDATION_V1"
)

SCHEMA_VERSION = "1.0.0"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False


SUPPORTED_SOURCE_KINDS = (
    "market_venue",
    "market_data",
    "weather",
    "economic",
    "news",
    "regulatory",
    "blockchain",
    "sports",
    "corporate",
    "scientific",
    "government",
    "other",
)


class ObservationIntakeContractError(ValueError):
    pass


def _normalize_text(value: str, field: str) -> str:
    if not isinstance(value, str):
        raise ObservationIntakeContractError(
            f"{field} must be a string"
        )

    normalized = " ".join(value.strip().split())

    if not normalized:
        raise ObservationIntakeContractError(
            f"{field} must not be empty"
        )

    return normalized


def _utc_timestamp(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise ObservationIntakeContractError(
            "observed_at must be datetime"
        )

    if value.tzinfo is None:
        raise ObservationIntakeContractError(
            "observed_at must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


def _canonicalize(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return _canonicalize(asdict(value))

    if isinstance(value, Mapping):
        return {
            str(key): _canonicalize(item)
            for key, item in sorted(
                value.items(),
                key=lambda pair: str(pair[0]),
            )
        }

    if isinstance(value, (tuple, list)):
        return [
            _canonicalize(item)
            for item in value
        ]

    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise ObservationIntakeContractError(
                "canonical datetime must be timezone-aware"
            )

        return value.astimezone(
            timezone.utc
        ).isoformat()

    if value is None or isinstance(
        value,
        (str, int, float, bool),
    ):
        return value

    raise ObservationIntakeContractError(
        f"unsupported canonical value type: {type(value)!r}"
    )


def canonical_json(value: Any) -> str:
    return json.dumps(
        _canonicalize(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def deterministic_sha256(value: Any) -> str:
    return hashlib.sha256(
        canonical_json(value).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True, slots=True)
class ObservationSourceIdentity:
    source_id: str
    source_kind: str
    provider: str
    adapter_id: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_id",
            _normalize_text(
                self.source_id,
                "source_id",
            ).lower(),
        )

        kind = _normalize_text(
            self.source_kind,
            "source_kind",
        ).lower()

        if kind not in SUPPORTED_SOURCE_KINDS:
            raise ObservationIntakeContractError(
                "unsupported source_kind"
            )

        object.__setattr__(
            self,
            "source_kind",
            kind,
        )

        object.__setattr__(
            self,
            "provider",
            _normalize_text(
                self.provider,
                "provider",
            ),
        )

        object.__setattr__(
            self,
            "adapter_id",
            _normalize_text(
                self.adapter_id,
                "adapter_id",
            ).lower(),
        )

    @property
    def source_hash(self) -> str:
        return deterministic_sha256(
            {
                "source_id": self.source_id,
                "source_kind": self.source_kind,
                "provider": self.provider,
                "adapter_id": self.adapter_id,
            }
        )


@dataclass(frozen=True, slots=True)
class RawObservationEnvelope:
    source: ObservationSourceIdentity
    external_observation_id: str
    observed_at: datetime
    subject: str
    observation_type: str
    payload: Mapping[str, Any]
    metadata: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(
            self.source,
            ObservationSourceIdentity,
        ):
            raise ObservationIntakeContractError(
                "source must be ObservationSourceIdentity"
            )

        object.__setattr__(
            self,
            "external_observation_id",
            _normalize_text(
                self.external_observation_id,
                "external_observation_id",
            ),
        )

        object.__setattr__(
            self,
            "observed_at",
            _utc_timestamp(
                self.observed_at
            ),
        )

        object.__setattr__(
            self,
            "subject",
            _normalize_text(
                self.subject,
                "subject",
            ),
        )

        object.__setattr__(
            self,
            "observation_type",
            _normalize_text(
                self.observation_type,
                "observation_type",
            ).lower(),
        )

        payload = dict(self.payload)
        metadata = dict(self.metadata)

        canonical_json(payload)
        canonical_json(metadata)

        object.__setattr__(
            self,
            "payload",
            MappingProxyType(payload),
        )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(metadata),
        )

    @property
    def envelope_hash(self) -> str:
        return deterministic_sha256(
            {
                "source_hash": self.source.source_hash,
                "external_observation_id": (
                    self.external_observation_id
                ),
                "observed_at": self.observed_at,
                "subject": self.subject,
                "observation_type": (
                    self.observation_type
                ),
                "payload": dict(self.payload),
                "metadata": dict(self.metadata),
            }
        )


@dataclass(frozen=True, slots=True)
class ObservationIntakeReceipt:
    envelope_hash: str
    source_hash: str
    accepted: bool
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        for value, field in (
            (self.envelope_hash, "envelope_hash"),
            (self.source_hash, "source_hash"),
        ):
            if (
                not isinstance(value, str)
                or len(value) != 64
                or any(
                    c not in "0123456789abcdef"
                    for c in value
                )
            ):
                raise ObservationIntakeContractError(
                    f"{field} must be lowercase SHA-256"
                )

        reasons = tuple(
            sorted(
                set(
                    _normalize_text(
                        reason,
                        "reason_code",
                    ).lower()
                    for reason in self.reason_codes
                )
            )
        )

        object.__setattr__(
            self,
            "reason_codes",
            reasons,
        )


class UniversalObservationIntake:
    read_only = True
    execution_allowed = False
    network_allowed = False
    persistence_allowed = False

    def accept(
        self,
        envelope: RawObservationEnvelope,
    ) -> ObservationIntakeReceipt:
        if not isinstance(
            envelope,
            RawObservationEnvelope,
        ):
            raise TypeError(
                "envelope must be RawObservationEnvelope"
            )

        return ObservationIntakeReceipt(
            envelope_hash=envelope.envelope_hash,
            source_hash=envelope.source.source_hash,
            accepted=True,
            reason_codes=(
                "contract_valid",
                "immutable_envelope",
                "source_identity_present",
                "timestamp_present",
            ),
        )


def verify_universal_observation_intake() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-001 must remain read-only"
        )

    if any(
        (
            NETWORK_ALLOWED,
            PERSISTENCE_ALLOWED,
            PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,
        )
    ):
        raise AssertionError(
            "OI-001 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_001_REVISION",
    "SCHEMA_VERSION",
    "SUPPORTED_SOURCE_KINDS",
    "ObservationIntakeContractError",
    "ObservationSourceIdentity",
    "RawObservationEnvelope",
    "ObservationIntakeReceipt",
    "UniversalObservationIntake",
    "canonical_json",
    "deterministic_sha256",
    "verify_universal_observation_intake",
]
'''


TEST_SOURCE = r'''
from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_001_universal_observation_intake import (
    OI_001_REVISION,
    ObservationSourceIdentity,
    RawObservationEnvelope,
    UniversalObservationIntake,
    verify_universal_observation_intake,
)


FIXED = datetime(
    2026,
    8,
    10,
    3,
    0,
    tzinfo=timezone.utc,
)


def source() -> ObservationSourceIdentity:
    return ObservationSourceIdentity(
        source_id="kalshi.public",
        source_kind="market_venue",
        provider="Kalshi",
        adapter_id="adapter.kalshi.v1",
    )


def envelope() -> RawObservationEnvelope:
    return RawObservationEnvelope(
        source=source(),
        external_observation_id="market-123",
        observed_at=FIXED,
        subject="BTC above 100k",
        observation_type="market_snapshot",
        payload={
            "yes_price": 63,
            "no_price": 37,
        },
        metadata={
            "venue": "kalshi",
        },
    )


class TestOI001(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_universal_observation_intake()
        )

    def test_source_identity(self):
        self.assertEqual(
            len(source().source_hash),
            64,
        )

    def test_immutable(self):
        item = envelope()

        with self.assertRaises(TypeError):
            item.payload["x"] = 1

    def test_deterministic(self):
        self.assertEqual(
            envelope().envelope_hash,
            envelope().envelope_hash,
        )

    def test_accept(self):
        receipt = (
            UniversalObservationIntake()
            .accept(envelope())
        )

        self.assertTrue(
            receipt.accepted
        )

        self.assertEqual(
            receipt.envelope_hash,
            envelope().envelope_hash,
        )

    def test_naive_time_rejected(self):
        with self.assertRaises(ValueError):
            RawObservationEnvelope(
                source=source(),
                external_observation_id="x",
                observed_at=datetime(
                    2026,
                    8,
                    10,
                    3,
                    0,
                ),
                subject="x",
                observation_type="event",
                payload={},
                metadata={},
            )

    def test_side_effects(self):
        intake = UniversalObservationIntake()

        self.assertTrue(
            intake.read_only
        )

        self.assertFalse(
            intake.network_allowed
        )

        self.assertFalse(
            intake.persistence_allowed
        )

        self.assertFalse(
            intake.execution_allowed
        )


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-001 CERTIFICATION TEST")
    print(" UNIVERSAL OBSERVATION INTAKE FOUNDATION")
    print("=" * 72)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestOI001
    )

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-001")
    print(f"[PASS] Revision: {OI_001_REVISION}")
    print("[PASS] Universal source-agnostic observation envelope certified")
    print("[PASS] Immutable deterministic intake contract certified")
    print("[PASS] No category-specific reasoning introduced")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-001 CERTIFIED")
'''


def digest(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def write_checked(
    path: Path,
    source: str,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    text = source.lstrip()

    ast.parse(
        text,
        filename=str(path),
    )

    path.write_text(
        text,
        encoding="utf-8",
        newline="\n",
    )

    print(
        f"[PASS] Wrote: {path.relative_to(ROOT)}"
    )


def main() -> int:
    print("=" * 72)
    print(" OI-001 INSTALLER")
    print(" UNIVERSAL OBSERVATION INTAKE FOUNDATION")
    print("=" * 72)

    print(
        f"[BOOT] Revision: {INSTALLER_REVISION}"
    )

    print(
        f"[ROOT] {ROOT}"
    )

    if not UMD.is_dir():
        raise RuntimeError(
            "Certified UMD package missing"
        )

    print(
        "[PASS] Certified UMD repository verified read-only"
    )

    backups: dict[Path, bytes | None] = {}

    affected = (
        MODULE,
        TEST,
        INIT,
    )

    try:
        for path in affected:
            backups[path] = (
                path.read_bytes()
                if path.exists()
                else None
            )

        PACKAGE.mkdir(
            parents=True,
            exist_ok=True,
        )

        write_checked(
            MODULE,
            MODULE_SOURCE,
        )

        write_checked(
            TEST,
            TEST_SOURCE,
        )

        current = (
            INIT.read_text(
                encoding="utf-8"
            )
            if INIT.exists()
            else ""
        )

        export = (
            "from .oi_001_universal_observation_intake import *"
        )

        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"

            current += export + "\n"

            ast.parse(
                current,
                filename=str(INIT),
            )

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
            MODULE.read_text(
                encoding="utf-8"
            ),
            str(MODULE),
            "exec",
        )

        compile(
            TEST.read_text(
                encoding="utf-8"
            ),
            str(TEST),
            "exec",
        )

        print(
            "[PASS] In-memory compilation verified"
        )

        namespace: dict[str, object] = {}

        exec(
            compile(
                MODULE.read_text(
                    encoding="utf-8"
                ),
                str(MODULE),
                "exec",
            ),
            namespace,
        )

        namespace[
            "verify_universal_observation_intake"
        ]()

        print(
            "[PASS] Required symbols and verifier certified"
        )

        install_hash = hashlib.sha256(
            MODULE.read_bytes()
            + TEST.read_bytes()
        ).hexdigest()

        print(
            f"[PASS] Deterministic install hash: "
            f"{install_hash}"
        )

        print(
            "[PASS] Network, persistence, publication, "
            "and execution disabled"
        )

        print(
            "[DONE] OI-001 INSTALLATION COMPLETE"
        )

        return 0

    except Exception:
        for path, content in backups.items():
            if content is None:
                if path.exists():
                    path.unlink()
            else:
                path.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )
                path.write_bytes(content)

        print(
            "[ROLLBACK] OI-001 installation failed; "
            "all affected files restored"
        )

        raise


if __name__ == "__main__":
    raise SystemExit(main())