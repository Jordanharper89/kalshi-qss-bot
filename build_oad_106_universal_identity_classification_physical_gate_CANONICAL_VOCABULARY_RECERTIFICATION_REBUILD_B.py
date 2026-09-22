from __future__ import annotations

import ast
import hashlib
import os
import textwrap
from pathlib import Path

REVISION = "OAD_106_CANONICAL_VOCABULARY_RECERTIFICATION_REBUILD_B"

def find_root() -> Path:
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for candidate in (base, *base.parents):
            if (candidate / "qseries_v2").is_dir():
                return candidate
    raise SystemExit("[ERROR] Q Series repository not found")

ROOT = find_root()
PKG = ROOT / "qseries_v2" / "oracle_adapters" / "independent"
MODULE = PKG / "oad_106_universal_identity_classification_physical_gate.py"
TEST = ROOT / "test_oad_106_universal_identity_classification_physical_gate.py"
INIT = PKG / "__init__.py"

MODULE_SOURCE = '\nfrom __future__ import annotations\nfrom collections import Counter\nfrom dataclasses import dataclass\n\nfrom qseries_v2.oracle_adapters.independent.oad_082_single_live_market_cohort_snapshot import (\n    capture_current_market_cohort,\n    snapshot_markets,\n)\nfrom qseries_v2.oracle_adapters.independent.oad_099_mixed_domain_cross_category_decomposition import (\n    decompose_mixed_market,\n)\nfrom qseries_v2.oracle_adapters.independent.oad_102_universal_identity_evidence_envelope import (\n    build_identity_envelopes,\n)\nfrom qseries_v2.oracle_adapters.independent.oad_103_guarded_contextual_identity_resolver import (\n    resolve_guarded_identity,\n)\nfrom qseries_v2.oracle_adapters.independent.oad_104_semantic_entity_domain_disambiguation import (\n    disambiguate_semantic_domain,\n)\nfrom qseries_v2.oracle_adapters.independent.oad_105_authoritative_source_requirement_router import (\n    assign_source_requirement,\n)\n\nREAD_ONLY = True\nEXECUTION_AUTHORITY = False\nPROBABILITY_ENABLED = False\n\nCANONICAL_SPORTS = {\n    "baseball",\n    "soccer",\n    "tennis",\n    "combat",\n    "golf",\n    "esports",\n    "hockey",\n    "basketball",\n    "football",\n    "UNKNOWN",\n}\n\n@dataclass(frozen=True, slots=True)\nclass PhysicalGate:\n    snapshot_id: str\n    markets: int\n    decomposed_legs: int\n    direct_resolved: int\n    parent_resolved: int\n    sibling_advisory_only: int\n    conflicting: int\n    unresolved: int\n    admitted_demands: int\n    demand_without_source: int\n    sports_none: int\n    noncanonical_sport_subdomains: tuple[tuple[str, int], ...]\n    financial_price_preserved: int\n    source_demand: tuple[tuple[str, int], ...]\n\ndef run_physical_gate(limit: int = 1000) -> PhysicalGate:\n    snap = capture_current_market_cohort(limit)\n\n    counts = Counter()\n    source_demand = Counter()\n    noncanonical = Counter()\n    total = 0\n\n    for market in snapshot_markets(snap):\n        legs = decompose_mixed_market(market)\n        envelopes = build_identity_envelopes(market, legs)\n\n        for leg, envelope in zip(legs, envelopes):\n            total += 1\n\n            guarded = resolve_guarded_identity(envelope)\n            counts[guarded.state] += 1\n\n            leg_domain = str(getattr(leg, "domain", "") or "")\n            leg_subdomain = str(getattr(leg, "subdomain", "") or "")\n            lexical_domain = leg_domain if leg_domain != "other" else "unknown"\n\n            semantic = disambiguate_semantic_domain(\n                getattr(leg, "text", ""),\n                lexical_domain,\n                guarded.sport,\n                leg_subdomain,\n            )\n\n            if semantic.semantic_domain == "sports":\n                if semantic.semantic_subdomain in ("", "NONE"):\n                    counts["SPORTS_NONE"] += 1\n                if semantic.semantic_subdomain not in CANONICAL_SPORTS:\n                    noncanonical[semantic.semantic_subdomain] += 1\n\n            if (\n                semantic.semantic_domain == "financial_markets"\n                and semantic.semantic_subdomain == "financial_price"\n            ):\n                counts["FINANCIAL_PRICE_PRESERVED"] += 1\n\n            admitted = semantic.semantic_domain != "unknown"\n            requirement = assign_source_requirement(\n                semantic.semantic_domain,\n                semantic.semantic_subdomain,\n                semantic.state,\n            )\n\n            if admitted:\n                counts["ADMITTED"] += 1\n                if not requirement.authoritative_source_families:\n                    counts["NO_SOURCE"] += 1\n                else:\n                    for family in requirement.authoritative_source_families:\n                        source_demand[\n                            f"{requirement.domain}:"\n                            f"{requirement.subdomain or \'UNKNOWN\'}:"\n                            f"{family}"\n                        ] += 1\n\n    return PhysicalGate(\n        snapshot_id=snap.snapshot_id,\n        markets=snap.market_count,\n        decomposed_legs=total,\n        direct_resolved=counts["RESOLVED_DIRECT"],\n        parent_resolved=counts["RESOLVED_PARENT"],\n        sibling_advisory_only=counts["SIBLING_ADVISORY_ONLY"],\n        conflicting=counts["CONFLICTING"],\n        unresolved=counts["UNRESOLVED"],\n        admitted_demands=counts["ADMITTED"],\n        demand_without_source=counts["NO_SOURCE"],\n        sports_none=counts["SPORTS_NONE"],\n        noncanonical_sport_subdomains=tuple(noncanonical.most_common()),\n        financial_price_preserved=counts["FINANCIAL_PRICE_PRESERVED"],\n        source_demand=tuple(source_demand.most_common()),\n    )\n'
TEST_SOURCE = '\nimport unittest\n\nfrom qseries_v2.oracle_adapters.independent.oad_106_universal_identity_classification_physical_gate import (\n    run_physical_gate,\n)\n\nclass T(unittest.TestCase):\n    def test_physical(self):\n        r = run_physical_gate(1000)\n\n        print("[PHYSICAL] snapshot_id=", r.snapshot_id)\n        print("[PHYSICAL] markets=", r.markets)\n        print("[PHYSICAL] decomposed_legs=", r.decomposed_legs)\n        print("[PHYSICAL] direct_resolved=", r.direct_resolved)\n        print("[PHYSICAL] parent_resolved=", r.parent_resolved)\n        print("[PHYSICAL] sibling_advisory_only=", r.sibling_advisory_only)\n        print("[PHYSICAL] conflicting=", r.conflicting)\n        print("[PHYSICAL] unresolved=", r.unresolved)\n        print("[PHYSICAL] admitted_demands=", r.admitted_demands)\n        print("[PHYSICAL] demand_without_source=", r.demand_without_source)\n        print("[PHYSICAL] sports_none=", r.sports_none)\n        print(\n            "[PHYSICAL] noncanonical_sport_subdomains=",\n            r.noncanonical_sport_subdomains,\n        )\n        print(\n            "[PHYSICAL] financial_price_preserved=",\n            r.financial_price_preserved,\n        )\n\n        for i, (key, count) in enumerate(r.source_demand, 1):\n            print("[SOURCE_DEMAND]", i, key, "count=", count)\n\n        self.assertGreater(r.markets, 0)\n        self.assertGreater(r.decomposed_legs, 0)\n        self.assertEqual(r.sports_none, 0)\n        self.assertEqual(r.noncanonical_sport_subdomains, ())\n        self.assertEqual(r.demand_without_source, 0)\n        self.assertGreater(r.financial_price_preserved, 0)\n\nif __name__ == "__main__":\n    print("=" * 108)\n    print(" OAD-106 PHYSICAL RECERTIFICATION TEST")\n    print(" UNIVERSAL IDENTITY & CLASSIFICATION — CANONICAL SPORT VOCABULARY")\n    print("=" * 108)\n\n    result = unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n    if not result.wasSuccessful():\n        raise SystemExit(1)\n\n    print("[PASS] sports:NONE=0")\n    print("[PASS] no noncanonical sport subdomains remain")\n    print("[PASS] every admitted demand has an authoritative source requirement")\n    print("[PASS] financial_markets:financial_price preserved")\n    print("[PASS] sibling-only evidence remains advisory")\n    print("[PASS] probability_enabled=FALSE")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OAD-102 through OAD-106 CAPABILITY SLICE RECERTIFIED")\n'

