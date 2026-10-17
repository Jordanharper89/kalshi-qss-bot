from pathlib import Path

OUT = Path(
    "tools/pumpswap_funded_public_preflight/"
    "mtr_029_direct_meteora_pair_discovery.mjs"
)

OUT.parent.mkdir(parents=True, exist_ok=True)

js = r'''import { pathToFileURL } from "node:url";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);

function loadPackage(name) {
  const resolved = require.resolve(name);
  return import(pathToFileURL(resolved).href).then(
    (m) => m.default ?? m
  );
}

const {
  Connection,
  PublicKey,
} = await loadPackage("@solana/web3.js");

const RPC_URL = "https://api.mainnet-beta.solana.com";

const METEORA_PROGRAM_ID =
  "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo";

const PUMPSWAP_BASE_MINT =
  "7i7DCiJytzEnbThvCD85gYJsmoBG5XUfqUEAkb3C7XXz";

const USDC_MINT =
  "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v";

function assert(condition, message) {
  if (!condition) {
    throw new Error(`[ASSERTION FAILED] ${message}`);
  }
}

function pubkeyBytes(pubkey) {
  return new PublicKey(pubkey).toBytes();
}

async function rpc(method, params) {
  const response = await fetch(RPC_URL, {
    method: "POST",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify({
      jsonrpc: "2.0",
      id: 1,
      method,
      params,
    }),
  });

  const json = await response.json();

  if (json.error) {
    throw new Error(
      `[RPC ERROR] ${method}: ${JSON.stringify(json.error)}`
    );
  }

  return json.result;
}

console.log("[MTR-029] START");
console.log("[MTR-029] DIRECT METEORA ON-CHAIN PAIR DISCOVERY");
console.log(`[RPC] ${RPC_URL}`);

const connection = new Connection(RPC_URL, "confirmed");

const meteoraProgram = new PublicKey(METEORA_PROGRAM_ID);
const targetBase = new PublicKey(PUMPSWAP_BASE_MINT);
const usdc = new PublicKey(USDC_MINT);

console.log("[PROGRAM_ID]", meteoraProgram.toBase58());
console.log("[TARGET_BASE]", targetBase.toBase58());
console.log("[USDC]", usdc.toBase58());

assert(
  meteoraProgram.toBase58() === METEORA_PROGRAM_ID,
  "Meteora program ID mismatch"
);

assert(
  targetBase.toBase58() === PUMPSWAP_BASE_MINT,
  "PumpSwap base mint mismatch"
);

assert(
  usdc.toBase58() === USDC_MINT,
  "USDC mint mismatch"
);

console.log("[PUBLIC_KEY_VALIDATION] PASS");

/*
  Current Meteora LbPair account layout:

  8-byte Anchor account discriminator
  1-byte creator_pool_on_off_control
  tokenXMint begins at byte 9
  tokenYMint begins at byte 41

  Therefore:

  tokenXMint offset = 9
  tokenYMint offset = 41
*/

const TARGET_X = pubkeyBytes(targetBase);
const TARGET_Y = pubkeyBytes(usdc);

console.log("[METEORA_FILTER_OFFSETS]");
console.log("[TOKEN_X_MINT_OFFSET] 9");
console.log("[TOKEN_Y_MINT_OFFSET] 41");

const exactX = await rpc("getProgramAccounts", [
  METEORA_PROGRAM_ID,
  {
    encoding: "base64",
    filters: [
      {
        memcmp: {
          offset: 9,
          bytes: targetBase.toBase58(),
        },
      },
      {
        memcmp: {
          offset: 41,
          bytes: usdc.toBase58(),
        },
      },
    ],
  },
]);

const exactY = await rpc("getProgramAccounts", [
  METEORA_PROGRAM_ID,
  {
    encoding: "base64",
    filters: [
      {
        memcmp: {
          offset: 9,
          bytes: usdc.toBase58(),
        },
      },
      {
        memcmp: {
          offset: 41,
          bytes: targetBase.toBase58(),
        },
      },
    ],
  },
]);

console.log(
  `[DIRECT_X_TO_USDC_COUNT] ${exactX.length}`
);

console.log(
  `[DIRECT_USDC_TO_X_COUNT] ${exactY.length}`
);

const matches = [
  ...exactX.map((x) => ({
    pubkey: x.pubkey,
    direction: "X=BASE,Y=USDC",
  })),
  ...exactY.map((x) => ({
    pubkey: x.pubkey,
    direction: "X=USDC,Y=BASE",
  })),
];

console.log(
  `[DIRECT_BASE_USDC_MATCH_COUNT] ${matches.length}`
);

assert(
  matches.length > 0,
  "no direct Meteora BASE/USDC LbPair account found"
);

console.log("[DIRECT_MINT_FILTER] PASS");

const first = matches[0];

console.log(`[METEORA_LB_PAIR] ${first.pubkey}`);
console.log(`[METEORA_DIRECTION] ${first.direction}`);

const accountInfo = await rpc("getAccountInfo", [
  first.pubkey,
  {
    encoding: "base64",
  },
]);

assert(
  accountInfo !== null,
  "selected Meteora LbPair account disappeared"
);

assert(
  accountInfo.owner === METEORA_PROGRAM_ID,
  "selected account owner is not Meteora DLMM program"
);

console.log("[ACCOUNT_OWNER] PASS");

const raw = Buffer.from(accountInfo.data[0], "base64");

assert(
  raw.length > 73,
  `selected LbPair account unexpectedly short: ${raw.length}`
);

const tokenX = new PublicKey(raw.subarray(9, 41));
const tokenY = new PublicKey(raw.subarray(41, 73));

console.log(`[DECODED_TOKEN_X] ${tokenX.toBase58()}`);
console.log(`[DECODED_TOKEN_Y] ${tokenY.toBase58()}`);

const orientationMatches =
  (
    tokenX.equals(targetBase) &&
    tokenY.equals(usdc)
  ) ||
  (
    tokenX.equals(usdc) &&
    tokenY.equals(targetBase)
  );

assert(
  orientationMatches,
  "decoded LbPair mints do not match target BASE/USDC"
);

console.log("[DECODED_MINT_BINDING] PASS");

/*
  Now load the exact discovered pool through the official Meteora SDK.
  This does NOT sign or send anything.
*/

const DLMM = await loadPackage("@meteora-ag/dlmm");

assert(
  typeof DLMM.create === "function",
  "official Meteora DLMM.create unavailable"
);

console.log("[OFFICIAL_SDK] PASS");

const pool = await DLMM.create(
  connection,
  new PublicKey(first.pubkey),
  {
    cluster: "mainnet-beta",
  }
);

await pool.refetchStates();

const sdkTokenX = new PublicKey(pool.tokenX.mint.address);
const sdkTokenY = new PublicKey(pool.tokenY.mint.address);

console.log(
  `[SDK_TOKEN_X] ${sdkTokenX.toBase58()}`
);

console.log(
  `[SDK_TOKEN_Y] ${sdkTokenY.toBase58()}`
);

assert(
  (
    sdkTokenX.equals(targetBase) &&
    sdkTokenY.equals(usdc)
  ) ||
  (
    sdkTokenX.equals(usdc) &&
    sdkTokenY.equals(targetBase)
  ),
  "official SDK pool binding does not match BASE/USDC"
);

console.log("[SDK_POOL_BINDING] PASS");
console.log(`[MTR-029] VERIFIED_LB_PAIR ${first.pubkey}`);
console.log("[MTR-029] NO SIGNING");
console.log("[MTR-029] NO SENDING");
console.log("[MTR-029] NO CANONICAL EXECUTOR");
console.log("[MTR-029] DIRECT METEORA DISCOVERY COMPLETE");
'''

OUT.write_text(js, encoding="utf-8")

print(f"[CREATED] {OUT}")
print("[MTR-029] installer complete")
'''

Path("build_mtr_029_direct_meteora_pair_discovery.py").write_text(
    js,
    encoding="utf-8",
)

print(f"[CREATED] {OUT}")
print("[MTR-029] installer complete")