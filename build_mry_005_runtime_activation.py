from __future__ import annotations

import ast
from pathlib import Path

TARGET=Path("qseries_v2/oracle_execution/solana_atomic_executor/mry_005_runtime_activation.py")
TEST=Path("test_mry_005_runtime_activation.py")

MODULE=(
    'from __future__ import annotations\nimpor'
    't time\nfrom . import mry_001_continuous_'
    'replenishment as m1\nfrom . import mry_00'
    '2_warm_inventory as m2\nfrom . import mry'
    '_003_hot_rotation as m3\nfrom . import mr'
    'y_004_adaptive_capacity as m4\n\nROTATE_SE'
    'CONDS=60.0\nACCOUNT_BUDGET=480\n\nasync def'
    ' serve_rotating(rt,root,state,seconds,la'
    'ne):\n    worker=m1.ReplenishmentWorker(r'
    'oot).start()\n    ctl=m4.CapacityControll'
    'er(start=20,minimum=4,maximum=40)\n    cu'
    'rsor=0;started=time.monotonic();last_pos'
    'itive=int(getattr(lane,"positive",0))\n  '
    '  segment=0\n    try:\n        while time.'
    'monotonic()-started<float(seconds):\n    '
    '        segment+=1\n            generatio'
    'n,hints=worker.latest()\n            inv='
    'm2.inventory(state,rt.READY_TOKENS,hints'
    ')\n            selected=m3.select_hot(inv'
    ',ctl.target,ACCOUNT_BUDGET,cursor)\n     '
    '       if not selected:raise RuntimeErro'
    'r("MRIYA_NO_HOT_READY_PAIRS")\n          '
    '  view=m3.hot_view(state,selected)\n     '
    '       queued=[x for x in hints if x.get'
    '("token") not in {r["token"] for r in in'
    'v}]\n            print("[MRIYA_HOT_SET] s'
    'egment=%d target=%d active=%d warm=%d ac'
    'counts=%d generation=%d queued_unhydrate'
    'd=%d"%(\n                segment,ctl.targ'
    'et,len(selected),len(inv),len(view["addr'
    'esses"]),generation,len(queued)),flush=T'
    'rue)\n            age0=len(getattr(lane,"'
    'event_start_ms",[]) or [])\n            s'
    'can0=len(getattr(lane,"scan_ms",[]) or ['
    '])\n            left=float(seconds)-(time'
    '.monotonic()-started)\n            result'
    '=await rt.serve_canonical(view,min(ROTAT'
    'E_SECONDS,max(.1,left)),lane)\n          '
    '  positives=int(getattr(lane,"positive",'
    '0))\n            idle=(positives==last_po'
    'sitive)\n            last_positive=positi'
    'ves\n            ages=list(getattr(lane,"'
    'event_start_ms",[]) or [])[age0:]\n      '
    '      scans=list(getattr(lane,"scan_ms",'
    '[]) or [])[scan0:]\n            metrics={'
    '\n                "rate_limits":int(resul'
    't.get("rate_limit_disconnects") or 0),\n '
    '               "reconnects":int(result.g'
    'et("reconnects") or 0),\n                '
    '"p95_event_age_ms":m4.percentile(ages,.9'
    '5),\n                "p95_pricing_ms":m4.'
    'percentile(scans,.95),\n            }\n   '
    '         old=ctl.target;ctl.observe(metr'
    'ics)\n            if idle:cursor=(cursor+'
    'max(1,len(selected)//2))%max(1,len(inv))'
    '\n            print("[MRIYA_ROTATE] idle='
    '%s old_target=%d new_target=%d cursor=%d'
    ' p95_age_ms=%.3f p95_pricing_ms=%.3f rat'
    'e_limits=%d reconnects=%d"%(\n           '
    '     idle,old,ctl.target,cursor,metrics['
    '"p95_event_age_ms"],metrics["p95_pricing'
    '_ms"],metrics["rate_limits"],metrics["re'
    'connects"]),flush=True)\n    finally:\n   '
    '     worker.close()\n    return {"segment'
    's":segment,"positive":int(getattr(lane,"'
    'positive",0))}\n'
)

