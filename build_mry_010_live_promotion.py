from pathlib import Path
import ast

TARGET=Path("qseries_v2/oracle_execution/solana_atomic_executor/mry_010_live_promotion.py")
TEST=Path("test_mry_010_live_promotion.py")

MODULE='from __future__ import annotations\nfrom pathlib import Path\n\nfrom . import mry_007_candidate_hydrator as h\nfrom . import mry_008_execution_readiness as r\nfrom . import mry_009_atomic_warm_admission as a\n\nMAX_ADMISSIONS_PER_ROTATION=2\n\ndef queued(hints,state):\n    have={\n        str(p.token)\n        for p in state.get("pairs",[])\n    }\n\n    return [\n        dict(x)\n        for x in (hints or [])\n        if x.get("token")\n        and str(x["token"]) not in have\n    ]\n\ndef admit_batch(\n    rt,\n    root,\n    state,\n    hints,\n    limit=MAX_ADMISSIONS_PER_ROTATION,\n):\n    rows=queued(\n        hints,\n        state,\n    )\n\n    admitted=0\n    held=0\n\n    for row in rows[\n        :max(0,int(limit))\n    ]:\n        token=str(\n            row["token"]\n        )\n\n        try:\n            pair=h.hydrate_candidate(\n                Path(root),\n                row,\n            )\n\n            ready=r.install_forward(\n                rt,\n                pair,\n            )\n\n            a.admit(\n                rt,\n                state,\n                pair,\n                ready,\n            )\n\n            admitted+=1\n\n        except Exception as exc:\n            held+=1\n\n            print(\n                "[MRIYA_ADMISSION_HOLD] "\n                "token=%s %s:%s"\n                %(\n                    token[:10],\n                    type(exc).__name__,\n                    str(exc)[:220],\n                ),\n                flush=True,\n            )\n\n    print(\n        "[MRIYA_ADMISSION_BATCH] "\n        "queued=%d attempted=%d "\n        "admitted=%d held=%d warm=%d"\n        %(\n            len(rows),\n            min(\n                len(rows),\n                max(0,int(limit)),\n            ),\n            admitted,\n            held,\n            len(rt.READY_TOKENS),\n        ),\n        flush=True,\n    )\n\n    return {\n        "queued":len(rows),\n        "admitted":admitted,\n        "held":held,\n    }\n'
TEST_SOURCE='import ast\nimport unittest\nfrom pathlib import Path\n\nPKG=Path(\n    "qseries_v2/oracle_execution/"\n    "solana_atomic_executor"\n)\n\nclass T(unittest.TestCase):\n    def test_module(self):\n        from qseries_v2.oracle_execution.solana_atomic_executor import mry_010_live_promotion as m\n\n        self.assertEqual(\n            m.MAX_ADMISSIONS_PER_ROTATION,\n            2,\n        )\n\n        self.assertTrue(\n            callable(m.admit_batch)\n        )\n\n    def test_activation(self):\n        src=(\n            PKG/\n            "mry_005_runtime_activation.py"\n        ).read_text(\n            encoding="utf-8"\n        )\n\n        ast.parse(src)\n\n        self.assertIn(\n            "mry_010_live_promotion",\n            src,\n        )\n\n        self.assertIn(\n            "m10.admit_batch(",\n            src,\n        )\n\nif __name__=="__main__":\n    unittest.main(verbosity=2)\n'

ast.parse(MODULE)
ast.parse(TEST_SOURCE)

TARGET.parent.mkdir(
    parents=True,
    exist_ok=True,
)

TARGET.write_text(
    MODULE,
    encoding="utf-8",
)

TEST.write_text(
    TEST_SOURCE,
    encoding="utf-8",
)

M5=Path(
    "qseries_v2/oracle_execution/solana_atomic_executor/mry_005_runtime_activation.py"
)

src=M5.read_text(
    encoding="utf-8"
)

ast.parse(src)

if (
    "mry_010_live_promotion as m10"
    not in src
):
    anchor=(
        "from . import "
        "mry_004_adaptive_capacity as m4\n"
    )

    if anchor not in src:
        raise RuntimeError(
            "MRY010_IMPORT_ANCHOR_MISSING"
        )

    src=src.replace(
        anchor,
        anchor
        +"from . import "
        +"mry_010_live_promotion as m10\n",
        1,
    )

call=(
    "            generation,hints="
    "worker.latest()\n"
)

if "m10.admit_batch(" not in src:
    if call not in src:
        raise RuntimeError(
            "MRY010_ROTATION_ANCHOR_MISSING"
        )

    src=src.replace(
        call,
        call
        +"            "
        +"m10.admit_batch("
        +"rt,root,state,hints)\n",
        1,
    )

ast.parse(src)

M5.write_text(
    src,
    encoding="utf-8",
)

print("[PASS] MRY-010 installed")
print("[PASS] module:",TARGET)
print("[PASS] test:",TEST)
print("[PASS] runtime activation: mry_005")
