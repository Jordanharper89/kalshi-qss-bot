from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
MOD = PKG / "historical_intelligence_dashboard_engine.py"
TEST = ROOT / "test_oi_153_historical_intelligence_dashboard_engine.py"
INIT = PKG / "__init__.py"

MODULE = r'''"""
OI-153 — Oracle Historical Intelligence Dashboard Engine

Read-only dashboard formatter for historical Oracle intelligence manifests.
Oracle never executes trades, manages positions, or submits orders.
Execution ownership remains with Q Series.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


@dataclass
class OracleHistoricalIntelligenceDashboardEngine:
    name: str = "oracle_historical_intelligence_dashboard_engine"
    version: str = "OI-153"
    read_only: bool = True
    execution_allowed: bool = False
    execution_owner: str = "Q Series"

    def build_dashboard(self, manifest: Dict[str, Any]) -> Dict[str, Any]:
        manifest = _safe_dict(manifest)
        entries = _safe_list(manifest.get("entries"))

        top_entries = sorted(
            entries,
            key=lambda e: float(_safe_dict(e).get("historical_score", 0.0) or 0.0),
            reverse=True,
        )[:5]

        market_counts = _safe_dict(manifest.get("market_counts"))
        tier_counts = _safe_dict(manifest.get("tier_counts"))
        status_counts = _safe_dict(manifest.get("status_counts"))

        top_market = None
        if market_counts:
            top_market = max(market_counts.items(), key=lambda x: x[1])[0]

        dashboard = {
            "module": self.name,
            "version": self.version,
            "dashboard_id": f"hist-dash-{manifest.get('manifest_id', 'unknown')}",
            "generated_at": _utc_now(),
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "execution_owner": self.execution_owner,
            "manifest_id": manifest.get("manifest_id"),
            "manifest_status": manifest.get("manifest_status"),
            "entry_count": manifest.get("entry_count", len(entries)),
            "top_market": top_market or manifest.get("top_market"),
            "top_manifest_tier": manifest.get("top_manifest_tier"),
            "tiles": {
                "overview": {
                    "title": "Historical Intelligence Overview",
                    "entry_count": manifest.get("entry_count", len(entries)),
                    "manifest_status": manifest.get("manifest_status"),
                    "universal_market_model_ready": manifest.get("universal_market_model_ready", True),
                },
                "market_distribution": market_counts,
                "tier_distribution": tier_counts,
                "status_distribution": status_counts,
                "top_entries": top_entries,
            },
            "executive_summary": self._summary(manifest, top_entries, top_market),
        }

        return dashboard

    def _summary(self, manifest: Dict[str, Any], top_entries: List[Dict[str, Any]], top_market: str) -> Dict[str, Any]:
        top = _safe_dict(top_entries[0]) if top_entries else {}
        return {
            "headline": (
                f"Historical intelligence dashboard ready; top market is {top_market or top.get('market', 'UNKNOWN')}."
                if top_entries else
                "Historical intelligence dashboard ready; no manifest entries available."
            ),
            "top_source_id": top.get("source_id"),
            "top_score": top.get("historical_score"),
            "top_status": top.get("manifest_status"),
            "top_tier": top.get("manifest_tier"),
            "read_only": True,
            "execution_allowed": False,
            "execution_owner": self.execution_owner,
            "operator_note": "Oracle dashboard is intelligence-only. Q Series owns all execution decisions.",
        }


oracle_historical_intelligence_dashboard_engine = OracleHistoricalIntelligenceDashboardEngine()
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.historical_intelligence_dashboard_engine import (
    oracle_historical_intelligence_dashboard_engine,
)


def test_dashboard_builds_read_only():
    manifest = {
        "manifest_id": "manifest-001",
        "manifest_status": "manifest_built",
        "entry_count": 2,
        "top_market": "CRYPTO",
        "top_manifest_tier": "institutional_historical_manifest",
        "universal_market_model_ready": True,
        "market_counts": {"CRYPTO": 1, "STOCKS": 1},
        "tier_counts": {"institutional_historical_manifest": 1, "validated_historical_manifest": 1},
        "status_counts": {"executive_ready_manifest": 1, "validated_manifest": 1},
        "entries": [
            {
                "source_id": "source-low",
                "market": "STOCKS",
                "historical_score": 80.0,
                "manifest_tier": "validated_historical_manifest",
                "manifest_status": "validated_manifest",
                "read_only": True,
                "execution_allowed": False,
            },
            {
                "source_id": "source-high",
                "market": "CRYPTO",
                "historical_score": 95.0,
                "manifest_tier": "institutional_historical_manifest",
                "manifest_status": "executive_ready_manifest",
                "read_only": True,
                "execution_allowed": False,
            },
        ],
    }

    dashboard = oracle_historical_intelligence_dashboard_engine.build_dashboard(manifest)

    assert dashboard["read_only"] is True
    assert dashboard["execution_allowed"] is False
    assert dashboard["execution_owner"] == "Q Series"
    assert dashboard["manifest_id"] == "manifest-001"
    assert dashboard["top_market"] == "CRYPTO"
    assert dashboard["tiles"]["top_entries"][0]["source_id"] == "source-high"


def test_dashboard_handles_empty_manifest():
    dashboard = oracle_historical_intelligence_dashboard_engine.build_dashboard({
        "manifest_id": "manifest-empty",
        "manifest_status": "empty_manifest",
        "entries": [],
    })

    assert dashboard["entry_count"] == 0
    assert dashboard["tiles"]["top_entries"] == []
    assert dashboard["executive_summary"]["read_only"] is True
    assert dashboard["executive_summary"]["execution_allowed"] is False


def test_dashboard_market_distribution():
    manifest = {
        "manifest_id": "manifest-002",
        "market_counts": {"FOREX": 3, "CRYPTO": 1},
        "tier_counts": {},
        "status_counts": {},
        "entries": [
            {"source_id": "a", "market": "FOREX", "historical_score": 77},
            {"source_id": "b", "market": "CRYPTO", "historical_score": 88},
        ],
    }

    dashboard = oracle_historical_intelligence_dashboard_engine.build_dashboard(manifest)

    assert dashboard["top_market"] == "FOREX"
    assert dashboard["tiles"]["market_distribution"]["FOREX"] == 3


if __name__ == "__main__":
    test_dashboard_builds_read_only()
    test_dashboard_handles_empty_manifest()
    test_dashboard_market_distribution()
    print("[PASS] OI-153 Oracle Historical Intelligence Dashboard Engine")
'''

def update_init():
    INIT.parent.mkdir(parents=True, exist_ok=True)
    content = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    line = "from .historical_intelligence_dashboard_engine import oracle_historical_intelligence_dashboard_engine\n"
    if line not in content:
        content += ("\n" if content and not content.endswith("\n") else "") + line
    INIT.write_text(content, encoding="utf-8")


def main():
    print("=" * 40)
    print(" OI-153 INSTALLER")
    print(" Oracle Historical Intelligence Dashboard Engine")
    print("=" * 40)

    PKG.mkdir(parents=True, exist_ok=True)
    MOD.write_text(MODULE, encoding="utf-8")
    TEST.write_text(TEST_CODE, encoding="utf-8")
    update_init()

    print(f"[OK] Wrote {MOD}")
    print(f"[OK] Wrote {TEST}")
    print(f"[OK] Updated {INIT}")
    print("\n[DONE] OI-153 installed")
    print("\nRun:")
    print("py test_oi_153_historical_intelligence_dashboard_engine.py")


if __name__ == "__main__":
    main()