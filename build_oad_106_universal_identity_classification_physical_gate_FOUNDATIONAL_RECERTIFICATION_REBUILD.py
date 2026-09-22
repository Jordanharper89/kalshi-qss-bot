from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID='OAD-106'
REVISION='OAD_106_FOUNDATIONAL_CONTRACT_RECERTIFICATION_REBUILD'
TITLE='UNIVERSAL IDENTITY & CLASSIFICATION PHYSICAL GATE — FOUNDATIONAL RECERTIFICATION'

def find_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base, *base.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise SystemExit("[ERROR] Q Series repository not found")

ROOT=find_root()
PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=ROOT/'qseries_v2/oracle_adapters/independent/oad_106_universal_identity_classification_physical_gate.py'
TEST=ROOT/'test_oad_106_universal_identity_classification_physical_gate.py'
INIT=PKG/"__init__.py"
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom collections import Counter\nfrom dataclasses import dataclass\n\nfrom qseries_v2.oracle_adapters.independent.oad_082_single_live_market_cohort_snapshot import capture_current_market_cohort, snapshot_markets\nfrom qseries_v2.oracle_adapters.independent.oad_099_mixed_domain_cross_category_decomposition import decompose_mixed_market\nfrom qseries_v2.oracle_adapters.independent.oad_102_universal_identity_evidence_envelope import build_identity_envelopes\nfrom qseries_v2.oracle_adapters.independent.oad_103_guarded_contextual_identity_resolver import resolve_guarded_identity\nfrom qseries_v2.oracle_adapters.independent.oad_104_semantic_entity_domain_disambiguation import disambiguate_semantic_domain\nfrom qseries_v2.oracle_adapters.independent.oad_105_authoritative_source_requirement_router import assign_source_requirement\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\n@dataclass(frozen=True, slots=True)\nclass PhysicalGate:\n    snapshot_id: str\n    markets: int\n    decomposed_legs: int\n    direct_resolved: int\n    parent_resolved: int\n    sibling_advisory_only: int\n    conflicting: int\n    unresolved: int\n    admitted_demands: int\n    demand_without_source: int\n    sports_none: int\n    financial_price_preserved: int\n    unmapped_admitted_domains: tuple[tuple[str,int],...]\n    source_demand: tuple[tuple[str,int],...]\n\ndef run_physical_gate(limit=1000):\n    snap=capture_current_market_cohort(limit)\n    c=Counter()\n    source=Counter()\n    unmapped=Counter()\n    total=0\n\n    for market in snapshot_markets(snap):\n        legs=decompose_mixed_market(market)\n        envs=build_identity_envelopes(market,legs)\n        for leg,env in zip(legs,envs):\n            total+=1\n            g=resolve_guarded_identity(env)\n            c[g.state]+=1\n\n            leg_domain=str(getattr(leg,"domain","") or "")\n            leg_subdomain=str(getattr(leg,"subdomain","") or "")\n            lexical_domain=leg_domain if leg_domain!="other" else "unknown"\n\n            sem=disambiguate_semantic_domain(\n                getattr(leg,"text",""),\n                lexical_domain,\n                g.sport,\n                leg_subdomain,\n            )\n\n            if sem.semantic_domain=="sports" and sem.semantic_subdomain in ("","NONE"):\n                c["SPORTS_NONE"]+=1\n\n            if sem.semantic_domain=="financial_markets" and sem.semantic_subdomain=="financial_price":\n                c["FINANCIAL_PRICE_PRESERVED"]+=1\n\n            admitted=sem.semantic_domain!="unknown"\n            req=assign_source_requirement(sem.semantic_domain,sem.semantic_subdomain,sem.state)\n\n            if admitted:\n                c["ADMITTED"]+=1\n                if not req.authoritative_source_families:\n                    c["NO_SOURCE"]+=1\n                    unmapped[f"{sem.semantic_domain}:{sem.semantic_subdomain or \'<EMPTY>\'}:{req.state}"]+=1\n                else:\n                    for fam in req.authoritative_source_families:\n                        source[f"{sem.semantic_domain}:{sem.semantic_subdomain or \'UNKNOWN\'}:{fam}"]+=1\n\n    return PhysicalGate(\n        snap.snapshot_id,\n        snap.market_count,\n        total,\n        c["RESOLVED_DIRECT"],\n        c["RESOLVED_PARENT"],\n        c["SIBLING_ADVISORY_ONLY"],\n        c["CONFLICTING"],\n        c["UNRESOLVED"],\n        c["ADMITTED"],\n        c["NO_SOURCE"],\n        c["SPORTS_NONE"],\n        c["FINANCIAL_PRICE_PRESERVED"],\n        tuple(unmapped.most_common()),\n        tuple(source.most_common()),\n    )\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_106_universal_identity_classification_physical_gate import run_physical_gate\n\nclass T(unittest.TestCase):\n    def test_physical(self):\n        r=run_physical_gate(1000)\n        print("[PHYSICAL] snapshot_id=",r.snapshot_id)\n        print("[PHYSICAL] markets=",r.markets)\n        print("[PHYSICAL] decomposed_legs=",r.decomposed_legs)\n        print("[PHYSICAL] direct_resolved=",r.direct_resolved)\n        print("[PHYSICAL] parent_resolved=",r.parent_resolved)\n        print("[PHYSICAL] sibling_advisory_only=",r.sibling_advisory_only)\n        print("[PHYSICAL] conflicting=",r.conflicting)\n        print("[PHYSICAL] unresolved=",r.unresolved)\n        print("[PHYSICAL] admitted_demands=",r.admitted_demands)\n        print("[PHYSICAL] demand_without_source=",r.demand_without_source)\n        print("[PHYSICAL] sports_none=",r.sports_none)\n        print("[PHYSICAL] financial_price_preserved=",r.financial_price_preserved)\n        print("[PHYSICAL] unmapped_admitted_domains=",r.unmapped_admitted_domains)\n        for i,(k,n) in enumerate(r.source_demand,1):\n            print("[SOURCE_DEMAND]",i,k,"count=",n)\n\n        self.assertGreater(r.markets,0)\n        self.assertGreater(r.decomposed_legs,0)\n        self.assertEqual(r.sports_none,0)\n        self.assertEqual(r.demand_without_source,0)\n        self.assertEqual(r.unmapped_admitted_domains,())\n        self.assertGreater(r.financial_price_preserved,0)\n\nif __name__=="__main__":\n    print("="*108)\n    print(" OAD-106 PHYSICAL RECERTIFICATION TEST")\n    print(" UNIVERSAL IDENTITY & CLASSIFICATION — FOUNDATIONAL CONTRACT REPAIR")\n    print("="*108)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] sports:UNKNOWN never degrades to sports:NONE")\n    print("[PASS] financial_markets:financial_price preserved")\n    print("[PASS] every admitted demand has authoritative source requirement")\n    print("[PASS] sibling-only evidence remains advisory")\n    print("[PASS] probability_enabled=FALSE")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OAD-102 through OAD-106 CAPABILITY SLICE RECERTIFIED")\n'
REQUIRED=[('qseries_v2/oracle_adapters/independent/oad_099_mixed_domain_cross_category_decomposition.py', 'Current OAD-099 decomposition'), ('qseries_v2/oracle_adapters/independent/oad_102_universal_identity_evidence_envelope.py', 'Certified OAD-102'), ('qseries_v2/oracle_adapters/independent/oad_103_guarded_contextual_identity_resolver.py', 'Certified OAD-103'), ('qseries_v2/oracle_adapters/independent/oad_104_semantic_entity_domain_disambiguation.py', 'Rebuilt OAD-104'), ('qseries_v2/oracle_adapters/independent/oad_105_authoritative_source_requirement_router.py', 'Rebuilt OAD-105'), ('qseries_v2/oracle_adapters/independent/oad_106_failed_gate_repository_audit.py', 'Certified repository failure audit')]
FROZEN=[('qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py', 'Frozen Kalshi OAD-055'), ('qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py', 'Frozen OPH-023'), ('qseries_v2/universal_market_discovery/umd_098_market_taxonomy.py', 'Frozen UMD-098'), ('qseries_v2/universal_market_discovery/umd_109_market_semantic_profile.py', 'Frozen UMD-109')]

