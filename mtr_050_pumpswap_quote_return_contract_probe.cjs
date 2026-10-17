const fs=require("fs");
function all(src,name){
 let out=[],at=0;
 while(true){let i=src.indexOf(`${name}(`,at);if(i<0)break;out.push(src.slice(Math.max(0,i-180),Math.min(src.length,i+2200)));at=i+name.length+1}
 return out;
}
function main(){
 console.log("[MTR-050] START");
 console.log("[SCOPE] installed PumpSwap quote source/return contract; no RPC; no signing; no sending");
 const entry=require.resolve("@pump-fun/pump-swap-sdk"),src=fs.readFileSync(entry,"utf8");
 console.log(`[SDK_ENTRY] ${entry}`);
 const names=["buyQuoteInput","buyBaseInput","sellBaseInput","sellQuoteInput"];
 for(const n of names){
  const hits=all(src,n);
  console.log(`[${n}] source_hits=${hits.length}`);
  hits.slice(0,4).forEach((x,i)=>console.log(`----- ${n} HIT ${i+1} -----\n${x}\n----- END -----`));
 }
 const P=require("@pump-fun/pump-swap-sdk");
 for(const n of names){
  const f=P.PumpAmmSdk&&P.PumpAmmSdk.prototype[n],g=P[n];
  if(f)console.log(`[METHOD_${n}] arity=${f.length} text=${String(f).slice(0,1800)}`);
  if(g)console.log(`[EXPORT_${n}] arity=${g.length} text=${String(g).slice(0,1800)}`);
 }
 fs.writeFileSync("mtr_050_pumpswap_quote_contract.json",JSON.stringify({schema:"MTR-050",sdk_entry:entry,names,execution_authority:false,signing:false,sending:false},null,2));
 console.log("[RESULT] PUMPSWAP_QUOTE_RETURN_CONTRACT_CAPTURED");
 console.log("[NEXT_GATE] LIVE_BIDIRECTIONAL_QUOTE_WITH_EXACT_RETURN_SEMANTICS");
 console.log("[MTR-050] COMPLETE");
}
try{main()}catch(e){console.error("[MTR-050] FAIL");console.error(e.stack||e);process.exit(1)}
