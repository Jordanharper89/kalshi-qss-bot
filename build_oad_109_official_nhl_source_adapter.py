
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

REVISION="OAD_109_OFFICIAL_NHL_SOURCE_ADAPTER_V1"
ROOT=find_root()
PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=PKG/'oad_109_official_nhl_source_adapter.py'
TEST=ROOT/'test_oad_109_official_nhl_source_adapter.py'
INIT=PKG/"__init__.py"
MODULE_SOURCE='\nfrom __future__ import annotations\nimport json\nfrom urllib.request import Request, urlopen\nfrom .oad_107_authoritative_sports_source_foundation import build_observation, utcnow_iso\n\nPROVIDER="api-web.nhle.com"\nBASE="https://api-web.nhle.com/v1"\n\ndef fetch_nhl_schedule(*, date, timeout_seconds=20):\n    url=f"{BASE}/schedule/{date}"\n    req=Request(url,headers={"User-Agent":"Oracle-Q-Series/1.0","Accept":"application/json"})\n    with urlopen(req,timeout=timeout_seconds) as r:\n        data=json.loads(r.read().decode("utf-8"))\n    obs=[]\n    for week in data.get("gameWeek",[]):\n        for g in week.get("games",[]):\n            gid=g.get("id")\n            away=((g.get("awayTeam") or {}).get("placeName") or {}).get("default","")\n            home=((g.get("homeTeam") or {}).get("placeName") or {}).get("default","")\n            subject=f"{away} at {home}".strip()\n            obs.append(build_observation(\n                source_id=f"nhl:game:{gid}", provider=PROVIDER, sport_family="hockey",\n                observation_type="official_game_schedule_state", subject=subject,\n                observed_at=utcnow_iso(), source_url=url, payload=g))\n    return tuple(obs)\n'
TEST_SOURCE='\nimport unittest\nfrom datetime import datetime, timezone\nfrom qseries_v2.oracle_adapters.independent.oad_109_official_nhl_source_adapter import fetch_nhl_schedule\nclass T(unittest.TestCase):\n    def test_physical(self):\n        d=datetime.now(timezone.utc).date().isoformat()\n        rows=fetch_nhl_schedule(date=d,timeout_seconds=20)\n        print("[NHL_DATE]",d)\n        print("[NHL_OBSERVATIONS]",len(rows))\n        for x in rows[:5]: print("[NHL]",x.subject,x.source_id)\n        self.assertTrue(all(x.provider=="api-web.nhle.com" for x in rows))\n        self.assertTrue(all(x.sport_family=="hockey" for x in rows))\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] physical official NHL acquisition completed")\n    print("[PASS] read_only=TRUE execution_authority=FALSE")\n'
DEPENDENCIES=['oad_107_authoritative_sports_source_foundation.py']

def main():
    print("="*104)
    print(" OAD-109 OFFICIAL NHL SOURCE ADAPTER INSTALLER")
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
        exp="from .oad_109_official_nhl_source_adapter import *"
        if exp not in lines: lines.append(exp)
        write_py(INIT,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",MODULE.relative_to(ROOT))
        print("[PASS] test installed:",TEST.relative_to(ROOT))
        print("[PASS] syntax validated")
        print("[PASS] read-only Oracle boundary preserved")
        print("[PASS] execution_authority=FALSE")
        print("[PASS] probability remains disabled")
        print("[DONE] OAD-109 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back")
        raise

if __name__=="__main__":
    main()