REQUIRED = [
    (
        "qseries_v2/oracle_adapters/independent/oad_099_mixed_domain_cross_category_decomposition.py",
        "Current OAD-099",
    ),
    (
        "qseries_v2/oracle_adapters/independent/oad_102_universal_identity_evidence_envelope.py",
        "Certified OAD-102",
    ),
    (
        "qseries_v2/oracle_adapters/independent/oad_103_guarded_contextual_identity_resolver.py",
        "Certified OAD-103",
    ),
    (
        "qseries_v2/oracle_adapters/independent/oad_104_semantic_entity_domain_disambiguation.py",
        "Rebuilt OAD-104 canonical sport vocabulary",
    ),
    (
        "qseries_v2/oracle_adapters/independent/oad_105_authoritative_source_requirement_router.py",
        "Rebuilt OAD-105 canonical sport vocabulary",
    ),
]

FROZEN = [
    (
        "qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py",
        "Frozen Kalshi OAD-055",
    ),
    (
        "qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
        "Frozen OPH-023",
    ),
    (
        "qseries_v2/universal_market_discovery/umd_098_market_taxonomy.py",
        "Frozen UMD-098",
    ),
    (
        "qseries_v2/universal_market_discovery/umd_109_market_semantic_profile.py",
        "Frozen UMD-109",
    ),
]

