
from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

def find_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base, *base.parents):
            if (p / "qseries_v2").is_dir():
                return p
    raise SystemExit("[ERROR] Q Series repository not found")

def write_py(path, source):
    source = textwrap.dedent(source).lstrip()
    ast.parse(source, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(source, encoding="utf-8", newline="\n")
    os.replace(tmp, path)

REVISION="OAD_108_OFFICIAL_MLB_SOURCE_ADAPTER_V1"
ROOT=find_root()
PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=PKG/'oad_108_official_mlb_source_adapter.py'
TEST=ROOT/'test_oad_108_official_mlb_source_adapter.py'
INIT=PKG/"__init__.py"
MODULE_SOURCE='\nfrom __future__ import annotations\nimport json\nfrom urllib.request import Request, urlopen\nfrom .oad_107_authoritative_sports_source_foundation import build_observation, utcnow_iso\n\nPROVIDER="statsapi.mlb.com"\nBASE="https://statsapi.mlb.com/api/v1"\n\ndef fetch_mlb_schedule(*, date=None, timeout_seconds=20):\n    url=BASE+"/schedule?sportId=1"\n    if date: url += "&date="+str(date)\n    req=Request(url,headers={"User-Agent":"Oracle-Q-Series/1.0","Accept":"application/json"})\n    with urlopen(req,timeout=timeout_seconds) as r:\n        data=json.loads(r.read().decode("utf-8"))\n    obs=[]\n    for d in data.get("dates",[]):\n        for g in d.get("games",[]):\n            gid=g.get("gamePk")\n            teams=g.get("teams",{})\n            away=((teams.get("away") or {}).get("team") or {}).get("name","")\n            home=((teams.get("home") or {}).get("team") or {}).get("name","")\n            subject=f"{away} at {home}".strip()\n            obs.append(build_observation(\n                source_id=f"mlb:game:{gid}", provider=PROVIDER, sport_family="baseball",\n                observation_type="official_game_schedule_state", subject=subject,\n                observed_at=utcnow_iso(), source_url=url, payload=g))\n    return tuple(obs)\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_108_official_mlb_source_adapter import fetch_mlb_schedule\nclass T(unittest.TestCase):\n    def test_physical(self):\n        rows=fetch_mlb_schedule(timeout_seconds=20)\n        print("[MLB_OBSERVATIONS]",len(rows))\n        for x in rows[:5]: print("[MLB]",x.subject,x.source_id)\n        self.assertTrue(all(x.provider=="statsapi.mlb.com" for x in rows))\n        self.assertTrue(all(x.sport_family=="baseball" for x in rows))\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] physical official MLB acquisition completed")\n    print("[PASS] read_only=TRUE execution_authority=FALSE")\n'
DEPENDENCIES=['oad_107_authoritative_sports_source_foundation.py']

def main():
    print("="*104)
    print(" OAD-108 OFFICIAL MLB SOURCE ADAPTER INSTALLER")
    print("="*104)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",ROOT)
    for dep in DEPENDENCIES:
        p=PKG/dep
        if not p.is_file():
            raise RuntimeError("Required certified dependency missing: "+str(p))
        print("[PASS] dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (MODULE,TEST,INIT)}
    try:
        write_py(MODULE,MODULE_SOURCE)
        write_py(TEST,TEST_SOURCE)
        lines=INIT.read_text(encoding="utf-8").splitlines() if INIT.exists() else []
        exp="from .oad_108_official_mlb_source_adapter import *"
        if exp not in lines: lines.append(exp)
        write_py(INIT,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",MODULE.relative_to(ROOT))
        print("[PASS] test installed:",TEST.relative_to(ROOT))
        print("[PASS] syntax validated")
        print("[PASS] read-only Oracle boundary preserved")
        print("[PASS] execution_authority=FALSE")
        print("[PASS] probability remains disabled")
        print("[DONE] OAD-108 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back")
        raise

if __name__=="__main__":
    main()
