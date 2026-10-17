import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);

function resolvePackage(name) {
  return require.resolve(name);
}

async function loadPackage(name) {
  const resolved = resolvePackage(name);

  // Windows ESM requires file:// URLs for absolute filesystem paths.
  const url = pathToFileURL(resolved).href;

  console.log(`[MODULE_RESOLVED] ${name}`);
  console.log(`[MODULE_PATH] ${resolved}`);
  console.log(`[MODULE_URL] ${url}`);

  const mod = await import(url);
  return mod;
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(`[ASSERTION FAILED] ${message}`);
  }
}

console.log("[MTR-021] START");
console.log("[MTR-021] WINDOWS ESM MODULE LOADER PREFLIGHT");

const pumpModule = await loadPackage("@pump-fun/pump-swap-sdk");
const meteoraModule = await loadPackage("@meteora-ag/dlmm");
const web3Module = await loadPackage("@solana/web3.js");
const splModule = await loadPackage("@solana/spl-token");
const bnModule = await loadPackage("bn.js");

assert(pumpModule, "PumpSwap module loaded");
assert(meteoraModule, "Meteora module loaded");
assert(web3Module, "web3 module loaded");
assert(splModule, "SPL Token module loaded");
assert(bnModule, "bn.js module loaded");

const pumpExports = Object.keys(pumpModule).sort();
const meteoraExports = Object.keys(meteoraModule).sort();

console.log(`[PUMPSWAP_EXPORT_COUNT] ${pumpExports.length}`);
console.log(`[METEORA_EXPORT_COUNT] ${meteoraExports.length}`);

console.log(
  `[PUMPSWAP_EXPORTS] ${pumpExports.slice(0, 40).join(",")}`
);

console.log(
  `[METEORA_EXPORTS] ${meteoraExports.slice(0, 40).join(",")}`
);

const PumpAmmSdk =
  pumpModule.PumpAmmSdk ??
  pumpModule.default?.PumpAmmSdk;

const OnlinePumpAmmSdk =
  pumpModule.OnlinePumpAmmSdk ??
  pumpModule.default?.OnlinePumpAmmSdk;

const PUMP_AMM_SDK =
  pumpModule.PUMP_AMM_SDK ??
  pumpModule.default?.PUMP_AMM_SDK;

const DLMM =
  meteoraModule.default ??
  meteoraModule.DLMM ??
  meteoraModule;

const Connection =
  web3Module.Connection ??
  web3Module.default?.Connection;

const PublicKey =
  web3Module.PublicKey ??
  web3Module.default?.PublicKey;

const Transaction =
  web3Module.Transaction ??
  web3Module.default?.Transaction;

const BN =
  bnModule.default ??
  bnModule;

assert(PumpAmmSdk, "PumpAmmSdk export available");
assert(OnlinePumpAmmSdk, "OnlinePumpAmmSdk export available");
assert(PUMP_AMM_SDK, "PUMP_AMM_SDK export available");
assert(DLMM, "Meteora DLMM export available");
assert(Connection, "Connection export available");
assert(PublicKey, "PublicKey export available");
assert(Transaction, "Transaction export available");
assert(BN, "BN constructor available");

console.log("[PUMPSWAP_SDK] PASS");
console.log("[METEORA_DLMM] PASS");
console.log("[WEB3] PASS");
console.log("[SPL_TOKEN] PASS");
console.log("[BN] PASS");

const METEORA_PROGRAM =
  "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo";

const PUMPSWAP_PROGRAM =
  "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA";

const LB_PAIR =
  "ARwi1S4DaiTG5DX7S4M4ZsrXqpMD1MrTmbu9ue2tpmEq";

const PUBLIC_CANDIDATE =
  "CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR";

new PublicKey(METEORA_PROGRAM);
new PublicKey(PUMPSWAP_PROGRAM);
new PublicKey(LB_PAIR);
new PublicKey(PUBLIC_CANDIDATE);

console.log("[METEORA_PROGRAM_ID] PASS");
console.log("[PUMPSWAP_PROGRAM_ID] PASS");
console.log("[LB_PAIR] PASS");
console.log("[PUBLIC_CANDIDATE] PASS");

console.log("[MTR-021] WINDOWS ESM LOADER PREFLIGHT PASS");
console.log("[MTR-021] NO SIGNING.");
console.log("[MTR-021] NO SENDING.");
console.log("[MTR-021] NO CANONICAL EXECUTOR.");
