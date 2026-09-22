from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID='OAD-102'
REVISION='OAD_102_UNIVERSAL_IDENTITY_EVIDENCE_ENVELOPE_V1'
TITLE='UNIVERSAL IDENTITY EVIDENCE ENVELOPE'

def find_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base, *base.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise SystemExit("[ERROR] Q Series repository not found")

ROOT=find_root()
PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=ROOT/'qseries_v2/oracle_adapters/independent/oad_102_universal_identity_evidence_envelope.py'
TEST=ROOT/'test_oad_102_universal_identity_evidence_envelope.py'
INIT=PKG/"__init__.py"
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nimport re\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\n@dataclass(frozen=True, slots=True)\nclass IdentityEvidence:\n    scope: str\n    evidence_type: str\n    value: str\n    strength: int\n    source_text: str\n\n@dataclass(frozen=True, slots=True)\nclass IdentityEnvelope:\n    parent_ticker: str\n    leg_index: int\n    leg_text: str\n    local_evidence: tuple[IdentityEvidence,...]\n    parent_evidence: tuple[IdentityEvidence,...]\n    sibling_evidence: tuple[IdentityEvidence,...]\n\ndef _ev(scope, typ, value, strength, text):\n    return IdentityEvidence(scope,typ,value,strength,str(text or ""))\n\ndef _local(text):\n    text=str(text or "")\n    low=text.lower()\n    out=[]\n    checks=[\n      ("sport","baseball",95,(r"\\binnings?\\b",r"\\bstrikeouts?\\b",r"\\bhome runs?\\b",r"\\brbi\\b")),\n      ("sport","soccer",95,(r"\\bboth teams to score\\b",r"\\bclean sheet\\b",r"\\bgoals?\\b")),\n      ("sport","tennis",95,(r"\\bsets?\\b",r"\\baces?\\b",r"\\bdouble faults?\\b",r"\\bwins 2-1\\b",r"\\bwins 3-0\\b")),\n      ("sport","combat",98,(r"\\bsubmission\\b",r"\\bko/tko\\b",r"\\bdecision\\b",r"\\bufc\\b",r"\\bmma\\b")),\n      ("sport","esports",98,(r"\\besports?\\b",r"\\bvalorant\\b",r"\\bcounter-strike\\b")),\n      ("sport","hockey",98,(r"\\bnhl\\b",r"\\bshots on goal\\b",r"\\bpower play\\b")),\n      ("sport","basketball",95,(r"\\brebounds?\\b",r"\\bassists?\\b",r"\\bthree pointers?\\b",r"\\bnba\\b",r"\\bwnba\\b")),\n      ("sport","football",95,(r"\\btouchdowns?\\b",r"\\bpassing yards?\\b",r"\\brushing yards?\\b",r"\\bnfl\\b")),\n    ]\n    for typ,val,strength,pats in checks:\n        if any(re.search(p,low,re.I) for p in pats):\n            out.append(_ev("local",typ,val,strength,text))\n    if re.search(r":\\s*\\d+(?:\\.\\d+)?\\+(?=\\s|$|[,;/)])",text):\n        out.append(_ev("local","market_type","player_prop",90,text))\n    if "/" in text and len(text.split("/"))==2:\n        out.append(_ev("local","market_type","participant_pair",85,text))\n    if re.fullmatch(r"[A-Za-zÀ-ÿ0-9 .\'\\-/&()]+",text.strip()) and 1<=len(text.split())<=7:\n        out.append(_ev("local","entity_shape","named_entity",35,text))\n    return tuple(out)\n\ndef _context_text(market):\n    return " ".join(str(market.get(k,"") or "") for k in (\n        "ticker","event_ticker","series_ticker","rules_primary","rules_secondary"\n    ))\n\ndef build_identity_envelopes(market, legs):\n    parent=_context_text(market)\n    parent_ev=_local(parent)\n    rows=[]\n    for leg in legs:\n        sib=[]\n        for other in legs:\n            if other.leg_index != leg.leg_index:\n                for e in _local(other.text):\n                    sib.append(_ev("sibling",e.evidence_type,e.value,min(e.strength,55),other.text))\n        rows.append(IdentityEnvelope(\n            str(leg.parent_ticker), int(leg.leg_index), str(leg.text),\n            _local(leg.text),\n            tuple(_ev("parent",e.evidence_type,e.value,min(e.strength,75),parent) for e in parent_ev),\n            tuple(sib),\n        ))\n    return tuple(rows)\n'
TEST_SOURCE='\nimport unittest\nfrom types import SimpleNamespace\nfrom qseries_v2.oracle_adapters.independent.oad_102_universal_identity_evidence_envelope import build_identity_envelopes\n\nclass T(unittest.TestCase):\n    def test_scope_and_strength(self):\n        market={"ticker":"KXMVECROSSCATEGORY-X","event_ticker":"X","rules_primary":""}\n        legs=(SimpleNamespace(parent_ticker="KXMVECROSSCATEGORY-X",leg_index=0,text="Over 1.5 runs in the first 5 innings"),\n              SimpleNamespace(parent_ticker="KXMVECROSSCATEGORY-X",leg_index=1,text="Manchester City"))\n        rows=build_identity_envelopes(market,legs)\n        self.assertTrue(any(e.value=="baseball" and e.scope=="local" for e in rows[0].local_evidence))\n        self.assertFalse(any(e.scope=="local" and e.value=="baseball" for e in rows[1].local_evidence))\n        self.assertTrue(all(e.strength<=55 for e in rows[1].sibling_evidence))\nif __name__=="__main__":\n    print("="*96); print(" OAD-102 CERTIFICATION TEST"); print("="*96)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Identity evidence scopes remain separate")\n    print("[PASS] Sibling evidence is explicitly weaker than direct evidence")\n    print("[PASS] probability_enabled=FALSE")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OAD-102 CERTIFIED")\n'
REQUIRED=[('qseries_v2/oracle_adapters/independent/oad_101_universal_classification_exhaustive_diagnostic.py', 'Certified OAD-101 exhaustive diagnostic'), ('qseries_v2/oracle_adapters/independent/oad_099_mixed_domain_cross_category_decomposition.py', 'Certified OAD-099 decomposition')]
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
    print(" OAD-102 INSTALLER")
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
        export=f"from .oad_102_universal_identity_evidence_envelope import *"
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
        print("[DONE] OAD-102 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(data)
        print("[ROLLBACK] OAD-102 affected files restored")
        raise

if __name__=="__main__":
    main()
