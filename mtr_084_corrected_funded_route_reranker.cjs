const fs=require("fs");
const {Connection,PublicKey}=require("@solana/web3.js");
const BN=require("bn.js"),D=require("@meteora-ag/dlmm"),P=require("@pump-fun/pump-swap-sdk");
const DLMM=D.default||D.DLMM||D;
const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||
"https://api.mainnet-beta.solana.com";
const W=new PublicKey("So11111111111111111111111111111111111111112");
const USER=new PublicKey("CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR");
const SIZES=["1000000","2500000","5000000","10000000","20000000"].map(x=>new BN(x));
const c=new Connection(RPC,"confirmed"),Online=P.OnlinePumpAmmSdk,sdk=new Online(c);

function rows(x){
 if(Array.isArray(x))return x;
 for(const k of ["candidates","funded","rows","results","items"])
  if(Array.isArray(x?.[k]))return x[k];
 return[];
}
function pk(x){try{return new PublicKey(x)}catch{return null}}
function pools(r){
 const x=r.meteora_pools||r.meteoraPools||r.meteora||r.lb_pairs||r.lbPairs||[];
 return Array.isArray(x)?x.map(v=>typeof v==="string"?v:(v.address||v.pool||v.publicKey)).filter(Boolean):[];
}
function pumpKey(r){return r.pump_pool||r.pumpPool||r.pool||r.pump_pool_address}
function args(s,base){
 const {baseMint,baseMintAccount,feeConfig,globalConfig,pool,poolBaseAmount,poolQuoteAmount}=s;
 return {base,slippage:0,baseReserve:poolBaseAmount,quoteReserve:poolQuoteAmount,
  virtualQuoteReserves:pool.virtualQuoteReserves,globalConfig,baseMintAccount,baseMint,
  coinCreator:pool.coinCreator,creator:pool.creator,feeConfig,quoteMint:pool.quoteMint,
  isMayhemMode:pool.isMayhemMode,creatorFeeBps:pool.creatorFeeBps};
}
function buyArgs(s,quote){const a=args(s,new BN(0));delete a.base;a.quote=quote;return a}
function bps(final,input){return final.sub(input).mul(new BN(10000)).div(input)}

(async()=>{
 console.log("[MTR-084] START");
 console.log("[SCOPE] corrected funded exact-pair rerank; read-only");
 const file="mtr_057_funded_exact_pair_candidates.json";
 if(!fs.existsSync(file))throw Error("MTR_057_FUNDED_SET_NOT_FOUND");
 const R=rows(JSON.parse(fs.readFileSync(file,"utf8")));
 console.log(`[FUNDED_ROWS] ${R.length}`);
 let links=0,quotes=0,fail=0; const out=[];

 for(let i=0;i<R.length;i++){
  const r=R[i],pp=pk(pumpKey(r)); if(!pp)continue;
  let s;
  try{s=await sdk.swapSolanaState(pp,USER)}catch(e){fail++;continue}
  const base=s.baseMint,quote=s.pool.quoteMint;
  if(!quote.equals(W))continue;

  for(const mp0 of pools(r)){
   links++; const mp=pk(mp0); if(!mp)continue;
   try{
    const m=await DLMM.create(c,mp),X=m.tokenX.mint.address,Y=m.tokenY.mint.address;
    if(!(X.equals(base)&&Y.equals(W))&&!(Y.equals(base)&&X.equals(W)))continue;

    const wToBase=W.equals(X),baseToW=base.equals(X);
    const binsM=await m.getBinArrayForSwap(wToBase);
    const binsP=await m.getBinArrayForSwap(baseToW);

    for(const input of SIZES){
     try{
      const mq=m.swapQuote(input,wToBase,new BN(100),binsM);
      const pq=P.sellBaseInput(args(s,new BN(mq.outAmount.toString())));
      const final=new BN(pq.uiQuote.toString()),g=final.sub(input),bp=bps(final,input);
      quotes++;
      out.push({direction:"METEORA_TO_PUMP",pump:pp.toBase58(),meteora:mp.toBase58(),
       size:input.toString(),middle:mq.outAmount.toString(),final:final.toString(),
       gross:g.toString(),bps:bp.toString()});
     }catch(e){fail++}

     try{
      const pq=P.buyQuoteInput(buyArgs(s,input));
      const mid=new BN(pq.base.toString());
      const mq=m.swapQuote(mid,baseToW,new BN(100),binsP);
      const final=new BN(mq.outAmount.toString()),g=final.sub(input),bp=bps(final,input);
      quotes++;
      out.push({direction:"PUMP_TO_METEORA",pump:pp.toBase58(),meteora:mp.toBase58(),
       size:input.toString(),middle:mid.toString(),final:final.toString(),
       gross:g.toString(),bps:bp.toString()});
     }catch(e){fail++}
    }
   }catch(e){fail++}
  }
  console.log(`[PROGRESS] candidate=${i+1}/${R.length} links=${links} quotes=${quotes} failures=${fail}`);
 }

 out.sort((a,b)=>BigInt(a.gross)>BigInt(b.gross)?-1:BigInt(a.gross)<BigInt(b.gross)?1:0);
 const positive=out.filter(x=>BigInt(x.gross)>0n);
 fs.writeFileSync("mtr_084_corrected_funded_route_ranking.json",
  JSON.stringify({links,quotes,failures:fail,positive_count:positive.length,ranking:out},null,2));

 console.log(`[SUMMARY] links=${links} quotes=${quotes} failures=${fail} positive=${positive.length}`);
 for(const x of out.slice(0,20))
  console.log(`[TOP] dir=${x.direction} size=${x.size} bps=${x.bps} gross=${x.gross} pump=${x.pump} meteora=${x.meteora}`);

 console.log(positive.length?
  "[RESULT] CORRECTED_POSITIVE_FUNDED_ROUTES_FOUND":
  "[RESULT] NO_CORRECTED_POSITIVE_FUNDED_ROUTES");
 console.log("[OUTPUT] mtr_084_corrected_funded_route_ranking.json");
 console.log("[PRIVATE_KEY] NOT_USED");
 console.log("[BROADCAST] FALSE");
 console.log("[MTR-084] COMPLETE");
})().catch(e=>{console.error("[MTR-084] FAIL");console.error(e.stack||e);process.exit(1)});