TEST_SOURCE=(
    'import ast,unittest\nfrom pathlib import '
    'Path\nPKG=Path("qseries_v2/oracle_executi'
    'on/solana_atomic_executor")\nRT=PKG/"runt'
    'ime.py"\nclass T(unittest.TestCase):\n    '
    '@classmethod\n    def setUpClass(cls):\n  '
    '      cls.src=RT.read_text(encoding="utf'
    '-8");cls.tree=ast.parse(cls.src)\n    def'
    ' test_imports(self):\n        self.assert'
    'In("mry_005_runtime_activation",self.src'
    ')\n        self.assertIn("mry_002_warm_in'
    'ventory",self.src)\n    def test_warm_40_'
    'before_prepare(self):\n        run=next(n'
    ' for n in self.tree.body if isinstance(n'
    ',ast.FunctionDef) and n.name=="run")\n   '
    '     s=ast.get_source_segment(self.src,r'
    'un) or ""\n        self.assertIn("configu'
    're_hydration(40)",s)\n        self.assert'
    'Less(s.index("configure_hydration(40)"),'
    's.index("q25.prepare_once"))\n    def tes'
    't_rotating_serve(self):\n        self.ass'
    'ertIn("mry5.serve_rotating(",self.src)\n '
    '   def test_money_path_preserved(self):\n'
    '        for x in ("_live_010_certify_or_'
    'send","CANARY_TRADE_LAMPORTS=10_000_000"'
    ',\'"skipPreflight":False\',\'"maxRetries":0'
    "'):\n            self.assertIn(x,self.src"
    ')\nif __name__=="__main__":unittest.main('
    'verbosity=2)\n'
)

ast.parse(MODULE)
ast.parse(TEST_SOURCE)
TARGET.parent.mkdir(parents=True,exist_ok=True)
TARGET.write_text(MODULE,encoding="utf-8")
TEST.write_text(TEST_SOURCE,encoding="utf-8")

RT=Path(
    "qseries_v2/oracle_execution/"
    "solana_atomic_executor/runtime.py"
)

src=RT.read_text(
    encoding="utf-8"
)

ast.parse(src)

if (
    "mry_005_runtime_activation as mry5"
    not in src
):
    anchor=(
        "from qseries_v2.oracle_execution import (\n"
        "    oracle_025_single_hydration_exact_live_reuse as q25\n"
        ")\n"
    )

    if anchor not in src:
        raise RuntimeError(
            "MRY005_IMPORT_ANCHOR_MISSING"
        )

    extra=(
        anchor
        +"\n"
        +"from qseries_v2.oracle_execution.solana_atomic_executor "
        +"import mry_001_continuous_replenishment as mry1\n"
        +"from qseries_v2.oracle_execution.solana_atomic_executor "
        +"import mry_002_warm_inventory as mry2\n"
        +"from qseries_v2.oracle_execution.solana_atomic_executor "
        +"import mry_005_runtime_activation as mry5\n"
    )

    src=src.replace(
        anchor,
        extra,
        1,
    )

run_start="    root=Path.cwd()\n"

if (
    "mry2.configure_hydration(40)"
    not in src
):
    if run_start not in src:
        raise RuntimeError(
            "MRY005_RUN_ROOT_ANCHOR_MISSING"
        )

    src=src.replace(
        run_start,
        run_start
        +"\n"
        +"    mry1.configure(40)\n"
        +"    mry2.configure_hydration(40)\n",
        1,
    )

old=(
    "            serve_canonical(\n"
    "                state,\n"
    "                float(seconds),\n"
    "                lane,\n"
    "            )\n"
)

new=(
    "            mry5.serve_rotating(\n"
    "                __import__(__name__,fromlist=['*']),\n"
    "                root,\n"
    "                state,\n"
    "                float(seconds),\n"
    "                lane,\n"
    "            )\n"
)

if (
    "mry5.serve_rotating("
    not in src
):
    if old not in src:
        raise RuntimeError(
            "MRY005_SERVE_ANCHOR_MISSING"
        )

    src=src.replace(
        old,
        new,
        1,
    )

ast.parse(src)
RT.write_text(src,encoding="utf-8")

print("[PASS] MRY-005 installed")
print("[PASS] module: qseries_v2/oracle_execution/solana_atomic_executor/mry_005_runtime_activation.py")
print("[PASS] test: test_mry_005_runtime_activation.py")
