
"""
OI-118 Q Series Intake Packet Engine
Read-only Oracle Intelligence module.

Purpose:
- Convert validated Oracle handoff manifest into a Q Series intake packet.
- Preserve Oracle read-only boundaries while preparing clean downstream visibility.
- Does not execute trades.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
"""

from datetime import datetime, timezone


class QSeriesIntakePacketEngine:
    module = "oi_118_qseries_intake_packet_engine"

    def __init__(self):
        self.last_intake = {}

    def build_intake_packet(self, handoff_manifest=None):
        handoff_manifest = handoff_manifest or {}

        manifest_items = [
            x for x in handoff_manifest.get("manifest_items", [])
            if isinstance(x, dict)
        ]

        visibility_ready = bool(handoff_manifest.get("q_series_visibility_ready", False))
        manifest_status = str(handoff_manifest.get("manifest_status") or "unknown")
        validation_status = str(handoff_manifest.get("validation_status") or "unknown")

        intake_items = []
        for item in manifest_items:
            intake_score = self._intake_score(item, visibility_ready)

            intake_items.append({
                "market": item.get("market"),
                "intake_score": round(intake_score, 4),
                "intake_tier": self._tier(intake_score),
                "handoff_rank": int(self._float(item.get("handoff_rank"), 0)),
                "handoff_score": round(self._float(item.get("handoff_score")), 4),
                "handoff_tier": item.get("handoff_tier"),
                "digest_tier": item.get("digest_tier"),
                "support_tier": item.get("support_tier"),
                "review_conclusion": item.get("review_conclusion"),
                "oracle_observation": item.get("oracle_observation"),
                "q_series_visibility": visibility_ready,
                "execution_permission_from_oracle": False,
                "execution_owner": "Q Series",
                "read_only": True,
                "intake_note": self._intake_note(item, intake_score, visibility_ready),
            })

        intake_items.sort(
            key=lambda x: (
                -x["intake_score"],
                x["handoff_rank"] if x["handoff_rank"] else 999999,
            )
        )

        for idx, item in enumerate(intake_items, start=1):
            item["intake_rank"] = idx

        packet = {
            "module": self.module,
            "status": "ok",
            "read_only": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "execution_allowed": False,
            "execution_owner": "Q Series",
            "input_module": "oi_117_oracle_handoff_manifest_engine",
            "manifest_status": manifest_status,
            "validation_status": validation_status,
            "q_series_visibility_ready": visibility_ready,
            "intake_status": self._intake_status(visibility_ready, manifest_status, validation_status),
            "intake_count": len(intake_items),
            "intake_items": intake_items,
            "top_intake_items": intake_items[:10],
            "blocked_items": [x for x in intake_items if not x["q_series_visibility"]],
            "intake_summary": self._summary(
                intake_items=intake_items,
                visibility_ready=visibility_ready,
                manifest_status=manifest_status,
                validation_status=validation_status,
            ),
            "oracle_boundary_notice": [
                "This is an Oracle read-only intake packet.",
                "Oracle does not execute.",
                "Oracle does not approve execution.",
                "Q Series is the execution owner.",
            ],
        }

        self.last_intake = packet
        return packet

    def _intake_score(self, item, visibility_ready):
        base = self._float(item.get("handoff_score"))
        tier_bonus = {
            "critical": 8,
            "high": 5,
            "elevated": 2,
            "watch": 0,
            "low": -3,
        }.get(str(item.get("handoff_tier") or ""), 0)

        conclusion_bonus = {
            "high_confidence_review": 7,
            "confirmed_review": 4,
            "partial_review": 0,
            "needs_more_evidence": -10,
        }.get(str(item.get("review_conclusion") or ""), 0)

        visibility_penalty = 0 if visibility_ready else 35
        score = base + tier_bonus + conclusion_bonus - visibility_penalty
        return max(0.0, min(100.0, score))

    def _tier(self, score):
        if score >= 85:
            return "critical"
        if score >= 70:
            return "high"
        if score >= 50:
            return "elevated"
        if score >= 30:
            return "watch"
        return "blocked"

    def _intake_status(self, visibility_ready, manifest_status, validation_status):
        if not visibility_ready:
            return "blocked"
        if manifest_status == "ready" and validation_status == "validated":
            return "ready"
        if manifest_status == "ready_with_warnings":
            return "ready_with_warnings"
        return "review_required"

    def _intake_note(self, item, score, visibility_ready):
        market = item.get("market")
        if not visibility_ready:
            return f"{market} intake blocked because Oracle manifest is not Q Series visible."
        return (
            f"{market} intake tier is {self._tier(score)}. "
            "Oracle data is visible to Q Series for evaluation only; Oracle grants no execution permission."
        )

    def _summary(self, intake_items, visibility_ready, manifest_status, validation_status):
        counts = {}
        for item in intake_items:
            tier = item["intake_tier"]
            counts[tier] = counts.get(tier, 0) + 1

        top = intake_items[0] if intake_items else None

        if not visibility_ready:
            headline = "Q Series intake is blocked because Oracle manifest is not visibility-ready."
        elif top:
            headline = f"Q Series intake ready; top Oracle intake market is {top['market']}."
        else:
            headline = "Q Series intake ready with no market items."

        return {
            "headline": headline,
            "intake_tier_counts": counts,
            "top_market": top["market"] if top else None,
            "top_intake_tier": top["intake_tier"] if top else None,
            "visibility_ready": visibility_ready,
            "manifest_status": manifest_status,
            "validation_status": validation_status,
            "execution_allowed": False,
            "execution_owner": "Q Series",
        }

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
            "has_intake": bool(self.last_intake),
            "intake_count": self.last_intake.get("intake_count", 0),
            "intake_status": self.last_intake.get("intake_status"),
            "execution_allowed": False,
            "read_only": True,
        }


qseries_intake_packet_engine = QSeriesIntakePacketEngine()
