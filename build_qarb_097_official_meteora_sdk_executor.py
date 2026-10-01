from pathlib import Path
import subprocess
import shutil

ROOT=Path.cwd()

JS=ROOT/(
    "qseries_v2/oracle_strategy_intelligence/"
    "solana_money/qsb059d_pump_native/"
    "build_meteora_swap_ix.mjs"
)

if not JS.is_file():
    raise SystemExit("[FAIL] Meteora builder missing")

s=JS.read_text(encoding="utf-8")

old='''import DLMM from "@meteora-ag/dlmm";'''

new='''import {createRequire} from "node:module";
const require=createRequire(import.meta.url);
const _dlmm=require("@meteora-ag/dlmm");
const DLMM=_dlmm.default ?? _dlmm;'''

if old not in s:
    if 'require("@meteora-ag/dlmm")' not in s:
        raise SystemExit(
            "[FAIL] expected Meteora import seam missing"
        )
else:
    s=s.replace(old,new,1)

JS.write_text(
    s,
    encoding="utf-8"
)

# Prove Node 24 resolves the CJS export NOW,
# before claiming this installer passed.
node=shutil.which("node")

if not node:
    raise SystemExit("[FAIL] node missing")

cwd=JS.parent

probe=subprocess.run(
    [
        node,
        "--input-type=module",
        "-e",
        (
            'import {createRequire} from "node:module";'
            'const require=createRequire(import.meta.url);'
            'const m=require("@meteora-ag/dlmm");'
            'const D=m.default??m;'
            'if(!D) process.exit(7);'
            'console.log("[METEORA_CJS_IMPORT_OK]",typeof D);'
        )
    ],
    cwd=cwd,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    timeout=30
)

print(probe.stdout.strip())

if probe.returncode!=0:
    raise SystemExit(
        "[FAIL] Meteora CommonJS import still broken"
    )

check=JS.read_text(encoding="utf-8")

assert 'createRequire' in check
assert 'require("@meteora-ag/dlmm")' in check
assert 'import DLMM from "@meteora-ag/dlmm"' not in check

print("[PASS] QARB-097 Node 24 Meteora compatibility repaired")
print("[ENTRYPOINT] CommonJS dist/index.js forced")
print("[BYPASS] broken ESM dist/index.mjs not used")
print("[RUNTIME] QARB-097 executor unchanged")
print("[OWNER] Q_SERIES")
print("[CAP] exact 0.001 SOL unchanged")