const fs=require("fs");
const {Connection,PublicKey}=require("@solana/web3.js");
const BN=require("bn.js"),D=require("@meteora-ag/dlmm"),P=require("@pump-fun/pump-swap-sdk");
const DLMM=D.default||D.DLMM||D;
const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||
"https://api.mainnet-beta.solana.com";
const W=new PublicKey("So11111111111111111111111111111111111111112");
const USER=new PublicKey("CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR");
const INPUT=new BN("10000000");
const c=new Connection(RPC,"confirmed"),sdk=new P.OnlinePumpAmmSdk(c);
const sleep=ms=>new Promise(r=>setTimeout(r,ms));

function rows(x){
 if(Array.isArray(x))return x;
 for(const k of ["candidates","funded","rows","results","items"])
  if(Array.isArray(x?.[k]))return x[k];
 return[];
}
function poolList(r){
 const x=r.meteora_pools||r.meteoraPools||r.meteora||[];
 return Array.isArray(x)?x.map(v=>typeof v==="string"?v:(v.address||v.pool||v.publicKey)).filter(Boolean):[];
}
function pumpKey(r){return r.pump_pool||r.pumpPool||r.pool||r.pump_pool_address}
function sellArgs(s,base){
 const {baseMint,baseMintAccount,feeConfig,globalConfig,pool,poolBaseAmount,poolQuoteAmount}=s;
 return {base,slippage:0,baseReserve:poolBaseAmount,quoteReserve:poolQuoteAmount,
  virtualQuoteReserves:pool.virtualQuoteReserves,globalConfig,baseMintAccount,baseMint,
  coinCreator:pool.coinCreator,creator:pool.creator,feeConfig,quoteMint:pool.quoteMint,
  isMayhemMode:pool.isMayhemMode,creatorFeeBps:pool.creatorFeeBps};
}
function buyArgs(s,quote){const a=sellArgs(s,new BN(0));delete a.base;a.quote=quote;return a}
function bp(final){return final.sub(INPUT).mul(new BN(10000)).div(INPUT)}

(async()=>{
 console.log("[MTR-085] START");
 console.log("[SCOPE] rate-bounded corrected 0.010 SOL funded route scan");

 const src="mtr_057_funded_exact_pair_candidates.json";
 if(!fs.existsSync(src))throw Error("MTR_057_FUNDED_SET_NOT_FOUND");
 const R=rows(JSON.parse(fs.readFileSync(src,"utf8")));
 console.log(`[FUNDED_ROWS] ${R.length}`);

 let links=0,quotes=0,failures=0;
 const out=[];

 for(let i=0;i<R.length;i++){
  const pp=new PublicKey(pumpKey(R[i]));
  let s;
  try{s=await sdk.swapSolanaState(pp,USER)}
  catch(e){failures++;console.log(`[PUMP_HOLD] ${pp.toBase58()}`);await sleep(1500);continue}

  if(!s.pool.quoteMint.equals(W)){await sleep(500);continue}
  const base=s.baseMint;

  for(const mp0 of poolList(R[i])){
   links++;
   try{
    const mp=new PublicKey(mp0);
    const m=await DLMM.create(c,mp);
    const X=m.tokenX.mint.address,Y=m.tokenY.mint.address;
    if(!((X.equals(base)&&Y.equals(W))||(Y.equals(base)&&X.equals(W))))continue;

    const wToBase=W.equals(X);
    const bins1=await m.getBinArrayForSwap(wToBase);
    const mq=m.swapQuote(INPUT,wToBase,new BN(100),bins1);
    const ps=P.sellBaseInput(sellArgs(s,new BN(mq.outAmount.toString())));
    const f1=new BN(ps.uiQuote.toString());
    out.push({direction:"METEORA_TO_PUMP",pump:pp.toBase58(),meteora:mp.toBase58(),
      final:f1.toString(),gross:f1.sub(INPUT).toString(),bps:bp(f1).toString()});
    quotes++;

    const pq=P.buyQuoteInput(buyArgs(s,INPUT));
    const baseIn=new BN(pq.base.toString());
    const baseToW=base.equals(X);
    const bins2=await m.getBinArrayForSwap(baseToW);
    const mq2=m.swapQuote(baseIn,baseToW,new BN(100),bins2);
    const f2=new BN(mq2.outAmount.toString());
    out.push({direction:"PUMP_TO_METEORA",pump:pp.toBase58(),meteora:mp.toBase58(),
      final:f2.toString(),gross:f2.sub(INPUT).toString(),bps:bp(f2).toString()});
    quotes++;
   }catch(e){
    failures++;
    console.log(`[LINK_HOLD] ${mp0} ${String(e.message||e).slice(0,100)}`);
   }
   await sleep(750);
  }

  console.log(`[PROGRESS] ${i+1}/${R.length} links=${links} quotes=${quotes} failures=${failures}`);
  await sleep(1200);
 }

 out.sort((a,b)=>BigInt(a.gross)>BigInt(b.gross)?-1:BigInt(a.gross)<BigInt(b.gross)?1:0);
 const positive=out.filter(x=>BigInt(x.gross)>0n);

 fs.writeFileSync("mtr_085_rate_bounded_corrected_routes.json",
  JSON.stringify({links,quotes,failures,positive_count:positive.length,ranking:out},null,2));

 console.log(`[SUMMARY] links=${links} quotes=${quotes} failures=${failures} positive=${positive.length}`);
 for(const x of out.slice(0,15))
  console.log(`[TOP] dir=${x.direction} bps=${x.bps} gross=${x.gross} pump=${x.pump} meteora=${x.meteora}`);

 console.log(positive.length?
  "[RESULT] CORRECTED_POSITIVE_010_ROUTES_FOUND":
  "[RESULT] NO_CORRECTED_POSITIVE_010_ROUTES");
 console.log("[OUTPUT] mtr_085_rate_bounded_corrected_routes.json");
 console.log("[PRIVATE_KEY] NOT_USED");
 console.log("[BROADCAST] FALSE");
 console.log("[MTR-085] COMPLETE");
})().catch(e=>{console.error("[MTR-085] FAIL");console.error(e.stack||e);process.exit(1)});
