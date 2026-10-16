const fs=require('fs'),path=require('path'),{pathToFileURL}=require('url');
const {chromium}=require(process.env.PLAYWRIGHT_ROOT);
const variant=process.argv[2]||'original';
(async()=>{
const start=Date.now(),browser=await chromium.launch({channel:'chrome',headless:true});
const page=await browser.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
const cdp=await page.context().newCDPSession(page);await cdp.send('Debugger.enable');
const html=fs.readFileSync(`${variant}/gosh/index.html`,'utf8');
const line=html.split('\n').findIndex(x=>x.includes("var text = document.getElementById('src').value;"));
const url=pathToFileURL(path.resolve(`${variant}/gosh/index.html`)).href;
await cdp.send('Debugger.setBreakpointByUrl',{url,lineNumber:line});
const installed=new Promise((resolve,reject)=>cdp.once('Debugger.paused',async ev=>{
try {
const out=await cdp.send('Debugger.evaluateOnCallFrame',{callFrameId:ev.callFrames[0].callFrameId,expression:`
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
fs.mkdirSync(`app-${variant}`,{recursive:true});const index=[];
for(const d of corpus)for(const model of ['FE','DL']){
 const key=d.id+'::'+model;
 const out=await page.evaluate(({d,model})=>{
  window.__capture=[];document.querySelector('#model').value=model;
  window.__almGoshLoad(d.te.map((yi,i)=>({yi,vi:d.se[i]*d.se[i],study:String(i+1)})));
  return {summary:window._almLastGosh(),points:window.__capture,ui:{count:document.querySelector('#m-n').textContent,estimate:document.querySelector('#m-est').textContent,i2:document.querySelector('#m-i2').textContent,circles:[...document.querySelectorAll('#plot circle')].map(c=>[+c.getAttribute('cx'),+c.getAttribute('cy')]),ticks:[...document.querySelectorAll('#plot text')].map(c=>c.textContent),sampleVisible:document.querySelector('#sample-label').style.display}};
 },{d,model});
 out.id=d.id;out.model=model;out.k=d.k;out.key=key;
 const filename=key.replaceAll(':','_')+'.json';fs.writeFileSync(`app-${variant}/${filename}`,JSON.stringify(out));
 fs.writeFileSync(`app-${variant}/${filename.replace('.json','.txt')}`,out.points.map(p=>p.members.join(',')).join('\n'));
 index.push({key,file:`app-${variant}/${filename}`,n:out.points.length,refused:out.summary===null});
 if(index.length%20===0)console.log(`${variant}: ${index.length}/${corpus.length*2} configurations`);
}
fs.writeFileSync(`app-${variant}.json`,JSON.stringify({index,errors,page_sha256:require('crypto').createHash('sha256').update(html).digest('hex'),seconds:(Date.now()-start)/1000,chrome:browser.version()},null,2));
console.log(`${variant}: ${index.length} configurations captured; ${errors.length} page errors`);
await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
