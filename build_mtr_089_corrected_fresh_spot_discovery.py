from pathlib import Path

p=Path("mtr_089_corrected_fresh_spot_discovery.cjs")
p.write_text(r'''const fs=require("fs");
const {Connection,PublicKey}=require("@solana/web3.js");
const BN=require("bn.js"),D=require("@meteora-ag/dlmm"),P=require("@pump-fun/pump-swap-sdk");
const DLMM=D.default||D.DLMM||D;
const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||
"https://api.mainnet-beta.solana.com";
const W="So11111111111111111111111111111111111111112";
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
function mets(r){const x=r.meteora_pools||r.meteoraPools||r.meteora||[];
 return Array.isArray(x)?x.map(v=>typeof v==="string"?v:(v.address||v.pool||v.publicKey)).filter(Boolean):[]}
function key(v){return v?.toBase58?v.toBase58():String(v)}
function n(v){return Number(v?.toString?.()??v)}
function metRawPrice(a){
 const active=n(a.activeId),step=n(a.binStep);
 return Math.pow(1+step/10000,active);
}
function gapBps(a,b){return Math.round((a/b-1)*10000)}

(async()=>{
 console.log("[MTR-089] START");
 console.log("[SCOPE] corrected fresh spot discovery; prefilter only");

 const src="mtr_057_funded_exact_pair_candidates.json";
 if(!fs.existsSync(src))throw Error("MTR_057_FUNDED_SET_NOT_FOUND");
 const R=rows(JSON.parse(fs.readFileSync(src,"utf8")));
 console.log(`[FUNDED_ROWS] ${R.length}`);

 console.log("[METEORA] loading LB-pair inventory once");
 const all=await DLMM.getLbPairs(c);
 console.log(`[METEORA_PAIRS] ${all.length}`);

 const mm=new Map();
 for(const z of all){
  const pk=key(z.publicKey||z.pubkey||z.address);
  const a=z.account||z;
  if(pk)mm.set(pk,a);
 }

 const out=[];let pumpStates=0,links=0,usable=0;

 for(let i=0;i<R.length;i++){
  const pump=new PublicKey(pumpKey(R[i]));
  let s;
  try{s=await sdk.swapSolanaState(pump,USER)}
  catch(e){console.log(`[PUMP_HOLD] ${pump}`);await sleep(1200);continue}

  pumpStates++;
  const base=key(s.baseMint),quote=key(s.pool.quoteMint);
  if(quote!==W)continue;

  const br=n(s.poolBaseAmount);
  const qr=n(s.poolQuoteAmount)+n(s.pool.virtualQuoteReserves||0);
  if(!(br>0&&qr>0))continue;
  const pumpPrice=qr/br;

  for(const ms of mets(R[i])){
   links++;
   const a=mm.get(ms); if(!a)continue;
   const X=key(a.tokenXMint),Y=key(a.tokenYMint);
   if(!((X===base&&Y===W)||(Y===base&&X===W)))continue;

   let mp=metRawPrice(a);
   if(X===W)mp=1/mp;
   if(!(mp>0&&Number.isFinite(mp)))continue;

   usable++;
   const m2p=gapBps(pumpPrice,mp);
   const p2m=gapBps(mp,pumpPrice);

   out.push({pump:pump.toBase58(),meteora:ms,base,
    pump_raw_price:pumpPrice,meteora_raw_price:mp,
    m2p_spot_bps:m2p,p2m_spot_bps:p2m,
    best_direction:m2p>=p2m?"METEORA_TO_PUMP":"PUMP_TO_METEORA",
    best_spot_bps:Math.max(m2p,p2m)});
  }

  console.log(`[PROGRESS] ${i+1}/${R.length} pump_states=${pumpStates} links=${links} usable=${usable}`);
  await sleep(900);
 }

 out.sort((a,b)=>b.best_spot_bps-a.best_spot_bps);
 fs.writeFileSync("mtr_089_corrected_fresh_spot_candidates.json",
  JSON.stringify({pump_states:pumpStates,links,usable,ranking:out},null,2));

 console.log(`[SUMMARY] pump_states=${pumpStates} links=${links} usable=${usable}`);
 for(const x of out.slice(0,20))
  console.log(`[TOP] dir=${x.best_direction} spot_bps=${x.best_spot_bps} pump=${x.pump} meteora=${x.meteora}`);

 console.log(out.length?"[RESULT] CORRECTED_FRESH_SPOT_CANDIDATES_RANKED":
  "[RESULT] NO_CORRECTED_FRESH_SPOT_CANDIDATES");
 console.log("[NOTE] spot gaps are prefilter only; not executable profit");
 console.log("[OUTPUT] mtr_089_corrected_fresh_spot_candidates.json");
 console.log("[PRIVATE_KEY] NOT_USED");
 console.log("[BROADCAST] FALSE");
 console.log("[MTR-089] COMPLETE");
})().catch(e=>{console.error("[MTR-089] FAIL");console.error(e.stack||e);process.exit(1)});
''',encoding="utf-8")

print(f"[BUILD] wrote {p}")
print("[BUILD] corrected fresh cross-venue spot discovery")
print("[SCOPE] prefilter only; no signing; no sending")