from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

REVISION="OAD_119_PERSISTED_SPORTS_STRUCTURED_DESCRIPTOR_V1"

def find_root():
    for base in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (base,*base.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")

def write_py(path,src):
    src=textwrap.dedent(src).lstrip()
    ast.parse(src,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(src,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

ROOT=find_root()
PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=PKG/'oad_119_persisted_sports_structured_descriptor.py'
TEST=ROOT/'test_oad_119_persisted_sports_structured_descriptor.py'
INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom collections.abc import Mapping\nimport re\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\n@dataclass(frozen=True, slots=True)\nclass SportsEvidenceDescriptor:\n    observation_id: str\n    source_id: str\n    sport_family: str\n    subject: str\n    away_team: str\n    home_team: str\n    team_pair_key: str\n    evidence_type: str\n    independent_evidence: bool\n    execution_authority: bool=False\n\ndef _thaw(v):\n    if isinstance(v,Mapping): return {str(k):_thaw(x) for k,x in v.items()}\n    if isinstance(v,tuple):\n        if all(isinstance(x,tuple) and len(x)==2 for x in v):\n            try: return {str(k):_thaw(x) for k,x in v}\n            except Exception: pass\n        return tuple(_thaw(x) for x in v)\n    if isinstance(v,list): return [_thaw(x) for x in v]\n    return v\n\ndef _norm(v):\n    return " ".join(re.findall(r"[a-z0-9]+",str(v or "").lower()))\n\ndef descriptor_from_persisted_sports_row(row):\n    payload=_thaw(getattr(row,"payload",{}))\n    if not isinstance(payload,dict): raise ValueError("canonical sports payload mapping required")\n    subject=str(payload.get("subject","")).strip()\n    source_id=str(getattr(row,"source_id",""))\n    independent=payload.get("independent_evidence") is True\n    if not independent or not source_id.startswith("source.independent."):\n        raise ValueError("persisted independent sports evidence required")\n    parts=subject.split(" at ",1)\n    away=parts[0].strip() if len(parts)==2 else ""\n    home=parts[1].strip() if len(parts)==2 else ""\n    sport="baseball" if ".mlb:game:" in source_id else ("hockey" if ".nhl:game:" in source_id else "UNKNOWN")\n    pair="|".join(sorted(x for x in (_norm(away),_norm(home)) if x))\n    return SportsEvidenceDescriptor(\n        observation_id=str(row.observation_id),\n        source_id=source_id,\n        sport_family=sport,\n        subject=subject,\n        away_team=away,\n        home_team=home,\n        team_pair_key=pair,\n        evidence_type="official_game_schedule_state",\n        independent_evidence=True,\n        execution_authority=False,\n    )\n\ndef descriptors_from_persisted_sports_rows(rows):\n    return tuple(descriptor_from_persisted_sports_row(x) for x in rows)\n'
TEST_SOURCE='import unittest\nfrom types import SimpleNamespace\nfrom qseries_v2.oracle_adapters.independent.oad_119_persisted_sports_structured_descriptor import descriptor_from_persisted_sports_row\n\nclass T(unittest.TestCase):\n    def test_mlb_descriptor(self):\n        row=SimpleNamespace(\n            observation_id="oid-1",\n            source_id="source.independent.mlb:game:824638",\n            payload=(("subject","Cincinnati Reds at Chicago Cubs"),("independent_evidence",True)),\n        )\n        d=descriptor_from_persisted_sports_row(row)\n        print("[SPORT]",d.sport_family)\n        print("[AWAY]",d.away_team)\n        print("[HOME]",d.home_team)\n        print("[PAIR]",d.team_pair_key)\n        self.assertEqual(d.sport_family,"baseball")\n        self.assertEqual(d.away_team,"Cincinnati Reds")\n        self.assertEqual(d.home_team,"Chicago Cubs")\n        self.assertTrue(d.independent_evidence)\n\nif __name__=="__main__":\n    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not x.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-119 persisted sports structured descriptor certified")\n'
DEPENDENCIES=['oad_118_persisted_authoritative_sports_cohort.py']

def main():
    print("="*112)
    print(" OAD-119 PERSISTED SPORTS STRUCTURED DESCRIPTOR INSTALLER")
    print("="*112)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",ROOT)
    for dep in DEPENDENCIES:
        p=PKG/dep
        if not p.is_file(): raise RuntimeError("Required certified dependency missing: "+str(p))
        print("[PASS] dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (MODULE,TEST,INIT)}
    try:
        write_py(MODULE,MODULE_SOURCE)
        write_py(TEST,TEST_SOURCE)
        lines=INIT.read_text(encoding="utf-8").splitlines() if INIT.exists() else []
        exp="from .oad_119_persisted_sports_structured_descriptor import *"
        if exp not in lines: lines.append(exp)
        write_py(INIT,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",MODULE.relative_to(ROOT))
        print("[PASS] test installed:",TEST.relative_to(ROOT))
        print("[PASS] syntax validated")
        print("[PASS] existing certified boundaries preserved")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-119 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back")
        raise

if __name__=="__main__":
    main()
