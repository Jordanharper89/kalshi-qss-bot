from pathlib import Path

p=Path("mtr_107_fresh_top_route_size_sweep.cjs")
p.write_text(r'''const fs=require("fs");
const {Connection,PublicKey}=require("@solana/web3.js");
const BN=require("bn.js"),D=require("@meteora-ag/dlmm"),P=require("@pump-fun/pump-swap-sdk");
const DLMM=D.default||D.DLMM||D;
const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||
"https://api.mainnet-beta.solana.com";
const USER=new PublicKey("CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR");
const W=new PublicKey("So11111111111111111111111111111111111111112");
const c=new Connection(RPC,"confirmed"),sdk=new P.OnlinePumpAmmSdk(c);
const FEE=new BN("5000"),SIZES=["1000000","2500000","5000000","10000000","20000000","30000000","50000000"];
const sleep=ms=>new Promise(r=>setTimeout(r,ms));

function sellArgs(s,base){
 const {baseMint,baseMintAccount,feeConfig,globalConfig,pool,poolBaseAmount,poolQuoteAmount}=s;
 return {base,slippage:0,baseReserve:poolBaseAmount,quoteReserve:poolQuoteAmount,
 virtualQuoteReserves:pool.virtualQuoteReserves,globalConfig,baseMintAccount,baseMint,
 coinCreator:pool.coinCreator,creator:pool.creator,feeConfig,quoteMint:pool.quoteMint,
 isMayhemMode:pool.isMayhemMode,creatorFeeBps:pool.creatorFeeBps};
}
function buyArgs(s,quote){const a=sellArgs(s,new BN(0));delete a.base;a.quote=quote;return a}
function bp(gross,input){return gross.mul(new BN(10000)).div(input).toString()}

(async()=>{
 console.log("[MTR-107] START");
 console.log("[SCOPE] fresh top-route dynamic size sweep; no signing; no sending");

 const src="mtr_106_deep_replenishment_exact_010_economics.json";
 if(!fs.existsSync(src))throw Error("MTR_106_NOT_FOUND");
 const j=JSON.parse(fs.readFileSync(src,"utf8"));
 const rank=Array.isArray(j.ranking)?j.ranking:[];

 const seen=new Set(),top=[];
 for(const r of rank){
  const k=`${r.direction}|${r.pump}|${r.meteora}`;
  if(seen.has(k))continue;
  seen.add(k);top.push(r);
  if(top.length===6)break;
 }

 console.log(`[ROUTES] ${top.length}`);
 const states=new Map(),markets=new Map(),out=[];
 let holds=0;

 for(let ri=0;ri<top.length;ri++){
  const r=top[ri];
  let s=states.get(r.pump);
  if(!s){
   s=await sdk.swapSolanaState(new PublicKey(r.pump),USER);
   states.set(r.pump,s);
   await sleep(700);
  }
  if(!s.pool.quoteMint.equals(W)){holds++;continue}

  let m=markets.get(r.meteora);
  if(!m){
   m=await DLMM.create(c,new PublicKey(r.meteora));
   markets.set(r.meteora,m);
   await sleep(700);
  }

  const X=m.tokenX.mint.address,Y=m.tokenY.mint.address,base=s.baseMint;
  if(!((X.equals(base)&&Y.equals(W))||(Y.equals(base)&&X.equals(W)))){holds++;continue}

  for(const raw of SIZES){
   const input=new BN(raw);
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
     input:raw,middle:mid.toString(),final:final.toString(),
     gross:gross.toString(),gross_bps:bp(gross,input),
     net_ref:net.toString(),net_ref_bps:bp(net,input)};
    out.push(row);

    if(net.gt(new BN(0)))
     console.log(`[NET_POSITIVE] dir=${r.direction} size=${raw} gross_bps=${row.gross_bps} net=${net} pump=${r.pump} meteora=${r.meteora}`);
   }catch(e){holds++}

   await sleep(650);
  }

  console.log(`[ROUTE] ${ri+1}/${top.length} dir=${r.direction} pump=${r.pump} meteora=${r.meteora}`);
 }

 out.sort((a,b)=>BigInt(a.net_ref)>BigInt(b.net_ref)?-1:BigInt(a.net_ref)<BigInt(b.net_ref)?1:0);
 const pos=out.filter(x=>BigInt(x.net_ref)>0n);

 fs.writeFileSync("mtr_107_fresh_top_route_size_sweep.json",
  JSON.stringify({routes:top.length,quotes:out.length,net_positive:pos.length,holds,ranking:out},null,2));

 console.log(`[SUMMARY] routes=${top.length} quotes=${out.length} net_positive=${pos.length} holds=${holds}`);
 for(const x of out.slice(0,20))
  console.log(`[TOP] dir=${x.direction} size=${x.input} gross_bps=${x.gross_bps} net=${x.net_ref} net_bps=${x.net_ref_bps} pump=${x.pump} meteora=${x.meteora}`);

 console.log(pos.length?
  "[RESULT] FRESH_DYNAMIC_SIZE_NET_POSITIVE_FOUND":
  "[RESULT] FRESH_DYNAMIC_SIZE_NOT_NET_POSITIVE");
 console.log("[NOTE] 5000 lamports remains historical fee reference; exact atomic fee not yet certified");
 console.log("[OUTPUT] mtr_107_fresh_top_route_size_sweep.json");
 console.log("[PRIVATE_KEY] NOT_USED");
 console.log("[BROADCAST] FALSE");
 console.log("[MTR-107] COMPLETE");
})().catch(e=>{console.error("[MTR-107] FAIL");console.error(e.stack||e);process.exit(1)});
''',encoding="utf-8")

print(f"[BUILD] wrote {p}")
print("[BUILD] fresh top-route dynamic size sweep")
print("[SCOPE] top 6 MTR-106 route/directions; no signing; no sending")