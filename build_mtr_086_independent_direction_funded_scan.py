from pathlib import Path

p=Path("mtr_086_independent_direction_funded_scan.cjs")
p.write_text(r'''const fs=require("fs");
const {Connection,PublicKey}=require("@solana/web3.js");
const BN=require("bn.js"),D=require("@meteora-ag/dlmm"),P=require("@pump-fun/pump-swap-sdk");
const DLMM=D.default||D.DLMM||D;
const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||
"https://api.mainnet-beta.solana.com";
const W=new PublicKey("So11111111111111111111111111111111111111112");
const USER=new PublicKey("CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR");
const INPUT=new BN("10000000"),c=new Connection(RPC,"confirmed");
const sdk=new P.OnlinePumpAmmSdk(c),sleep=ms=>new Promise(r=>setTimeout(r,ms));

function rows(x){if(Array.isArray(x))return x;for(const k of
 ["candidates","funded","rows","results","items"])if(Array.isArray(x?.[k]))return x[k];return[]}
function pp(r){return r.pump_pool||r.pumpPool||r.pool||r.pump_pool_address}
function mets(r){const x=r.meteora_pools||r.meteoraPools||r.meteora||[];
 return Array.isArray(x)?x.map(v=>typeof v==="string"?v:(v.address||v.pool||v.publicKey)).filter(Boolean):[]}
function sellArgs(s,base){const {baseMint,baseMintAccount,feeConfig,globalConfig,pool,
 poolBaseAmount,poolQuoteAmount}=s;return{base,slippage:0,baseReserve:poolBaseAmount,
 quoteReserve:poolQuoteAmount,virtualQuoteReserves:pool.virtualQuoteReserves,globalConfig,
 baseMintAccount,baseMint,coinCreator:pool.coinCreator,creator:pool.creator,feeConfig,
 quoteMint:pool.quoteMint,isMayhemMode:pool.isMayhemMode,creatorFeeBps:pool.creatorFeeBps}}
function buyArgs(s,quote){const a=sellArgs(s,new BN(0));delete a.base;a.quote=quote;return a}
function bps(final){return final.sub(INPUT).mul(new BN(10000)).div(INPUT)}
function save(out,stats){
 out.sort((a,b)=>BigInt(a.gross)>BigInt(b.gross)?-1:BigInt(a.gross)<BigInt(b.gross)?1:0);
 fs.writeFileSync("mtr_086_independent_direction_routes.json",
  JSON.stringify({...stats,positive_count:out.filter(x=>BigInt(x.gross)>0n).length,ranking:out},null,2));
}

(async()=>{
 console.log("[MTR-086] START");
 console.log("[SCOPE] independent corrected 0.010 SOL direction scan");
 const src="mtr_057_funded_exact_pair_candidates.json";
 if(!fs.existsSync(src))throw Error("MTR_057_FUNDED_SET_NOT_FOUND");
 const R=rows(JSON.parse(fs.readFileSync(src,"utf8")));
 console.log(`[FUNDED_ROWS] ${R.length}`);
 const out=[];let links=0,m2p=0,p2m=0,holds=0;

 for(let i=0;i<R.length;i++){
  const pump=new PublicKey(pp(R[i]));let s;
  try{s=await sdk.swapSolanaState(pump,USER)}
  catch(e){holds++;console.log(`[PUMP_HOLD] ${pump}`);await sleep(1200);continue}
  if(!s.pool.quoteMint.equals(W)){console.log(`[SKIP_NON_WSOL] ${pump}`);continue}
  const base=s.baseMint;

  for(const ms of mets(R[i])){
   links++;let m,X,Y;
   try{
    m=await DLMM.create(c,new PublicKey(ms));
    X=m.tokenX.mint.address;Y=m.tokenY.mint.address;
    if(!((X.equals(base)&&Y.equals(W))||(Y.equals(base)&&X.equals(W))))continue;
   }catch(e){holds++;console.log(`[POOL_HOLD] ${ms} ${String(e.message||e).slice(0,90)}`);continue}

   try{
    const wToBase=W.equals(X);
    const bins=await m.getBinArrayForSwap(wToBase);
    const mq=m.swapQuote(INPUT,wToBase,new BN(100),bins);
    const pq=P.sellBaseInput(sellArgs(s,new BN(mq.outAmount.toString())));
    const final=new BN(pq.uiQuote.toString());
    out.push({direction:"METEORA_TO_PUMP",pump:pump.toBase58(),meteora:ms,
     final:final.toString(),gross:final.sub(INPUT).toString(),bps:bps(final).toString()});
    m2p++;
    console.log(`[M2P] bps=${bps(final)} pump=${pump} meteora=${ms}`);
   }catch(e){
    holds++;
    console.log(`[M2P_HOLD] ${ms} ${String(e.message||e).slice(0,100)}`);
   }

   await sleep(500);

   try{
    const pq=P.buyQuoteInput(buyArgs(s,INPUT));
    const mid=new BN(pq.base.toString());
    const baseToW=base.equals(X);
    const bins=await m.getBinArrayForSwap(baseToW);
    const mq=m.swapQuote(mid,baseToW,new BN(100),bins);
    const final=new BN(mq.outAmount.toString());
    out.push({direction:"PUMP_TO_METEORA",pump:pump.toBase58(),meteora:ms,
     final:final.toString(),gross:final.sub(INPUT).toString(),bps:bps(final).toString()});
    p2m++;
    console.log(`[P2M] bps=${bps(final)} pump=${pump} meteora=${ms}`);
   }catch(e){
    holds++;
    console.log(`[P2M_HOLD] ${ms} ${String(e.message||e).slice(0,100)}`);
   }

   await sleep(700);
  }

  save(out,{links,m2p_quotes:m2p,p2m_quotes:p2m,holds});
  console.log(`[CHECKPOINT] candidate=${i+1}/${R.length} links=${links} m2p=${m2p} p2m=${p2m} holds=${holds}`);
  await sleep(1200);
 }

 save(out,{links,m2p_quotes:m2p,p2m_quotes:p2m,holds});
 const positive=out.filter(x=>BigInt(x.gross)>0n);
 console.log(`[SUMMARY] links=${links} m2p=${m2p} p2m=${p2m} holds=${holds} positive=${positive.length}`);
 out.sort((a,b)=>BigInt(a.gross)>BigInt(b.gross)?-1:BigInt(a.gross)<BigInt(b.gross)?1:0);
 for(const x of out.slice(0,15))
  console.log(`[TOP] dir=${x.direction} bps=${x.bps} gross=${x.gross} pump=${x.pump} meteora=${x.meteora}`);
 console.log(positive.length?"[RESULT] CORRECTED_POSITIVE_010_ROUTES_FOUND":
  "[RESULT] NO_CORRECTED_POSITIVE_010_ROUTES");
 console.log("[OUTPUT] mtr_086_independent_direction_routes.json");
 console.log("[PRIVATE_KEY] NOT_USED");
 console.log("[BROADCAST] FALSE");
 console.log("[MTR-086] COMPLETE");
})().catch(e=>{console.error("[MTR-086] FAIL");console.error(e.stack||e);process.exit(1)});
''',encoding="utf-8")

print(f"[BUILD] wrote {p}")
print("[BUILD] independent-direction corrected funded scanner")
print("[SCOPE] 0.010 SOL read-only pricing; no signing; no sending")