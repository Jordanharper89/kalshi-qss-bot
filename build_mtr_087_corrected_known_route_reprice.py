from pathlib import Path

p=Path("mtr_087_corrected_known_route_reprice.cjs")
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

function field(o,names){for(const n of names)if(typeof o?.[n]==="string")return o[n]}
function collect(x,out){
 if(Array.isArray(x)){for(const v of x)collect(v,out);return}
 if(!x||typeof x!=="object")return;
 const pump=field(x,["pump","pump_pool","pumpPool","pump_pool_address"]);
 const met=field(x,["meteora","meteora_pool","meteoraPool","lb_pair","lbPair"]);
 if(pump&&met)out.set(pump+"|"+met,{pump,meteora:met});
 for(const v of Object.values(x))if(v&&typeof v==="object")collect(v,out);
}
function sellArgs(s,base){
 const {baseMint,baseMintAccount,feeConfig,globalConfig,pool,poolBaseAmount,poolQuoteAmount}=s;
 return {base,slippage:0,baseReserve:poolBaseAmount,quoteReserve:poolQuoteAmount,
  virtualQuoteReserves:pool.virtualQuoteReserves,globalConfig,baseMintAccount,baseMint,
  coinCreator:pool.coinCreator,creator:pool.creator,feeConfig,quoteMint:pool.quoteMint,
  isMayhemMode:pool.isMayhemMode,creatorFeeBps:pool.creatorFeeBps};
}
function buyArgs(s,quote){const a=sellArgs(s,new BN(0));delete a.base;a.quote=quote;return a}
function bp(final){return final.sub(INPUT).mul(new BN(10000)).div(INPUT)}
function save(out,done,holds){
 out.sort((a,b)=>BigInt(a.gross)>BigInt(b.gross)?-1:BigInt(a.gross)<BigInt(b.gross)?1:0);
 fs.writeFileSync("mtr_087_corrected_known_routes.json",
  JSON.stringify({done,holds,positive_count:out.filter(x=>BigInt(x.gross)>0n).length,ranking:out},null,2));
}

(async()=>{
 console.log("[MTR-087] START");
 console.log("[SCOPE] corrected repricing of previously discovered route links");

 const src="mtr_058_funded_multisize_ranking.json";
 if(!fs.existsSync(src))throw Error("MTR_058_RANKING_NOT_FOUND");
 const links=new Map();
 collect(JSON.parse(fs.readFileSync(src,"utf8")),links);
 const L=[...links.values()];
 console.log(`[KNOWN_UNIQUE_LINKS] ${L.length}`);
 if(!L.length)throw Error("NO_ROUTE_LINKS_EXTRACTED");

 const states=new Map(),out=[];let done=0,holds=0;

 for(const r of L){
  try{
   let s=states.get(r.pump);
   if(!s){s=await sdk.swapSolanaState(new PublicKey(r.pump),USER);states.set(r.pump,s);await sleep(500)}
   if(!s.pool.quoteMint.equals(W))continue;

   const m=await DLMM.create(c,new PublicKey(r.meteora));
   const X=m.tokenX.mint.address,Y=m.tokenY.mint.address,base=s.baseMint;
   if(!((X.equals(base)&&Y.equals(W))||(Y.equals(base)&&X.equals(W))))continue;

   try{
    const wToBase=W.equals(X);
    const bins=await m.getBinArrayForSwap(wToBase);
    const mq=m.swapQuote(INPUT,wToBase,new BN(100),bins);
    const pq=P.sellBaseInput(sellArgs(s,new BN(mq.outAmount.toString())));
    const f=new BN(pq.uiQuote.toString());
    out.push({direction:"METEORA_TO_PUMP",pump:r.pump,meteora:r.meteora,
      final:f.toString(),gross:f.sub(INPUT).toString(),bps:bp(f).toString()});
   }catch(e){holds++}

   try{
    const pq=P.buyQuoteInput(buyArgs(s,INPUT));
    const mid=new BN(pq.base.toString()),baseToW=base.equals(X);
    const bins=await m.getBinArrayForSwap(baseToW);
    const mq=m.swapQuote(mid,baseToW,new BN(100),bins);
    const f=new BN(mq.outAmount.toString());
    out.push({direction:"PUMP_TO_METEORA",pump:r.pump,meteora:r.meteora,
      final:f.toString(),gross:f.sub(INPUT).toString(),bps:bp(f).toString()});
   }catch(e){holds++}

   done++;
   if(done%10===0){
    save(out,done,holds);
    const pos=out.filter(x=>BigInt(x.gross)>0n).length;
    console.log(`[CHECKPOINT] done=${done}/${L.length} quotes=${out.length} positive=${pos} holds=${holds}`);
   }
  }catch(e){
   holds++;
   console.log(`[LINK_HOLD] pump=${r.pump} meteora=${r.meteora} ${String(e.message||e).slice(0,90)}`);
  }
  await sleep(750);
 }

 save(out,done,holds);
 out.sort((a,b)=>BigInt(a.gross)>BigInt(b.gross)?-1:BigInt(a.gross)<BigInt(b.gross)?1:0);
 const pos=out.filter(x=>BigInt(x.gross)>0n);
 console.log(`[SUMMARY] links=${L.length} done=${done} quotes=${out.length} positive=${pos.length} holds=${holds}`);
 for(const x of out.slice(0,15))
  console.log(`[TOP] dir=${x.direction} bps=${x.bps} gross=${x.gross} pump=${x.pump} meteora=${x.meteora}`);
 console.log(pos.length?"[RESULT] CORRECTED_KNOWN_POSITIVE_ROUTES_FOUND":
  "[RESULT] NO_CORRECTED_KNOWN_POSITIVE_ROUTES");
 console.log("[OUTPUT] mtr_087_corrected_known_routes.json");
 console.log("[PRIVATE_KEY] NOT_USED");
 console.log("[BROADCAST] FALSE");
 console.log("[MTR-087] COMPLETE");
})().catch(e=>{console.error("[MTR-087] FAIL");console.error(e.stack||e);process.exit(1)});
''',encoding="utf-8")

print(f"[BUILD] wrote {p}")
print("[BUILD] corrected known-route repricer")
print("[SCOPE] 0.010 SOL read-only repricing; no signing; no sending")