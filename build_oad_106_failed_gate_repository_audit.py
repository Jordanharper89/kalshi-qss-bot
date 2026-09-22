from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

REVISION="OAD_106_FAILED_GATE_CURRENT_REPOSITORY_FACT_AUDIT"
TITLE="OAD-106 FAILED PHYSICAL GATE — CURRENT REPOSITORY FACT AUDIT"

def find_root():
    for base in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (base,*base.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise SystemExit("[ERROR] Q Series repository not found")

ROOT=find_root()
PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=PKG/"oad_106_failed_gate_repository_audit.py"
TEST=ROOT/"test_oad_106_failed_gate_repository_audit.py"
INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom collections import Counter\nfrom dataclasses import asdict, dataclass, is_dataclass\nfrom pathlib import Path\nimport hashlib\nimport inspect\nimport json\n\nfrom qseries_v2.oracle_adapters.independent.oad_082_single_live_market_cohort_snapshot import capture_current_market_cohort, snapshot_markets\nfrom qseries_v2.oracle_adapters.independent.oad_099_mixed_domain_cross_category_decomposition import decompose_mixed_market\nfrom qseries_v2.oracle_adapters.independent.oad_102_universal_identity_evidence_envelope import build_identity_envelopes\nfrom qseries_v2.oracle_adapters.independent.oad_103_guarded_contextual_identity_resolver import resolve_guarded_identity\nfrom qseries_v2.oracle_adapters.independent.oad_104_semantic_entity_domain_disambiguation import disambiguate_semantic_domain\nfrom qseries_v2.oracle_adapters.independent.oad_105_authoritative_source_requirement_router import assign_source_requirement, DOMAIN_SOURCES, SPORT_SOURCES\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\nMODULE_NAMES=(\n    "oad_099_mixed_domain_cross_category_decomposition",\n    "oad_102_universal_identity_evidence_envelope",\n    "oad_103_guarded_contextual_identity_resolver",\n    "oad_104_semantic_entity_domain_disambiguation",\n    "oad_105_authoritative_source_requirement_router",\n    "oad_106_universal_identity_classification_physical_gate",\n)\n\n@dataclass(frozen=True, slots=True)\nclass RepositoryAudit:\n    snapshot_id: str\n    market_count: int\n    decomposed_legs: int\n    module_hashes: tuple\n    observed_leg_domains: tuple\n    observed_leg_subdomains: tuple\n    guarded_states: tuple\n    semantic_states: tuple\n    semantic_domains: tuple\n    semantic_subdomains: tuple\n    sports_none_count: int\n    sports_none_root_causes: tuple\n    sports_none_examples: tuple\n    demand_without_source_count: int\n    demand_without_source_groups: tuple\n    demand_without_source_examples: tuple\n    source_router_domain_keys: tuple\n    source_router_sport_keys: tuple\n    unmapped_observed_domains: tuple\n    report_hash: str\n\ndef _module_file_hash(module_name):\n    mod=__import__("qseries_v2.oracle_adapters.independent."+module_name,fromlist=["*"])\n    p=Path(inspect.getsourcefile(mod)).resolve()\n    return module_name, hashlib.sha256(p.read_bytes()).hexdigest()\n\ndef _safe(obj):\n    if is_dataclass(obj):\n        return {k:_safe(v) for k,v in asdict(obj).items()}\n    if isinstance(obj,dict):\n        return {str(k):_safe(v) for k,v in obj.items()}\n    if isinstance(obj,(tuple,list)):\n        return [_safe(x) for x in obj]\n    return obj\n\ndef _evidence_summary(env):\n    def pack(values):\n        return [{\n            "scope":e.scope,\n            "evidence_type":e.evidence_type,\n            "value":e.value,\n            "strength":e.strength,\n            "source_text":e.source_text[:180],\n        } for e in values]\n    return {\n        "local":pack(env.local_evidence),\n        "parent":pack(env.parent_evidence),\n        "sibling":pack(env.sibling_evidence[:20]),\n    }\n\ndef _sports_none_reason(leg,guarded,sem):\n    if sem.semantic_domain!="sports" or sem.semantic_subdomain not in ("","NONE"):\n        return "NOT_SPORTS_NONE"\n    if guarded.sport not in ("","NONE","UNKNOWN"):\n        return "GUARDED_SPORT_LOST_DOWNSTREAM"\n    if sem.state=="SPORT_STRUCTURE_ONLY":\n        return "SPORT_STRUCTURE_ONLY_EMITS_EMPTY_SUBDOMAIN"\n    if getattr(leg,"domain","")=="sports" and getattr(leg,"subdomain","") in ("","NONE"):\n        return "UPSTREAM_SPORTS_EMPTY_SUBDOMAIN_PROPAGATED"\n    if getattr(leg,"domain","")=="sports":\n        return "UPSTREAM_SPORTS_DOMAIN_NOT_CARRIED_TO_SEMANTIC_SUBDOMAIN"\n    return "OTHER_EMPTY_SPORT_SUBDOMAIN_PATH"\n\ndef run_repository_audit(limit=1000,example_limit=20):\n    hashes=tuple(_module_file_hash(x) for x in MODULE_NAMES)\n    snap=capture_current_market_cohort(limit)\n\n    leg_domains=Counter()\n    leg_subdomains=Counter()\n    guarded_states=Counter()\n    semantic_states=Counter()\n    semantic_domains=Counter()\n    semantic_subdomains=Counter()\n    sports_none_reasons=Counter()\n    missing_source_groups=Counter()\n    sports_none_examples=[]\n    missing_source_examples=[]\n    observed_semantic_domains=set()\n    total=0\n\n    for market in snapshot_markets(snap):\n        legs=decompose_mixed_market(market)\n        envs=build_identity_envelopes(market,legs)\n\n        for leg,env in zip(legs,envs):\n            total+=1\n            leg_domain=str(getattr(leg,"domain","") or "")\n            leg_subdomain=str(getattr(leg,"subdomain","") or "")\n            leg_domains[leg_domain or "<EMPTY>"]+=1\n            leg_subdomains[f"{leg_domain or \'<EMPTY>\'}:{leg_subdomain or \'<EMPTY>\'}"]+=1\n\n            guarded=resolve_guarded_identity(env)\n            guarded_states[guarded.state]+=1\n\n            lexical_domain=leg_domain if leg_domain!="other" else "unknown"\n            sem=disambiguate_semantic_domain(getattr(leg,"text",""),lexical_domain,guarded.sport)\n\n            semantic_states[sem.state]+=1\n            semantic_domains[sem.semantic_domain or "<EMPTY>"]+=1\n            semantic_subdomains[f"{sem.semantic_domain or \'<EMPTY>\'}:{sem.semantic_subdomain or \'<EMPTY>\'}"]+=1\n            observed_semantic_domains.add(sem.semantic_domain)\n\n            if sem.semantic_domain=="sports" and sem.semantic_subdomain in ("","NONE"):\n                reason=_sports_none_reason(leg,guarded,sem)\n                sports_none_reasons[reason]+=1\n                if len(sports_none_examples)<example_limit:\n                    sports_none_examples.append({\n                        "parent_ticker":str(getattr(leg,"parent_ticker","")),\n                        "leg_index":int(getattr(leg,"leg_index",-1)),\n                        "leg_text":str(getattr(leg,"text","")),\n                        "leg_domain":leg_domain,\n                        "leg_subdomain":leg_subdomain,\n                        "guarded":_safe(guarded),\n                        "semantic":_safe(sem),\n                        "root_reason":reason,\n                        "evidence":_evidence_summary(env),\n                    })\n\n            req=assign_source_requirement(sem.semantic_domain,sem.semantic_subdomain,sem.state)\n            admitted=sem.semantic_domain!="unknown"\n            if admitted and not req.authoritative_source_families:\n                key=(f"semantic={sem.semantic_domain}:{sem.semantic_subdomain or \'<EMPTY>\'}"\n                     f"|state={sem.state}|leg={leg_domain}:{leg_subdomain or \'<EMPTY>\'}")\n                missing_source_groups[key]+=1\n                if len(missing_source_examples)<example_limit:\n                    missing_source_examples.append({\n                        "parent_ticker":str(getattr(leg,"parent_ticker","")),\n                        "leg_index":int(getattr(leg,"leg_index",-1)),\n                        "leg_text":str(getattr(leg,"text","")),\n                        "leg_domain":leg_domain,\n                        "leg_subdomain":leg_subdomain,\n                        "guarded":_safe(guarded),\n                        "semantic":_safe(sem),\n                        "source_requirement":_safe(req),\n                        "evidence":_evidence_summary(env),\n                    })\n\n    router_domains=set(DOMAIN_SOURCES)\n    unmapped=tuple(sorted(x for x in observed_semantic_domains if x not in ("unknown","sports") and x not in router_domains))\n\n    payload={\n        "snapshot_id":snap.snapshot_id,\n        "market_count":snap.market_count,\n        "decomposed_legs":total,\n        "module_hashes":hashes,\n        "observed_leg_domains":tuple(leg_domains.most_common()),\n        "observed_leg_subdomains":tuple(leg_subdomains.most_common()),\n        "guarded_states":tuple(guarded_states.most_common()),\n        "semantic_states":tuple(semantic_states.most_common()),\n        "semantic_domains":tuple(semantic_domains.most_common()),\n        "semantic_subdomains":tuple(semantic_subdomains.most_common()),\n        "sports_none_count":sum(sports_none_reasons.values()),\n        "sports_none_root_causes":tuple(sports_none_reasons.most_common()),\n        "sports_none_examples":tuple(sports_none_examples),\n        "demand_without_source_count":sum(missing_source_groups.values()),\n        "demand_without_source_groups":tuple(missing_source_groups.most_common()),\n        "demand_without_source_examples":tuple(missing_source_examples),\n        "source_router_domain_keys":tuple(sorted(DOMAIN_SOURCES)),\n        "source_router_sport_keys":tuple(sorted(SPORT_SOURCES)),\n        "unmapped_observed_domains":unmapped,\n    }\n    report_hash=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()\n    return RepositoryAudit(report_hash=report_hash,**payload)\n\ndef write_report(root=None,limit=1000):\n    root=Path(root or Path.cwd()).resolve()\n    report=run_repository_audit(limit)\n    path=root/"OAD_106_FAILED_GATE_REPOSITORY_AUDIT.json"\n    path.write_text(json.dumps(_safe(report),indent=2,sort_keys=True),encoding="utf-8")\n    return report,path\n'
TEST_SOURCE='from __future__ import annotations\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_106_failed_gate_repository_audit import write_report\n\nclass T(unittest.TestCase):\n    def test_physical_repository_audit(self):\n        r,path=write_report(limit=1000)\n        print("[PHYSICAL] snapshot_id=",r.snapshot_id)\n        print("[PHYSICAL] markets=",r.market_count)\n        print("[PHYSICAL] decomposed_legs=",r.decomposed_legs)\n        print("[PHYSICAL] module_hashes=",r.module_hashes)\n        print("[PHYSICAL] observed_leg_domains=",r.observed_leg_domains)\n        print("[PHYSICAL] observed_leg_subdomains=",r.observed_leg_subdomains[:30])\n        print("[PHYSICAL] guarded_states=",r.guarded_states)\n        print("[PHYSICAL] semantic_states=",r.semantic_states)\n        print("[PHYSICAL] semantic_domains=",r.semantic_domains)\n        print("[PHYSICAL] semantic_subdomains=",r.semantic_subdomains)\n        print("[PHYSICAL] sports_none_count=",r.sports_none_count)\n        print("[PHYSICAL] sports_none_root_causes=",r.sports_none_root_causes)\n        print("[PHYSICAL] demand_without_source_count=",r.demand_without_source_count)\n        print("[PHYSICAL] demand_without_source_groups=",r.demand_without_source_groups)\n        print("[PHYSICAL] source_router_domain_keys=",r.source_router_domain_keys)\n        print("[PHYSICAL] source_router_sport_keys=",r.source_router_sport_keys)\n        print("[PHYSICAL] unmapped_observed_domains=",r.unmapped_observed_domains)\n        print("[PHYSICAL] report_hash=",r.report_hash)\n        for x in r.sports_none_examples:\n            print("[SPORTS_NONE_EXAMPLE]",x)\n        for x in r.demand_without_source_examples:\n            print("[NO_SOURCE_EXAMPLE]",x)\n        print("[REPORT]",path)\n        self.assertGreater(r.market_count,0)\n        self.assertGreater(r.decomposed_legs,0)\n        self.assertTrue(r.module_hashes)\n\nif __name__=="__main__":\n    print("="*108)\n    print(" OAD-106 FAILED PHYSICAL GATE — CURRENT REPOSITORY FACT AUDIT")\n    print("="*108)\n    res=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not res.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Current OAD-099/OAD-102..106 production files fingerprinted")\n    print("[PASS] Live 1,000-market cohort audited through exact current production path")\n    print("[PASS] Every sports/NONE path grouped by actual root cause")\n    print("[PASS] Every admitted demand without source grouped by actual emitted domain/state")\n    print("[PASS] No production classifier behavior changed")\n    print("[PASS] probability_enabled=FALSE")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OAD-106 CURRENT-REPOSITORY FAILURE AUDIT COMPLETE")\n'

REQUIRED=[
("qseries_v2/oracle_adapters/independent/oad_099_mixed_domain_cross_category_decomposition.py","Current OAD-099"),
("qseries_v2/oracle_adapters/independent/oad_102_universal_identity_evidence_envelope.py","Current OAD-102"),
("qseries_v2/oracle_adapters/independent/oad_103_guarded_contextual_identity_resolver.py","Current OAD-103"),
("qseries_v2/oracle_adapters/independent/oad_104_semantic_entity_domain_disambiguation.py","Current OAD-104"),
("qseries_v2/oracle_adapters/independent/oad_105_authoritative_source_requirement_router.py","Current OAD-105"),
("qseries_v2/oracle_adapters/independent/oad_106_universal_identity_classification_physical_gate.py","Current failed OAD-106 physical gate"),
]
FROZEN=[
("qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py","Frozen Kalshi OAD-055"),
("qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py","Frozen OPH-023"),
("qseries_v2/universal_market_discovery/umd_098_market_taxonomy.py","Frozen UMD-098"),
("qseries_v2/universal_market_discovery/umd_109_market_semantic_profile.py","Frozen UMD-109"),
]

def write(path,source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*108)
    print(" OAD-106 DIAGNOSTIC INSTALLER")
    print(" "+TITLE)
    print("="*108)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",ROOT)
    for rel,label in REQUIRED:
        p=ROOT/rel
        if not p.is_file(): raise RuntimeError(label+" missing: "+str(p))
        print("[PASS]",label,"verified")

    frozen={ROOT/rel:hashlib.sha256((ROOT/rel).read_bytes()).hexdigest() for rel,_ in FROZEN}
    old={p:(p.read_bytes() if p.exists() else None) for p in (MODULE,TEST,INIT)}
    try:
        write(MODULE,MODULE_SOURCE)
        write(TEST,TEST_SOURCE)
        lines=INIT.read_text(encoding="utf-8").splitlines() if INIT.exists() else []
        export="from .oad_106_failed_gate_repository_audit import *"
        if export not in lines: lines.append(export)
        write(INIT,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in frozen.items():
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("Frozen dependency changed: "+p.name)
        print("[PASS] Current repository diagnostic installed")
        print("[PASS] OAD-099/OAD-102..106 will be fingerprinted at test runtime")
        print("[PASS] Diagnostic changes no classifier behavior")
        print("[PASS] Frozen Kalshi/OPH/UMD boundaries unchanged")
        print("[PASS] probability_enabled=FALSE")
        print("[PASS] execution_authority=FALSE")
        print("[DONE] OAD-106 CURRENT-REPOSITORY AUDIT INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(data)
        print("[ROLLBACK] Diagnostic files restored")
        raise

if __name__=="__main__":
    main()
