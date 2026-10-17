from pathlib import Path
T=Path("mtr_046_installed_quote_api_contract.cjs")
J=r'''const fs=require("fs");
function methods(x){
 if(!x)return [];
 const p=typeof x==="function"?x.prototype:Object.getPrototypeOf(x);
 return p?Object.getOwnPropertyNames(p).filter(k=>k!=="constructor"&&typeof p[k]==="function").sort():[];
}
function main(){
 console.log("[MTR-046] START");
 console.log("[SCOPE] installed SDK contract inspection; no RPC mutation; no signing; no sending");
 const P=require("@pump-fun/pump-swap-sdk"),D=require("@meteora-ag/dlmm");
 const DLMM=D.default||D.DLMM||D;
 console.log(`[PUMP_EXPORTS] ${Object.keys(P).sort().join(",")}`);
 for(const n of ["PumpAmmSdk","OnlinePumpAmmSdk","PumpAmmInternalSdk"])
  console.log(`[PUMP_${n}_METHODS] ${methods(P[n]).join(",")}`);
 console.log(`[METEORA_STATIC_METHODS] ${Object.getOwnPropertyNames(DLMM).filter(k=>typeof DLMM[k]==="function").sort().join(",")}`);
 console.log(`[METEORA_INSTANCE_METHODS] ${methods(DLMM).join(",")}`);
 if(!fs.existsSync("mtr_045_normalized_exact_pairs.json"))throw Error("MISSING_MTR_045_NORMALIZED_EXACT_PAIRS");
 const d=JSON.parse(fs.readFileSync("mtr_045_normalized_exact_pairs.json","utf8")),rows=d.rows||[];
 if(!rows.length)throw Error("NO_NORMALIZED_ROWS");
 const r=rows[0];
 console.log(`[PROBE_PUMP_POOL] ${r.pump_pool}`);
 console.log(`[PROBE_BASE] ${r.base_mint}`);
 console.log(`[PROBE_QUOTE] ${r.quote_mint}`);
 console.log(`[PROBE_METEORA_POOL] ${r.meteora_pools[0]}`);
 const pumpMethods=[...new Set([...methods(P.PumpAmmSdk),...methods(P.OnlinePumpAmmSdk),...methods(P.PumpAmmInternalSdk)])];
 const needed=["swapSolanaState","buyQuoteInput","sellQuoteInput"];
 for(const n of needed)console.log(`[PUMP_METHOD_${n}] ${pumpMethods.includes(n)?"PRESENT":"ABSENT"}`);
 const dm=methods(DLMM);
 for(const n of ["getBinArrayForSwap","swapQuote"])console.log(`[METEORA_METHOD_${n}] ${dm.includes(n)?"PRESENT":"ABSENT"}`);
 const out={schema:"MTR-046",pump_exports:Object.keys(P).sort(),pump_methods:pumpMethods,
  meteora_methods:dm,probe:r,execution_authority:false,signing:false,sending:false};
 fs.writeFileSync("mtr_046_quote_api_contract.json",JSON.stringify(out,null,2));
 console.log("[RESULT] INSTALLED_QUOTE_API_CONTRACT_CAPTURED");
 console.log("[NEXT_GATE] LIVE_BIDIRECTIONAL_QUOTE_PROOF_FROM_PHYSICAL_METHODS");
 console.log("[OUTPUT] mtr_046_quote_api_contract.json");
 console.log("[MTR-046] COMPLETE");
}
try{main()}catch(e){console.error("[MTR-046] FAIL");console.error(e.stack||e);process.exit(1)}'''
T.write_text(J,encoding="utf-8")
print(f"[BUILD] wrote {T}")
print("[BUILD] installed PumpSwap + Meteora quote API contract probe")
print("[SCOPE] no signing; no sending; canonical executor untouched")