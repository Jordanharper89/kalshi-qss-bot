from __future__ import annotations
from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
import hashlib
import inspect
import json

from qseries_v2.oracle_adapters.independent.oad_082_single_live_market_cohort_snapshot import capture_current_market_cohort, snapshot_markets
from qseries_v2.oracle_adapters.independent.oad_099_mixed_domain_cross_category_decomposition import decompose_mixed_market
from qseries_v2.oracle_adapters.independent.oad_102_universal_identity_evidence_envelope import build_identity_envelopes
from qseries_v2.oracle_adapters.independent.oad_103_guarded_contextual_identity_resolver import resolve_guarded_identity
from qseries_v2.oracle_adapters.independent.oad_104_semantic_entity_domain_disambiguation import disambiguate_semantic_domain
from qseries_v2.oracle_adapters.independent.oad_105_authoritative_source_requirement_router import assign_source_requirement, DOMAIN_SOURCES, SPORT_SOURCES

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

MODULE_NAMES=(
    "oad_099_mixed_domain_cross_category_decomposition",
    "oad_102_universal_identity_evidence_envelope",
    "oad_103_guarded_contextual_identity_resolver",
    "oad_104_semantic_entity_domain_disambiguation",
    "oad_105_authoritative_source_requirement_router",
    "oad_106_universal_identity_classification_physical_gate",
)

@dataclass(frozen=True, slots=True)
class RepositoryAudit:
    snapshot_id: str
    market_count: int
    decomposed_legs: int
    module_hashes: tuple
    observed_leg_domains: tuple
    observed_leg_subdomains: tuple
    guarded_states: tuple
    semantic_states: tuple
    semantic_domains: tuple
    semantic_subdomains: tuple
    sports_none_count: int
    sports_none_root_causes: tuple
    sports_none_examples: tuple
    demand_without_source_count: int
    demand_without_source_groups: tuple
    demand_without_source_examples: tuple
    source_router_domain_keys: tuple
    source_router_sport_keys: tuple
    unmapped_observed_domains: tuple
    report_hash: str

def _module_file_hash(module_name):
    mod=__import__("qseries_v2.oracle_adapters.independent."+module_name,fromlist=["*"])
    p=Path(inspect.getsourcefile(mod)).resolve()
    return module_name, hashlib.sha256(p.read_bytes()).hexdigest()

def _safe(obj):
    if is_dataclass(obj):
        return {k:_safe(v) for k,v in asdict(obj).items()}
    if isinstance(obj,dict):
        return {str(k):_safe(v) for k,v in obj.items()}
    if isinstance(obj,(tuple,list)):
        return [_safe(x) for x in obj]
    return obj

def _evidence_summary(env):
    def pack(values):
        return [{
            "scope":e.scope,
            "evidence_type":e.evidence_type,
            "value":e.value,
            "strength":e.strength,
            "source_text":e.source_text[:180],
        } for e in values]
    return {
        "local":pack(env.local_evidence),
        "parent":pack(env.parent_evidence),
        "sibling":pack(env.sibling_evidence[:20]),
    }

def _sports_none_reason(leg,guarded,sem):
    if sem.semantic_domain!="sports" or sem.semantic_subdomain not in ("","NONE"):
        return "NOT_SPORTS_NONE"
    if guarded.sport not in ("","NONE","UNKNOWN"):
        return "GUARDED_SPORT_LOST_DOWNSTREAM"
    if sem.state=="SPORT_STRUCTURE_ONLY":
        return "SPORT_STRUCTURE_ONLY_EMITS_EMPTY_SUBDOMAIN"
    if getattr(leg,"domain","")=="sports" and getattr(leg,"subdomain","") in ("","NONE"):
        return "UPSTREAM_SPORTS_EMPTY_SUBDOMAIN_PROPAGATED"
    if getattr(leg,"domain","")=="sports":
        return "UPSTREAM_SPORTS_DOMAIN_NOT_CARRIED_TO_SEMANTIC_SUBDOMAIN"
    return "OTHER_EMPTY_SPORT_SUBDOMAIN_PATH"

