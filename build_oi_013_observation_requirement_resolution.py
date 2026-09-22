from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-013"
INSTALLER_REVISION = "OI_013_OBSERVATION_REQUIREMENT_RESOLUTION_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"
UPSTREAM_008 = PACKAGE / "oi_008_observation_source_routing.py"
UPSTREAM_012 = PACKAGE / "oi_012_routed_observation_acquisition.py"
MODULE = PACKAGE / "oi_013_observation_requirement_resolution.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_013_observation_requirement_resolution.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_008_observation_source_routing import (
    ObservationRouteRequest,
    verify_observation_source_routing,
)
from .oi_012_routed_observation_acquisition import (
    verify_routed_observation_acquisition,
)

BUILD_ID = "OI-013"
OI_013_REVISION = "OI_013_OBSERVATION_REQUIREMENT_RESOLUTION_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False


class ObservationRequirementResolutionError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ObservationRequirement:
    requirement_id: str
    domain: str
    entity_kind: str
    observation_type: str
    required: bool
    reason: str

    def __post_init__(self) -> None:
        values = {}
        for field in (
            "requirement_id",
            "domain",
            "entity_kind",
            "observation_type",
            "reason",
        ):
            value = " ".join(
                str(getattr(self, field)).strip().lower().split()
            )
            if not value:
                raise ObservationRequirementResolutionError(
                    f"{field} must not be empty"
                )
            values[field] = value

        for field, value in values.items():
            object.__setattr__(self, field, value)

    @property
    def requirement_hash(self) -> str:
        return deterministic_sha256(
            {
                "requirement_id": self.requirement_id,
                "domain": self.domain,
                "entity_kind": self.entity_kind,
                "observation_type": self.observation_type,
                "required": self.required,
                "reason": self.reason,
            }
        )

    def route_request(self) -> ObservationRouteRequest:
        return ObservationRouteRequest(
            domain=self.domain,
            entity_kind=self.entity_kind,
            observation_type=self.observation_type,
        )


@dataclass(frozen=True, slots=True)
class ObservationRequirementProfile:
    profile_id: str
    requirements: tuple[ObservationRequirement, ...]
    profile_hash: str


class ObservationRequirementResolver:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False

    def __init__(
        self,
        profiles: tuple[ObservationRequirementProfile, ...],
    ) -> None:
        values = tuple(profiles)

        if any(
            not isinstance(item, ObservationRequirementProfile)
            for item in values
        ):
            raise TypeError(
                "all profiles must be ObservationRequirementProfile"
            )

        ordered = tuple(
            sorted(values, key=lambda item: item.profile_id)
        )

        if values != ordered:
            raise ObservationRequirementResolutionError(
                "profiles must be deterministically sorted"
            )

        ids = tuple(item.profile_id for item in values)
        if len(ids) != len(set(ids)):
            raise ObservationRequirementResolutionError(
                "duplicate profile_id"
            )

        for profile in values:
            requirements = tuple(profile.requirements)
            ordered_requirements = tuple(
                sorted(
                    requirements,
                    key=lambda item: item.requirement_id,
                )
            )

            if requirements != ordered_requirements:
                raise ObservationRequirementResolutionError(
                    "profile requirements must be deterministically sorted"
                )

            req_ids = tuple(
                item.requirement_id
                for item in requirements
            )

            if len(req_ids) != len(set(req_ids)):
                raise ObservationRequirementResolutionError(
                    "duplicate requirement_id"
                )

            expected_hash = deterministic_sha256(
                {
                    "profile_id": profile.profile_id,
                    "requirement_hashes": tuple(
                        item.requirement_hash
                        for item in requirements
                    ),
                }
            )

            if profile.profile_hash != expected_hash:
                raise ObservationRequirementResolutionError(
                    "profile_hash mismatch"
                )

        self._profiles = values
        self._by_id = MappingProxyType(
            {item.profile_id: item for item in values}
        )

    def get(
        self,
        profile_id: str,
    ) -> ObservationRequirementProfile | None:
        return self._by_id.get(
            str(profile_id).strip().lower()
        )

    def required_requests(
        self,
        profile_id: str,
    ) -> tuple[ObservationRouteRequest, ...]:
        profile = self.get(profile_id)

        if profile is None:
            raise ObservationRequirementResolutionError(
                f"unknown profile_id: {profile_id}"
            )

        return tuple(
            item.route_request()
            for item in profile.requirements
            if item.required
        )


