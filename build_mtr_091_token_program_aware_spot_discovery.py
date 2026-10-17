from pathlib import Path

p=Path("mtr_091_token_program_aware_spot_discovery.cjs")
p.write_text(r'''const fs=require("fs");
const {Connection,PublicKey}=require("@solana/web3.js");
const {getMint,TOKEN_PROGRAM_ID,TOKEN_2022_PROGRAM_ID}=require("@solana/spl-token");
const D=require("@meteora-ag/dlmm"),P=require("@pump-fun/pump-swap-sdk");
const DLMM=D.default||D.DLMM||D;

const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||
"https://api.mainnet-beta.solana.com";
const W=new PublicKey("So11111111111111111111111111111111111111112");
const USER=new PublicKey("CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR");
const c=new Connection(RPC,"confirmed"),sdk=new P.OnlinePumpAmmSdk(c);
const sleep=ms=>new Promise(r=>setTimeout(r,ms));

function rows(x){if(Array.isArray(x))return x;for(const k of
 ["candidates","funded","rows","results","items"])if(Array.isArray(x?.[k]))return x[k];return[]}
function pumpKey(r){return r.pump_pool||r.pumpPool||r.pool||r.pump_pool_address}
function mets(r){const x=r.meteora_pools||r.meteoraPools||r.meteora||[];
 return Array.isArray(x)?x.map(v=>typeof v==="string"?v:(v.address||v.pool||v.publicKey)).filter(Boolean):[]}
function key(v){return v?.toBase58?v.toBase58():String(v)}
function num(v){return Number(v?.toString?.()??v)}
function bps(a,b){return Math.round((a/b-1)*10000)}

(async()=>{
 console.log("[MTR-091] START");
 console.log("[SCOPE] Token/Token-2022 aware decimal-normalized spot discovery");

 const src="mtr_057_funded_exact_pair_candidates.json";
 if(!fs.existsSync(src))throw Error("MTR_057_FUNDED_SET_NOT_FOUND");
 const R=rows(JSON.parse(fs.readFileSync(src,"utf8")));
 console.log(`[FUNDED_ROWS] ${R.length}`);

 const all=await DLMM.getLbPairs(c);
 console.log(`[METEORA_PAIRS] ${all.length}`);
 const mm=new Map();
 for(const z of all){
  const pk=key(z.publicKey||z.pubkey||z.address),a=z.account||z;
  if(pk)mm.set(pk,a);
 }

 const dec=new Map([[W.toBase58(),9]]);
 async function decimals(m){
  const k=key(m); if(dec.has(k))return dec.get(k);
  const pk=new PublicKey(k),ai=await c.getAccountInfo(pk,"confirmed");
  if(!ai)throw Error(`MINT_NOT_FOUND_${k}`);
  let program;
  if(ai.owner.equals(TOKEN_PROGRAM_ID))program=TOKEN_PROGRAM_ID;
  else if(ai.owner.equals(TOKEN_2022_PROGRAM_ID))program=TOKEN_2022_PROGRAM_ID;
  else throw Error(`UNSUPPORTED_MINT_OWNER_${ai.owner.toBase58()}_${k}`);
  const x=await getMint(c,pk,"confirmed",program);
  dec.set(k,x.decimals);
  console.log(`[MINT] ${k} decimals=${x.decimals} program=${program.toBase58()}`);
  await sleep(250);
  return x.decimals;
 }

 const out=[];let links=0,usable=0,pumpStates=0,holds=0;

 for(let i=0;i<R.length;i++){
  const pump=new PublicKey(pumpKey(R[i])); let s;
  try{s=await sdk.swapSolanaState(pump,USER)}
  catch(e){holds++;console.log(`[PUMP_HOLD] ${pump}`);continue}

  pumpStates++;
  const base=s.baseMint;
  if(!s.pool.quoteMint.equals(W))continue;

  let bd;
  try{bd=await decimals(base)}
  catch(e){holds++;console.log(`[MINT_HOLD] ${base} ${e.message}`);continue}

  const br=num(s.poolBaseAmount);
  const qr=num(s.poolQuoteAmount)+num(s.pool.virtualQuoteReserves||0);
  if(!(br>0&&qr>0))continue;
  const pumpPrice=(qr/1e9)/(br/(10**bd));

  for(const ms of mets(R[i])){
   links++;
   const a=mm.get(ms); if(!a)continue;
   const X=new PublicKey(key(a.tokenXMint)),Y=new PublicKey(key(a.tokenYMint));
   if(!((X.equals(base)&&Y.equals(W))||(Y.equals(base)&&X.equals(W))))continue;

   let raw=Math.pow(1+num(a.binStep)/10000,num(a.activeId));
   let metPrice=X.equals(base)?raw*Math.pow(10,bd-9):(1/raw)*Math.pow(10,bd-9);
   if(!(metPrice>0&&Number.isFinite(metPrice)))continue;

   usable++;
   const m2p=bps(pumpPrice,metPrice),p2m=bps(metPrice,pumpPrice);
   out.push({pump:pump.toBase58(),meteora:ms,base:base.toBase58(),
    base_decimals:bd,pump_wsol_per_base:pumpPrice,meteora_wsol_per_base:metPrice,
    m2p_spot_bps:m2p,p2m_spot_bps:p2m,
    best_direction:m2p>=p2m?"METEORA_TO_PUMP":"PUMP_TO_METEORA",
    best_spot_bps:Math.max(m2p,p2m)});
  }

  console.log(`[PROGRESS] ${i+1}/${R.length} pump_states=${pumpStates} links=${links} usable=${usable} holds=${holds}`);
  await sleep(600);
 }

 out.sort((a,b)=>b.best_spot_bps-a.best_spot_bps);
 fs.writeFileSync("mtr_091_token_program_aware_spot_candidates.json",
  JSON.stringify({pump_states:pumpStates,links,usable,holds,ranking:out},null,2));

 console.log(`[SUMMARY] pump_states=${pumpStates} links=${links} usable=${usable} holds=${holds}`);
 for(const x of out.slice(0,25))
  console.log(`[TOP] dir=${x.best_direction} spot_bps=${x.best_spot_bps} dec=${x.base_decimals} pump=${x.pump} meteora=${x.meteora}`);

 console.log(out.length?"[RESULT] TOKEN_PROGRAM_AWARE_SPOT_CANDIDATES_RANKED":
 "[RESULT] NO_TOKEN_PROGRAM_AWARE_CANDIDATES");
 console.log("[NOTE] spot bps is prefilter only; exact executable quote still required");
 console.log("[PRIVATE_KEY] NOT_USED");
 console.log("[BROADCAST] FALSE");
 console.log("[MTR-091] COMPLETE");
})().catch(e=>{console.error("[MTR-091] FAIL");console.error(e.stack||e);process.exit(1)});
''',encoding="utf-8")

print(f"[BUILD] wrote {p}")
print("[BUILD] Token/Token-2022 aware decimal-normalized fresh discovery")
print("[SCOPE] prefilter only; no signing; no sending")