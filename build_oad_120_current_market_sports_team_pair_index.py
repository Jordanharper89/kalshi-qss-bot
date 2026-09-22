from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

REVISION="OAD_120_CURRENT_MARKET_SPORTS_TEAM_PAIR_INDEX_V1"

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
MODULE=PKG/'oad_120_current_market_sports_team_pair_index.py'
TEST=ROOT/'test_oad_120_current_market_sports_team_pair_index.py'
INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nimport re\n\nfrom .oad_069_current_open_kalshi_market_index import fetch_current_open_kalshi_market_index\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\ndef _norm(v):\n    return " ".join(re.findall(r"[a-z0-9]+",str(v or "").lower()))\n\ndef _market_text(m):\n    return _norm(" ".join(str(m.get(k,"") or "") for k in (\n        "ticker","event_ticker","title","subtitle","yes_sub_title","no_sub_title","rules_primary"\n    )))\n\n@dataclass(frozen=True, slots=True)\nclass SportsMarketCandidate:\n    observation_id: str\n    market_id: str\n    away_team: str\n    home_team: str\n    matched_teams: tuple\n    association_strength: str\n    candidate_only: bool=True\n\ndef candidate_markets_for_sports_descriptor(descriptor, markets, max_candidates=25):\n    away=_norm(descriptor.away_team)\n    home=_norm(descriptor.home_team)\n    if not away or not home:\n        return ()\n    out=[]\n    for m in tuple(markets):\n        ticker=str(m.get("ticker","")).strip()\n        if not ticker: continue\n        text=_market_text(m)\n        hits=tuple(x for x in (away,home) if x and x in text)\n        if len(hits)==2:\n            out.append(SportsMarketCandidate(\n                observation_id=descriptor.observation_id,\n                market_id=ticker,\n                away_team=descriptor.away_team,\n                home_team=descriptor.home_team,\n                matched_teams=hits,\n                association_strength="EXACT_TWO_TEAM_PAIR",\n                candidate_only=True,\n            ))\n    return tuple(sorted(out,key=lambda x:x.market_id)[:max_candidates])\n\ndef fetch_current_market_sports_candidates(descriptors, limit=1000, timeout_seconds=20):\n    markets,_=fetch_current_open_kalshi_market_index(limit=limit,timeout_seconds=timeout_seconds)\n    groups=tuple((d,candidate_markets_for_sports_descriptor(d,markets)) for d in tuple(descriptors))\n    return tuple(markets),groups\n'
TEST_SOURCE='import unittest\nfrom types import SimpleNamespace\nfrom qseries_v2.oracle_adapters.independent.oad_120_current_market_sports_team_pair_index import candidate_markets_for_sports_descriptor\n\nclass T(unittest.TestCase):\n    def test_exact_two_team_pair_only(self):\n        d=SimpleNamespace(observation_id="o1",away_team="Houston Astros",home_team="New York Mets")\n        markets=(\n            {"ticker":"GOOD","title":"Houston Astros at New York Mets"},\n            {"ticker":"ONE","title":"Will the Houston Astros win?"},\n            {"ticker":"NOISE","title":"New York weather"},\n        )\n        r=candidate_markets_for_sports_descriptor(d,markets)\n        print("[CANDIDATES]",[(x.market_id,x.association_strength) for x in r])\n        self.assertEqual(tuple(x.market_id for x in r),("GOOD",))\n        self.assertTrue(all(x.candidate_only for x in r))\n\nif __name__=="__main__":\n    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not x.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-120 exact two-team market candidate index certified")\n'
DEPENDENCIES=['oad_069_current_open_kalshi_market_index.py', 'oad_119_persisted_sports_structured_descriptor.py']

def main():
    print("="*112)
    print(" OAD-120 CURRENT MARKET SPORTS TEAM-PAIR INDEX INSTALLER")
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
        exp="from .oad_120_current_market_sports_team_pair_index import *"
        if exp not in lines: lines.append(exp)
        write_py(INIT,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",MODULE.relative_to(ROOT))
        print("[PASS] test installed:",TEST.relative_to(ROOT))
        print("[PASS] syntax validated")
        print("[PASS] existing certified boundaries preserved")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-120 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back")
        raise

if __name__=="__main__":
    main()
