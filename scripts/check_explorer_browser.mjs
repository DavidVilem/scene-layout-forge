// Real browser exercise; screenshots require a separate visual review.
import {createRequire} from 'node:module';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const [runtime,html,out,executable]=process.argv.slice(2);
if(!runtime||!html||!out||!executable)throw Error('Usage: runtime-workspace html out-dir browser-executable');
const require=createRequire(path.join(path.resolve(runtime),'package.json'));
const {chromium}=require('playwright');mkdirSync(out,{recursive:true});
const browser=await chromium.launch({headless:true,executablePath:executable,args:['--enable-unsafe-swiftshader','--use-angle=swiftshader-webgl']});
const errors=[],network=[];
const context=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
await context.route(/^https?:/,route=>{network.push(route.request().url());return route.abort();});
const page=await context.newPage();page.on('pageerror',e=>errors.push(String(e)));
const report={candidate_sha256:createHash('sha256').update(readFileSync(html)).digest('hex')};
const check=(name,value)=>{report[name]=!!value;if(!value)throw Error('Failed browser check: '+name);};
try{
 await page.goto(pathToFileURL(path.resolve(html)).href);await page.waitForFunction(()=>window.__explorer?.ready,{timeout:20000});
 await page.waitForTimeout(400);check('webgl',await page.evaluate(()=>!!document.querySelector('canvas').getContext('webgl2')));
 await page.screenshot({path:path.join(out,'assembled.png'),fullPage:true});
 const references=page.locator('[data-image]:visible');
 for(let i=0;i<await references.count();i++){await references.nth(i).click();await page.waitForFunction(()=>{const im=document.getElementById('reference');return im.complete&&im.naturalWidth>0;});}
 if(await references.count())await page.locator('[data-view="iso"]').click();
 check('source_reference',true);
 const buttons=page.locator('[data-select]');const id=await buttons.nth(1).getAttribute('data-select');await buttons.nth(1).click();
 check('selection',(await page.evaluate(()=>window.__explorer.snapshot())).selected===id);
 check('no_separation_controls',await page.locator('#explode, #toggleExplode').count()===0);
 const original=await page.evaluate(()=>window.__explorer.snapshot().positions);
 await page.locator('#isolate').click();
 const isolated=await page.evaluate(()=>window.__explorer.snapshot());
 check('isolation',isolated.visible.length===1&&JSON.stringify(isolated.positions)===JSON.stringify(original));
 await page.screenshot({path:path.join(out,'isolated.png'),fullPage:true});
 await page.locator('#showAll').click();await page.locator('#reset').click();
 const restored=await page.evaluate(()=>window.__explorer.snapshot());
 check('fixed_assemblies',restored.fixed===true&&JSON.stringify(original)===JSON.stringify(restored.positions)&&Object.values(restored.positions).every(v=>v.every(x=>x===0)));
 check('reset',restored.visible.length===restored.assemblies);
 let views=true;for(const name of ['top','front','side','iso']){await page.locator(`[data-view="${name}"]`).click();views&&=(await page.evaluate(()=>window.__explorer.snapshot())).view===name;if(name==='top')await page.screenshot({path:path.join(out,'plan.png'),fullPage:true});}
 check('views',views);
 await page.locator('#cutEnabled').check();await page.locator('#cut').fill('40');await page.locator('#cut').dispatchEvent('input');
 check('section',(await page.evaluate(()=>window.__explorer.snapshot())).clip);await page.screenshot({path:path.join(out,'section.png'),fullPage:true});
 await page.locator('#cutEnabled').uncheck();await buttons.nth(1).click();await page.locator('#isolate').click();
 check('visibility',(await page.evaluate(()=>window.__explorer.snapshot())).visible.length===1);await page.locator('#reset').click();
 await page.locator('#viewport').focus();const before=await page.evaluate(()=>window.__explorer.snapshot().camera);await page.keyboard.press('ArrowLeft');
 const after=await page.evaluate(()=>window.__explorer.snapshot().camera);check('keyboard',JSON.stringify(before)!==JSON.stringify(after));await page.keyboard.press('Escape');
 const download=page.waitForEvent('download');await page.locator('#export').click();const file=await download;await file.saveAs(path.join(out,'plan.svg'));
 check('svg_export',readFileSync(path.join(out,'plan.svg'),'utf8').includes('<polygon'));
 await page.setViewportSize({width:390,height:844});await page.waitForTimeout(200);await page.screenshot({path:path.join(out,'mobile.png'),fullPage:true});
 check('mobile',await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1&&document.querySelector('canvas').getBoundingClientRect().width>100));
 check('offline',network.length===0);report.errors=errors;report.requests=network;
 if(errors.length)throw Error(errors.join('\n'));
}catch(error){report.errors=[...errors,String(error)];writeFileSync(path.join(out,'browser-report.json'),JSON.stringify(report,null,2));throw error;}
finally{await browser.close();}
writeFileSync(path.join(out,'browser-report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
