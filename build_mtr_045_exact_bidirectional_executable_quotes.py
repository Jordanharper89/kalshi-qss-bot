from pathlib import Path
target=Path("mtr_045_exact_bidirectional_executable_quotes.cjs")
target.write_text(r"""const fs=require("fs");
const {Connection,PublicKey}=require("@solana/web3.js");
const D=require("@meteora-ag/dlmm"), P=require("@pump-fun/pump-swap-sdk"), BN=require("bn.js");
const DLMM=D.default||D.DLMM||D, PumpAmmSdk=P.PumpAmmSdk;
const RPC=process.env.SOLANA_RPC_URL||process.env.QSB_SOLANA_RPC_URL||"https://api.mainnet-beta.solana.com";
const WSOL="So11111111111111111111111111111111111111112", conn=new Connection(RPC,"confirmed");
const S=x=>x&&x.toBase58?x.toBase58():String(x), M=x=>S(x?.address||x?.mint||x), K=(a,b)=>[a,b].sort().join("|");
(async()=>{
 console.log("[MTR-045] START"); console.log("[SCOPE] live quotes only; signing=false; sending=false; executor=false");
 if(!fs.existsSync("mtr_044_exact_pairs.json")) throw Error("MISSING_MTR_044_EXACT_PAIRS_JSON");
 const d=JSON.parse(fs.readFileSync("mtr_044_exact_pairs.json")), rows=Array.isArray(d)?d:(d.exact_pairs||d.pairs||d.intersections||d.rows||[]);
 if(!rows.length) throw Error("NO_MTR_044_ROWS");
 const lbs=await DLMM.getLbPairs(conn), idx=new Map();
 for(const r of lbs){let a=M(r.account?.tokenXMint||r.tokenXMint),b=M(r.account?.tokenYMint||r.tokenYMint);if(!a||!b)continue;let k=K(a,b);if(!idx.has(k))idx.set(k,[]);idx.get(k).push(S(r.publicKey||r.pubkey));}
 const pump=new PumpAmmSdk(conn), cs=[];
 for(const r of rows){let base=r.base||r.base_mint||r.baseMint,quote=r.quote||r.quote_mint||r.quoteMint,pp=r.pump||r.pump_pool||r.pumpPool||r.pool;
  if(!base||!quote||!pp||(base!==WSOL&&quote!==WSOL))continue;
  let ms=r.meteora||r.meteora_pools||r.meteoraPools||idx.get(K(base,quote))||[]; if(!Array.isArray(ms))ms=String(ms).split(",").filter(Boolean);
  if(ms.length)cs.push({pp,base,quote,ms}); if(cs.length>=12)break;
 }
 console.log(`[INPUT_ROWS] ${rows.length}`);console.log(`[WSOL_EXACT_CANDIDATES] ${cs.length}`);if(!cs.length)throw Error("NO_WS0L_EXACT_CANDIDATES");
 const sizes=[.001,.005,.010,.025,.050], out=[];
 for(const c of cs){let ps;try{ps=await pump.fetchPool(new PublicKey(c.pp));}catch(e){console.log(`[SKIP_PUMP] ${c.pp} ${e.message}`);continue;}
  for(const mp of c.ms.slice(0,6)){let dl;try{dl=await DLMM.create(conn,new PublicKey(mp));}catch(e){console.log(`[SKIP_METEORA] ${mp} ${e.message}`);continue;}
   for(const sol of sizes)try{
    let input=new BN(Math.floor(sol*1e9)),pb=M(ps.baseMint||ps.base?.mint),pqm=M(ps.quoteMint||ps.quote?.mint),q;
    if(pqm===WSOL&&pump.buyQuoteInput)q=await pump.buyQuoteInput(ps,input);else if(pb===WSOL&&pump.sellQuoteInput)q=await pump.sellQuoteInput(ps,input);else continue;
    let mid=new BN(String(q.baseAmountOut||q.quoteAmountOut||q.amountOut||q.outputAmount||0));if(mid.isZero())continue;
    let bins=await dl.getBinArrayForSwap(false),mq=dl.swapQuote(mid,false,new BN(50),bins),fin=new BN(String(mq.outAmount||mq.amountOut||0));
    let gross=fin.sub(input),bps=Number(gross.muln(10000).div(input)),r={direction:"PUMP_TO_METEORA",pump_pool:c.pp,meteora_pool:mp,input_sol:sol,pump_out_raw:mid.toString(),final_wsol_raw:fin.toString(),gross_raw:gross.toString(),gross_bps:bps};
    out.push(r);console.log(`[QUOTE] dir=${r.direction} size=${sol.toFixed(3)} gross_bps=${bps} pump=${c.pp} meteora=${mp}`);
   }catch(e){console.log(`[QUOTE_FAIL] size=${sol.toFixed(3)} pump=${c.pp} meteora=${mp} reason=${e.message}`);}
  }
 }
 out.sort((a,b)=>b.gross_bps-a.gross_bps);fs.writeFileSync("mtr_045_quotes.json",JSON.stringify({generated_at:new Date().toISOString(),results:out},null,2));
 console.log(`[SUCCESSFUL_QUOTES] ${out.length}`);
 if(out.length){let b=out[0];console.log(`[BEST_GROSS] dir=${b.direction} size=${b.input_sol} gross_bps=${b.gross_bps} pump=${b.pump_pool} meteora=${b.meteora_pool}`);console.log("[RESULT] EXACT_EXECUTABLE_QUOTE_PATH_OBSERVED");console.log("[NEXT_GATE] COMPLETE_BIDIRECTIONAL_QUOTING_AND_FEE_ADJUSTED_RANKING");}
 else{console.log("[RESULT] NO_EXECUTABLE_QUOTES_FROM_BOUNDED_SAMPLE");console.log("[NEXT_GATE] INSPECT_QUOTE_API_DIRECTION_AND_PAIR_STATE");}
 console.log("[OUTPUT] mtr_045_quotes.json");console.log("[MTR-045] COMPLETE");
})().catch(e=>{console.error("[MTR-045] FAIL");console.error(e.stack||e);process.exit(1);});
""",encoding="utf-8")
print("[BUILD] wrote",target)
print("[SCOPE] bounded quote proof; no signing; no sending; canonical executor untouched")
