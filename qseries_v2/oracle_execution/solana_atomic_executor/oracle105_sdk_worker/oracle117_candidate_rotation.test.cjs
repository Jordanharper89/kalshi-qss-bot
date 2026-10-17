"use strict";
const assert=require('assert'),m=require('./oracle117_candidate_rotation.cjs');
const a=[{index:0},{index:1},{index:2},{index:3},{index:4}];
assert.deepStrictEqual(m.order(a,2,2).map(x=>x.index),[2,3]);
assert.deepStrictEqual(m.order(a,4,2).map(x=>x.index),[4]);
assert.deepStrictEqual(m.order(a,5,2),[]);
assert.deepStrictEqual(m.bounds({consumedInAmount:'5',minOutAmount:'3',outAmount:'4'}),{consumed:'5',min:'3',out:'4'});
console.log('[PASS] ORACLE-117 four deterministic candidate rotation checks');