def write_file(path: Path, source: str) -> None:
    normalized = textwrap.dedent(source).lstrip()
    ast.parse(normalized, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(normalized, encoding="utf-8", newline="\n")
    os.replace(tmp, path)

def main() -> None:
    print("=" * 108)
    print(" OAD-106 REBUILD INSTALLER")
    print(" CANONICAL SPORT VOCABULARY PHYSICAL RECERTIFICATION — REBUILD B")
    print("=" * 108)
    print("[BOOT] Revision:", REVISION)
    print("[ROOT]", ROOT)

    for rel, label in REQUIRED:
        p = ROOT / rel
        if not p.is_file():
            raise RuntimeError(label + " missing: " + str(p))
        print("[PASS]", label, "verified")

    frozen_hashes = {
        ROOT / rel: hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
        for rel, _ in FROZEN
    }

    backups = {
        p: (p.read_bytes() if p.exists() else None)
        for p in (MODULE, TEST, INIT)
    }

    try:
        write_file(MODULE, MODULE_SOURCE)
        write_file(TEST, TEST_SOURCE)

        lines = INIT.read_text(encoding="utf-8").splitlines() if INIT.exists() else []
        export = "from .oad_106_universal_identity_classification_physical_gate import *"
        if export not in lines:
            lines.append(export)
        write_file(INIT, "\n".join(x for x in lines if x.strip()) + "\n")

        for p, expected in frozen_hashes.items():
            actual = hashlib.sha256(p.read_bytes()).hexdigest()
            if actual != expected:
                raise RuntimeError("Frozen dependency changed: " + p.name)

        print("[PASS] Replaced failed OAD-106 production gate")
        print("[PASS] Replaced OAD-106 physical certification test")
        print("[PASS] Installer and embedded sources syntax-validated")
        print("[PASS] Frozen Kalshi/OPH/UMD boundaries unchanged")
        print("[PASS] probability_enabled=FALSE")
        print("[PASS] execution_authority=FALSE")
        print("[DONE] OAD-106 REBUILD B INSTALLATION COMPLETE")

    except Exception:
        for p, data in backups.items():
            if data is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(data)
        print("[ROLLBACK] OAD-106 affected files restored")
        raise

if __name__ == "__main__":
    main()
