
"""
OI-138 Archive Search Engine
Read-only Oracle Intelligence module.

Purpose:
- Search Oracle visibility archive catalog records.
- Support keyword, market, archive type, tier, minimum priority, and time-window filters.
- Produce ranked read-only search results for historical intelligence lookup.
- Does not execute trades.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
"""

from typing import Dict, Any, List
import time


class ArchiveSearchEngine:
    module = "oi_138_archive_search_engine"

    def __init__(self):
        self.last_search = {}

    def search_archive(
        self,
        catalog_report=None,
        query=None,
        market=None,
        archive_type=None,
        tier=None,
        min_priority=None,
        start_timestamp=None,
        end_timestamp=None,
        limit=25,
    ):
        catalog_report = catalog_report or {}
        records = [x for x in catalog_report.get("catalog_records", []) if isinstance(x, dict)]

        query_terms = self._query_terms(query)
        market_filter = str(market).lower().strip() if market is not None else None
        type_filter = str(archive_type).lower().strip() if archive_type is not None else None
        tier_filter = str(tier).lower().strip() if tier is not None else None
        min_priority = self._float(min_priority, None)
        start_timestamp = self._float(start_timestamp, None)
        end_timestamp = self._float(end_timestamp, None)

        results = []

        for record in records:
            if not self._matches_filters(
                record=record,
                query_terms=query_terms,
                market_filter=market_filter,
                type_filter=type_filter,
                tier_filter=tier_filter,
                min_priority=min_priority,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
            ):
                continue

            score = self._search_score(record, query_terms, market_filter, type_filter, tier_filter)
            result = self._result_record(record, score, query_terms)
            results.append(result)

        results.sort(
            key=lambda x: (
                x["search_score"],
                x["catalog_priority"],
                x["archive_timestamp"],
                x["catalog_key"],
            ),
            reverse=True,
        )

        max_limit = int(self._float(limit, 25))
        if max_limit <= 0:
            max_limit = 25

        results = results[:max_limit]

        for idx, result in enumerate(results, start=1):
            result["search_rank"] = idx

        report = {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "execution_allowed": False,
            "input_modules": [
                "oi_137_q_series_visibility_archive_catalog_engine",
            ],
            "query": query,
            "filters": {
                "market": market,
                "archive_type": archive_type,
                "tier": tier,
                "min_priority": min_priority,
                "start_timestamp": start_timestamp,
                "end_timestamp": end_timestamp,
                "limit": max_limit,
            },
            "searched_record_count": len(records),
            "result_count": len(results),
            "results": results,
            "top_results": results[:10],
            "search_summary": self._summary(results, len(records), query_terms),
            "qseries_handoff": {
                "execution_owner": "Q Series",
                "oracle_permission": "read_only",
                "execution_allowed": False,
                "handoff_type": "archive_search_context_only",
            },
        }

        self.last_search = report
        return report

    def _matches_filters(
        self,
        record,
        query_terms,
        market_filter,
        type_filter,
        tier_filter,
        min_priority,
        start_timestamp,
        end_timestamp,
    ):
        market = str(record.get("market") or "").lower()
        archive_type = str(record.get("archive_type") or "").lower()
        catalog_tier = str(record.get("catalog_tier") or "").lower()
        priority = self._float(record.get("catalog_priority"), 0)
        timestamp = self._float(record.get("archive_timestamp"), 0)
        haystack = self._haystack(record)

        if query_terms and not all(term in haystack for term in query_terms):
            return False
        if market_filter and market_filter not in market:
            return False
        if type_filter and type_filter not in archive_type:
            return False
        if tier_filter and tier_filter != catalog_tier:
            return False
        if min_priority is not None and priority < min_priority:
            return False
        if start_timestamp is not None and timestamp < start_timestamp:
            return False
        if end_timestamp is not None and timestamp > end_timestamp:
            return False

        return True

    def _search_score(self, record, query_terms, market_filter, type_filter, tier_filter):
        catalog_priority = self._float(record.get("catalog_priority"), 0)
        visibility_score = self._float(record.get("visibility_score"), 0)
        integrity_score = self._float(record.get("integrity_score"), 0)

        score = catalog_priority * 0.55 + visibility_score * 0.25 + integrity_score * 0.10

        haystack = self._haystack(record)
        search_terms = [str(x).lower() for x in record.get("search_terms", [])]

        for term in query_terms:
            if term in search_terms:
                score += 8
            elif term in haystack:
                score += 4

        if market_filter and market_filter == str(record.get("market") or "").lower():
            score += 6
        if type_filter and type_filter == str(record.get("archive_type") or "").lower():
            score += 5
        if tier_filter and tier_filter == str(record.get("catalog_tier") or "").lower():
            score += 4

        return round(max(0.0, min(100.0, score)), 4)

    def _result_record(self, record, search_score, query_terms):
        return {
            "catalog_key": record.get("catalog_key"),
            "archive_id": record.get("archive_id"),
            "receipt_id": record.get("receipt_id"),
            "market": record.get("market"),
            "archive_type": record.get("archive_type"),
            "archive_timestamp": self._float(record.get("archive_timestamp"), 0),
            "catalog_priority": self._float(record.get("catalog_priority"), 0),
            "catalog_tier": record.get("catalog_tier"),
            "search_score": search_score,
            "match_terms": self._match_terms(record, query_terms),
            "catalog_label": record.get("catalog_label"),
            "catalog_summary": record.get("catalog_summary"),
            "read_only": True,
            "execution_allowed": False,
        }

    def _match_terms(self, record, query_terms):
        if not query_terms:
            return []

        haystack = self._haystack(record)
        return [term for term in query_terms if term in haystack]

    def _summary(self, results, searched_count, query_terms):
        tier_counts = {}
        market_counts = {}
        type_counts = {}

        for result in results:
            tier = result.get("catalog_tier")
            market = result.get("market")
            archive_type = result.get("archive_type")

            tier_counts[tier] = tier_counts.get(tier, 0) + 1
            market_counts[market] = market_counts.get(market, 0) + 1
            type_counts[archive_type] = type_counts.get(archive_type, 0) + 1

        top = results[0] if results else None

        return {
            "searched_record_count": searched_count,
            "result_count": len(results),
            "query_terms": query_terms,
            "tier_counts": tier_counts,
            "market_counts": market_counts,
            "type_counts": type_counts,
            "top_catalog_key": top.get("catalog_key") if top else None,
            "top_market": top.get("market") if top else None,
            "top_archive_type": top.get("archive_type") if top else None,
            "top_search_score": top.get("search_score") if top else None,
            "execution_allowed": False,
            "read_only": True,
        }

    def _query_terms(self, query):
        if query is None:
            return []
        if isinstance(query, list):
            raw_terms = []
            for item in query:
                raw_terms.extend(str(item).lower().replace(",", " ").split())
        else:
            raw_terms = str(query).lower().replace(",", " ").split()

        return sorted(set(x.strip() for x in raw_terms if x.strip()))

    def _haystack(self, record):
        pieces = []

        for key in [
            "catalog_key",
            "archive_id",
            "receipt_id",
            "market",
            "archive_type",
            "catalog_tier",
            "catalog_label",
            "catalog_summary",
            "index_status",
            "visibility_status",
            "release_status",
        ]:
            value = record.get(key)
            if value is not None:
                pieces.append(str(value).lower())

        for term in record.get("search_terms", []) or []:
            pieces.append(str(term).lower())

        return " ".join(pieces)

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
            "has_search": bool(self.last_search),
            "result_count": self.last_search.get("result_count", 0),
            "execution_allowed": False,
            "read_only": True,
        }


archive_search_engine = ArchiveSearchEngine()
