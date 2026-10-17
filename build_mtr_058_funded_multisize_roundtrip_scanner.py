from pathlib import Path
target=Path("mtr_058_funded_multisize_roundtrip_scanner.cjs")
target.write_text(r"""const fs=require("fs"),{Connection,PublicKey,SystemProgram}=require("@solana/web3.js"),BN=require("bn.js");
const P=require("@pump-fun/pump-swap-sdk"),D=require("@meteora-ag/dlmm"),DLMM=D.default||D.DLMM||D;
const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||"https://api.mainnet-beta.solana.com";
const W="So11111111111111111111111111111111111111112",c=new Connection(RPC,"confirmed"),sleep=ms=>new Promise(r=>setTimeout(r,ms));
const sizes=["1000000","2500000","5000000","10000000"].map(x=>new BN(x));
const V=x=>x&&x.toString?x.toString():String(x);
async function mq(pool,amt,inMint){const x=pool.tokenX.mint.address.toBase58(),y=pool.tokenY.mint.address.toBase58();
 const y2x=inMint===y,bins=await pool.getBinArrayForSwap(y2x);return pool.swapQuote(amt,y2x,new BN(50),bins).outAmount}
(async()=>{
 console.log("[MTR-058] START");console.log("[SCOPE] funded exact-pair multi-size live economics; no signing; no sending");
 const d=JSON.parse(fs.readFileSync("mtr_057_funded_exact_pair_candidates.json","utf8")),rows=d.candidates||[];
 if(!rows.length)throw Error("NO_MTR057_CANDIDATES");const on=new P.OnlinePumpAmmSdk(c),out=[];let links=0,quotes=0;
 for(const r of rows){const s=await on.swapSolanaState(new PublicKey(r.pump_pool),SystemProgram.programId);
  const bm=s.pool.baseMint.toBase58(),qm=s.pool.quoteMint.toBase58();if(qm!==W){console.log(`[SKIP_ORIENTATION] ${r.pump_pool}`);continue}
  const common={slippage:0,baseReserve:s.poolBaseAmount,quoteReserve:s.poolQuoteAmount,virtualQuoteReserves:s.pool.virtualQuoteReserves,
   globalConfig:s.globalConfig,baseMintAccount:s.baseMintAccount,baseMint:s.pool.baseMint,coinCreator:s.pool.coinCreator,creator:s.pool.creator,
   feeConfig:s.feeConfig,quoteMint:s.pool.quoteMint,isMayhemMode:s.pool.isMayhemMode,creatorFeeBps:s.pool.creatorFeeBps};
  for(const mp of r.meteora_pools.slice(0,12)){let m;try{m=await DLMM.create(c,new PublicKey(mp))}catch(e){continue}links++;
   for(const z of sizes){try{
    const b=P.buyQuoteInput({...common,quote:z}),f=await mq(m,b.base,bm),g=f.sub(z),bp=Number(g.muln(10000).div(z));
    out.push({pump:r.pump_pool,meteora:mp,direction:"PUMP_TO_METEORA",input:z.toString(),mid:V(b.base),final:V(f),gross_raw:V(g),gross_bps:bp});quotes++;
    if(bp>0)console.log(`[POSITIVE] dir=P2M size=${z} bps=${bp} pump=${r.pump_pool} meteora=${mp}`);
   }catch(e){}
   try{
    const mid=await mq(m,z,W),q=P.sellBaseInput({...common,base:mid}),f=q.uiQuote,g=f.sub(z),bp=Number(g.muln(10000).div(z));
    out.push({pump:r.pump_pool,meteora:mp,direction:"METEORA_TO_PUMP",input:z.toString(),mid:V(mid),final:V(f),gross_raw:V(g),gross_bps:bp});quotes++;
    if(bp>0)console.log(`[POSITIVE] dir=M2P size=${z} bps=${bp} pump=${r.pump_pool} meteora=${mp}`);
   }catch(e){}}
   await sleep(80);
  }}
 out.sort((a,b)=>b.gross_bps-a.gross_bps);out.slice(0,20).forEach((x,i)=>console.log(`[RANK ${i+1}] dir=${x.direction} size=${x.input} bps=${x.gross_bps} final=${x.final} pump=${x.pump} meteora=${x.meteora}`));
 const pos=out.filter(x=>BigInt(x.gross_raw)>0n);
 fs.writeFileSync("mtr_058_funded_multisize_ranking.json",JSON.stringify({schema:"MTR-058",links,quotes,positive:pos.length,routes:out,signing:false,sending:false},null,2));
 console.log(`[SUMMARY] candidates=${rows.length} links=${links} quotes=${quotes} positive=${pos.length} best_bps=${out.length?out[0].gross_bps:"NA"}`);
 console.log(pos.length?"[RESULT] POSITIVE_FUNDED_EXACT_ROUTES_FOUND":"[RESULT] NO_POSITIVE_FUNDED_ROUTES_IN_BOUNDED_SCAN");
 console.log("[NEXT_GATE] FRESH_FEE_ADJUSTED_TOP_ROUTE_PROOF");console.log("[OUTPUT] mtr_058_funded_multisize_ranking.json");console.log("[MTR-058] COMPLETE");
})().catch(e=>{console.error("[MTR-058] FAIL");console.error(e.stack||e);process.exit(1)});
""",encoding="utf-8")
print(f"[BUILD] wrote {target}")
print("[BUILD] funded exact-pair bidirectional 0.001/0.0025/0.005/0.010 SOL scanner")
print("[SCOPE] no private key; no signing; no sending; canonical executor untouched")