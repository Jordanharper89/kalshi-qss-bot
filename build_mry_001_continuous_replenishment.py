from __future__ import annotations

import ast
from pathlib import Path

TARGET=Path("qseries_v2/oracle_execution/solana_atomic_executor/mry_001_continuous_replenishment.py")
TEST=Path("test_mry_001_continuous_replenishment.py")

MODULE=(
    'from __future__ import annotations\nimpor'
    't threading,time\nfrom pathlib import Pat'
    'h\nfrom qseries_v2.oracle_strategy_intell'
    'igence.solana_money.qarb_clean_bot impor'
    't engine\n\nTARGET_WARM=40\nREFRESH_SECONDS'
    '=20.0\n\ndef configure(target=TARGET_WARM)'
    ':\n    target=max(4,int(target))\n    engi'
    'ne.MAX_TOKENS=max(int(getattr(engine,"MA'
    'X_TOKENS",0)),target)\n    engine.DISCOVE'
    'RY_BUDGET=max(int(getattr(engine,"DISCOV'
    'ERY_BUDGET",0)),max(96,target*3))\n    en'
    'gine.CROSSLIST_TTL=min(float(getattr(eng'
    'ine,"CROSSLIST_TTL",20.0)),10.0)\n    ret'
    'urn target\n\ndef snapshot(root):\n    conf'
    'igure()\n    cache=getattr(engine,"_cross'
    '_cache",None)\n    if isinstance(cache,di'
    'ct):\n        cache["at"]=0.0\n    rows=li'
    'st(engine.candidate_universe(Path(root))'
    ' or [])\n    return [{\n        "token":st'
    'r(x.get("token") or ""),\n        "pump_p'
    'ool":str(x.get("pump_pool") or ""),\n    '
    '    "source":str(x.get("source") or "UNK'
    'NOWN"),\n        "age":x.get("age"),\n    '
    '    "meteora_pool":str(x.get("meteora_po'
    'ol") or ""),\n    } for x in rows if x.ge'
    't("token")]\n\nclass ReplenishmentWorker:\n'
    '    def __init__(self,root,interval=REFR'
    'ESH_SECONDS):\n        self.root=Path(roo'
    't);self.interval=max(5.0,float(interval)'
    ')\n        self.lock=threading.Lock();sel'
    'f.rows=[];self.generation=0\n        self'
    '.stop=False;self.thread=None;self.last_e'
    'rror=None\n    def refresh(self):\n       '
    ' rows=snapshot(self.root)\n        with s'
    'elf.lock:\n            old={x["token"] fo'
    'r x in self.rows}\n            new={x["to'
    'ken"] for x in rows}\n            self.ro'
    'ws=rows;self.generation+=1;self.last_err'
    'or=None\n            g=self.generation\n  '
    '      print("[MRIYA_REPLENISH] generatio'
    'n=%d candidates=%d new=%d mriya=%d"%(\n  '
    '          g,len(rows),len(new-old),sum(1'
    ' for x in rows if x["source"]=="MRIYA_HO'
    'T")),flush=True)\n        return rows\n   '
    ' def latest(self):\n        with self.loc'
    'k:return self.generation,[dict(x) for x '
    'in self.rows]\n    def _loop(self):\n     '
    '   while not self.stop:\n            try:'
    'self.refresh()\n            except Except'
    'ion as exc:\n                with self.lo'
    'ck:self.last_error="%s:%s"%(type(exc).__'
    'name__,exc)\n                print("[MRIY'
    'A_REPLENISH_WARN] %s"%self.last_error,fl'
    'ush=True)\n            for _ in range(int'
    '(self.interval*10)):\n                if '
    'self.stop:return\n                time.sl'
    'eep(.1)\n    def start(self):\n        if '
    'self.thread and self.thread.is_alive():r'
    'eturn self\n        self.thread=threading'
    '.Thread(target=self._loop,name="mriya-re'
    'plenishment",daemon=True)\n        self.t'
    'hread.start();return self\n    def close('
    'self):\n        self.stop=True\n        if'
    ' self.thread:self.thread.join(timeout=2)'
    '\n'
)

TEST_SOURCE=(
    'import unittest\nfrom qseries_v2.oracle_e'
    'xecution.solana_atomic_executor import m'
    'ry_001_continuous_replenishment as m\ncla'
    'ss T(unittest.TestCase):\n    def test_co'
    'nfig(self):\n        self.assertGreaterEq'
    'ual(m.configure(40),40)\n        self.ass'
    'ertGreaterEqual(m.engine.MAX_TOKENS,40)\n'
    '        self.assertGreaterEqual(m.engine'
    '.DISCOVERY_BUDGET,96)\n    def test_worke'
    'r_contract(self):\n        w=m.Replenishm'
    'entWorker(".",20)\n        self.assertEqu'
    'al(w.generation,0)\n        g,rows=w.late'
    'st()\n        self.assertEqual(g,0);self.'
    'assertEqual(rows,[])\nif __name__=="__mai'
    'n__":unittest.main(verbosity=2)\n'
)

ast.parse(MODULE)
ast.parse(TEST_SOURCE)
TARGET.parent.mkdir(parents=True,exist_ok=True)
TARGET.write_text(MODULE,encoding="utf-8")
TEST.write_text(TEST_SOURCE,encoding="utf-8")

print("[PASS] MRY-001 installed")
print("[PASS] module: qseries_v2/oracle_execution/solana_atomic_executor/mry_001_continuous_replenishment.py")
print("[PASS] test: test_mry_001_continuous_replenishment.py")
