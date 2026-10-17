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
