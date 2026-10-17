from pathlib import Path

p=Path("mtr_090_decimal_normalized_spot_discovery.cjs")
p.write_text(r'''const fs=require("fs");
const {Connection,PublicKey}=require("@solana/web3.js");
const {getMint}=require("@solana/spl-token");
const D=require("@meteora-ag/dlmm"),P=require("@pump-fun/pump-swap-sdk");
const DLMM=D.default||D.DLMM||D;

const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||
"https://api.mainnet-beta.solana.com";
const W=new PublicKey("So11111111111111111111111111111111111111112");
const USER=new PublicKey("CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR");
const c=new Connection(RPC,"confirmed"),sdk=new P.OnlinePumpAmmSdk(c);
const sleep=ms=>new Promise(r=>setTimeout(r,ms));

function rows(x){
 if(Array.isArray(x))return x;
 for(const k of ["candidates","funded","rows","results","items"])
  if(Array.isArray(x?.[k]))return x[k];
 return[];
}
function pumpKey(r){return r.pump_pool||r.pumpPool||r.pool||r.pump_pool_address}
function mets(r){
 const x=r.meteora_pools||r.meteoraPools||r.meteora||[];
 return Array.isArray(x)?x.map(v=>typeof v==="string"?v:(v.address||v.pool||v.publicKey)).filter(Boolean):[];
}
function key(v){return v?.toBase58?v.toBase58():String(v)}
function num(v){return Number(v?.toString?.()??v)}
function scale(d){return 10**d}
function bps(a,b){return Math.round((a/b-1)*10000)}

(async()=>{
 console.log("[MTR-090] START");
 console.log("[SCOPE] decimal-normalized corrected fresh spot discovery");

 const src="mtr_057_funded_exact_pair_candidates.json";
 if(!fs.existsSync(src))throw Error("MTR_057_FUNDED_SET_NOT_FOUND");
 const R=rows(JSON.parse(fs.readFileSync(src,"utf8")));
 console.log(`[FUNDED_ROWS] ${R.length}`);

 const all=await DLMM.getLbPairs(c);
 console.log(`[METEORA_PAIRS] ${all.length}`);

 const mm=new Map();
 for(const z of all){
  const pk=key(z.publicKey||z.pubkey||z.address);
  const a=z.account||z;
  if(pk)mm.set(pk,a);
 }

 const dec=new Map();
 dec.set(W.toBase58(),9);

 async function decimals(m){
  const k=key(m);
  if(dec.has(k))return dec.get(k);
  const x=await getMint(c,new PublicKey(k),"confirmed");
  dec.set(k,x.decimals);
  await sleep(250);
  return x.decimals;
 }

 const out=[];
 let links=0,usable=0,pumpStates=0;

 for(let i=0;i<R.length;i++){
  const pump=new PublicKey(pumpKey(R[i]));
  let s;
  try{s=await sdk.swapSolanaState(pump,USER)}
  catch(e){console.log(`[PUMP_HOLD] ${pump}`);continue}

  pumpStates++;
  const base=s.baseMint;
  if(!s.pool.quoteMint.equals(W))continue;

  const bd=await decimals(base),wd=9;
  const br=num(s.poolBaseAmount);
  const qr=num(s.poolQuoteAmount)+num(s.pool.virtualQuoteReserves||0);
  if(!(br>0&&qr>0))continue;

  const pumpWsolPerBase=(qr/scale(wd))/(br/scale(bd));

  for(const ms of mets(R[i])){
   links++;
   const a=mm.get(ms); if(!a)continue;

   const X=new PublicKey(key(a.tokenXMint)),Y=new PublicKey(key(a.tokenYMint));
   if(!((X.equals(base)&&Y.equals(W))||(Y.equals(base)&&X.equals(W))))continue;

   let raw=Math.pow(1+num(a.binStep)/10000,num(a.activeId));
   let meteoraWsolPerBase;

   if(X.equals(base)&&Y.equals(W))
    meteoraWsolPerBase=raw*Math.pow(10,bd-wd);
   else
    meteoraWsolPerBase=(1/raw)*Math.pow(10,bd-wd);

   if(!(meteoraWsolPerBase>0&&Number.isFinite(meteoraWsolPerBase)))continue;

   usable++;
   const m2p=bps(pumpWsolPerBase,meteoraWsolPerBase);
   const p2m=bps(meteoraWsolPerBase,pumpWsolPerBase);

   out.push({
    pump:pump.toBase58(),meteora:ms,base:base.toBase58(),
    base_decimals:bd,wsol_decimals:wd,
    pump_wsol_per_base:pumpWsolPerBase,
    meteora_wsol_per_base:meteoraWsolPerBase,
    m2p_spot_bps:m2p,p2m_spot_bps:p2m,
    best_direction:m2p>=p2m?"METEORA_TO_PUMP":"PUMP_TO_METEORA",
    best_spot_bps:Math.max(m2p,p2m)
   });
  }

  console.log(`[PROGRESS] ${i+1}/${R.length} pump_states=${pumpStates} links=${links} usable=${usable}`);
  await sleep(600);
 }

 out.sort((a,b)=>b.best_spot_bps-a.best_spot_bps);

 fs.writeFileSync("mtr_090_decimal_normalized_spot_candidates.json",
  JSON.stringify({pump_states:pumpStates,links,usable,ranking:out},null,2));

 console.log(`[SUMMARY] pump_states=${pumpStates} links=${links} usable=${usable}`);
 for(const x of out.slice(0,25))
  console.log(`[TOP] dir=${x.best_direction} spot_bps=${x.best_spot_bps} base_dec=${x.base_decimals} pump=${x.pump} meteora=${x.meteora}`);

 console.log(out.length?
  "[RESULT] DECIMAL_NORMALIZED_SPOT_CANDIDATES_RANKED":
  "[RESULT] NO_DECIMAL_NORMALIZED_CANDIDATES");
 console.log("[NOTE] spot_bps remains prefilter only; executable quotes required");
 console.log("[PRIVATE_KEY] NOT_USED");
 console.log("[BROADCAST] FALSE");
 console.log("[MTR-090] COMPLETE");
})().catch(e=>{
 console.error("[MTR-090] FAIL");
 console.error(e.stack||e);
 process.exit(1);
});
''',encoding="utf-8")

print(f"[BUILD] wrote {p}")
print("[BUILD] decimal-normalized corrected fresh spot discovery")
print("[SCOPE] prefilter only; no signing; no sending")