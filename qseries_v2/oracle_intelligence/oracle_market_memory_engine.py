
"""
OI-140 Oracle Market Memory Engine
Read-only Oracle Intelligence module.

Purpose:
- Convert historical visibility patterns into persistent market memory records.
- Build per-market memory profiles using archive/search/pattern intelligence.
- Track repeated themes, dominant archive types, historical priority, and memory strength.
- Does not execute trades.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
"""

from typing import Dict, Any, List
import time


class OracleMarketMemoryEngine:
    module = "oi_140_oracle_market_memory_engine"

    def __init__(self):
        self.last_memory_report = {}

    def build_market_memory(self, pattern_report=None, catalog_report=None, search_report=None):
        pattern_report = pattern_report or {}
        catalog_report = catalog_report or {}
        search_report = search_report or {}

        patterns = [x for x in pattern_report.get("patterns", []) if isinstance(x, dict)]
        catalog_records = [x for x in catalog_report.get("catalog_records", []) if isinstance(x, dict)]
        search_results = [x for x in search_report.get("results", []) if isinstance(x, dict)]

        records = self._combine_records(catalog_records, search_results)
        markets = self._market_set(records, patterns)

        memory_profiles = []
        for market in markets:
            market_records = [x for x in records if str(x.get("market") or "UNKNOWN") == market]
            market_patterns = self._patterns_for_market(patterns, market)

            profile = self._memory_profile(market, market_records, market_patterns)
            memory_profiles.append(profile)

        memory_profiles.sort(
            key=lambda x: (
                x["memory_strength"],
                x["record_count"],
                x["market"],
            ),
            reverse=True,
        )

        for idx, profile in enumerate(memory_profiles, start=1):
            profile["memory_rank"] = idx

        report = {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "execution_allowed": False,
            "input_modules": [
                "oi_137_q_series_visibility_archive_catalog_engine",
                "oi_138_archive_search_engine",
                "oi_139_historical_visibility_pattern_engine",
            ],
            "market_memory_count": len(memory_profiles),
            "market_memory_profiles": memory_profiles,
            "top_market_memory": memory_profiles[:10],
            "memory_summary": self._summary(memory_profiles),
            "qseries_handoff": {
                "execution_owner": "Q Series",
                "oracle_permission": "read_only",
                "execution_allowed": False,
                "handoff_type": "market_memory_context_only",
            },
        }

        self.last_memory_report = report
        return report

    def _memory_profile(self, market, records, patterns):
        avg_priority = self._avg(records, "catalog_priority")
        avg_visibility = self._avg(records, "visibility_score")
        avg_search = self._avg(records, "search_score")
        avg_integrity = self._avg(records, "integrity_score", default=100)
        avg_pattern = self._avg(patterns, "pattern_score")

        dominant_types = self._counts(records, "archive_type")
        dominant_tiers = self._counts(records, "catalog_tier")
        dominant_patterns = self._counts(patterns, "pattern_type")

        memory_strength = self._memory_strength(
            avg_priority=avg_priority,
            avg_visibility=avg_visibility,
            avg_search=avg_search,
            avg_integrity=avg_integrity,
            avg_pattern=avg_pattern,
            record_count=len(records),
            pattern_count=len(patterns),
        )

        return {
            "market": market,
            "memory_strength": round(memory_strength, 4),
            "memory_tier": self._tier(memory_strength),
            "record_count": len(records),
            "pattern_count": len(patterns),
            "avg_catalog_priority": round(avg_priority, 4),
            "avg_visibility_score": round(avg_visibility, 4),
            "avg_search_score": round(avg_search, 4),
            "avg_integrity_score": round(avg_integrity, 4),
            "avg_pattern_score": round(avg_pattern, 4),
            "dominant_archive_types": dominant_types,
            "dominant_catalog_tiers": dominant_tiers,
            "dominant_pattern_types": dominant_patterns,
            "historical_signature": self._signature(market, records, patterns),
            "memory_note": self._note(market, memory_strength, len(records), len(patterns)),
            "read_only": True,
            "execution_allowed": False,
        }

    def _memory_strength(
        self,
        avg_priority,
        avg_visibility,
        avg_search,
        avg_integrity,
        avg_pattern,
        record_count,
        pattern_count,
    ):
        frequency_component = min((record_count * 5) + (pattern_count * 3), 22)

        score = (
            avg_priority * 0.28
            + avg_visibility * 0.18
            + avg_search * 0.14
            + avg_integrity * 0.10
            + avg_pattern * 0.20
            + frequency_component
        )

        return max(0.0, min(100.0, score))

    def _tier(self, score):
        if score >= 85:
            return "institutional_memory"
        if score >= 70:
            return "strong_memory"
        if score >= 50:
            return "developing_memory"
        if score >= 30:
            return "thin_memory"
        return "archive_trace"

    def _signature(self, market, records, patterns):
        archive_types = list(self._counts(records, "archive_type").keys())[:3]
        pattern_types = list(self._counts(patterns, "pattern_type").keys())[:3]
        tiers = list(self._counts(records, "catalog_tier").keys())[:3]

        return {
            "market": market,
            "archive_type_signature": archive_types,
            "pattern_type_signature": pattern_types,
            "tier_signature": tiers,
            "signature_label": (
                f"{market} memory signature: "
                f"{', '.join(archive_types) if archive_types else 'no archive type'} / "
                f"{', '.join(pattern_types) if pattern_types else 'no pattern type'}"
            ),
            "read_only": True,
            "execution_allowed": False,
        }

    def _note(self, market, score, record_count, pattern_count):
        return (
            f"{market} market memory strength is {round(score, 2)} from "
            f"{record_count} archived visibility record(s) and {pattern_count} "
            "historical pattern(s). This memory is read-only context for Q Series."
        )

    def _summary(self, profiles):
        tier_counts = {}
        for profile in profiles:
            tier = profile["memory_tier"]
            tier_counts[tier] = tier_counts.get(tier, 0) + 1

        top = profiles[0] if profiles else None

        return {
            "market_memory_count": len(profiles),
            "tier_counts": tier_counts,
            "top_market": top["market"] if top else None,
            "top_memory_tier": top["memory_tier"] if top else None,
            "top_memory_strength": top["memory_strength"] if top else None,
            "institutional_memory_count": tier_counts.get("institutional_memory", 0),
            "execution_allowed": False,
            "read_only": True,
        }

    def _combine_records(self, catalog_records, search_results):
        records = {}

        for row in catalog_records + search_results:
            key = str(
                row.get("catalog_key")
                or row.get("archive_id")
                or row.get("receipt_id")
                or f"{row.get('market')}:{row.get('archive_type')}:{row.get('archive_timestamp')}"
            )
            if key not in records:
                records[key] = {}
            records[key].update(row)
            records[key]["catalog_key"] = key

        return list(records.values())

    def _market_set(self, records, patterns):
        markets = []

        for row in records:
            market = str(row.get("market") or "UNKNOWN")
            if market not in markets:
                markets.append(market)

        for pattern in patterns:
            for market in pattern.get("markets", []) or []:
                market = str(market or "UNKNOWN")
                if market not in markets:
                    markets.append(market)

        if not markets:
            markets.append("UNKNOWN")

        return markets

    def _patterns_for_market(self, patterns, market):
        out = []
        for pattern in patterns:
            markets = [str(x) for x in pattern.get("markets", []) or []]
            key = str(pattern.get("pattern_key") or "")
            pattern_type = str(pattern.get("pattern_type") or "")

            if market in markets or key == market or (pattern_type == "market_visibility" and key == market):
                out.append(pattern)

        return out

    def _counts(self, rows, field):
        counts = {}
        for row in rows:
            value = row.get(field)
            if value is None:
                continue
            value = str(value)
            counts[value] = counts.get(value, 0) + 1

        return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))

    def _avg(self, rows, field, default=0.0):
        values = []
        for row in rows:
            value = row.get(field)
            if value is None:
                continue
            values.append(self._float(value, default))

        if not values:
            return default

        return sum(values) / len(values)

    def _float(self, value, default=0.0):
        try:
            if value is None:
                return default
            return float(value)
        except Exception:
            return default

    def diagnostics(self):
        return {
            "module": self.module,
            "status": "ok",
            "has_memory_report": bool(self.last_memory_report),
            "market_memory_count": self.last_memory_report.get("market_memory_count", 0),
            "execution_allowed": False,
            "read_only": True,
        }


oracle_market_memory_engine = OracleMarketMemoryEngine()