def run_repository_audit(limit=1000,example_limit=20):
    hashes=tuple(_module_file_hash(x) for x in MODULE_NAMES)
    snap=capture_current_market_cohort(limit)

    leg_domains=Counter()
    leg_subdomains=Counter()
    guarded_states=Counter()
    semantic_states=Counter()
    semantic_domains=Counter()
    semantic_subdomains=Counter()
    sports_none_reasons=Counter()
    missing_source_groups=Counter()
    sports_none_examples=[]
    missing_source_examples=[]
    observed_semantic_domains=set()
    total=0

    for market in snapshot_markets(snap):
        legs=decompose_mixed_market(market)
        envs=build_identity_envelopes(market,legs)

        for leg,env in zip(legs,envs):
            total+=1
            leg_domain=str(getattr(leg,"domain","") or "")
            leg_subdomain=str(getattr(leg,"subdomain","") or "")
            leg_domains[leg_domain or "<EMPTY>"]+=1
            leg_subdomains[f"{leg_domain or '<EMPTY>'}:{leg_subdomain or '<EMPTY>'}"]+=1

            guarded=resolve_guarded_identity(env)
            guarded_states[guarded.state]+=1

            lexical_domain=leg_domain if leg_domain!="other" else "unknown"
            sem=disambiguate_semantic_domain(getattr(leg,"text",""),lexical_domain,guarded.sport)

            semantic_states[sem.state]+=1
            semantic_domains[sem.semantic_domain or "<EMPTY>"]+=1
            semantic_subdomains[f"{sem.semantic_domain or '<EMPTY>'}:{sem.semantic_subdomain or '<EMPTY>'}"]+=1
            observed_semantic_domains.add(sem.semantic_domain)

            if sem.semantic_domain=="sports" and sem.semantic_subdomain in ("","NONE"):
                reason=_sports_none_reason(leg,guarded,sem)
                sports_none_reasons[reason]+=1
                if len(sports_none_examples)<example_limit:
                    sports_none_examples.append({
                        "parent_ticker":str(getattr(leg,"parent_ticker","")),
                        "leg_index":int(getattr(leg,"leg_index",-1)),
                        "leg_text":str(getattr(leg,"text","")),
                        "leg_domain":leg_domain,
                        "leg_subdomain":leg_subdomain,
                        "guarded":_safe(guarded),
                        "semantic":_safe(sem),
                        "root_reason":reason,
                        "evidence":_evidence_summary(env),
                    })

            req=assign_source_requirement(sem.semantic_domain,sem.semantic_subdomain,sem.state)
            admitted=sem.semantic_domain!="unknown"
            if admitted and not req.authoritative_source_families:
                key=(f"semantic={sem.semantic_domain}:{sem.semantic_subdomain or '<EMPTY>'}"
                     f"|state={sem.state}|leg={leg_domain}:{leg_subdomain or '<EMPTY>'}")
                missing_source_groups[key]+=1
                if len(missing_source_examples)<example_limit:
                    missing_source_examples.append({
                        "parent_ticker":str(getattr(leg,"parent_ticker","")),
                        "leg_index":int(getattr(leg,"leg_index",-1)),
                        "leg_text":str(getattr(leg,"text","")),
                        "leg_domain":leg_domain,
                        "leg_subdomain":leg_subdomain,
                        "guarded":_safe(guarded),
                        "semantic":_safe(sem),
                        "source_requirement":_safe(req),
                        "evidence":_evidence_summary(env),
                    })

    router_domains=set(DOMAIN_SOURCES)
    unmapped=tuple(sorted(x for x in observed_semantic_domains if x not in ("unknown","sports") and x not in router_domains))

    payload={
        "snapshot_id":snap.snapshot_id,
        "market_count":snap.market_count,
        "decomposed_legs":total,
        "module_hashes":hashes,
        "observed_leg_domains":tuple(leg_domains.most_common()),
        "observed_leg_subdomains":tuple(leg_subdomains.most_common()),
        "guarded_states":tuple(guarded_states.most_common()),
        "semantic_states":tuple(semantic_states.most_common()),
        "semantic_domains":tuple(semantic_domains.most_common()),
        "semantic_subdomains":tuple(semantic_subdomains.most_common()),
        "sports_none_count":sum(sports_none_reasons.values()),
        "sports_none_root_causes":tuple(sports_none_reasons.most_common()),
        "sports_none_examples":tuple(sports_none_examples),
        "demand_without_source_count":sum(missing_source_groups.values()),
        "demand_without_source_groups":tuple(missing_source_groups.most_common()),
        "demand_without_source_examples":tuple(missing_source_examples),
        "source_router_domain_keys":tuple(sorted(DOMAIN_SOURCES)),
        "source_router_sport_keys":tuple(sorted(SPORT_SOURCES)),
        "unmapped_observed_domains":unmapped,
    }
    report_hash=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
    return RepositoryAudit(report_hash=report_hash,**payload)

def write_report(root=None,limit=1000):
    root=Path(root or Path.cwd()).resolve()
    report=run_repository_audit(limit)
    path=root/"OAD_106_FAILED_GATE_REPOSITORY_AUDIT.json"
    path.write_text(json.dumps(_safe(report),indent=2,sort_keys=True),encoding="utf-8")
    return report,path
