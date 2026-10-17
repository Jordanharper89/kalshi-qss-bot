from pathlib import Path

p=Path("mtr_112_bounded_event_reprice_queue.cjs")
p.write_text(r'''const fs=require("fs"),WebSocket=require("ws");
const {Connection,PublicKey}=require("@solana/web3.js");
const BN=require("bn.js"),D=require("@meteora-ag/dlmm"),P=require("@pump-fun/pump-swap-sdk");
const DLMM=D.default||D.DLMM||D;
const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||"https://api.mainnet-beta.solana.com";
const WS=process.env.QSB_SOLANA_WS_URL||RPC.replace(/^https:/,"wss:").replace(/^http:/,"ws:");
const USER=new PublicKey("CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR");
const W=new PublicKey("So11111111111111111111111111111111111111112");
const INPUT=new BN("10000000"),FEE=new BN("5000"),WATCH=60000,ROUTES=12,WORKERS=2;
const c=new Connection(RPC,"confirmed"),sdk=new P.OnlinePumpAmmSdk(c);
const sleep=m=>new Promise(r=>setTimeout(r,m)),bps=g=>g.mul(new BN(10000)).div(INPUT).toString();
function add(m,k,v){if(!m.has(k))m.set(k,[]);m.get(k).push(v)}
function sellArgs(s,base){const {baseMint,baseMintAccount,feeConfig,globalConfig,pool,poolBaseAmount,poolQuoteAmount}=s;
return {base,slippage:0,baseReserve:poolBaseAmount,quoteReserve:poolQuoteAmount,virtualQuoteReserves:pool.virtualQuoteReserves,
globalConfig,baseMintAccount,baseMint,coinCreator:pool.coinCreator,creator:pool.creator,feeConfig,quoteMint:pool.quoteMint,
isMayhemMode:pool.isMayhemMode,creatorFeeBps:pool.creatorFeeBps}}
function buyArgs(s,q){const a=sellArgs(s,new BN(0));delete a.base;a.quote=q;return a}

(async()=>{
 console.log("[MTR-112] START");
 console.log("[SCOPE] bounded coalesced event-driven exact repricing");

 const j105=JSON.parse(fs.readFileSync("mtr_105_ultra_hot_meteora_reserve_filter.json","utf8"));
 const j100=JSON.parse(fs.readFileSync("mtr_100_new_pool_physical_liquidity.json","utf8"));
 const pm=new Map((j100.rows||[]).map(r=>[r.pump_pool,r]));
 const deep=(j105.rows||[]).filter(r=>Number(r.meteora_wsol_sol)>=1)
  .sort((a,b)=>Number(b.meteora_wsol_sol)-Number(a.meteora_wsol_sol)).slice(0,ROUTES);

 const routeMap=new Map(),accountRoutes=new Map();
 for(const r of deep){const p=pm.get(r.pump_pool);if(!p?.quote_vault)continue;
  const key=`${r.pump_pool}|${r.meteora_pool}`,x={key,pump:r.pump_pool,meteora:r.meteora_pool};
  routeMap.set(key,x);add(accountRoutes,p.quote_vault,key);add(accountRoutes,r.wsol_reserve,key)}
 console.log(`[ROUTES] ${routeMap.size} [ACCOUNTS] ${accountRoutes.size}`);

 const queue=[],queued=new Set(),dirty=new Map(),rows=[];let active=0,accept=true,events=0,coalesced=0,holds=0,reprices=0,netpos=0;
 function enqueue(key,slot){dirty.set(key,slot);if(queued.has(key)){coalesced++;return}queued.add(key);queue.push(key);pump()}
 function pump(){while(active<WORKERS&&queue.length){const key=queue.shift();queued.delete(key);active++;price(key,dirty.get(key)).finally(()=>{active--;if(dirty.has(key)){dirty.delete(key)}pump()})}}
 async function price(key,slot){const r=routeMap.get(key),t=performance.now();try{
  const s=await sdk.swapSolanaState(new PublicKey(r.pump),USER),m=await DLMM.create(c,new PublicKey(r.meteora));
  const X=m.tokenX.mint.address,Y=m.tokenY.mint.address,base=s.baseMint;if(!((X.equals(base)&&Y.equals(W))||(Y.equals(base)&&X.equals(W))))throw Error("PAIR_MISMATCH");
  const qs=[];
  try{const d=W.equals(X),ba=await m.getBinArrayForSwap(d),mid=new BN(m.swapQuote(INPUT,d,new BN(100),ba).outAmount.toString());
   const fin=new BN(P.sellBaseInput(sellArgs(s,mid)).uiQuote.toString());qs.push(["M2P",fin.sub(INPUT)])}catch{holds++}
  try{const mid=new BN(P.buyQuoteInput(buyArgs(s,INPUT)).base.toString()),d=base.equals(X),ba=await m.getBinArrayForSwap(d);
   const fin=new BN(m.swapQuote(mid,d,new BN(100),ba).outAmount.toString());qs.push(["P2M",fin.sub(INPUT)])}catch{holds++}
  const ms=Math.round(performance.now()-t);for(const [dir,g] of qs){const n=g.sub(FEE);reprices++;if(n.gt(new BN(0)))netpos++;
   rows.push({slot,key,dir,gross:g.toString(),gross_bps:bps(g),net:n.toString(),latency_ms:ms});
   console.log(`[REPRICE] slot=${slot} latency_ms=${ms} dir=${dir} gross_bps=${bps(g)} net=${n} route=${key}`)}
 }catch(e){holds++;console.log(`[HOLD] slot=${slot} route=${key} reason=${String(e.message||e).slice(0,100)}`)}}

 const ws=new WebSocket(WS),pending=new Map(),subs=new Map();let id=1;
 ws.on("message",b=>{let m;try{m=JSON.parse(b)}catch{return}if(m.id&&pending.has(m.id)){const f=pending.get(m.id);pending.delete(m.id);return f(m)}
  if(accept&&m.method==="accountNotification"){const a=subs.get(String(m.params.subscription));if(!a)return;events++;
   for(const k of new Set(accountRoutes.get(a)||[]))enqueue(k,m.params.result.context.slot)}});

 await new Promise((res,rej)=>{ws.once("open",res);ws.once("error",rej)});
 async function sub(a){const n=id++,p=new Promise((res,rej)=>{const t=setTimeout(()=>rej(Error("SUB_TIMEOUT")),7000);
  pending.set(n,m=>{clearTimeout(t);res(m)})});ws.send(JSON.stringify({jsonrpc:"2.0",id:n,method:"accountSubscribe",params:[a,{encoding:"base64",commitment:"confirmed"}]}));
  const r=await p;if(r.error)throw Error(JSON.stringify(r.error));subs.set(String(r.result),a)}
 let ok=0,fail=0;for(const a of accountRoutes.keys()){try{await sub(a);ok++}catch{fail++}await sleep(250)}
 console.log(`[READY] subscriptions=${ok} failures=${fail} workers=${WORKERS}`);
 await sleep(WATCH);accept=false;console.log(`[DRAIN] events=${events} queued=${queue.length} active=${active} coalesced=${coalesced}`);
 while(queue.length||active)await sleep(250);

 fs.writeFileSync("mtr_112_bounded_event_reprice_queue.json",JSON.stringify({events,coalesced,reprices,holds,net_positive:netpos,rows},null,2));
 console.log(`[SUMMARY] events=${events} coalesced=${coalesced} reprices=${reprices} holds=${holds} net_positive=${netpos}`);
 console.log(netpos?"[RESULT] BOUNDED_EVENT_NET_POSITIVE_FOUND":"[RESULT] BOUNDED_EVENT_REPRICE_COMPLETE");
 console.log("[PRIVATE_KEY] NOT_USED");console.log("[BROADCAST] FALSE");console.log("[MTR-112] COMPLETE");ws.close();
})().catch(e=>{console.error("[MTR-112] FAIL");console.error(e.stack||e);process.exit(1)});
''',encoding="utf-8")

print(f"[BUILD] wrote {p}")
print("[BUILD] bounded coalesced event-driven repricing queue")
print("[SCOPE] 2 workers; route single-flight; full drain; no signing; no sending")