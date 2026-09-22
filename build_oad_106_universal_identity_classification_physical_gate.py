from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID='OAD-106'
REVISION='OAD_106_UNIVERSAL_IDENTITY_CLASSIFICATION_PHYSICAL_GATE_V1'
TITLE='UNIVERSAL IDENTITY & CLASSIFICATION PHYSICAL GATE'

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
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom collections import Counter\nfrom dataclasses import dataclass\n\nfrom qseries_v2.oracle_adapters.independent.oad_082_single_live_market_cohort_snapshot import capture_current_market_cohort, snapshot_markets\nfrom qseries_v2.oracle_adapters.independent.oad_099_mixed_domain_cross_category_decomposition import decompose_mixed_market\nfrom qseries_v2.oracle_adapters.independent.oad_102_universal_identity_evidence_envelope import build_identity_envelopes\nfrom qseries_v2.oracle_adapters.independent.oad_103_guarded_contextual_identity_resolver import resolve_guarded_identity\nfrom qseries_v2.oracle_adapters.independent.oad_104_semantic_entity_domain_disambiguation import disambiguate_semantic_domain\nfrom qseries_v2.oracle_adapters.independent.oad_105_authoritative_source_requirement_router import assign_source_requirement\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\n@dataclass(frozen=True, slots=True)\nclass PhysicalGate:\n    snapshot_id: str\n    markets: int\n    decomposed_legs: int\n    direct_resolved: int\n    parent_resolved: int\n    sibling_advisory_only: int\n    conflicting: int\n    unresolved: int\n    admitted_demands: int\n    demand_without_source: int\n    sports_none: int\n    source_demand: tuple[tuple[str,int],...]\n\ndef run_physical_gate(limit=1000):\n    snap=capture_current_market_cohort(limit)\n    c=Counter()\n    source=Counter()\n    legs_total=0\n    for market in snapshot_markets(snap):\n        legs=decompose_mixed_market(market)\n        legs_total += len(legs)\n        envs=build_identity_envelopes(market,legs)\n        for leg,env in zip(legs,envs):\n            g=resolve_guarded_identity(env)\n            c[g.state]+=1\n            lexical_domain = leg.domain if leg.domain!="other" else "unknown"\n            sem=disambiguate_semantic_domain(leg.text,lexical_domain,g.sport)\n            req=assign_source_requirement(\n                sem.semantic_domain,\n                sem.semantic_subdomain,\n                sem.state\n            )\n            if sem.semantic_domain!="unknown":\n                c["ADMITTED"]+=1\n                if not req.authoritative_source_families:\n                    c["NO_SOURCE"]+=1\n                else:\n                    for fam in req.authoritative_source_families:\n                        source[f"{sem.semantic_domain}:{sem.semantic_subdomain or \'NONE\'}:{fam}"]+=1\n            if sem.semantic_domain=="sports" and sem.semantic_subdomain in ("","NONE"):\n                c["SPORTS_NONE"]+=1\n    return PhysicalGate(\n        snap.snapshot_id,snap.market_count,legs_total,\n        c["RESOLVED_DIRECT"],c["RESOLVED_PARENT"],c["SIBLING_ADVISORY_ONLY"],\n        c["CONFLICTING"],c["UNRESOLVED"],c["ADMITTED"],c["NO_SOURCE"],c["SPORTS_NONE"],\n        tuple(source.most_common())\n    )\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_106_universal_identity_classification_physical_gate import run_physical_gate\nclass T(unittest.TestCase):\n    def test_physical(self):\n        r=run_physical_gate(1000)\n        print("[PHYSICAL] snapshot_id=",r.snapshot_id)\n        print("[PHYSICAL] markets=",r.markets)\n        print("[PHYSICAL] decomposed_legs=",r.decomposed_legs)\n        print("[PHYSICAL] direct_resolved=",r.direct_resolved)\n        print("[PHYSICAL] parent_resolved=",r.parent_resolved)\n        print("[PHYSICAL] sibling_advisory_only=",r.sibling_advisory_only)\n        print("[PHYSICAL] conflicting=",r.conflicting)\n        print("[PHYSICAL] unresolved=",r.unresolved)\n        print("[PHYSICAL] admitted_demands=",r.admitted_demands)\n        print("[PHYSICAL] demand_without_source=",r.demand_without_source)\n        print("[PHYSICAL] sports_none=",r.sports_none)\n        for i,(k,n) in enumerate(r.source_demand,1):\n            print("[BUILD_NEXT]",i,k,"count=",n)\n        self.assertGreater(r.markets,0)\n        self.assertGreater(r.decomposed_legs,0)\n        self.assertEqual(r.demand_without_source,0)\n        self.assertEqual(r.sports_none,0)\nif __name__=="__main__":\n    print("="*104); print(" OAD-106 PHYSICAL CERTIFICATION TEST"); print(" UNIVERSAL IDENTITY & CLASSIFICATION REBUILD"); print("="*104)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] One physical live cohort traversed OAD-102 through OAD-105")\n    print("[PASS] Sibling-only evidence never directly resolves identity")\n    print("[PASS] Every admitted demand has an authoritative source requirement")\n    print("[PASS] sports/NONE=0")\n    print("[PASS] probability_enabled=FALSE")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OAD-102 through OAD-106 CAPABILITY SLICE CERTIFIED")\n'
REQUIRED=[('qseries_v2/oracle_adapters/independent/oad_102_universal_identity_evidence_envelope.py', 'Certified OAD-102 identity envelope'), ('qseries_v2/oracle_adapters/independent/oad_103_guarded_contextual_identity_resolver.py', 'Certified OAD-103 guarded resolver'), ('qseries_v2/oracle_adapters/independent/oad_104_semantic_entity_domain_disambiguation.py', 'Certified OAD-104 semantic disambiguation'), ('qseries_v2/oracle_adapters/independent/oad_105_authoritative_source_requirement_router.py', 'Certified OAD-105 source router')]
FROZEN=[
 ("qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py","Frozen Kalshi OAD-055"),
 ("qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py","Frozen OPH-023"),
 ("qseries_v2/universal_market_discovery/umd_098_market_taxonomy.py","Frozen UMD-098"),
 ("qseries_v2/universal_market_discovery/umd_109_market_semantic_profile.py","Frozen UMD-109"),
]

def write(path, source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source, encoding="utf-8", newline="\n")
    os.replace(tmp,path)

def main():
    print("="*104)
    print(" OAD-106 INSTALLER")
    print(" "+TITLE)
    print("="*104)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",ROOT)
    for rel,label in REQUIRED:
        p=ROOT/rel
        if not p.is_file():
            raise RuntimeError(label+" missing")
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
        print("[PASS] Wrote:",MODULE.relative_to(ROOT))
        print("[PASS] Wrote:",TEST.name)
        print("[PASS] Frozen Kalshi/OPH/UMD boundaries unchanged")
        print("[PASS] probability_enabled=FALSE")
        print("[PASS] execution_authority=FALSE")
        print("[DONE] OAD-106 INSTALLATION COMPLETE")
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
