from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
MOD = PKG / "universal_market_adapter_directory_engine.py"
TEST = ROOT / "test_oi_175_universal_market_adapter_directory_engine.py"
INIT = PKG / "__init__.py"

MODULE = r'''"""
OI-175 — Oracle Universal Market Adapter Directory Engine

Read-only directory engine for Universal Market Adapter routing tables.

Purpose:
- Convert adapter routing tables into a searchable institutional adapter directory.
- Preserve domain, adapter, route, registry, lifecycle, and safety metadata.
- Provide directory lookup for Oracle Terminal, future Market OS routing, and audit views.

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
class AdapterDirectoryEntry:
    directory_entry_id: str
    domain: str
    adapter_id: str
    adapter_role: str
    route_id: str
    route_status: str
    route_priority: int
    directory_status: str
    searchable_terms: List[str]
    lineage_hash: str
    read_only: bool = True
    execution_allowed: bool = False
    execution_owner: str = "Q Series"


@dataclass
class OracleUniversalMarketAdapterDirectoryEngine:
    name: str = "oracle_universal_market_adapter_directory_engine"
    version: str = "OI-175"
    read_only: bool = True
    execution_allowed: bool = False
    execution_owner: str = "Q Series"
    directory_schema_version: str = "universal_market_adapter_directory_v1"

    def classify_directory_status(self, route: Dict[str, Any]) -> str:
        route = _safe_dict(route)

        if route.get("read_only") is not True:
            return "directory_blocked_read_only_violation"
        if route.get("execution_allowed") is not False:
            return "directory_blocked_execution_violation"
        if route.get("execution_owner") != "Q Series":
            return "directory_blocked_execution_owner_violation"

        route_status = str(route.get("route_status") or "")
        if route_status == "route_institutional_ready":
            return "directory_institutional"
        if route_status == "route_ready":
            return "directory_active"
        if route_status == "route_ready_with_review":
            return "directory_active_with_review"
        if route_status.startswith("route_blocked"):
            return "directory_blocked"
        return "directory_review_required"

    def terms(self, route: Dict[str, Any]) -> List[str]:
        route = _safe_dict(route)
        raw = [
            route.get("domain"),
            route.get("adapter_id"),
            route.get("adapter_role"),
            route.get("route_status"),
            route.get("route_id"),
        ]

        out: List[str] = []
        for item in raw:
            if item is None:
                continue
            cleaned = str(item).strip().lower()
            if cleaned and cleaned not in out:
                out.append(cleaned)
        return out

    def build_entry(self, route: Dict[str, Any]) -> AdapterDirectoryEntry:
        route = _safe_dict(route)

        domain = str(route.get("domain") or "UNKNOWN").upper()
        adapter_id = str(route.get("adapter_id") or "unknown_adapter")
        adapter_role = str(route.get("adapter_role") or f"{domain.lower()}_umm_ingestion_adapter")
        route_id = str(route.get("route_id") or _hash(route, 12))
        route_status = str(route.get("route_status") or "unknown_route_status")

        try:
            route_priority = int(route.get("route_priority") or 99)
        except Exception:
            route_priority = 99

        directory_status = self.classify_directory_status(route)

        payload = {
            "domain": domain,
            "adapter_id": adapter_id,
            "adapter_role": adapter_role,
            "route_id": route_id,
            "route_status": route_status,
            "route_priority": route_priority,
            "directory_status": directory_status,
        }
        lineage_hash = _hash(payload)

        return AdapterDirectoryEntry(
            directory_entry_id=_hash({"payload": payload, "lineage": lineage_hash}),
            domain=domain,
            adapter_id=adapter_id,
            adapter_role=adapter_role,
            route_id=route_id,
            route_status=route_status,
            route_priority=route_priority,
            directory_status=directory_status,
            searchable_terms=self.terms({
                **route,
                "domain": domain,
                "adapter_id": adapter_id,
                "adapter_role": adapter_role,
                "route_id": route_id,
                "route_status": route_status,
            }),
            lineage_hash=lineage_hash,
            read_only=True,
            execution_allowed=False,
            execution_owner=self.execution_owner,
        )

    def build_directory(self, routing_table: Dict[str, Any]) -> Dict[str, Any]:
        routing_table = _safe_dict(routing_table)
        routes = _safe_list(routing_table.get("routes"))

        entries = [self.build_entry(route) for route in routes]
        entries.sort(key=lambda e: (e.domain, e.route_priority, e.adapter_id))

        domain_counts: Dict[str, int] = {}
        adapter_counts: Dict[str, int] = {}
        status_counts: Dict[str, int] = {}
        route_status_counts: Dict[str, int] = {}

        blocked_count = 0
        active_count = 0
        institutional_count = 0

        for entry in entries:
            domain_counts[entry.domain] = domain_counts.get(entry.domain, 0) + 1
            adapter_counts[entry.adapter_id] = adapter_counts.get(entry.adapter_id, 0) + 1
            status_counts[entry.directory_status] = status_counts.get(entry.directory_status, 0) + 1
            route_status_counts[entry.route_status] = route_status_counts.get(entry.route_status, 0) + 1

            if entry.directory_status.startswith("directory_blocked") or entry.directory_status == "directory_blocked":
                blocked_count += 1
            if entry.directory_status in {"directory_institutional", "directory_active", "directory_active_with_review"}:
                active_count += 1
            if entry.directory_status == "directory_institutional":
                institutional_count += 1

        if not entries:
            directory_status = "empty_adapter_directory"
        elif blocked_count:
            directory_status = "adapter_directory_blocked"
        elif institutional_count == len(entries):
            directory_status = "adapter_directory_institutional"
        elif active_count == len(entries):
            directory_status = "adapter_directory_active"
        else:
            directory_status = "adapter_directory_review_required"

        directory_id = _hash({
            "source_adapter_routing_table_id": routing_table.get("adapter_routing_table_id"),
            "directory_status": directory_status,
            "entries": [entry.__dict__ for entry in entries],
        })

        return {
            "module": self.name,
            "version": self.version,
            "directory_schema_version": self.directory_schema_version,
            "adapter_directory_id": directory_id,
            "directory_status": directory_status,
            "created_at": _utc_now(),
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "execution_owner": self.execution_owner,
            "single_oracle_instance": True,
            "adapter_based_expansion": True,
            "source_adapter_routing_table_id": routing_table.get("adapter_routing_table_id"),
            "source_routing_status": routing_table.get("routing_status"),
            "entry_count": len(entries),
            "domain_count": len(domain_counts),
            "adapter_count": len(adapter_counts),
            "active_count": active_count,
            "institutional_count": institutional_count,
            "blocked_count": blocked_count,
            "domain_counts": domain_counts,
            "adapter_counts": adapter_counts,
            "status_counts": status_counts,
            "route_status_counts": route_status_counts,
            "executive_summary": {
                "headline": (
                    "Universal Market adapter directory is institutional."
                    if directory_status == "adapter_directory_institutional"
                    else f"Universal Market adapter directory status: {directory_status}."
                ),
                "adapter_directory_id": directory_id,
                "entry_count": len(entries),
                "domain_count": len(domain_counts),
                "adapter_count": len(adapter_counts),
                "operator_note": "Adapter directory is read-only. Oracle remains intelligence-only. Q Series owns execution.",
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": self.execution_owner,
            },
            "entries": [entry.__dict__ for entry in entries],
        }

    def lookup_adapter(self, directory: Dict[str, Any], adapter_id: str) -> Dict[str, Any]:
        directory = _safe_dict(directory)
        entries = _safe_list(directory.get("entries"))
        target = str(adapter_id or "").strip().lower()

        matches = [
            _safe_dict(entry)
            for entry in entries
            if str(_safe_dict(entry).get("adapter_id") or "").strip().lower() == target
        ]

        return {
            "module": self.name,
            "version": self.version,
            "found": bool(matches),
            "adapter_id": adapter_id,
            "match_count": len(matches),
            "entries": matches,
            "read_only": True,
            "execution_allowed": False,
            "execution_owner": self.execution_owner,
        }

    def lookup_domain(self, directory: Dict[str, Any], domain: str) -> Dict[str, Any]:
        directory = _safe_dict(directory)
        entries = _safe_list(directory.get("entries"))
        target = str(domain or "").strip().upper()

        matches = [
            _safe_dict(entry)
            for entry in entries
            if str(_safe_dict(entry).get("domain") or "").strip().upper() == target
        ]
        matches.sort(key=lambda e: int(e.get("route_priority") or 99))

        return {
            "module": self.name,
            "version": self.version,
            "found": bool(matches),
            "domain": target,
            "match_count": len(matches),
            "entries": matches,
            "read_only": True,
            "execution_allowed": False,
            "execution_owner": self.execution_owner,
        }

    def search(self, directory: Dict[str, Any], query: str, limit: int = 10) -> Dict[str, Any]:
        directory = _safe_dict(directory)
        entries = _safe_list(directory.get("entries"))
        terms = [t.strip().lower() for t in str(query or "").split() if t.strip()]

        matches: List[Dict[str, Any]] = []
        for entry in entries:
            entry = _safe_dict(entry)
            searchable = " ".join(str(x).lower() for x in [
                entry.get("domain"),
                entry.get("adapter_id"),
                entry.get("adapter_role"),
                entry.get("route_status"),
                entry.get("directory_status"),
                " ".join(_safe_list(entry.get("searchable_terms"))),
            ])
            if all(term in searchable for term in terms):
                matches.append(entry)

        matches.sort(key=lambda e: int(e.get("route_priority") or 99))

        return {
            "module": self.name,
            "version": self.version,
            "query": query,
            "match_count": len(matches),
            "entries": matches[: max(0, int(limit))],
            "read_only": True,
            "execution_allowed": False,
            "execution_owner": self.execution_owner,
        }


oracle_universal_market_adapter_directory_engine = OracleUniversalMarketAdapterDirectoryEngine()
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.universal_market_adapter_directory_engine import (
    oracle_universal_market_adapter_directory_engine,
)


def routing_table():
    return {
        "adapter_routing_table_id": "route-table-001",
        "routing_status": "adapter_routing_institutional",
        "read_only": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "routes": [
            {
                "route_id": "route-001",
                "domain": "CRYPTO",
                "adapter_id": "adp.crypto",
                "adapter_role": "crypto_umm_ingestion_adapter",
                "route_status": "route_institutional_ready",
                "route_priority": 1,
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": "Q Series",
            },
            {
                "route_id": "route-002",
                "domain": "STOCKS",
                "adapter_id": "adp.stocks",
                "adapter_role": "stocks_umm_ingestion_adapter",
                "route_status": "route_ready",
                "route_priority": 2,
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": "Q Series",
            },
        ],
    }


def test_directory_builds():
    directory = oracle_universal_market_adapter_directory_engine.build_directory(routing_table())

    assert directory["read_only"] is True
    assert directory["execution_allowed"] is False
    assert directory["execution_owner"] == "Q Series"
    assert directory["directory_status"] == "adapter_directory_active"
    assert directory["entry_count"] == 2
    assert directory["domain_count"] == 2
    assert directory["adapter_count"] == 2
    assert directory["blocked_count"] == 0


def test_institutional_directory():
    table = routing_table()
    table["routes"] = [table["routes"][0]]

    directory = oracle_universal_market_adapter_directory_engine.build_directory(table)

    assert directory["directory_status"] == "adapter_directory_institutional"
    assert directory["institutional_count"] == 1
    assert directory["entries"][0]["directory_status"] == "directory_institutional"


def test_blocked_directory():
    table = routing_table()
    table["routes"][0]["route_status"] = "route_blocked"

    directory = oracle_universal_market_adapter_directory_engine.build_directory(table)

    assert directory["directory_status"] == "adapter_directory_blocked"
    assert directory["blocked_count"] == 1


def test_lookup_adapter():
    directory = oracle_universal_market_adapter_directory_engine.build_directory(routing_table())
    result = oracle_universal_market_adapter_directory_engine.lookup_adapter(directory, "adp.crypto")

    assert result["found"] is True
    assert result["match_count"] == 1
    assert result["entries"][0]["adapter_id"] == "adp.crypto"
    assert result["read_only"] is True


def test_lookup_domain():
    directory = oracle_universal_market_adapter_directory_engine.build_directory(routing_table())
    result = oracle_universal_market_adapter_directory_engine.lookup_domain(directory, "crypto")

    assert result["found"] is True
    assert result["domain"] == "CRYPTO"
    assert result["entries"][0]["domain"] == "CRYPTO"


def test_search_directory():
    directory = oracle_universal_market_adapter_directory_engine.build_directory(routing_table())
    result = oracle_universal_market_adapter_directory_engine.search(directory, "crypto institutional")

    assert result["match_count"] == 1
    assert result["entries"][0]["adapter_id"] == "adp.crypto"
    assert result["execution_allowed"] is False


def test_empty_directory():
    directory = oracle_universal_market_adapter_directory_engine.build_directory({
        "adapter_routing_table_id": "empty",
        "routes": [],
    })

    assert directory["directory_status"] == "empty_adapter_directory"
    assert directory["entry_count"] == 0
    assert directory["entries"] == []
    assert directory["executive_summary"]["read_only"] is True


if __name__ == "__main__":
    test_directory_builds()
    test_institutional_directory()
    test_blocked_directory()
    test_lookup_adapter()
    test_lookup_domain()
    test_search_directory()
    test_empty_directory()
    print("[PASS] OI-175 Oracle Universal Market Adapter Directory Engine")
'''

def update_init():
    INIT.parent.mkdir(parents=True, exist_ok=True)
    content = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    line = "from .universal_market_adapter_directory_engine import oracle_universal_market_adapter_directory_engine\n"
    if line not in content:
        content += ("\n" if content and not content.endswith("\n") else "") + line
    INIT.write_text(content, encoding="utf-8")


def main():
    print("=" * 40)
    print(" OI-175 INSTALLER")
    print(" Oracle Universal Market Adapter Directory Engine")
    print("=" * 40)

    PKG.mkdir(parents=True, exist_ok=True)
    MOD.write_text(MODULE, encoding="utf-8")
    TEST.write_text(TEST_CODE, encoding="utf-8")
    update_init()

    print(f"[OK] Wrote {MOD}")
    print(f"[OK] Wrote {TEST}")
    print(f"[OK] Updated {INIT}")
    print("\n[DONE] OI-175 installed")
    print("\nRun:")
    print("py test_oi_175_universal_market_adapter_directory_engine.py")


if __name__ == "__main__":
    main()