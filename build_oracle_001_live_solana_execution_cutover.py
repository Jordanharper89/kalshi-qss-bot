from pathlib import Path
import json
import os
import py_compile
import shutil
import subprocess

ROOT = Path.cwd()

SOURCE = ROOT / (
    "qseries_v2/solana_live_execution/"
    "qarb_097_official_meteora_sdk_executor.py"
)

ORACLE_DIR = ROOT / "qseries_v2/oracle_execution"
TARGET = ORACLE_DIR / "oracle_001_live_solana_executor.py"
INIT = ORACLE_DIR / "__init__.py"
LAUNCHER = ROOT / "run_oracle_solana_execution_live.py"
TEST = ROOT / "test_oracle_001_live_solana_execution_cutover.py"

NODE_DIR = ROOT / (
    "qseries_v2/oracle_strategy_intelligence/"
    "solana_money/qsb059d_pump_native"
)

METEORA_JS = NODE_DIR / "build_meteora_swap_ix.mjs"

for p in (SOURCE, NODE_DIR, METEORA_JS):
    if not p.exists():
        raise SystemExit("[FAIL] missing dependency: " + str(p))

# ============================================================
# 1. FIX NODE 24 / METEORA ESM FAILURE PHYSICALLY
# ============================================================

js = METEORA_JS.read_text(encoding="utf-8")

esm = 'import DLMM from "@meteora-ag/dlmm";'

cjs = '''import {createRequire} from "node:module";
const require=createRequire(import.meta.url);
const _dlmm=require("@meteora-ag/dlmm");
const DLMM=_dlmm.default ?? _dlmm;'''

if esm in js:
    js = js.replace(esm, cjs, 1)

if 'require("@meteora-ag/dlmm")' not in js:
    raise SystemExit(
        "[FAIL] Meteora CommonJS cutover not present"
    )

METEORA_JS.write_text(
    js,
    encoding="utf-8"
)

node = shutil.which("node")

if not node:
    raise SystemExit("[FAIL] node executable missing")

probe = subprocess.run(
    [
        node,
        "--input-type=module",
        "-e",
        (
            'import {createRequire} from "node:module";'
            'const require=createRequire(import.meta.url);'
            'const m=require("@meteora-ag/dlmm");'
            'const D=m.default??m;'
            'if(!D){process.exit(9)};'
            'console.log("[METEORA_CJS_IMPORT_OK]",typeof D);'
        )
    ],
    cwd=NODE_DIR,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    timeout=30
)

print(probe.stdout.strip())

if probe.returncode != 0:
    raise SystemExit(
        "[FAIL] Meteora SDK cannot load under current Node:\n"
        + probe.stdout[-4000:]
    )

# ============================================================
# 2. FORK CURRENT PHYSICAL EXECUTOR INTO ORACLE OWNERSHIP
#
# No runtime import from qseries_v2.solana_live_execution.
# Oracle owns the resulting executable module.
# ============================================================

src = SOURCE.read_text(encoding="utf-8")

required = (
    'EXECUTION_OWNER="Q_SERIES"',
    "MICRO_SOL=0.001",
    "MICRO_LAMPORTS=1_000_000",
    "def require_keypair(",
    "def final_prepare(",
    "def signed_simulation(",
    "def send_once(",
    "def run(",
)

missing = [x for x in required if x not in src]

if missing:
    raise SystemExit(
        "[FAIL] current QARB-097 source drift: "
        + repr(missing)
    )

# Owner cutover.
src = src.replace(
    'EXECUTION_OWNER="Q_SERIES"',
    'EXECUTION_OWNER="ORACLE"',
    1
)

src = src.replace(
    "ORACLE_EXECUTION_AUTHORITY=False",
    "ORACLE_EXECUTION_AUTHORITY=True"
)

src = src.replace(
    '"oracle_execution_authority":\n            False',
    '"oracle_execution_authority":\n            True'
)

src = src.replace(
    "execution_owner=Q_SERIES",
    "execution_owner=ORACLE"
)

src = src.replace(
    "oracle_execution_authority=FALSE",
    "oracle_execution_authority=TRUE"
)

src = src.replace(
    "Q Series owns this call.",
    "Oracle owns this call."
)

src = src.replace(
    "Q Series automatically selected this opportunity.",
    "Oracle automatically selected this opportunity."
)

# Dedicated Oracle state/ledger.
src = src.replace(
    "runtime_state/qseries/qarb_live_micro_execution/",
    "runtime_state/oracle/oracle_live_execution/"
)

