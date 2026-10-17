
import { pathToFileURL } from "node:url";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);

async function loadPackage(name) {
    const resolved = require.resolve(name);
    const imported = await import(pathToFileURL(resolved).href);
    return imported.default ?? imported;
}

const { PublicKey } =
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

console.log("[MTR-031] START");
console.log("[MTR-031] METEORA BASE-MINT PAIR INVENTORY");
console.log(`[RPC] ${RPC_URL}`);

const base = new PublicKey(BASE_MINT);
const usdc = new PublicKey(USDC_MINT);

console.log(`[BASE_MINT] ${base.toBase58()}`);
console.log(`[USDC_MINT] ${usdc.toBase58()}`);

/*
    Find every Meteora LbPair where BASE is tokenX.
*/
const tokenXMatches = await rpc("getProgramAccounts", [
    METEORA_PROGRAM_ID,
    {
        encoding: "base64",
        filters: [
            {
                memcmp: {
                    offset: 9,
                    bytes: base.toBase58(),
                },
            },
        ],
    },
]);

/*
    Find every Meteora LbPair where BASE is tokenY.
*/
const tokenYMatches = await rpc("getProgramAccounts", [
    METEORA_PROGRAM_ID,
    {
        encoding: "base64",
        filters: [
            {
                memcmp: {
                    offset: 41,
                    bytes: base.toBase58(),
                },
            },
        ],
    },
]);

console.log(
    `[BASE_AS_TOKEN_X] ${tokenXMatches.length}`
);

console.log(
    `[BASE_AS_TOKEN_Y] ${tokenYMatches.length}`
);

const all = [
    ...tokenXMatches.map((x) => ({
        pubkey: x.pubkey,
        data: x.account.data[0],
    })),
    ...tokenYMatches.map((x) => ({
        pubkey: x.pubkey,
        data: x.account.data[0],
    })),
];

console.log(
    `[TOTAL_BASE_PAIRS] ${all.length}`
);

assert(
    all.length > 0,
    "PumpSwap base mint has no Meteora DLMM pair at all"
);

console.log("[BASE_MINT_METEORA_DISCOVERY] PASS");

/*
    Decode every discovered pair and identify the quote mint.
*/
const unique = new Map();

for (const item of all) {
    const raw = Buffer.from(item.data, "base64");

    if (raw.length < 73) {
        continue;
    }

    const tokenX = new PublicKey(raw.subarray(9, 41));
    const tokenY = new PublicKey(raw.subarray(41, 73));

    const baseIsX = tokenX.equals(base);
    const baseIsY = tokenY.equals(base);

    if (!baseIsX && !baseIsY) {
        continue;
    }

    const quote = baseIsX ? tokenY : tokenX;

    unique.set(item.pubkey, {
        pubkey: item.pubkey,
        tokenX: tokenX.toBase58(),
        tokenY: tokenY.toBase58(),
        quote: quote.toBase58(),
        isUsdc: quote.equals(usdc),
    });
}

const pairs = [...unique.values()];

console.log(
    `[DECODED_BASE_PAIRS] ${pairs.length}`
);

const usdcPairs = pairs.filter((x) => x.isUsdc);

console.log(
    `[BASE_USDC_PAIRS] ${usdcPairs.length}`
);

console.log("");

for (const pair of pairs.slice(0, 25)) {
    console.log(
        `[PAIR] ${pair.pubkey} ` +
        `X=${pair.tokenX} ` +
        `Y=${pair.tokenY} ` +
        `QUOTE=${pair.quote}`
    );
}

console.log("");

if (usdcPairs.length > 0) {
    console.log("[DIRECT_BASE_USDC] PASS");

    for (const pair of usdcPairs) {
        console.log(
            `[USDC_PAIR] ${pair.pubkey} ` +
            `X=${pair.tokenX} ` +
            `Y=${pair.tokenY}`
        );
    }
} else {
    console.log("[DIRECT_BASE_USDC] NONE");
}

/*
    Hydrate one non-USDC pool through the official SDK if available.
    This is discovery only; no swap construction and no transaction.
*/
const DLMM = await loadPackage("@meteora-ag/dlmm");

assert(
    typeof DLMM.create === "function",
    "official Meteora DLMM.create unavailable"
);

console.log("[METEORA_SDK] PASS");

const selected = usdcPairs[0] ?? pairs[0];

console.log(
    `[SELECTED_LB_PAIR] ${selected.pubkey}`
);

const pool = await DLMM.create(
    new (await loadPackage("@solana/web3.js")).Connection(
        RPC_URL,
        "confirmed"
    ),
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

console.log(
    `[SDK_TOKEN_X] ${sdkX.toBase58()}`
);

console.log(
    `[SDK_TOKEN_Y] ${sdkY.toBase58()}`
);

assert(
    sdkX.equals(base) || sdkY.equals(base),
    "official SDK selected pool does not contain PumpSwap base"
);

console.log("[SDK_BASE_BINDING] PASS");

console.log("");
console.log("[MTR-031] COMPLETE");
console.log(`[MTR-031] TOTAL_BASE_PAIRS=${pairs.length}`);
console.log(`[MTR-031] DIRECT_USDC_PAIRS=${usdcPairs.length}`);
console.log("[MTR-031] NO SIGNING");
console.log("[MTR-031] NO SENDING");
console.log("[MTR-031] NO CANONICAL EXECUTOR");
