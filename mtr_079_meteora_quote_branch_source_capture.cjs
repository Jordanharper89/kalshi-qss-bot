const fs=require("fs");

console.log("[MTR-079] START");
console.log("[SCOPE] exact installed Meteora quote-branch source capture");

const entry=require.resolve("@meteora-ag/dlmm");
const src=fs.readFileSync(entry,"utf8");

console.log(`[SDK_ENTRY] ${entry}`);
console.log(`[SDK_BYTES] ${src.length}`);

const terms=[
 "function swapExactInQuoteAtBin",
 "function getBinMaxAmountOut",
 "function getLimitOrderLiquidity",
 "supportLimitOrder"
];

for(const term of terms){
 let pos=0,count=0;
 while((pos=src.indexOf(term,pos))!==-1){
  count++;
  if(count<=12){
   const a=Math.max(0,pos-700);
   const b=Math.min(src.length,pos+3500);
   console.log(`\n===== ${term} OCCURRENCE ${count} @ ${pos} =====`);
   console.log(src.slice(a,b));
  }
  pos+=term.length;
 }
 console.log(`\n[TERM_COUNT] ${term}=${count}`);
}

console.log("[RESULT] EXACT_QUOTE_BRANCH_SOURCE_CAPTURED");
console.log("[NETWORK] NOT_USED");
console.log("[PRIVATE_KEY] NOT_USED");
console.log("[BROADCAST] FALSE");
console.log("[MTR-079] COMPLETE");
