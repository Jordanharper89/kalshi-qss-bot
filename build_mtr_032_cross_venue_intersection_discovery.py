from pathlib import Path

OUT = Path("tools") / "pumpswap_funded_public_preflight"
OUT.mkdir(parents=True, exist_ok=True)

JS = r"""
const RPC_URL = process.env.QSB_SOLANA_RPC_URL || "https://api.mainnet-beta.solana.com";

const PUMPSWAP_PROGRAM = "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA";
const METEORA_PROGRAM = "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo";
const USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v";
const USDT = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB";
const WSOL = "So11111111111111111111111111111111111111112";

const PUMP_POOL_SIZE = 211;
const PUMP_BASE_MINT_OFFSET = 43;
const PUMP_QUOTE_MINT_OFFSET = 75;

const DLMM_TOKEN_X_OFFSET = 9;
const DLMM_TOKEN_Y_OFFSET = 41;

function assert(cond, msg) {
  if (!cond) throw new Error(`[ASSERTION FAILED] ${msg}`);
}

function bytesToBase58(bytes) {
  const alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
  let zeros = 0;
  while (zeros < bytes.length && bytes[zeros] === 0) zeros++;
  let digits = [0];
  for (let i = zeros; i < bytes.length; i++) {
    let carry = bytes[i];
    for (let j = 0; j < digits.length; j++) {
      const x = digits[j] * 256 + carry;
      digits[j] = x % 58;
      carry = Math.floor(x / 58);
    }
    while (carry) {
      digits.push(carry % 58);
      carry = Math.floor(carry / 58);
    }
  }
  let out = "";
  for (let i = 0; i < zeros; i++) out += "1";
  for (let i = digits.length - 1; i >= 0; i--) out += alphabet[digits[i]];
  return out;
}

function readPubkey(data, offset) {
  return bytesToBase58(data.slice(offset, offset + 32));
}

async function rpc(method, params) {
  const response = await fetch(RPC_URL, {
    method: "POST",
    headers: {"content-type": "application/json"},
    body: JSON.stringify({
      jsonrpc: "2.0",
      id: Date.now(),
      method,
      params
    })
  });
  assert(response.ok, `${method} HTTP ${response.status}`);
  const body = await response.json();
  assert(!body.error, `${method} RPC error: ${JSON.stringify(body.error)}`);
  return body.result;
}

async function getProgramAccounts(program, filters) {
  return rpc("getProgramAccounts", [
    program,
    {
      encoding: "base64",
      filters
    }
  ]);
}

async function main() {
  console.log("[MTR-032] START");
  console.log("[MTR-032] CROSS-VENUE PUMPSWAP/METEORA INTERSECTION DISCOVERY");
  console.log(`[RPC] ${RPC_URL}`);
  console.log(`[PUMPSWAP_PROGRAM] ${PUMPSWAP_PROGRAM}`);
  console.log(`[METEORA_PROGRAM] ${METEORA_PROGRAM}`);
  console.log(`[USDC] ${USDC}`);
  console.log(`[USDT] ${USDT}`);
  console.log(`[WSOL] ${WSOL}`);

  assert(PUMPSWAP_BASE_MINT_OFFSET === 43, "PumpSwap base mint offset changed");
  assert(PUMPSWAP_QUOTE_MINT_OFFSET === 75, "PumpSwap quote mint offset changed");
  assert(DLMM_TOKEN_X_OFFSET === 9, "DLMM tokenX offset changed");
  assert(DLMM_TOKEN_Y_OFFSET === 41, "DLMM tokenY offset changed");
  console.log("[LAYOUT_CONSTANTS] PASS");

  console.log("[PUMPSWAP_DISCOVERY] querying USDC-quoted pools");
  const pumpAccounts = await getProgramAccounts(PUMPSWAP_PROGRAM, [
    {dataSize: PUMP_POOL_SIZE},
    {memcmp: {offset: PUMPSWAP_QUOTE_MINT_OFFSET, bytes: USDC}}
  ]);

  assert(Array.isArray(pumpAccounts), "PumpSwap RPC result is not an array");
  console.log(`[PUMPSWAP_USDC_POOL_COUNT] ${pumpAccounts.length}`);
  assert(pumpAccounts.length > 0, "no PumpSwap USDC pools found");

  const pumpPools = [];
  const baseMints = new Set();

  for (const item of pumpAccounts) {
    const raw = Buffer.from(item.account.data[0], "base64");
    if (raw.length !== PUMP_POOL_SIZE) continue;

    const baseMint = readPubkey(raw, PUMPSWAP_BASE_MINT_OFFSET);
    const quoteMint = readPubkey(raw, PUMPSWAP_QUOTE_MINT_OFFSET);

    if (quoteMint !== USDC) continue;

    pumpPools.push({
      pool: item.pubkey,
      baseMint,
      quoteMint,
      dataLength: raw.length
    });
    baseMints.add(baseMint);
  }

  console.log(`[PUMPSWAP_USDC_BASE_MINT_COUNT] ${baseMints.size}`);
  assert(pumpPools.length > 0, "decoded PumpSwap pool inventory is empty");

  console.log("[METEORA_DISCOVERY] querying complete DLMM pair account inventory");
  const dlmmAccounts = await getProgramAccounts(METEORA_PROGRAM, [
    {dataSize: 904}
  ]);

  assert(Array.isArray(dlmmAccounts), "Meteora RPC result is not an array");
  console.log(`[METEORA_LBPAIR_ACCOUNT_COUNT] ${dlmmAccounts.length}`);
  assert(dlmmAccounts.length > 0, "no Meteora LbPair accounts returned");

  const meteoraByMint = new Map();

  function addMeteoraMint(mint, pair) {
    if (!meteoraByMint.has(mint)) meteoraByMint.set(mint, []);
    meteoraByMint.get(mint).push(pair);
  }

  for (const item of dlmmAccounts) {
    const raw = Buffer.from(item.account.data[0], "base64");
    if (raw.length < 73) continue;

    const tokenXMint = readPubkey(raw, DLMM_TOKEN_X_OFFSET);
    const tokenYMint = readPubkey(raw, DLMM_TOKEN_Y_OFFSET);

    const pair = {
      lbPair: item.pubkey,
      tokenXMint,
      tokenYMint,
      dataLength: raw.length
    };

    addMeteoraMint(tokenXMint, pair);
    addMeteoraMint(tokenYMint, pair);
  }

  console.log(`[METEORA_DISTINCT_MINT_COUNT] ${meteoraByMint.size}`);

  const overlaps = [];
  for (const pump of pumpPools) {
    const pairs = meteoraByMint.get(pump.baseMint) || [];
    for (const pair of pairs) {
      const otherMint =
        pair.tokenXMint === pump.baseMint
          ? pair.tokenYMint
          : pair.tokenXMint;

      let priority = 9;
      if (otherMint === USDC) priority = 1;
      else if (otherMint === USDT) priority = 2;
      else if (otherMint === WSOL) priority = 3;

      overlaps.push({
        priority,
        pumpSwapPool: pump.pool,
        baseMint: pump.baseMint,
        pumpSwapQuoteMint: pump.quoteMint,
        meteoraLbPair: pair.lbPair,
        meteoraTokenXMint: pair.tokenXMint,
        meteoraTokenYMint: pair.tokenYMint,
        meteoraOtherMint: otherMint
      });
    }
  }

  overlaps.sort((a, b) =>
    a.priority - b.priority ||
    a.pumpSwapPool.localeCompare(b.pumpSwapPool) ||
    a.meteoraLbPair.localeCompare(b.meteoraLbPair)
  );

  console.log(`[CROSS_VENUE_OVERLAP_COUNT] ${overlaps.length}`);

  if (overlaps.length === 0) {
    console.log("[RESULT] NO_CROSS_VENUE_USDC_PUMPSWAP_METEORA_INTERSECTION");
    console.log("[RESULT] No execution build should be attempted from this inventory.");
    console.log("[MTR-032] DISCOVERY COMPLETE WITHOUT VIABLE OVERLAP");
    process.exit(2);
  }

  const directUsdc = overlaps.filter(x => x.meteoraOtherMint === USDC);
  const stablePair = overlaps.filter(
    x => x.meteoraOtherMint === USDC || x.meteoraOtherMint === USDT
  );

  console.log(`[DIRECT_METEORA_USDC_COUNT] ${directUsdc.length}`);
  console.log(`[STABLE_METEORA_COUNT] ${stablePair.length}`);

  console.log("[TOP_CANDIDATES]");
  for (const candidate of overlaps.slice(0, 25)) {
    console.log(JSON.stringify(candidate));
  }

  const artifact = {
    schema: "MTR-032-CROSS-VENUE-CANDIDATE-V1",
    generatedAt: new Date().toISOString(),
    rpc: RPC_URL,
    programs: {
      pumpswap: PUMPSWAP_PROGRAM,
      meteora: METEORA_PROGRAM
    },
    quoteMint: USDC,
    pumpSwapUsdcPoolCount: pumpPools.length,
    meteoraLbPairAccountCount: dlmmAccounts.length,
    crossVenueOverlapCount: overlaps.length,
    directUsdcCount: directUsdc.length,
    stablePairCount: stablePair.length,
    candidates: overlaps.slice(0, 100)
  };

  const fs = await import("node:fs/promises");
  await fs.mkdir("tools/pumpswap_funded_public_preflight", {recursive: true});
  await fs.writeFile(
    "tools/pumpswap_funded_public_preflight/mtr_032_candidates.json",
    JSON.stringify(artifact, null, 2),
    "utf8"
  );

  console.log("[ARTIFACT] tools/pumpswap_funded_public_preflight/mtr_032_candidates.json");
  console.log("[MTR-032] CROSS-VENUE INTERSECTION DISCOVERY PASS");
  console.log("[NO_SIGNING] PASS");
  console.log("[NO_SENDING] PASS");
  console.log("[NO_CANONICAL_EXECUTOR] PASS");
}

main().catch(err => {
  console.error(err && err.stack ? err.stack : err);
  process.exit(1);
});
"""

OUTFILE = OUT / "mtr_032_cross_venue_intersection_discovery.mjs"
OUTFILE.write_text(JS.strip() + "\n", encoding="utf-8")

print(f"[BUILD] wrote {OUTFILE}")
print(f"[BUILD] JS lines: {len(JS.strip().splitlines())}")
print("[BUILD] MTR-032 is discovery-only.")
print("[BUILD] It does not sign, send, arm, or invoke the canonical executor.")
