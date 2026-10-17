const fs=require("fs");
const WebSocket=require("ws");
const {Connection,PublicKey}=require("@solana/web3.js");
const BN=require("bn.js"),D=require("@meteora-ag/dlmm"),P=require("@pump-fun/pump-swap-sdk");

const DLMM=D.default||D.DLMM||D;
const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||
"https://api.mainnet-beta.solana.com";
const WS=process.env.QSB_SOLANA_WS_URL||
RPC.replace(/^https:/,"wss:").replace(/^http:/,"ws:");

const USER=new PublicKey("CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR");
const W=new PublicKey("So11111111111111111111111111111111111111112");
const INPUT=new BN("10000000"),FEE=new BN("5000");
const WATCH_MS=60000,ROUTES=12,DEBOUNCE_MS=400;

const c=new Connection(RPC,"confirmed");
const sdk=new P.OnlinePumpAmmSdk(c);

function sleep(ms){return new Promise(r=>setTimeout(r,ms))}
function add(m,k,v){if(!m.has(k))m.set(k,[]);m.get(k).push(v)}
function bps(g){return g.mul(new BN(10000)).div(INPUT).toString()}

function sellArgs(s,base){
 const {baseMint,baseMintAccount,feeConfig,globalConfig,pool,poolBaseAmount,poolQuoteAmount}=s;
 return {base,slippage:0,baseReserve:poolBaseAmount,quoteReserve:poolQuoteAmount,
 virtualQuoteReserves:pool.virtualQuoteReserves,globalConfig,baseMintAccount,baseMint,
 coinCreator:pool.coinCreator,creator:pool.creator,feeConfig,quoteMint:pool.quoteMint,
 isMayhemMode:pool.isMayhemMode,creatorFeeBps:pool.creatorFeeBps};
}
function buyArgs(s,q){
 const a=sellArgs(s,new BN(0));
 delete a.base;
 a.quote=q;
 return a;
}

