"use strict";
const a=require('assert'),m=require('./oracle118_scanner_integrity.cjs');
const x='So11111111111111111111111111111111111111112',y='5UUH9RTDiSpq6HKS6bp4NdU9PNJpXRXuiw6ShBTBhgH2';
const p={token:y,pump_pool:x,meteora_pool:x,observed_unix:1000};
a.equal(m.normalized({rows:[p,p]}).length,2);
a.equal(m.unique(m.normalized({rows:[p,p]})).length,1);
a.equal(m.freshness(p,1050,90),true);
a.equal(m.freshness(p,1200,90),false);
a.equal(m.freshness({...p,observed_unix:null},1050,90),false);
a.equal(m.select([{file:'fixture',sha256:'abc',rows:[p,p]}],1050,90).length,1);
console.log('[PASS] ORACLE-118 six deterministic integrity checks');