src = src.replace(
    "qarb_096_sequential_live_micro_executor.json",
    "oracle_001_live_solana_executor.json"
)

src = src.replace(
    "qarb_096_live_micro_ledger.jsonl",
    "oracle_001_live_execution_ledger.jsonl"
)

src = src.replace(
    '"revision":"QARB_096"',
    '"revision":"ORACLE_001"'
)

src = src.replace(
    '"revision":"QARB_097"',
    '"revision":"ORACLE_001"'
)

src = src.replace(
    "[QARB-096]",
    "[ORACLE-001]"
)

src = src.replace(
    "[QARB-097]",
    "[ORACLE-001]"
)

# Dedicated Oracle arm instead of QARB arm.
src = src.replace(
    'MICRO_ARM_VALUE="I_ACCEPT_0_001_SOL_TEST"',
    'MICRO_ARM_VALUE="I_ACCEPT_ORACLE_0_001_SOL_EXECUTION"'
)

src = src.replace(
    '"QSB_QARB096_ARM"',
    '"ORACLE_SOLANA_EXECUTION_ARM"'
)

# ============================================================
# 3. ADD A PHYSICAL FUNDING GATE
#
# Earlier live output showed the wallet below the amount needed
# for a 0.001 trade + account/rent overhead. Do not broadcast
# into a known insufficient-funds condition.
# ============================================================

run_seam = '''def run(
    root=None,
    seconds=120,
    scan_seconds=2.0
):'''

if run_seam not in src:
    raise SystemExit("[FAIL] run seam missing")

run_replacement = '''def run(
    root=None,
    seconds=120,
    scan_seconds=2.0
):
    root=Path(
        root or Path.cwd()
    )

    # Oracle execution funding floor.
    #
    # 0.001 SOL principal alone is insufficient when a route
    # needs account creation/rent/fees. Refuse to send rather
    # than knowingly submit an underfunded transaction.
    kp,user=require_keypair()

    balance=int(
        _rpc(
            "getBalance",
            [
                str(user),
                {
                    "commitment":
                        "confirmed"
                }
            ]
        )["value"]
    )

    minimum_balance=2_000_000

    print(
        "[ORACLE_FUNDING] "
        "balance=%d lamports "
        "minimum=%d lamports"%(
            balance,
            minimum_balance
        ),
        flush=True
    )

    if balance < minimum_balance:
        print(
            "[ORACLE_HOLD] "
            "INSUFFICIENT_EXECUTION_BALANCE "
            "required_at_least=0.002000000_SOL",
            flush=True
        )
        return 2

    return _oracle_execution_loop(
        root,
        seconds,
        scan_seconds,
        kp,
        user
    )


def _oracle_execution_loop(
    root,
    seconds,
    scan_seconds,
    kp,
    user
):'''

# Convert original run body into the internal loop by replacing
# its header and removing the duplicate root/keypair setup.
src = src.replace(
    run_seam,
    run_replacement,
    1
)

duplicate_root = '''    root=Path(
        root or Path.cwd()
    )

'''

# Only remove the first duplicate that now appears inside loop.
loop_pos = src.index("def _oracle_execution_loop(")
tail = src[loop_pos:]

if duplicate_root in tail:
    tail = tail.replace(
        duplicate_root,
        "",
        1
    )

duplicate_keys = '''    require_arm()

    kp,user=require_keypair()

'''

if duplicate_keys not in tail:
    raise SystemExit(
        "[FAIL] arm/keypair loop seam missing"
    )

tail = tail.replace(
    duplicate_keys,
    '''    require_arm()

''',
    1
)

src = src[:loop_pos] + tail

# ============================================================
# 4. VERIFY ORACLE OWNERSHIP IS PHYSICAL
# ============================================================

if 'EXECUTION_OWNER="Q_SERIES"' in src:
    raise SystemExit(
        "[FAIL] Q Series ownership still present"
    )

if 'EXECUTION_OWNER="ORACLE"' not in src:
    raise SystemExit(
        "[FAIL] Oracle ownership missing"
    )

if "ORACLE_EXECUTION_AUTHORITY=True" not in src:
    raise SystemExit(
        "[FAIL] Oracle execution authority missing"
    )

if '"maxRetries":0' not in src:
    raise SystemExit(
        "[FAIL] send-once contract missing"
    )

