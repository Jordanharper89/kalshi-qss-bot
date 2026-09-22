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
