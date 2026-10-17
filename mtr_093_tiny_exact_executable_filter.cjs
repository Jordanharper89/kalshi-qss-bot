const fs=require("fs");
const {Connection,PublicKey}=require("@solana/web3.js");
const BN=require("bn.js"),D=require("@meteora-ag/dlmm"),P=require("@pump-fun/pump-swap-sdk");
const DLMM=D.default||D.DLMM||D;

const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||
"https://api.mainnet-beta.solana.com";
const W=new PublicKey("So11111111111111111111111111111111111111112");
const USER=new PublicKey("CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR");
const PROBE=new BN("100000");
const c=new Connection(RPC,"confirmed"),sdk=new P.OnlinePumpAmmSdk(c);
const sleep=ms=>new Promise(r=>setTimeout(r,ms));

function rows(x){if(Array.isArray(x))return x;for(const k of
 ["candidates","funded","rows","results","items"])if(Array.isArray(x?.[k]))return x[k];return[]}
function pumpKey(r){return r.pump_pool||r.pumpPool||r.pool||r.pump_pool_address}
function mets(r){const x=r.meteora_pools||r.meteoraPools||r.meteora||[];
 return Array.isArray(x)?x.map(v=>typeof v==="string"?v:(v.address||v.pool||v.publicKey)).filter(Boolean):[]}

function save(out,stats){
 fs.writeFileSync("mtr_093_tiny_exact_executable_routes.json",
  JSON.stringify({...stats,routes:out},null,2));
}

(async()=>{
 console.log("[MTR-093] START");
 console.log("[SCOPE] tiny exact executable filter; no profitability claim");

 const src="mtr_057_funded_exact_pair_candidates.json";
 if(!fs.existsSync(src))throw Error("MTR_057_FUNDED_SET_NOT_FOUND");
 const R=rows(JSON.parse(fs.readFileSync(src,"utf8")));
 console.log(`[FUNDED_ROWS] ${R.length}`);
 console.log(`[PROBE_RAW] ${PROBE}`);

 const out=[];
 let links=0,m2pOk=0,p2mOk=0,m2pHold=0,p2mHold=0;

 for(let i=0;i<R.length;i++){
  const pump=new PublicKey(pumpKey(R[i]));
  let s;
  try{s=await sdk.swapSolanaState(pump,USER)}
  catch(e){console.log(`[PUMP_HOLD] ${pump}`);await sleep(1200);continue}

  const base=s.baseMint;
  if(!s.pool.quoteMint.equals(W))continue;

  for(const ms of mets(R[i])){
   links++;
   let m,X,Y;
   try{
    m=await DLMM.create(c,new PublicKey(ms));
    X=m.tokenX.mint.address;Y=m.tokenY.mint.address;
    if(!((X.equals(base)&&Y.equals(W))||(Y.equals(base)&&X.equals(W))))continue;
   }catch(e){
    m2pHold++;p2mHold++;
    continue;
   }

   let m2p=false,p2m=false,m2pOut=null,p2mOut=null;

   try{
    const swapForY=W.equals(X);
    const bins=await m.getBinArrayForSwap(swapForY);
    const q=m.swapQuote(PROBE,swapForY,new BN(0),bins);
    m2p=true;m2pOk++;m2pOut=q.outAmount.toString();
   }catch(e){m2pHold++}

   await sleep(200);

   try{
    const swapForY=base.equals(X);
    const bins=await m.getBinArrayForSwap(swapForY);
    const q=m.swapQuote(PROBE,swapForY,new BN(0),bins);
    p2m=true;p2mOk++;p2mOut=q.outAmount.toString();
   }catch(e){p2mHold++}

   if(m2p||p2m)
    out.push({pump:pump.toBase58(),meteora:ms,base:base.toBase58(),
      m2p_executable:m2p,p2m_executable:p2m,
      m2p_probe_out:m2pOut,p2m_probe_out:p2mOut});

   if(links%25===0){
    save(out,{links,m2p_ok:m2pOk,p2m_ok:p2mOk,m2p_hold:m2pHold,p2m_hold:p2mHold});
    console.log(`[CHECKPOINT] links=${links} routes=${out.length} m2p_ok=${m2pOk} p2m_ok=${p2mOk}`);
   }

   await sleep(350);
  }

  console.log(`[PROGRESS] candidate=${i+1}/${R.length} links=${links} executable_routes=${out.length}`);
  await sleep(900);
 }

 save(out,{links,m2p_ok:m2pOk,p2m_ok:p2mOk,m2p_hold:m2pHold,p2m_hold:p2mHold});

 console.log(`[SUMMARY] links=${links} executable_routes=${out.length} m2p_ok=${m2pOk} p2m_ok=${p2mOk} m2p_hold=${m2pHold} p2m_hold=${p2mHold}`);
 console.log(out.length?
  "[RESULT] TINY_EXACT_EXECUTABLE_SET_FOUND":
  "[RESULT] NO_TINY_EXACT_EXECUTABLE_SET");
 console.log("[OUTPUT] mtr_093_tiny_exact_executable_routes.json");
 console.log("[NOTE] executability only; no profit claim");
 console.log("[PRIVATE_KEY] NOT_USED");
 console.log("[BROADCAST] FALSE");
 console.log("[MTR-093] COMPLETE");
})().catch(e=>{
 console.error("[MTR-093] FAIL");
 console.error(e.stack||e);
 process.exit(1);
});
