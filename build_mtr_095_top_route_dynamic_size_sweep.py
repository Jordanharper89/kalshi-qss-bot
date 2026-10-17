from pathlib import Path

p=Path("mtr_095_top_route_dynamic_size_sweep.cjs")
p.write_text(r'''const fs=require("fs");
const {Connection,PublicKey}=require("@solana/web3.js");
const BN=require("bn.js"),D=require("@meteora-ag/dlmm"),P=require("@pump-fun/pump-swap-sdk");
const DLMM=D.default||D.DLMM||D;
const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||
"https://api.mainnet-beta.solana.com";
const W=new PublicKey("So11111111111111111111111111111111111111112");
const USER=new PublicKey("CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR");
const SIZES=["1000000","2500000","5000000","10000000","20000000","30000000"].map(x=>new BN(x));
const FEE=new BN("5000");
const c=new Connection(RPC,"confirmed"),sdk=new P.OnlinePumpAmmSdk(c);
const sleep=ms=>new Promise(r=>setTimeout(r,ms));

function sellArgs(s,base){
 const {baseMint,baseMintAccount,feeConfig,globalConfig,pool,poolBaseAmount,poolQuoteAmount}=s;
 return {base,slippage:0,baseReserve:poolBaseAmount,quoteReserve:poolQuoteAmount,
 virtualQuoteReserves:pool.virtualQuoteReserves,globalConfig,baseMintAccount,baseMint,
 coinCreator:pool.coinCreator,creator:pool.creator,feeConfig,quoteMint:pool.quoteMint,
 isMayhemMode:pool.isMayhemMode,creatorFeeBps:pool.creatorFeeBps};
}
function buyArgs(s,quote){const a=sellArgs(s,new BN(0));delete a.base;a.quote=quote;return a}
function bp(x,input){return x.mul(new BN(10000)).div(input).toString()}

(async()=>{
 console.log("[MTR-095] START");
 console.log("[SCOPE] top corrected routes dynamic-size sweep");

 const src="mtr_094_survivor_010_exact_economics.json";
 if(!fs.existsSync(src))throw Error("MTR_094_RESULT_NOT_FOUND");
 const j=JSON.parse(fs.readFileSync(src,"utf8"));
 const ranking=(j.ranking||[]).slice().sort((a,b)=>
  BigInt(a.gross)>BigInt(b.gross)?-1:BigInt(a.gross)<BigInt(b.gross)?1:0);

 const chosen=[],seen=new Set();
 for(const r of ranking){
  const k=`${r.direction}|${r.pump}|${r.meteora}`;
  if(seen.has(k))continue;
  seen.add(k);chosen.push(r);
  if(chosen.length===12)break;
 }
 console.log(`[TOP_ROUTES] ${chosen.length}`);

 const states=new Map(),out=[];let holds=0;

 for(let i=0;i<chosen.length;i++){
  const r=chosen[i];
  let s=states.get(r.pump);
  if(!s){
   s=await sdk.swapSolanaState(new PublicKey(r.pump),USER);
   states.set(r.pump,s);await sleep(500);
  }
  const m=await DLMM.create(c,new PublicKey(r.meteora));
  const X=m.tokenX.mint.address,Y=m.tokenY.mint.address,base=s.baseMint;
  if(!((X.equals(base)&&Y.equals(W))||(Y.equals(base)&&X.equals(W))))continue;

  for(const input of SIZES){
   try{
    let final,mid;
    if(r.direction==="METEORA_TO_PUMP"){
     const dir=W.equals(X),bins=await m.getBinArrayForSwap(dir);
     const mq=m.swapQuote(input,dir,new BN(100),bins);
     mid=new BN(mq.outAmount.toString());
     const pq=P.sellBaseInput(sellArgs(s,mid));
     final=new BN(pq.uiQuote.toString());
    }else{
     const pq=P.buyQuoteInput(buyArgs(s,input));
     mid=new BN(pq.base.toString());
     const dir=base.equals(X),bins=await m.getBinArrayForSwap(dir);
     const mq=m.swapQuote(mid,dir,new BN(100),bins);
     final=new BN(mq.outAmount.toString());
    }

    const gross=final.sub(input),net=gross.sub(FEE);
    const row={direction:r.direction,pump:r.pump,meteora:r.meteora,
     input:input.toString(),middle:mid.toString(),final:final.toString(),
     gross:gross.toString(),gross_bps:bp(gross,input),
     net_ref:net.toString(),net_ref_bps:bp(net,input)};
    out.push(row);

    if(net.gt(new BN(0)))
     console.log(`[POSITIVE] route=${i+1} dir=${r.direction} size=${input} gross_bps=${row.gross_bps} net_bps=${row.net_ref_bps}`);
   }catch(e){
    holds++;
    console.log(`[HOLD] route=${i+1} dir=${r.direction} size=${input} ${String(e.message||e).slice(0,80)}`);
   }
   await sleep(350);
  }
  console.log(`[ROUTE_DONE] ${i+1}/${chosen.length} quotes=${out.length} holds=${holds}`);
  await sleep(700);
 }

 out.sort((a,b)=>BigInt(a.net_ref)>BigInt(b.net_ref)?-1:BigInt(a.net_ref)<BigInt(b.net_ref)?1:0);
 const pos=out.filter(x=>BigInt(x.net_ref)>0n);

 fs.writeFileSync("mtr_095_top_route_dynamic_size_sweep.json",
  JSON.stringify({routes:chosen.length,quotes:out.length,holds,positive:pos.length,ranking:out},null,2));

 console.log(`[SUMMARY] routes=${chosen.length} quotes=${out.length} positive=${pos.length} holds=${holds}`);
 for(const x of out.slice(0,15))
  console.log(`[TOP] dir=${x.direction} size=${x.input} gross_bps=${x.gross_bps} net_bps=${x.net_ref_bps} pump=${x.pump} meteora=${x.meteora}`);

 console.log(pos.length?"[RESULT] DYNAMIC_SIZE_POSITIVE_FOUND":
 "[RESULT] CURRENT_INVENTORY_DYNAMIC_SIZE_NOT_POSITIVE");
 console.log("[NOTE] 5000 lamports remains fee reference; exact atomic fee not yet certified");
 console.log("[PRIVATE_KEY] NOT_USED");
 console.log("[BROADCAST] FALSE");
 console.log("[MTR-095] COMPLETE");
})().catch(e=>{console.error("[MTR-095] FAIL");console.error(e.stack||e);process.exit(1)});
''',encoding="utf-8")

print(f"[BUILD] wrote {p}")
print("[BUILD] top corrected route dynamic-size sweep")
print("[SCOPE] 12 strongest routes; no signing; no sending")