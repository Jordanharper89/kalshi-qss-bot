from pathlib import Path

OUT = Path(
    "tools/pumpswap_funded_public_preflight/"
    "mtr_030_direct_meteora_pair_discovery.mjs"
)

OUT.parent.mkdir(parents=True, exist_ok=True)

source = r"""
import { pathToFileURL } from "node:url";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);

async function loadPackage(name) {
    const resolved = require.resolve(name);
    const url = pathToFileURL(resolved).href;
    const imported = await import(url);
    return imported.default ?? imported;
}

const { Connection, PublicKey } =
    await loadPackage("@solana/web3.js");

const RPC_URL = "https://api.mainnet-beta.solana.com";

const METEORA_PROGRAM_ID =
    "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo";

const BASE_MINT =
    "7i7DCiJytzEnbThvCD85gYJsmoBG5XUfqUEAkb3C7XXz";

const USDC_MINT =
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v";

function assert(condition, message) {
    if (!condition) {
        throw new Error(`[ASSERTION FAILED] ${message}`);
    }
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

console.log("[MTR-030] START");
console.log("[MTR-030] DIRECT METEORA PAIR DISCOVERY");
console.log(`[RPC] ${RPC_URL}`);

const connection = new Connection(RPC_URL, "confirmed");

const meteoraProgram = new PublicKey(METEORA_PROGRAM_ID);
const baseMint = new PublicKey(BASE_MINT);
const usdcMint = new PublicKey(USDC_MINT);

console.log(`[METEORA_PROGRAM] ${meteoraProgram.toBase58()}`);
console.log(`[BASE_MINT] ${baseMint.toBase58()}`);
console.log(`[USDC_MINT] ${usdcMint.toBase58()}`);

assert(
    meteoraProgram.toBase58() === METEORA_PROGRAM_ID,
    "Meteora program ID validation failed"
);

assert(
    baseMint.toBase58() === BASE_MINT,
    "BASE mint validation failed"
);

assert(
    usdcMint.toBase58() === USDC_MINT,
    "USDC mint validation failed"
);

console.log("[PUBLIC_KEY_VALIDATION] PASS");

/*
    Meteora DLMM LbPair account:

    Anchor discriminator: bytes 0..7
    creatorPoolOnOffControl: byte 8
    tokenXMint: bytes 9..40
    tokenYMint: bytes 41..72

    Therefore the mint memcmp offsets are:
        tokenXMint = 9
        tokenYMint = 41
*/

console.log("[TOKEN_X_OFFSET] 9");
console.log("[TOKEN_Y_OFFSET] 41");

const baseAsString = baseMint.toBase58();
const usdcAsString = usdcMint.toBase58();

/*
    Query both orientations directly against the Meteora program.
*/

console.log("[RPC_DISCOVERY] BASE -> USDC");

const baseUsdc = await rpc("getProgramAccounts", [
    METEORA_PROGRAM_ID,
    {
        encoding: "base64",
        filters: [
            {
                memcmp: {
                    offset: 9,
                    bytes: baseAsString,
                },
            },
            {
                memcmp: {
                    offset: 41,
                    bytes: usdcAsString,
                },
            },
        ],
    },
]);

console.log(
    `[BASE_USDC_MATCHES] ${baseUsdc.length}`
);

console.log("[RPC_DISCOVERY] USDC -> BASE");

const usdcBase = await rpc("getProgramAccounts", [
    METEORA_PROGRAM_ID,
    {
        encoding: "base64",
        filters: [
            {
                memcmp: {
                    offset: 9,
                    bytes: usdcAsString,
                },
            },
            {
                memcmp: {
                    offset: 41,
                    bytes: baseAsString,
                },
            },
        ],
    },
]);

console.log(
    `[USDC_BASE_MATCHES] ${usdcBase.length}`
);

const candidates = [];

for (const item of baseUsdc) {
    candidates.push({
        pubkey: item.pubkey,
        direction: "BASE_TO_USDC",
        data: item.account.data[0],
    });
}

for (const item of usdcBase) {
    candidates.push({
        pubkey: item.pubkey,
        direction: "USDC_TO_BASE",
        data: item.account.data[0],
    });
}

console.log(
    `[DIRECT_METEORA_CANDIDATES] ${candidates.length}`
);

assert(
    candidates.length > 0,
    "no direct Meteora BASE/USDC LbPair account found"
);

console.log("[DIRECT_MINT_FILTER] PASS");

const selected = candidates[0];

console.log(`[LB_PAIR] ${selected.pubkey}`);
console.log(`[DIRECTION] ${selected.direction}`);

/*
    Decode the returned account ourselves before trusting it.
*/

const raw = Buffer.from(selected.data, "base64");

console.log(`[LB_PAIR_DATA_BYTES] ${raw.length}`);

assert(
    raw.length >= 73,
    "LbPair account data is shorter than expected"
);

const decodedX = new PublicKey(raw.subarray(9, 41));
const decodedY = new PublicKey(raw.subarray(41, 73));

console.log(`[DECODED_TOKEN_X] ${decodedX.toBase58()}`);
console.log(`[DECODED_TOKEN_Y] ${decodedY.toBase58()}`);

const decodedMatch =
    (
        decodedX.equals(baseMint) &&
        decodedY.equals(usdcMint)
    ) ||
    (
        decodedX.equals(usdcMint) &&
        decodedY.equals(baseMint)
    );

assert(
    decodedMatch,
    "decoded LbPair mints do not match BASE/USDC"
);

console.log("[DECODED_MINT_BINDING] PASS");

/*
    Now hydrate the exact account with the official Meteora SDK.
*/

const DLMM =
    await loadPackage("@meteora-ag/dlmm");

assert(
    typeof DLMM.create === "function",
    "official Meteora DLMM.create unavailable"
);

console.log("[METEORA_SDK] PASS");

const pool = await DLMM.create(
    connection,
    new PublicKey(selected.pubkey),
    {
        cluster: "mainnet-beta",
    }
);

await pool.refetchStates();

const sdkX =
    new PublicKey(pool.tokenX.mint.address);

const sdkY =
    new PublicKey(pool.tokenY.mint.address);

console.log(`[SDK_TOKEN_X] ${sdkX.toBase58()}`);
console.log(`[SDK_TOKEN_Y] ${sdkY.toBase58()}`);

const sdkMatch =
    (
        sdkX.equals(baseMint) &&
        sdkY.equals(usdcMint)
    ) ||
    (
        sdkX.equals(usdcMint) &&
        sdkY.equals(baseMint)
    );

assert(
    sdkMatch,
    "official SDK pool does not match BASE/USDC"
);

console.log("[SDK_POOL_BINDING] PASS");

console.log("");
console.log("[MTR-030] VERIFIED METEORA LB PAIR");
console.log(`[MTR-030] LB_PAIR=${selected.pubkey}`);
console.log(`[MTR-030] DIRECTION=${selected.direction}`);
console.log("[MTR-030] NO SIGNING");
console.log("[MTR-030] NO SENDING");
console.log("[MTR-030] NO CANONICAL EXECUTOR");
console.log("[MTR-030] COMPLETE");
"""

OUT.write_text(source, encoding="utf-8")

print(f"[CREATED] {OUT}")
print("[MTR-030] installer complete")