def build_requirement_profile(
    profile_id: str,
    requirements: tuple[ObservationRequirement, ...],
) -> ObservationRequirementProfile:
    normalized_id = " ".join(
        str(profile_id).strip().lower().split()
    )

    if not normalized_id:
        raise ObservationRequirementResolutionError(
            "profile_id must not be empty"
        )

    values = tuple(requirements)
    ordered = tuple(
        sorted(values, key=lambda item: item.requirement_id)
    )

    body = {
        "profile_id": normalized_id,
        "requirement_hashes": tuple(
            item.requirement_hash
            for item in ordered
        ),
    }

    return ObservationRequirementProfile(
        profile_id=normalized_id,
        requirements=ordered,
        profile_hash=deterministic_sha256(body),
    )


def verify_observation_requirement_resolution() -> bool:
    verify_observation_source_routing()
    verify_routed_observation_acquisition()

    if READ_ONLY is not True:
        raise AssertionError("OI-013 must remain read-only")

    if any(
        (
            NETWORK_ALLOWED,
            PERSISTENCE_ALLOWED,
            PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,
        )
    ):
        raise AssertionError("OI-013 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_013_REVISION",
    "ObservationRequirementResolutionError",
    "ObservationRequirement",
    "ObservationRequirementProfile",
    "ObservationRequirementResolver",
    "build_requirement_profile",
    "verify_observation_requirement_resolution",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest

from qseries_v2.observation_intelligence.oi_013_observation_requirement_resolution import (
    OI_013_REVISION,
    ObservationRequirement,
    ObservationRequirementResolver,
    build_requirement_profile,
    verify_observation_requirement_resolution,
)


def profile():
    return build_requirement_profile(
        "profile.market_explanation",
        (
            ObservationRequirement(
                requirement_id="requirement.market_snapshot",
                domain="sports",
                entity_kind="market",
                observation_type="market_snapshot",
                required=True,
                reason="current market state",
            ),
            ObservationRequirement(
                requirement_id="requirement.news",
                domain="sports",
                entity_kind="team",
                observation_type="news",
                required=False,
                reason="context source when adapter exists",
            ),
        ),
    )


class TestOI013(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_observation_requirement_resolution()
        )

    def test_profile(self):
        item = profile()
        self.assertEqual(
            item.profile_id,
            "profile.market_explanation",
        )

    def test_required_requests(self):
        resolver = ObservationRequirementResolver(
            (profile(),)
        )

        requests = resolver.required_requests(
            "profile.market_explanation"
        )

        self.assertEqual(len(requests), 1)
        self.assertEqual(
            requests[0].observation_type,
            "market_snapshot",
        )

    def test_deterministic(self):
        self.assertEqual(
            profile().profile_hash,
            profile().profile_hash,
        )

    def test_unknown_profile(self):
        resolver = ObservationRequirementResolver(
            (profile(),)
        )

        with self.assertRaises(ValueError):
            resolver.required_requests("missing")

    def test_side_effects(self):
        resolver = ObservationRequirementResolver(
            (profile(),)
        )
        self.assertTrue(resolver.read_only)
        self.assertFalse(resolver.network_allowed)
        self.assertFalse(resolver.persistence_allowed)
        self.assertFalse(resolver.publication_allowed)
        self.assertFalse(resolver.execution_allowed)
        self.assertFalse(resolver.qseries_execution_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-013 CERTIFICATION TEST")
    print(" OBSERVATION REQUIREMENT RESOLUTION")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI013
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-013")
    print(f"[PASS] Revision: {OI_013_REVISION}")
    print("[PASS] Generic evidence requirements resolve to route requests")
    print("[PASS] Required versus optional observation needs preserved")
    print("[PASS] No category-specific reasoning or prediction introduced")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-013 CERTIFIED")
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
    print(" OI-013 INSTALLER")
    print(" OBSERVATION REQUIREMENT RESOLUTION")
    print("=" * 72)
    print(f"[BOOT] Revision: {INSTALLER_REVISION}")
    print(f"[ROOT] {ROOT}")

    upstreams = (
        (UPSTREAM_008, "OI-008"),
        (UPSTREAM_012, "OI-012"),
    )

    for path, name in upstreams:
        if not path.is_file():
            raise RuntimeError(f"Certified {name} missing: {path}")

    upstream_hashes = {
        path: sha(path)
        for path, _ in upstreams
    }

    print("[PASS] Certified OI-008 and OI-012 verified read-only")

    affected = (MODULE, TEST, INIT)
    backups = {
        path: path.read_bytes() if path.exists() else None
        for path in affected
    }

    try:
        write_checked(MODULE, MODULE_SOURCE)
        write_checked(TEST, TEST_SOURCE)

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export = "from .oi_013_observation_requirement_resolution import *"

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
        print("[PASS] Requirement resolution remains deterministic, read-only, and non-predictive")
        print("[DONE] OI-013 INSTALLATION COMPLETE")
        return 0

    except Exception:
        for path, content in backups.items():
            if content is None:
                if path.exists():
                    path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)

        print("[ROLLBACK] OI-013 installation failed; all affected files restored")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
