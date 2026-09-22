from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID='OAD-103'
REVISION='OAD_103_GUARDED_CONTEXTUAL_IDENTITY_RESOLVER_V1'
TITLE='GUARDED CONTEXTUAL IDENTITY RESOLVER'

def find_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base, *base.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise SystemExit("[ERROR] Q Series repository not found")

ROOT=find_root()
PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=ROOT/'qseries_v2/oracle_adapters/independent/oad_103_guarded_contextual_identity_resolver.py'
TEST=ROOT/'test_oad_103_guarded_contextual_identity_resolver.py'
INIT=PKG/"__init__.py"
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom qseries_v2.oracle_adapters.independent.oad_102_universal_identity_evidence_envelope import IdentityEnvelope\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\n@dataclass(frozen=True, slots=True)\nclass GuardedIdentity:\n    parent_ticker: str\n    leg_index: int\n    leg_text: str\n    domain: str\n    sport: str\n    state: str\n    confidence_basis: str\n    evidence_scope: str\n\ndef _sports_values(evs):\n    return sorted({e.value for e in evs if e.evidence_type=="sport"})\n\ndef resolve_guarded_identity(env: IdentityEnvelope):\n    local=_sports_values(env.local_evidence)\n    parent=_sports_values(env.parent_evidence)\n    sibling=_sports_values(env.sibling_evidence)\n\n    if len(local)==1:\n        return GuardedIdentity(env.parent_ticker,env.leg_index,env.leg_text,"sports",local[0],\n            "RESOLVED_DIRECT","direct structural sport evidence","local")\n    if len(local)>1:\n        return GuardedIdentity(env.parent_ticker,env.leg_index,env.leg_text,"unknown","UNKNOWN",\n            "CONFLICTING","multiple direct sport signatures","local")\n    if len(parent)==1:\n        return GuardedIdentity(env.parent_ticker,env.leg_index,env.leg_text,"sports",parent[0],\n            "RESOLVED_PARENT","single bounded parent sport signature","parent")\n    if len(parent)>1:\n        return GuardedIdentity(env.parent_ticker,env.leg_index,env.leg_text,"unknown","UNKNOWN",\n            "CONFLICTING","multiple parent sport signatures","parent")\n    if len(sibling)==1:\n        return GuardedIdentity(env.parent_ticker,env.leg_index,env.leg_text,"sports","UNKNOWN",\n            "SIBLING_ADVISORY_ONLY","sibling context cannot classify this leg","sibling")\n    if len(sibling)>1:\n        return GuardedIdentity(env.parent_ticker,env.leg_index,env.leg_text,"unknown","UNKNOWN",\n            "CONFLICTING","mixed sibling identities","sibling")\n    return GuardedIdentity(env.parent_ticker,env.leg_index,env.leg_text,"unknown","UNKNOWN",\n        "UNRESOLVED","insufficient identity evidence","none")\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_102_universal_identity_evidence_envelope import IdentityEvidence, IdentityEnvelope\nfrom qseries_v2.oracle_adapters.independent.oad_103_guarded_contextual_identity_resolver import resolve_guarded_identity\nclass T(unittest.TestCase):\n    def test_direct(self):\n        e=IdentityEnvelope("P",0,"x",(IdentityEvidence("local","sport","baseball",95,"x"),),(),())\n        r=resolve_guarded_identity(e); self.assertEqual((r.sport,r.state),("baseball","RESOLVED_DIRECT"))\n    def test_sibling_not_promoted(self):\n        e=IdentityEnvelope("P",0,"x",(),(),(IdentityEvidence("sibling","sport","soccer",55,"y"),))\n        r=resolve_guarded_identity(e); self.assertEqual((r.sport,r.state),("UNKNOWN","SIBLING_ADVISORY_ONLY"))\nif __name__=="__main__":\n    print("="*96); print(" OAD-103 CERTIFICATION TEST"); print("="*96)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Direct and parent evidence may resolve only under guarded rules")\n    print("[PASS] Sibling-only evidence cannot promote identity")\n    print("[DONE] OAD-103 CERTIFIED")\n'
REQUIRED=[('qseries_v2/oracle_adapters/independent/oad_102_universal_identity_evidence_envelope.py', 'Certified OAD-102 identity evidence envelope')]
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
    print(" OAD-103 INSTALLER")
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
        export=f"from .oad_103_guarded_contextual_identity_resolver import *"
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
        print("[DONE] OAD-103 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(data)
        print("[ROLLBACK] OAD-103 affected files restored")
        raise

if __name__=="__main__":
    main()
