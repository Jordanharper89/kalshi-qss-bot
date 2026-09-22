from __future__ import annotations
from dataclasses import dataclass
from qseries_v2.oracle_adapters.independent.oad_102_universal_identity_evidence_envelope import IdentityEnvelope

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

@dataclass(frozen=True, slots=True)
class GuardedIdentity:
    parent_ticker: str
    leg_index: int
    leg_text: str
    domain: str
    sport: str
    state: str
    confidence_basis: str
    evidence_scope: str

def _sports_values(evs):
    return sorted({e.value for e in evs if e.evidence_type=="sport"})

def resolve_guarded_identity(env: IdentityEnvelope):
    local=_sports_values(env.local_evidence)
    parent=_sports_values(env.parent_evidence)
    sibling=_sports_values(env.sibling_evidence)

    if len(local)==1:
        return GuardedIdentity(env.parent_ticker,env.leg_index,env.leg_text,"sports",local[0],
            "RESOLVED_DIRECT","direct structural sport evidence","local")
    if len(local)>1:
        return GuardedIdentity(env.parent_ticker,env.leg_index,env.leg_text,"unknown","UNKNOWN",
            "CONFLICTING","multiple direct sport signatures","local")
    if len(parent)==1:
        return GuardedIdentity(env.parent_ticker,env.leg_index,env.leg_text,"sports",parent[0],
            "RESOLVED_PARENT","single bounded parent sport signature","parent")
    if len(parent)>1:
        return GuardedIdentity(env.parent_ticker,env.leg_index,env.leg_text,"unknown","UNKNOWN",
            "CONFLICTING","multiple parent sport signatures","parent")
    if len(sibling)==1:
        return GuardedIdentity(env.parent_ticker,env.leg_index,env.leg_text,"sports","UNKNOWN",
            "SIBLING_ADVISORY_ONLY","sibling context cannot classify this leg","sibling")
    if len(sibling)>1:
        return GuardedIdentity(env.parent_ticker,env.leg_index,env.leg_text,"unknown","UNKNOWN",
            "CONFLICTING","mixed sibling identities","sibling")
    return GuardedIdentity(env.parent_ticker,env.leg_index,env.leg_text,"unknown","UNKNOWN",
        "UNRESOLVED","insufficient identity evidence","none")
