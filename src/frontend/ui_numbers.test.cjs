const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const path=require('node:path');
const context={document:{querySelectorAll:()=>[],querySelector:()=>null,body:{}},window:{},MutationObserver:class{observe(){}},WeakMap};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../static/js/ui_numbers.js'),'utf8'),context);
const {format,parse}=context.window.IhrmsNumbers;
test('Vietnamese numbers preserve all decimal digits without binary float rounding',()=>{
 assert.equal(format('1234567890123.0700'),'1.234.567.890.123,0700');
 assert.equal(parse('1.234.567.890.123,0700'),'1234567890123.0700');
 assert.equal(format('-1234.5'),'-1.234,5');
 assert.equal(parse('-1.234,5'),'-1234.5');
 assert.equal(parse('0,07'),'0.07');
 assert.equal(parse('0'),'0');
 assert.equal(parse(''),'');
});
test('reject malformed grouping instead of silently changing the entered amount',()=>{
 for(const value of ['12.34','1,2,3','NaN','1e6','12a','1.2345'])assert.equal(parse(value),null);
});
