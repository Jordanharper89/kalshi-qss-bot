from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
MOD = PKG / "universal_market_adapter_routing_engine.py"
TEST = ROOT / "test_oi_174_universal_market_adapter_routing_engine.py"
INIT = PKG / "__init__.py"

MODULE = r'''"""
OI-174 — Oracle Universal Market Adapter Routing Engine

Read-only routing engine for registered Universal Market Adapters.

Purpose:
- Route Universal Market Model domain requests to registered read-only adapters.
- Preserve adapter registry state, lifecycle approval, domain coverage, and safety.
- Prepare Oracle Market OS routing without adding execution capability.

Oracle never executes trades, manages positions, or submits orders.
Execution ownership remains with Q Series.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, List


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _stable_text(value: Any) -> str:
    if isinstance(value, dict):
        return "{" + ",".join(f"{k}:{_stable_text(value[k])}" for k in sorted(value)) + "}"
    if isinstance(value, list):
        return "[" + ",".join(_stable_text(v) for v in value) + "]"
    return repr(value)


def _hash(value: Any, size: int = 24) -> str:
    return sha256(_stable_text(value).encode("utf-8")).hexdigest()[:size]


@dataclass
class AdapterRouteRecord:
    route_id: str
    domain: str
    adapter_id: str
    adapter_role: str
    route_status: str
    route_priority: int
    routing_note: str
    lineage_hash: str
    read_only: bool = True
    execution_allowed: bool = False
    execution_owner: str = "Q Series"


@dataclass
class OracleUniversalMarketAdapterRoutingEngine:
    name: str = "oracle_universal_market_adapter_routing_engine"
    version: str = "OI-174"
    read_only: bool = True
    execution_allowed: bool = False
    execution_owner: str = "Q Series"
    routing_schema_version: str = "universal_market_adapter_routing_v1"

    def route_status(self, record: Dict[str, Any]) -> str:
        record = _safe_dict(record)

        if record.get("read_only") is not True:
            return "route_blocked_read_only_violation"
        if record.get("execution_allowed") is not False:
            return "route_blocked_execution_violation"
        if record.get("execution_owner") != "Q Series":
            return "route_blocked_execution_owner_violation"

        registry_status = str(record.get("registry_status") or "")
        if registry_status == "registered_institutional_adapter":
            return "route_institutional_ready"
        if registry_status == "registered_active_adapter":
            return "route_ready"
        if registry_status == "registered_review_adapter":
            return "route_ready_with_review"
        if registry_status.startswith("registry_blocked"):
            return "route_blocked"
        return "route_review_required"

    def route_priority(self, route_status: str) -> int:
        if route_status == "route_institutional_ready":
            return 1
        if route_status == "route_ready":
            return 2
        if route_status == "route_ready_with_review":
            return 3
        if route_status == "route_review_required":
            return 8
        return 99

    def build_route(self, registry_record: Dict[str, Any]) -> AdapterRouteRecord:
        record = _safe_dict(registry_record)

        domain = str(record.get("domain") or "UNKNOWN").upper()
        adapter_id = str(record.get("adapter_id") or "unknown_adapter")
        adapter_role = str(record.get("adapter_role") or f"{domain.lower()}_umm_ingestion_adapter")
        status = self.route_status(record)
        priority = self.route_priority(status)

        payload = {
            "domain": domain,
            "adapter_id": adapter_id,
            "adapter_role": adapter_role,
            "route_status": status,
            "priority": priority,
            "source_registry_record_id": record.get("registry_record_id"),
        }
        lineage_hash = _hash(payload)

        return AdapterRouteRecord(
            route_id=_hash({"payload": payload, "lineage": lineage_hash}),
            domain=domain,
            adapter_id=adapter_id,
            adapter_role=adapter_role,
            route_status=status,
            route_priority=priority,
            routing_note=(
                f"{domain} routes to {adapter_id} with status {status}. "
                "Routing is read-only; Q Series owns execution."
            ),
            lineage_hash=lineage_hash,
            read_only=True,
            execution_allowed=False,
            execution_owner=self.execution_owner,
        )

    def build_routing_table(self, registry: Dict[str, Any]) -> Dict[str, Any]:
        registry = _safe_dict(registry)
        registry_records = _safe_list(registry.get("records"))

        routes = [self.build_route(record) for record in registry_records]
        routes.sort(key=lambda r: (r.domain, r.route_priority, r.adapter_id))

        domain_counts: Dict[str, int] = {}
        status_counts: Dict[str, int] = {}
        adapter_counts: Dict[str, int] = {}

        blocked_count = 0
        ready_count = 0
        review_count = 0

        for route in routes:
            domain_counts[route.domain] = domain_counts.get(route.domain, 0) + 1
            status_counts[route.route_status] = status_counts.get(route.route_status, 0) + 1
            adapter_counts[route.adapter_id] = adapter_counts.get(route.adapter_id, 0) + 1
            if route.route_status.startswith("route_blocked"):
                blocked_count += 1
            elif route.route_status in {"route_institutional_ready", "route_ready", "route_ready_with_review"}:
                ready_count += 1
            else:
                review_count += 1

        if not routes:
            routing_status = "empty_adapter_routing_table"
        elif blocked_count:
            routing_status = "adapter_routing_blocked"
        elif ready_count == len(routes) and status_counts.get("route_institutional_ready", 0) == len(routes):
            routing_status = "adapter_routing_institutional"
        elif ready_count == len(routes):
            routing_status = "adapter_routing_ready"
        else:
            routing_status = "adapter_routing_review_required"

        routing_table_id = _hash({
            "source_adapter_registry_id": registry.get("adapter_registry_id"),
            "routing_status": routing_status,
            "routes": [route.__dict__ for route in routes],
        })

        return {
            "module": self.name,
            "version": self.version,
            "routing_schema_version": self.routing_schema_version,
            "adapter_routing_table_id": routing_table_id,
            "routing_status": routing_status,
            "created_at": _utc_now(),
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "execution_owner": self.execution_owner,
            "single_oracle_instance": True,
            "adapter_based_expansion": True,
            "source_adapter_registry_id": registry.get("adapter_registry_id"),
            "source_registry_status": registry.get("registry_status"),
            "route_count": len(routes),
            "ready_count": ready_count,
            "blocked_count": blocked_count,
            "review_count": review_count,
            "domain_counts": domain_counts,
            "status_counts": status_counts,
            "adapter_counts": adapter_counts,
            "executive_summary": {
                "headline": (
                    "Universal Market adapter routing is institutional."
                    if routing_status == "adapter_routing_institutional"
                    else f"Universal Market adapter routing status: {routing_status}."
                ),
                "adapter_routing_table_id": routing_table_id,
                "route_count": len(routes),
                "ready_count": ready_count,
                "blocked_count": blocked_count,
                "operator_note": "Routing selects read-only adapters only. Q Series owns execution.",
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": self.execution_owner,
            },
            "routes": [route.__dict__ for route in routes],
        }

    def route_domain(self, routing_table: Dict[str, Any], domain: str) -> Dict[str, Any]:
        routing_table = _safe_dict(routing_table)
        routes = _safe_list(routing_table.get("routes"))
        target = str(domain or "").strip().upper()

        matches = [
            _safe_dict(route)
            for route in routes
            if str(_safe_dict(route).get("domain") or "").strip().upper() == target
        ]
        matches.sort(key=lambda r: int(r.get("route_priority") or 99))

        selected = matches[0] if matches else None

        return {
            "module": self.name,
            "version": self.version,
            "found": bool(selected),
            "domain": target,
            "selected_route": selected,
            "candidate_count": len(matches),
            "candidates": matches,
            "read_only": True,
            "execution_allowed": False,
            "execution_owner": self.execution_owner,
        }


oracle_universal_market_adapter_routing_engine = OracleUniversalMarketAdapterRoutingEngine()
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.universal_market_adapter_routing_engine import (
    oracle_universal_market_adapter_routing_engine,
)


def adapter_registry():
    return {
        "adapter_registry_id": "reg-001",
        "registry_status": "adapter_registry_institutional",
        "read_only": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "records": [
            {
                "registry_record_id": "reg-rec-001",
                "adapter_id": "adp.crypto",
                "domain": "CRYPTO",
                "lifecycle_state": "active_institutional_read_only",
                "lifecycle_status": "lifecycle_institutional",
                "registry_status": "registered_institutional_adapter",
                "registered": True,
                "promoted": True,
                "blocked": False,
                "adapter_role": "crypto_umm_ingestion_adapter",
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": "Q Series",
            }
        ],
    }


def test_routing_table_institutional():
    table = oracle_universal_market_adapter_routing_engine.build_routing_table(adapter_registry())

    assert table["read_only"] is True
    assert table["execution_allowed"] is False
    assert table["execution_owner"] == "Q Series"
    assert table["routing_status"] == "adapter_routing_institutional"
    assert table["route_count"] == 1
    assert table["ready_count"] == 1
    assert table["blocked_count"] == 0
    assert table["routes"][0]["route_status"] == "route_institutional_ready"


def test_routing_table_review():
    registry = adapter_registry()
    registry["records"][0]["registry_status"] = "registered_review_adapter"

    table = oracle_universal_market_adapter_routing_engine.build_routing_table(registry)

    assert table["routing_status"] == "adapter_routing_ready"
    assert table["routes"][0]["route_status"] == "route_ready_with_review"
    assert table["routes"][0]["route_priority"] == 3


def test_routing_table_blocked():
    registry = adapter_registry()
    registry["records"][0]["registry_status"] = "registry_blocked_lifecycle"
    registry["records"][0]["blocked"] = True

    table = oracle_universal_market_adapter_routing_engine.build_routing_table(registry)

    assert table["routing_status"] == "adapter_routing_blocked"
    assert table["blocked_count"] == 1
    assert table["routes"][0]["route_status"] == "route_blocked"


def test_route_domain_found():
    table = oracle_universal_market_adapter_routing_engine.build_routing_table(adapter_registry())
    result = oracle_universal_market_adapter_routing_engine.route_domain(table, "crypto")

    assert result["found"] is True
    assert result["domain"] == "CRYPTO"
    assert result["selected_route"]["adapter_id"] == "adp.crypto"
    assert result["read_only"] is True
    assert result["execution_allowed"] is False


def test_route_domain_missing():
    table = oracle_universal_market_adapter_routing_engine.build_routing_table(adapter_registry())
    result = oracle_universal_market_adapter_routing_engine.route_domain(table, "FOREX")

    assert result["found"] is False
    assert result["selected_route"] is None
    assert result["candidate_count"] == 0
    assert result["execution_owner"] == "Q Series"


def test_empty_routing_table():
    table = oracle_universal_market_adapter_routing_engine.build_routing_table({
        "adapter_registry_id": "empty",
        "records": [],
    })

    assert table["routing_status"] == "empty_adapter_routing_table"
    assert table["route_count"] == 0
    assert table["routes"] == []
    assert table["executive_summary"]["read_only"] is True


if __name__ == "__main__":
    test_routing_table_institutional()
    test_routing_table_review()
    test_routing_table_blocked()
    test_route_domain_found()
    test_route_domain_missing()
    test_empty_routing_table()
    print("[PASS] OI-174 Oracle Universal Market Adapter Routing Engine")
'''

def update_init():
    INIT.parent.mkdir(parents=True, exist_ok=True)
    content = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    line = "from .universal_market_adapter_routing_engine import oracle_universal_market_adapter_routing_engine\n"
    if line not in content:
        content += ("\n" if content and not content.endswith("\n") else "") + line
    INIT.write_text(content, encoding="utf-8")


def main():
    print("=" * 40)
    print(" OI-174 INSTALLER")
    print(" Oracle Universal Market Adapter Routing Engine")
    print("=" * 40)

    PKG.mkdir(parents=True, exist_ok=True)
    MOD.write_text(MODULE, encoding="utf-8")
    TEST.write_text(TEST_CODE, encoding="utf-8")
    update_init()

    print(f"[OK] Wrote {MOD}")
    print(f"[OK] Wrote {TEST}")
    print(f"[OK] Updated {INIT}")
    print("\n[DONE] OI-174 installed")
    print("\nRun:")
    print("py test_oi_174_universal_market_adapter_routing_engine.py")


if __name__ == "__main__":
    main()