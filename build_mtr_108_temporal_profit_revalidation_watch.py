from pathlib import Path

p=Path("mtr_108_temporal_profit_revalidation_watch.cjs")
p.write_text(r'''const fs=require("fs");
const {Connection,PublicKey}=require("@solana/web3.js");
const BN=require("bn.js"),D=require("@meteora-ag/dlmm"),P=require("@pump-fun/pump-swap-sdk");
const DLMM=D.default||D.DLMM||D;
const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||
"https://api.mainnet-beta.solana.com";
const USER=new PublicKey("CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR");
const W=new PublicKey("So11111111111111111111111111111111111111112");
const INPUT=new BN("10000000"),FEE=new BN("5000"),CYCLES=10;
const c=new Connection(RPC,"confirmed"),sdk=new P.OnlinePumpAmmSdk(c);
const sleep=ms=>new Promise(r=>setTimeout(r,ms));

function sellArgs(s,base){
 const {baseMint,baseMintAccount,feeConfig,globalConfig,pool,poolBaseAmount,poolQuoteAmount}=s;
 return {base,slippage:0,baseReserve:poolBaseAmount,quoteReserve:poolQuoteAmount,
 virtualQuoteReserves:pool.virtualQuoteReserves,globalConfig,baseMintAccount,baseMint,
 coinCreator:pool.coinCreator,creator:pool.creator,feeConfig,quoteMint:pool.quoteMint,
 isMayhemMode:pool.isMayhemMode,creatorFeeBps:pool.creatorFeeBps};
}
function buyArgs(s,q){const a=sellArgs(s,new BN(0));delete a.base;a.quote=q;return a}
function bps(g){return g.mul(new BN(10000)).div(INPUT).toString()}

(async()=>{
 console.log("[MTR-108] START");
 console.log("[SCOPE] repeated fresh 0.010-SOL temporal revalidation");

 const j=JSON.parse(fs.readFileSync("mtr_106_deep_replenishment_exact_010_economics.json","utf8"));
 const rank=Array.isArray(j.ranking)?j.ranking:[];
 const seen=new Set(),routes=[];
 for(const r of rank){
  const k=`${r.direction}|${r.pump}|${r.meteora}`;
  if(seen.has(k))continue;
  seen.add(k);routes.push({direction:r.direction,pump:r.pump,meteora:r.meteora});
  if(routes.length===6)break;
 }

 console.log(`[ROUTES] ${routes.length}`);
 const rows=[],streak=new Map();

 for(let cycle=1;cycle<=CYCLES;cycle++){
  console.log(`[CYCLE] ${cycle}/${CYCLES} start=${new Date().toISOString()}`);

  for(const r of routes){
   const key=`${r.direction}|${r.pump}|${r.meteora}`;
   try{
    const s=await sdk.swapSolanaState(new PublicKey(r.pump),USER);
    if(!s.pool.quoteMint.equals(W))throw Error("QUOTE_NOT_WSOL");

    const m=await DLMM.create(c,new PublicKey(r.meteora));
    const X=m.tokenX.mint.address,Y=m.tokenY.mint.address,base=s.baseMint;
    if(!((X.equals(base)&&Y.equals(W))||(Y.equals(base)&&X.equals(W))))
      throw Error("PAIR_MISMATCH");

    let mid,final;
    if(r.direction==="METEORA_TO_PUMP"){
     const dir=W.equals(X),bins=await m.getBinArrayForSwap(dir);
     mid=new BN(m.swapQuote(INPUT,dir,new BN(100),bins).outAmount.toString());
     final=new BN(P.sellBaseInput(sellArgs(s,mid)).uiQuote.toString());
    }else{
     mid=new BN(P.buyQuoteInput(buyArgs(s,INPUT)).base.toString());
     const dir=base.equals(X),bins=await m.getBinArrayForSwap(dir);
     final=new BN(m.swapQuote(mid,dir,new BN(100),bins).outAmount.toString());
    }

    const gross=final.sub(INPUT),net=gross.sub(FEE);
    const old=streak.get(key)||0,now=net.gt(new BN(0))?old+1:0;
    streak.set(key,now);

    rows.push({cycle,time:new Date().toISOString(),...r,
      gross:gross.toString(),gross_bps:bps(gross),
      net_ref:net.toString(),net_ref_bps:bps(net),streak:now});

    console.log(`[QUOTE] cycle=${cycle} dir=${r.direction} gross_bps=${bps(gross)} net=${net} streak=${now} pump=${r.pump} meteora=${r.meteora}`);

    if(now>=2)
      console.log(`[PERSISTENT_NET_POSITIVE] streak=${now} dir=${r.direction} net=${net} pump=${r.pump} meteora=${r.meteora}`);
   }catch(e){
    streak.set(key,0);
    rows.push({cycle,time:new Date().toISOString(),...r,hold:String(e.message||e)});
    console.log(`[HOLD] cycle=${cycle} dir=${r.direction} reason=${String(e.message||e).slice(0,100)}`);
   }

   await sleep(800);
  }

  fs.writeFileSync("mtr_108_temporal_profit_revalidation_watch.json",
   JSON.stringify({cycles_complete:cycle,routes:routes.length,rows},null,2));

  if(cycle<CYCLES)await sleep(3000);
 }

 const netPos=rows.filter(r=>r.net_ref!==undefined&&BigInt(r.net_ref)>0n);
 const persistent=rows.filter(r=>Number(r.streak)>=2);

 console.log(`[SUMMARY] cycles=${CYCLES} observations=${rows.length} net_positive=${netPos.length} persistent=${persistent.length}`);
 console.log(persistent.length?
  "[RESULT] TEMPORALLY_PERSISTENT_NET_POSITIVE_FOUND":
  "[RESULT] NO_TEMPORALLY_PERSISTENT_NET_POSITIVE");
 console.log("[NOTE] 5000 lamports remains historical fee reference; exact atomic fee not yet certified");
 console.log("[OUTPUT] mtr_108_temporal_profit_revalidation_watch.json");
 console.log("[PRIVATE_KEY] NOT_USED");
 console.log("[BROADCAST] FALSE");
 console.log("[MTR-108] COMPLETE");
})().catch(e=>{console.error("[MTR-108] FAIL");console.error(e.stack||e);process.exit(1)});
''',encoding="utf-8")

print(f"[BUILD] wrote {p}")
print("[BUILD] temporal exact-profit revalidation watch")
print("[SCOPE] top fresh routes; repeated exact quotes; no signing; no sending")