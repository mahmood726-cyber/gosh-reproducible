const fs=require('fs'),path=require('path'),{pathToFileURL}=require('url');
const {chromium}=require(process.env.PLAYWRIGHT_ROOT);
const variant=process.argv[2]||'original';
(async()=>{
const start=Date.now(),browser=await chromium.launch({channel:'chrome',headless:true});
const page=await browser.newPage();await page.addInitScript({content:fs.readFileSync('export-boundaries.cjs','utf8')+';installExports(window);'});const errors=[];page.on('pageerror',e=>errors.push(e.message));
const cdp=await page.context().newCDPSession(page);await cdp.send('Debugger.enable');
const pagePath=process.env.GOSH_PAGE || `${variant}/gosh/index.html`;
const html=fs.readFileSync(pagePath,'utf8');
const line=html.split('\n').findIndex(x=>x.includes("var text = document.getElementById('src').value;"));
const url=pathToFileURL(path.resolve(pagePath)).href;
await cdp.send('Debugger.setBreakpointByUrl',{url,lineNumber:line});
const installed=new Promise((resolve,reject)=>cdp.once('Debugger.paused',async ev=>{
try {
const out=await cdp.send('Debugger.evaluateOnCallFrame',{callFrameId:ev.callFrames[0].callFrameId,expression:`
window.__empty=false;
const originalAll=allSubsets,originalSample=sampledSubsets;
allSubsets=function(...a){return window.__empty?[]:originalAll(...a);};
sampledSubsets=function(...a){return window.__empty?[]:originalSample(...a);};
window.__capture=[];
pool=(function(original){return function(rows,model){const result=original(rows,model); window.__capture.push({members:rows.map(r=>Number(r.label)),...result});return result;};})(pool);
window.__auditAxis=function(s){_axisState=s;run();};
`,returnByValue:true});
if(out.exceptionDetails)throw Error(JSON.stringify(out.exceptionDetails));
await cdp.send('Debugger.setSkipAllPauses',{skip:true});await cdp.send('Debugger.resume');resolve();
}catch(e){reject(e);}
}));
await page.goto(url);await installed;
await page.waitForFunction(()=>typeof window._almLastGosh==='function');
const corpus=JSON.parse(fs.readFileSync('corpus.json','utf8'));

const sampled=corpus.find(x=>x.k>15&&x.k<=100),small=corpus.find(x=>x.k<=15);
const records=[];
for(const model of ['FE','DL']) {
 const result=await page.evaluate(({d,model})=>{
  document.querySelector('#model').value=model;document.querySelector('#n-sample').value='1000';
  const rows=d.te.map((yi,i)=>({yi,vi:d.se[i]*d.se[i],study:String(i+1)}));
  window.__capture=[];window.__almGoshLoad(rows);
  const first=JSON.stringify(window.__capture);
  const summary=window._almLastGosh();const points=window.__capture;
  window.__capture=[];window.__almGoshLoad(rows);
  const repeat=first===JSON.stringify(window.__capture);
  const bounds={x:[Math.min(...points.map(p=>p.mu))-1,Math.max(...points.map(p=>p.mu))+1],y:[-10,110]};
  window.__auditAxis(bounds);
  const read=()=>[...document.querySelectorAll('#plot circle')].map(c=>[c.cx.baseVal.value,c.cy.baseVal.value]);
  const overrideNote=document.querySelector('#plot-note').textContent;
  const circles=read(),unchanged=JSON.stringify(summary)===JSON.stringify(window._almLastGosh());
  window.__auditAxis({});
  const automatic=read(),automaticNote=document.querySelector('#plot-note').textContent;
  return {summary,points,repeat,circles,bounds,unchanged,automatic,overrideNote,automaticNote};
 },{d:sampled,model});
 records.push({id:sampled.id,model,...result});
}
const axisCases=[];
for(const model of ['FE','DL']) for(const limits of [{x:[1,8]}, {y:[0,90]},
 {x:[1,8],y:[-10,110]}, {x:[null,4]}, {x:[2,null]}, {y:[10,null]},
 {y:[null,50]}, {x:[1.5,2],y:[0,100]}, {endpointY:true}, {x:[2.5,4],y:[10,80]}]) {
 axisCases.push(await page.evaluate(({model,limits})=>{
  document.querySelector('#model').value=model;window.__auditAxis({});window.__capture=[];
  window.__almGoshLoad([1,2,4,8].map((yi,i)=>({yi,sei:1,study:String(i+1)})));
  const points=window.__capture.slice(),original=JSON.stringify(window._almLastGosh());
  if(limits.endpointY) limits={y:[0,Math.max(...points.map(p=>p.I2))]};
  window.__auditAxis(limits);
  return {model,limits,points,plotNote:document.querySelector('#plot-note').textContent,circles:[...document.querySelectorAll('#plot circle')].map(c=>[c.cx.baseVal.value,c.cy.baseVal.value]),
   unchanged:original===JSON.stringify(window._almLastGosh())};
 },{model,limits}));
}
const invalidAxes=[],drawCases=[];
for(const model of ['FE','DL']) {
 for(const name of ['reversed-x','equal-y','nan-x','infinite-y']) {
  invalidAxes.push(await page.evaluate(({model,name})=>{
   document.querySelector('#model').value=model;window.__auditAxis({});
   window.__almGoshLoad([1,2,4,8].map((yi,i)=>({yi,sei:1,study:String(i+1)})));
   const before=JSON.stringify(window._almLastGosh()),svg=document.querySelector('#plot').innerHTML;
   const medians=()=>['m-est','m-i2'].map(id=>document.getElementById(id).textContent).join('|');
   const median=medians();
   const limits={'reversed-x':{x:[8,1]},'equal-y':{y:[50,50]},'nan-x':{x:[NaN,8]},'infinite-y':{y:[0,Infinity]}}[name];
   window.__auditAxis(limits);
   const el=document.querySelector('#plot-error'),error=el.innerText;
   const visible=getComputedStyle(el).display!=='none' && getComputedStyle(el).visibility!=='hidden';
   const empty=document.querySelector('#plot').innerHTML==='';
   const retained=before===JSON.stringify(window._almLastGosh()) && median===medians();
   window.__auditAxis({});
   const recovered=svg===document.querySelector('#plot').innerHTML && before===JSON.stringify(window._almLastGosh()) && !el.textContent;
   return {model,name,error,visible,empty,retained,recovered};
  },{model,name}));
 }
 for(const value of ['-1000','0','2.5','','100001']) {
  drawCases.push(await page.evaluate(({model,value})=>{
   document.querySelector('#model').value=model;window.__auditAxis({});
   const input=document.querySelector('#n-sample');input.value='37';
   window.__almGoshLoad(Array.from({length:16},(_,i)=>({yi:i+1,sei:1,study:String(i+1)})));
   input.value=value;document.querySelector('#btn-run').click();
   const el=document.querySelector('#sample-error'),error=el.innerText;
   const visible=getComputedStyle(el).display!=='none' && getComputedStyle(el).visibility!=='hidden';
   const cleared=window._almLastGosh()==null && !document.querySelector('#plot').innerHTML && !/\d/.test(['m-est','m-i2'].map(id=>document.getElementById(id).textContent).join(''));
   input.value='37';document.querySelector('#btn-run').click();
   const recovered=!el.textContent && window._almLastGosh().n_subsets===37 && document.querySelectorAll('#plot circle').length===37;
   return {model,value,error,visible,cleared,recovered};
  },{model,value}));
 }
}
const matrixSource=fs.readFileSync('numeric-matrix.cjs','utf8');
await page.addScriptTag({content:matrixSource});
const numericMatrix=await page.evaluate((source)=>window.numericMatrix({
 axis:s=>window.__auditAxis(s),model:s=>document.getElementById('model').value=s,
 draws:s=>document.getElementById('n-sample').value=s,empty:s=>window.__empty=s,
 load:values=>window.__almGoshLoad(values),
 read:()=>({exports:window.__readExports(),declarations:window.numericDeclarations(source),count:document.getElementById('m-n').textContent,
 median:document.getElementById('m-est').textContent,i2:document.getElementById('m-i2').textContent,
 note:document.getElementById('plot-note').textContent,error:document.getElementById('sample-error').textContent,
 plot_error:document.getElementById('plot-error').textContent,draws:document.getElementById('n-sample').value,src:document.getElementById('src').value,
 svg:document.getElementById('plot').innerHTML,result:window._almLastGosh()})
}),html);
const plain=await browser.newPage();await plain.goto(url);
const uninstrumented=[];
for(const model of ['FE','DL']){
 const z=await plain.evaluate(({d,model})=>{
 document.querySelector('#model').value=model;
 window.__almGoshLoad(d.te.map((yi,i)=>({yi,vi:d.se[i]*d.se[i],study:String(i+1)})));
 return {summary:window._almLastGosh(),circles:document.querySelectorAll('#plot circle').length};
 },{d:small,model});
 uninstrumented.push({id:small.id,model,...z});
}
// Compute coordinates outside the page, then use the browser's native SVG
// decimal parser on detached elements. Chrome parsing can differ by one ULP
// from a direct IEEE float32 cast; no rendered bounds/positions are inputs.
async function oracle(points, limits) {
 const proc=require('child_process').spawnSync('python',['-c',
  'import json,sys; from axis_oracle import coordinates; d=json.load(sys.stdin); print(json.dumps(coordinates(d["points"],d["limits"])))'],
  {input:JSON.stringify({points,limits}),encoding:'utf8'});
 if(proc.status!==0) throw Error(proc.stderr);
 const coordinates=JSON.parse(proc.stdout);
 const native=await page.evaluate(coords=>coords.map(pair=>{
  const c=document.createElementNS('htt<LOCAL_PATH>','circle');
  c.setAttribute('cx',String(pair[0]));c.setAttribute('cy',String(pair[1]));
  return [c.cx.baseVal.value,c.cy.baseVal.value];
 }),coordinates);
 return {coordinates,native};
}
for(const r of records){r.overrideOracle=await oracle(r.points,r.bounds);r.automaticOracle=await oracle(r.points,{});}
for(const r of axisCases)r.oracle=await oracle(r.points,r.limits);
fs.writeFileSync('options-'+variant+'.json',JSON.stringify({records,axisCases,invalidAxes,drawCases,numericMatrix,uninstrumented,errors}));
console.log(variant+': sample-count, deterministic replay, axis override and uninstrumented-page evidence captured');
await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