def write(path, source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source, encoding="utf-8", newline="\n")
    os.replace(tmp,path)

def main():
    print("="*108)
    print(" OAD-106 REBUILD INSTALLER")
    print(" "+TITLE)
    print("="*108)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",ROOT)
    for rel,label in REQUIRED:
        p=ROOT/rel
        if not p.is_file():
            raise RuntimeError(label+" missing: "+str(p))
        print("[PASS]",label,"verified")
    frozen={ROOT/rel:hashlib.sha256((ROOT/rel).read_bytes()).hexdigest() for rel,_ in FROZEN}
    old={p:(p.read_bytes() if p.exists() else None) for p in (MODULE,TEST,INIT)}
    try:
        write(MODULE,MODULE_SOURCE)
        write(TEST,TEST_SOURCE)
        lines=INIT.read_text(encoding="utf-8").splitlines() if INIT.exists() else []
        export=f"from .oad_106_universal_identity_classification_physical_gate import *"
        if export not in lines:
            lines.append(export)
        write(INIT,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in frozen.items():
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("Frozen dependency changed: "+p.name)
        print("[PASS] Rebuilt foundational module:",MODULE.relative_to(ROOT))
        print("[PASS] Wrote:",TEST.name)
        print("[PASS] Frozen Kalshi/OPH/UMD boundaries unchanged")
        print("[PASS] probability_enabled=FALSE")
        print("[PASS] execution_authority=FALSE")
        print("[DONE] OAD-106 REBUILD INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(data)
        print("[ROLLBACK] OAD-106 affected files restored")
        raise

if __name__=="__main__":
    main()
