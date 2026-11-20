// Capture the actual candidate meshes/materials from an explicit review camera.
import {createRequire} from 'node:module';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const [runtime,html,out,executable,cameraFile]=process.argv.slice(2);
const require=createRequire(path.join(path.resolve(runtime),'package.json'));
const {chromium}=require('playwright');const camera=JSON.parse(readFileSync(cameraFile,'utf8'));mkdirSync(out,{recursive:true});
const browser=await chromium.launch({headless:true,executablePath:executable,args:['--enable-unsafe-swiftshader','--use-angle=swiftshader-webgl']});
try{
 const page=await browser.newPage({viewport:{width:1870,height:960},reducedMotion:'reduce'});const errors=[];
 page.on('pageerror',e=>errors.push(String(e)));await page.route(/^https?:/,r=>r.abort());
 await page.goto(pathToFileURL(path.resolve(html)).href);await page.waitForFunction(()=>window.__explorer?.ready);
 // Use native canvas aspect ratio; no image crop, no altered scene or visibility.
 const actual=await page.evaluate(c=>window.__explorer.setReviewCamera(c),camera);
 await page.waitForTimeout(600);await page.locator('#viewport').screenshot({path:path.join(out,'model.png')});
 const sha=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
 writeFileSync(path.join(out,'capture.json'),JSON.stringify({candidate_sha256:sha(html),model_sha256:sha(path.join(out,'model.png')),camera:actual,requested_camera:camera,errors},null,2));
 if(errors.length)throw Error(errors.join('\n'));
}finally{await browser.close();}
