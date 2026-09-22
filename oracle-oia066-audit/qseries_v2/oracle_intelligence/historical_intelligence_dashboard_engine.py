"""
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