(async()=>{
 console.log("[MTR-111] START");
 console.log("[SCOPE] raw-WS affected-route immediate exact repricing");

 const j105=JSON.parse(fs.readFileSync("mtr_105_ultra_hot_meteora_reserve_filter.json","utf8"));
 const j100=JSON.parse(fs.readFileSync("mtr_100_new_pool_physical_liquidity.json","utf8"));

 const pumpMap=new Map((j100.rows||[]).map(r=>[r.pump_pool,r]));
 const deep=(j105.rows||[])
  .filter(r=>Number(r.meteora_wsol_sol)>=1)
  .sort((a,b)=>Number(b.meteora_wsol_sol)-Number(a.meteora_wsol_sol))
  .slice(0,ROUTES);

 const accountRoutes=new Map();
 const routeMap=new Map();

 for(const r of deep){
  const p=pumpMap.get(r.pump_pool);
  if(!p?.quote_vault)continue;

  const k=`${r.pump_pool}|${r.meteora_pool}`;
  const route={key:k,pump_pool:r.pump_pool,meteora_pool:r.meteora_pool,base_mint:r.base_mint};
  routeMap.set(k,route);

  add(accountRoutes,p.quote_vault,{venue:"PUMP",key:k});
  add(accountRoutes,r.wsol_reserve,{venue:"METEORA",key:k});
 }

 console.log(`[ROUTES] ${routeMap.size}`);
 console.log(`[ACCOUNTS] ${accountRoutes.size}`);

 const ws=new WebSocket(WS);
 const pending=new Map(),subToAccount=new Map();
 const lastTrigger=new Map(),rows=[];
 let nextId=1,reprices=0,holds=0,netPositive=0;

 async function priceRoute(route,slot,triggerAccount){
  const now=Date.now(),last=lastTrigger.get(route.key)||0;
  if(now-last<DEBOUNCE_MS)return;
  lastTrigger.set(route.key,now);

  const t0=performance.now();

  try{
   const s=await sdk.swapSolanaState(new PublicKey(route.pump_pool),USER);
   if(!s.pool.quoteMint.equals(W))throw Error("QUOTE_NOT_WSOL");

   const m=await DLMM.create(c,new PublicKey(route.meteora_pool));
   const X=m.tokenX.mint.address,Y=m.tokenY.mint.address,base=s.baseMint;

   if(!((X.equals(base)&&Y.equals(W))||(Y.equals(base)&&X.equals(W))))
    throw Error("PAIR_MISMATCH");

   const quotes=[];

   try{
    const dir=W.equals(X);
    const bins=await m.getBinArrayForSwap(dir);
    const mq=m.swapQuote(INPUT,dir,new BN(100),bins);
    const mid=new BN(mq.outAmount.toString());
    const pq=P.sellBaseInput(sellArgs(s,mid));
    const final=new BN(pq.uiQuote.toString());
    const gross=final.sub(INPUT),net=gross.sub(FEE);
    quotes.push({direction:"METEORA_TO_PUMP",gross,net});
   }catch(e){holds++}

   try{
    const pq=P.buyQuoteInput(buyArgs(s,INPUT));
    const mid=new BN(pq.base.toString());
    const dir=base.equals(X);
    const bins=await m.getBinArrayForSwap(dir);
    const mq=m.swapQuote(mid,dir,new BN(100),bins);
    const final=new BN(mq.outAmount.toString());
    const gross=final.sub(INPUT),net=gross.sub(FEE);
    quotes.push({direction:"PUMP_TO_METEORA",gross,net});
   }catch(e){holds++}

   const latency=Math.round(performance.now()-t0);

   for(const q of quotes){
    reprices++;
    const row={
     time:new Date().toISOString(),slot,trigger_account:triggerAccount,
     pump:route.pump_pool,meteora:route.meteora_pool,direction:q.direction,
     gross:q.gross.toString(),gross_bps:bps(q.gross),
     net_ref:q.net.toString(),net_ref_bps:bps(q.net),
     latency_ms:latency
    };
    rows.push(row);

    console.log(`[REPRICE] slot=${slot} latency_ms=${latency} dir=${q.direction} gross_bps=${row.gross_bps} net=${row.net_ref} pump=${route.pump_pool} meteora=${route.meteora_pool}`);

    if(q.net.gt(new BN(0))){
     netPositive++;
     console.log(`[EVENT_NET_POSITIVE] slot=${slot} latency_ms=${latency} dir=${q.direction} net=${q.net} pump=${route.pump_pool} meteora=${route.meteora_pool}`);
    }
   }
  }catch(e){
   holds++;
   console.log(`[HOLD] slot=${slot} route=${route.key} reason=${String(e.message||e).slice(0,120)}`);
  }
 }

 ws.on("message",buf=>{
  let m;
  try{m=JSON.parse(buf.toString())}catch{return}

  if(m.id&&pending.has(m.id)){
   const x=pending.get(m.id);pending.delete(m.id);x(m);return;
  }

  if(m.method==="accountNotification"){
   const sid=String(m.params?.subscription);
   const account=subToAccount.get(sid);
   if(!account)return;

   const slot=m.params?.result?.context?.slot;
   const refs=accountRoutes.get(account)||[];
   const keys=[...new Set(refs.map(x=>x.key))];

   console.log(`[EVENT] slot=${slot} account=${account} affected_routes=${keys.length}`);

   for(const k of keys){
    const r=routeMap.get(k);
    if(r)priceRoute(r,slot,account);
   }
  }
 });

 await new Promise((resolve,reject)=>{
  const t=setTimeout(()=>reject(Error("WS_OPEN_TIMEOUT")),10000);
  ws.once("open",()=>{clearTimeout(t);resolve()});
  ws.once("error",reject);
 });

 console.log("[WS_OPEN] TRUE");

 async function subscribe(account){
  const id=nextId++;
  const response=new Promise((resolve,reject)=>{
   const t=setTimeout(()=>{
    pending.delete(id);reject(Error("SUBSCRIBE_TIMEOUT"));
   },7000);
   pending.set(id,m=>{clearTimeout(t);resolve(m)});
  });

  ws.send(JSON.stringify({
   jsonrpc:"2.0",id,method:"accountSubscribe",
   params:[account,{encoding:"base64",commitment:"confirmed"}]
  }));

  const r=await response;
  if(r.error)throw Error(JSON.stringify(r.error));
  subToAccount.set(String(r.result),account);
 }

 let ok=0,fail=0;
 for(const account of accountRoutes.keys()){
  try{await subscribe(account);ok++}
  catch(e){fail++}
  await sleep(250);
 }

 console.log(`[READY] subscriptions=${ok} failures=${fail} watch_seconds=${WATCH_MS/1000}`);
 await sleep(WATCH_MS);

 fs.writeFileSync("mtr_111_event_driven_exact_reprice.json",JSON.stringify({
  routes:routeMap.size,accounts:accountRoutes.size,
  subscriptions:ok,failures:fail,
  reprices,holds,net_positive:netPositive,
  rows
 },null,2));

 console.log(`[SUMMARY] routes=${routeMap.size} subscriptions=${ok} failures=${fail} reprices=${reprices} holds=${holds} net_positive=${netPositive}`);
 console.log(netPositive?
  "[RESULT] EVENT_DRIVEN_NET_POSITIVE_FOUND":
  "[RESULT] EVENT_DRIVEN_REPRICE_ACTIVE_NO_NET_POSITIVE");
 console.log("[NOTE] 5000 lamports remains historical fee reference");
 console.log("[OUTPUT] mtr_111_event_driven_exact_reprice.json");
 console.log("[PRIVATE_KEY] NOT_USED");
 console.log("[BROADCAST] FALSE");
 console.log("[MTR-111] COMPLETE");
 ws.close();
})().catch(e=>{
 console.error("[MTR-111] FAIL");
 console.error(e.stack||e);
 process.exit(1);
});