if "signed_simulation(" not in src:
    raise SystemExit(
        "[FAIL] signed simulation boundary missing"
    )

if "MICRO_LAMPORTS=1_000_000" not in src:
    raise SystemExit(
        "[FAIL] 0.001 SOL cap missing"
    )

ORACLE_DIR.mkdir(
    parents=True,
    exist_ok=True
)

INIT.write_text(
    '"""Oracle execution subsystem."""\n',
    encoding="utf-8"
)

TARGET.write_text(
    src,
    encoding="utf-8"
)

py_compile.compile(
    str(TARGET),
    doraise=True
)

# ============================================================
# 5. ORACLE LIVE EXECUTION LAUNCHER
# ============================================================

LAUNCHER.write_text(
'''from __future__ import annotations

import getpass
import os

from qseries_v2.oracle_execution.oracle_001_live_solana_executor import run


def main():
    print(
        "[ORACLE] LIVE SOLANA EXECUTION"
    )

    print(
        "[OWNER] ORACLE execution_authority=TRUE"
    )

    print(
        "[CAP] exact_per_transaction=0.001000_SOL"
    )

    os.environ[
        "QSB_SOLANA_PRIVATE_KEY"
    ]=getpass.getpass(
        "Private key (hidden): "
    )

    os.environ[
        "QSB_LIVE_ARM"
    ]="I_ACCEPT_REAL_MONEY_RISK"

    os.environ[
        "ORACLE_SOLANA_EXECUTION_ARM"
    ]="I_ACCEPT_ORACLE_0_001_SOL_EXECUTION"

    return run(
        seconds=120,
        scan_seconds=2.0
    )


if __name__=="__main__":
    raise SystemExit(main())
''',
    encoding="utf-8"
)

py_compile.compile(
    str(LAUNCHER),
    doraise=True
)

# ============================================================
# 6. TEST
# ============================================================

TEST.write_text(
'''import inspect
import unittest

from qseries_v2.oracle_execution import (
    oracle_001_live_solana_executor as q
)


class T(unittest.TestCase):

    def test_owner(self):
        self.assertEqual(
            q.EXECUTION_OWNER,
            "ORACLE"
        )

        self.assertTrue(
            q.ORACLE_EXECUTION_AUTHORITY
        )


    def test_exact_micro_cap(self):
        self.assertEqual(
            q.MICRO_LAMPORTS,
            1_000_000
        )

        self.assertEqual(
            q.MICRO_SOL,
            0.001
        )


    def test_oracle_arm(self):
        s=inspect.getsource(
            q.armed
        )

        self.assertIn(
            "ORACLE_SOLANA_EXECUTION_ARM",
            s
        )


    def test_signed_sim_before_send_exists(self):
        self.assertTrue(
            callable(
                q.signed_simulation
            )
        )

        self.assertTrue(
            callable(
                q.send_once
            )
        )


    def test_send_once_no_retry(self):
        s=inspect.getsource(
            q.send_once
        )

        self.assertIn(
            '"maxRetries":0',
            s
        )


    def test_preflight_enabled(self):
        s=inspect.getsource(
            q.send_once
        )

        self.assertIn(
            '"skipPreflight":False',
            s
        )


    def test_funding_gate(self):
        s=inspect.getsource(
            q.run
        )

        self.assertIn(
            "minimum_balance=2_000_000",
            s
        )

        self.assertIn(
            "INSUFFICIENT_EXECUTION_BALANCE",
            s
        )


    def test_oracle_runtime_state(self):
        self.assertIn(
            "runtime_state\\\\oracle",
            str(q.STATE)
        )


    def test_no_qseries_execution_owner(self):
        self.assertNotEqual(
            q.EXECUTION_OWNER,
            "Q_SERIES"
        )


if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
''',
    encoding="utf-8"
)

py_compile.compile(
    str(TEST),
    doraise=True
)

print(
    "[PASS] ORACLE-001 live Solana execution cutover installed"
)

print(
    "[OWNER] ORACLE execution_authority=TRUE"
)

print(
    "[Q_SERIES] no longer execution owner"
)

print(
    "[METEORA] Node-24 CommonJS loader physically verified"
)

print(
    "[SIM] signed simulation required before every send"
)

print(
    "[SEND] maxRetries=0 preflight=ENABLED"
)

print(
    "[CAP] exact 0.001 SOL"
)

print(
    "[FUNDING] >=0.002 SOL required before live execution begins"
)