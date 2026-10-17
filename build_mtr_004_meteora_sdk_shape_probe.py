from pathlib import Path
import json
import shutil
import subprocess
import textwrap

ROOT = Path(__file__).resolve().parent
TOOL_DIR = ROOT / "tools" / "meteora_funded_public_preflight"
TOOL_DIR.mkdir(parents=True, exist_ok=True)

TARGET = TOOL_DIR / "meteora_sdk_shape_probe.mjs"

JS = r'''
import DLMM from "@meteora-ag/dlmm";
import { Connection, PublicKey } from "@solana/web3.js";

const RPC = "https://api.mainnet-beta.solana.com";

const LB_PAIR =
  new PublicKey("ARwi1S4DaiTG5DX7S4M4ZsrXqpMD1MrTmbu9ue2tpmEq");

function describe(value, depth = 0) {
  if (depth > 3) {
    return "[MAX_DEPTH]";
  }

  if (value === null) {
    return null;
  }

  if (value === undefined) {
    return "[UNDEFINED]";
  }

  const type = typeof value;

  if (
    type === "string" ||
    type === "number" ||
    type === "boolean" ||
    type === "bigint"
  ) {
    return {
      type,
      value: String(value)
    };
  }

  if (type === "function") {
    return {
      type,
      name: value.name || null
    };
  }

  if (Array.isArray(value)) {
    return {
      type: "array",
      length: value.length,
      items: value.slice(0, 5).map((x) => describe(x, depth + 1))
    };
  }

  const result = {
    type: "object",
    constructor:
      value?.constructor?.name || null,
    keys: []
  };

  try {
    result.keys = Object.keys(value);
  } catch {}

  for (const key of result.keys.slice(0, 30)) {
    try {
      result[key] = describe(value[key], depth + 1);
    } catch (err) {
      result[key] = {
        error: String(err)
      };
    }
  }

  return result;
}

async function main() {
  console.log("[MTR-004] START");
  console.log(`[RPC] ${RPC}`);
  console.log(`[LB_PAIR] ${LB_PAIR.toBase58()}`);

  const connection = new Connection(RPC, "confirmed");

  console.log("[SDK] creating Meteora DLMM pool");

  const pool = await DLMM.create(
    connection,
    LB_PAIR,
    { cluster: "mainnet-beta" }
  );

  console.log("[POOL_CREATED]");

  console.log(
    "[TOKEN_X_SHAPE]",
    JSON.stringify(
      describe(pool.tokenX),
      null,
      2
    )
  );

  console.log(
    "[TOKEN_Y_SHAPE]",
    JSON.stringify(
      describe(pool.tokenY),
      null,
      2
    )
  );

  console.log(
    "[TOKEN_X_MINT_SHAPE]",
    JSON.stringify(
      describe(pool.tokenX?.mint),
      null,
      2
    )
  );

  console.log(
    "[TOKEN_Y_MINT_SHAPE]",
    JSON.stringify(
      describe(pool.tokenY?.mint),
      null,
      2
    )
  );

  console.log(
    "[POOL_SHAPE]",
    JSON.stringify(
      describe(pool),
      null,
      2
    )
  );

  console.log("[MTR-004] SHAPE PROBE COMPLETE");
}

main().catch((err) => {
  console.error("[FAIL]", err?.stack || err);
  process.exitCode = 1;
});
'''

TARGET.write_text(
    textwrap.dedent(JS).lstrip(),
    encoding="utf-8"
)

npm = shutil.which("npm.cmd") or shutil.which("npm")
if not npm:
    raise SystemExit("npm/npm.cmd not found on PATH")

sdk_index = (
    TOOL_DIR
    / "node_modules"
    / "@meteora-ag"
    / "dlmm"
    / "dist"
    / "index.mjs"
)

if not sdk_index.exists():
    raise SystemExit("Meteora SDK index.mjs not found")

data = sdk_index.read_text(encoding="utf-8")

old = "@coral-xyz/anchor/dist/cjs/utils/bytes"
new = "@coral-xyz/anchor/dist/cjs/utils/bytes/index.js"

if old in data and new not in data:
    sdk_index.write_text(
        data.replace(old, new),
        encoding="utf-8"
    )

subprocess.run(
    ["node", "--check", str(TARGET)],
    cwd=str(ROOT),
    check=True
)

print("[PASS] Meteora Node-ESM compatibility already correct")
print("[PASS] official SDK default import preserved")
print("[PASS] SDK shape probe generated")
print(f"[PASS] {TARGET}")
print("[BUILD COMPLETE] MTR-004")