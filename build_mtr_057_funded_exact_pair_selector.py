from pathlib import Path

target = Path("mtr_057_funded_exact_pair_selector.cjs")

target.write_text(r'''const fs=require("fs"),{Connection,PublicKey,SystemProgram}=require("@solana/web3.js");
const P=require("@pump-fun/pump-swap-sdk");
const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||"https://api.mainnet-beta.solana.com";
const W="So11111111111111111111111111111111111111112";
const c=new Connection(RPC,"confirmed"),sleep=ms=>new Promise(r=>setTimeout(r,ms));
const str=x=>x&&x.toBase58?x.toBase58():typeof x==="string"?x:null;
const val=(o,names)=>{for(const n of names)if(o&&o[n]!=null)return o[n];return null};
const arr=(o,names)=>{const x=val(o,names);return Array.isArray(x)?x:[]};
(async()=>{
 console.log("[MTR-057] START");
 console.log("[SCOPE] normalized-row schema discovery + funded PumpSwap selection; no signing; no sending");
 const d=JSON.parse(fs.readFileSync("mtr_045_normalized_exact_pairs.json","utf8")),rows=d.rows||[];
 if(!rows.length)throw Error("NO_MTR045_ROWS");
 console.log(`[ROW_COUNT] ${rows.length}`);
 console.log(`[ROW_KEYS] ${Object.keys(rows[0]).sort().join(",")}`);
 console.log(`[ROW0] ${JSON.stringify(rows[0]).slice(0,1800)}`);
 const on=new P.OnlinePumpAmmSdk(c),seen=new Set(),good=[];let eligible=0,tested=0,failed=0;
 for(const r of rows){
  if(good.length>=12||tested>=120)break;
  const pump=str(val(r,["pump_pool","pumpswap_pool","pump","pool"]));
  const b=str(val(r,["base_mint","base","pump_base_mint","token_base"]));
  const q=str(val(r,["quote_mint","quote","pump_quote_mint","token_quote"]));
  const mets=arr(r,["meteora_pools","meteora_pairs","meteora","lb_pairs"]);
  if(!pump||!b||!q||!mets.length)continue;
  if(b!==W&&q!==W)continue;
  eligible++;if(seen.has(pump))continue;seen.add(pump);tested++;
  try{
   const s=await on.swapSolanaState(new PublicKey(pump),SystemProgram.programId);
   const br=BigInt(s.poolBaseAmount.toString()),qr=BigInt(s.poolQuoteAmount.toString());
   const liveBase=s.pool.baseMint.toBase58(),liveQuote=s.pool.quoteMint.toBase58();
   if(liveBase!==b||liveQuote!==q){
    console.log(`[REJECT_MINT_MISMATCH] pump=${pump} row=${b}/${q} live=${liveBase}/${liveQuote}`);
    continue;
   }
   if(q===W&&qr>=100000000n&&br>1000n){
    const x={pump_pool:pump,base_mint:b,quote_mint:q,base_reserve:br.toString(),
     quote_reserve:qr.toString(),quote_sol:Number(qr)/1e9,meteora_pools:mets};
    good.push(x);
    console.log(`[FUNDED] pump=${pump} quote_sol=${x.quote_sol} base_raw=${br} meteora=${mets.length}`);
   }else if(b===W&&br>=100000000n&&qr>1000n){
    const x={pump_pool:pump,base_mint:b,quote_mint:q,base_reserve:br.toString(),
     quote_reserve:qr.toString(),base_sol:Number(br)/1e9,meteora_pools:mets};
    good.push(x);
    console.log(`[FUNDED] pump=${pump} base_sol=${x.base_sol} quote_raw=${qr} meteora=${mets.length}`);
   }else console.log(`[REJECT_DUST] pump=${pump} base_raw=${br} quote_raw=${qr}`);
  }catch(e){failed++;console.log(`[STATE_FAIL] pump=${pump} ${String(e.message).slice(0,120)}`)}
  await sleep(120);
 }
 fs.writeFileSync("mtr_057_funded_exact_pair_candidates.json",JSON.stringify(
  {schema:"MTR-057",rows:rows.length,eligible,tested,failed,funded:good.length,candidates:good,
   signing:false,sending:false},null,2));
 console.log(`[SUMMARY] rows=${rows.length} eligible=${eligible} tested=${tested} failed=${failed} funded=${good.length}`);
 if(!eligible)throw Error("NORMALIZED_SCHEMA_NOT_RESOLVED_TO_WSOL_ROWS");
 if(!good.length)throw Error("NO_FUNDED_PUMPSWAP_CANDIDATES_IN_BOUNDED_SCAN");
 console.log("[RESULT] FUNDED_EXACT_CROSS_VENUE_SET_FOUND");
 console.log("[NEXT_GATE] LIVE_MULTI_SIZE_BIDIRECTIONAL_ROUNDTRIP_ON_FUNDED_SET");
 console.log("[OUTPUT] mtr_057_funded_exact_pair_candidates.json");
 console.log("[MTR-057] COMPLETE");
})().catch(e=>{console.error("[MTR-057] FAIL");console.error(e.stack||e);process.exit(1)});
''', encoding="utf-8")

print(f"[BUILD] wrote {target}")
print("[BUILD] normalized-contract funded PumpSwap selector")
print("[SCOPE] no private key; no signing; no sending; canonical executor untouched")