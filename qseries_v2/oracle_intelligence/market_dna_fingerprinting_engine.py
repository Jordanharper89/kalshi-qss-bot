"""
OI-046 Market DNA Fingerprinting Engine

Purpose:
- Convert market/setup behavior into stable market DNA fingerprints.
- Help Oracle recognize recurring market personalities over time.
- Feed future analog retrieval, outcome modeling, and knowledge graph modules.

Read-only:
- No execution.
- No order placement.
- No trade mutation.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional


DNA_NUMERIC_FIELDS = [
    "price",
    "yes_price",
    "no_price",
    "implied_probability",
    "volume",
    "liquidity",
    "spread",
    "momentum",
    "volatility",
    "time_to_expiration_minutes",
    "confidence",
    "forecast_value",
]

DNA_CATEGORICAL_FIELDS = [
    "category",
    "event_category",
    "regime",
    "rhythm_phase",
    "pattern_name",
    "strategy",
    "side",
]


class MarketDNAFingerprintingEngine:
    module_name = "oi_046_market_dna_fingerprinting_engine"

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "numeric_fields": DNA_NUMERIC_FIELDS,
            "categorical_fields": DNA_CATEGORICAL_FIELDS,
        }

    def fingerprint_market(self, setup: Dict[str, Any]) -> Dict[str, Any]:
        normalized = self._normalize_setup(setup)
        dna_string = json.dumps(normalized, sort_keys=True, default=str)

        full_hash = hashlib.sha256(dna_string.encode("utf-8")).hexdigest()
        family_hash = hashlib.sha256(
            json.dumps(normalized["family_profile"], sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()

        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "market_ticker": setup.get("ticker") or setup.get("market_ticker"),
            "dna_id": f"dna_{full_hash[:24]}",
            "dna_family": f"family_{family_hash[:16]}",
            "profile": normalized,
            "traits": self._traits_from_profile(normalized),
        }

    def compare_fingerprints(self, a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
        fa = a.get("profile") if "profile" in a else self.fingerprint_market(a)["profile"]
        fb = b.get("profile") if "profile" in b else self.fingerprint_market(b)["profile"]

        shared_traits = sorted(set(self._traits_from_profile(fa)) & set(self._traits_from_profile(fb)))
        all_traits = sorted(set(self._traits_from_profile(fa)) | set(self._traits_from_profile(fb)))

        trait_overlap = len(shared_traits) / len(all_traits) if all_traits else 0.0
        bucket_overlap = self._bucket_overlap(fa, fb)

        score = round((trait_overlap * 0.55) + (bucket_overlap * 0.45), 4)

        return {
            "status": "ok",
            "read_only": True,
            "dna_similarity": score,
            "dna_similarity_pct": round(score * 100, 2),
            "shared_traits": shared_traits,
            "trait_overlap": round(trait_overlap, 4),
            "bucket_overlap": round(bucket_overlap, 4),
        }

    def _normalize_setup(self, setup: Dict[str, Any]) -> Dict[str, Any]:
        numeric_profile = {}

        for field in DNA_NUMERIC_FIELDS:
            if field in setup and self._is_number(setup[field]):
                numeric_profile[field] = self._bucket_numeric(field, float(setup[field]))

        categorical_profile = {}

        for field in DNA_CATEGORICAL_FIELDS:
            value = setup.get(field)
            if value is not None:
                categorical_profile[field] = str(value).strip().lower()

        tags = sorted(set(str(t).strip().lower() for t in setup.get("tags", []) if str(t).strip()))

        family_profile = {
            "category": categorical_profile.get("category"),
            "event_category": categorical_profile.get("event_category"),
            "regime": categorical_profile.get("regime"),
            "pattern_name": categorical_profile.get("pattern_name"),
            "momentum": numeric_profile.get("momentum"),
            "volatility": numeric_profile.get("volatility"),
            "liquidity": numeric_profile.get("liquidity"),
            "spread": numeric_profile.get("spread"),
        }

        return {
            "numeric": numeric_profile,
            "categorical": categorical_profile,
            "tags": tags,
            "family_profile": family_profile,
        }

    def _bucket_numeric(self, field: str, value: float) -> str:
        if field in {"price", "yes_price", "no_price", "implied_probability", "confidence", "forecast_value"}:
            if value < 20:
                return "very_low"
            if value < 40:
                return "low"
            if value < 60:
                return "mid"
            if value < 80:
                return "high"
            return "very_high"

        if field in {"volume", "liquidity"}:
            if value < 1000:
                return "thin"
            if value < 10000:
                return "normal"
            if value < 50000:
                return "deep"
            return "very_deep"

        if field == "spread":
            if value <= 2:
                return "tight"
            if value <= 6:
                return "normal"
            return "wide"

        if field in {"momentum", "volatility"}:
            if value <= -5:
                return "strong_negative"
            if value < 0:
                return "negative"
            if value == 0:
                return "flat"
            if value < 5:
                return "positive"
            return "strong_positive"

        if field == "time_to_expiration_minutes":
            if value <= 15:
                return "closing"
            if value <= 60:
                return "short"
            if value <= 240:
                return "medium"
            return "long"

        return "unknown"

    def _traits_from_profile(self, profile: Dict[str, Any]) -> List[str]:
        traits = []

        for key, value in profile.get("numeric", {}).items():
            traits.append(f"{key}:{value}")

        for key, value in profile.get("categorical", {}).items():
            traits.append(f"{key}:{value}")

        for tag in profile.get("tags", []):
            traits.append(f"tag:{tag}")

        return sorted(set(traits))

    def _bucket_overlap(self, a: Dict[str, Any], b: Dict[str, Any]) -> float:
        a_items = set()
        b_items = set()

        for section in ["numeric", "categorical", "family_profile"]:
            for k, v in a.get(section, {}).items():
                if v is not None:
                    a_items.add(f"{section}:{k}:{v}")

            for k, v in b.get(section, {}).items():
                if v is not None:
                    b_items.add(f"{section}:{k}:{v}")

        if not a_items or not b_items:
            return 0.0

        return len(a_items & b_items) / len(a_items | b_items)

    def _is_number(self, value: Any) -> bool:
        try:
            float(value)
            return True
        except Exception:
            return False


market_dna_fingerprinting_engine = MarketDNAFingerprintingEngine()
