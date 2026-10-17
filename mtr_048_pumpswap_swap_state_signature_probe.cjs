const fs=require("fs"),path=require("path");
function clip(src,name){
 const needles=[`${name}(`,`async ${name}(`];
 let i=-1;for(const n of needles){i=src.indexOf(n);if(i>=0)break}
 if(i<0)return null;
 let a=Math.max(0,i-250),b=Math.min(src.length,i+1800);return src.slice(a,b);
}
function main(){
 console.log("[MTR-048] START");
 console.log("[SCOPE] installed SDK source signature probe; no RPC; no signing; no sending");
 const entry=require.resolve("@pump-fun/pump-swap-sdk");
 console.log(`[SDK_ENTRY] ${entry}`);
 const src=fs.readFileSync(entry,"utf8");
 for(const n of ["swapSolanaState","swapSolanaStateNoPool","fetchPool","resolveQuote"]){
  const x=clip(src,n);
  console.log(`[METHOD_${n}] ${x?"FOUND":"NOT_FOUND"}`);
  if(x)console.log(`----- ${n} SOURCE -----\n${x}\n----- END ${n} -----`);
 }
 const P=require("@pump-fun/pump-swap-sdk");
 if(P.OnlinePumpAmmSdk){
  for(const n of ["swapSolanaState","swapSolanaStateNoPool","fetchPool","resolveQuote"]){
   const f=P.OnlinePumpAmmSdk.prototype[n];
   if(f)console.log(`[FUNCTION_${n}] arity=${f.length} text=${String(f).slice(0,1200)}`);
  }
 }
 fs.writeFileSync("mtr_048_pumpswap_signature_probe.json",JSON.stringify({
  schema:"MTR-048",sdk_entry:entry,
  methods:["swapSolanaState","swapSolanaStateNoPool","fetchPool","resolveQuote"],
  execution_authority:false,signing:false,sending:false
 },null,2));
 console.log("[RESULT] PUMPSWAP_SWAP_STATE_SIGNATURE_PHYSICALLY_CAPTURED");
 console.log("[NEXT_GATE] LIVE_BIDIRECTIONAL_QUOTE_WITH_EXACT_ARGUMENT_CONTRACT");
 console.log("[MTR-048] COMPLETE");
}
try{main()}catch(e){console.error("[MTR-048] FAIL");console.error(e.stack||e);process.exit(1)}
