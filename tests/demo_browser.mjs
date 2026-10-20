// End-to-end public demo checks, including GitHub project-path hosting.
// These exercise software behavior, not human comprehension or difficulty.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import {pathToFileURL} from 'node:url';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const playwright=process.env.TRACE_PLAYWRIGHT_MODULE;
const {chromium}=playwright ? await import(pathToFileURL(path.resolve(playwright))) : require('playwright');
const site=path.resolve(process.argv[2]||'artifacts/pages-demo');
const output=path.resolve(process.argv[3]||path.join(path.dirname(site),'demo-browser-checks'));
const catalog=JSON.parse(fs.readFileSync(path.join(site,'catalog.json'),'utf8'));
const engine=require(path.join(site,'engine.js'));
fs.mkdirSync(output,{recursive:true});
const types={'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json'};
const server=http.createServer((request,response)=>{
  const pathname=new URL(request.url,'http://localhost').pathname;
  if(!pathname.startsWith('/TRACE/')){response.writeHead(404);response.end();return;}
  const relative=decodeURIComponent(pathname.slice('/TRACE/'.length))||'index.html';
  const file=path.resolve(site,relative);
  if(!file.startsWith(site+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){response.writeHead(404);response.end();return;}
  response.writeHead(200,{'Content-Type':types[path.extname(file)]||'application/octet-stream'});fs.createReadStream(file).pipe(response);
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const url='http://127.0.0.1:'+server.address().port+'/TRACE/';
let browser;
const checks=[],check=(name)=>checks.push(name);
try{
  browser=await chromium.launch({headless:true,...(process.env.TRACE_CHROME?{executablePath:process.env.TRACE_CHROME}:{})});
  const context=await browser.newContext({viewport:{width:1280,height:1000}}),page=await context.newPage(),errors=[],requests=[];
  page.on('pageerror',error=>errors.push(error.message));page.on('request',request=>requests.push(request.url()));
  const progress=()=>page.evaluate(()=>{const key=Object.keys(localStorage).find(k=>k.startsWith('trace.demo.progress.'));return JSON.parse(localStorage.getItem(key));});
  const visible=async selector=>{await page.locator(selector).waitFor({state:'visible'});};
  await page.goto(url);await visible('#welcome');
  assert.equal(await page.locator('#error').isVisible(),false);check('curated asset paths work under /TRACE/');
  await page.screenshot({path:path.join(output,'welcome.png'),fullPage:true});
  await page.locator('#startPlay').click();await visible('#play');
  let saved=await progress();const firstId=saved.session.current_item_id;
  assert.equal(firstId,catalog.items[0].id);
  await page.locator('#allSwitches').evaluate(e=>e.open=true);
  await page.locator('#switchList button[data-cell="0"]').click();
  await page.reload();await visible('#welcome');await page.locator('#resume').click();await visible('#play');
  assert.deepEqual((await progress()).session.draft,{cells:[0]});
  assert.equal(await page.locator('#switchList button[data-cell="0"]').getAttribute('aria-pressed'),'true');check('current marks and visit restore across refresh');
  await page.locator('#clear').click();await page.locator('#submit').click();await visible('#receipt');
  saved=await progress();assert.equal(saved.session.entries[firstId].first_submission.result.correct,false);
  assert.equal(saved.session.entries[firstId].reveals.length,0);assert.equal(await page.locator('#revealNote').isVisible(),false);
  check('immediate answer feedback does not reveal a canonical solution');
  await page.locator('#reveal').click();await visible('#revealNote');
  saved=await progress();assert.equal(saved.session.entries[firstId].reveals.length,1);assert.equal(saved.session.entries[firstId].submissions.length,1);
  check('explicit solution reveal is assistance, not a scored completion');
  await page.locator('#retry').click();await visible('#play');await page.locator('#clear').click();
  const firstEntry=catalog.items.find(e=>e.id===firstId),firstItem=JSON.parse(fs.readFileSync(path.join(site,firstEntry.path),'utf8'));
  const solution=engine.solve(firstItem);
  if(solution===null){await page.locator('#noExplanation').evaluate(e=>{e.closest('details').open=true;});await page.locator('#noExplanation').check();}
  else{await page.locator('#allSwitches').evaluate(e=>e.open=true);for(const cell of solution)await page.locator('#switchList button[data-cell="'+cell+'"]').click();}
  await page.locator('#submit').click();await visible('#receipt');
  saved=await progress();let history=saved.session.entries[firstId];
  assert.equal(history.first_submission.result.correct,false);assert.equal(history.submissions.length,2);assert.equal(history.submissions[1].result.correct,true);assert.equal(history.submissions[1].assistance.solution_revealed,true);assert.equal(history.completed,true);
  check('successful assisted retry preserves failed first answer');
  await page.screenshot({path:path.join(output,'desktop-feedback.png'),fullPage:true});
  await page.reload();await visible('#welcome');await page.locator('#resume').click();await visible('#receipt');
  assert.match(await page.locator('#receiptKicker').textContent(),/RETRY/);check('submitted receipt resumes after refresh');
  const secondPath=url+catalog.items[1].path;
  await page.route(secondPath,async route=>{const response=await route.fetch();const text=await response.text();await route.fulfill({response,body:text+' '});});
  await page.locator('#next').click();await visible('#error');
  saved=await progress();assert.equal(saved.session.current_item_id,firstId);assert.equal(Object.keys(saved.session.entries).length,1);
  await page.unroute(secondPath);check('stale or corrupt task is rejected before exposure or progress changes');
  for(let i=0;i<8;i++){await page.locator('#next').click();await visible('#play');await page.locator('#clear').click();await page.locator('#submit').click();await visible('#receipt');}
  saved=await progress();assert.equal(Object.keys(saved.session.entries).length,9);check('continuous play passes four- and six-item boundaries');
  await page.locator('#levels').click();await visible('#catalogDialog');
  const band=catalog.bands.at(-1);await page.locator('#bandSelect').selectOption(band.id);await page.locator('#nextInBand').click();await visible('#play');
  saved=await progress();const largeEntry=catalog.items.find(e=>e.id===saved.session.current_item_id);assert.equal(largeEntry.band,band.id);
  assert.equal(await page.locator('#switchList button').count(),largeEntry.dimensions.cells);check('all structural bands and all input cells are accessible');
  await page.locator('#board .board-navigation button').filter({hasText:/^Overview$/}).click();
  assert.equal(await page.locator('#board [data-target-lamp]').count(),1);
  const dashArrays=await page.locator('#board .rail').evaluateAll(nodes=>nodes.map(n=>getComputedStyle(n).strokeDasharray));assert(dashArrays.length>0&&dashArrays.every(v=>v==='none'));check('single target and unambiguous solid wire convention');
  await page.locator('#noExplanation').evaluate(e=>{e.closest('details').open=true;});await page.locator('#noExplanation').check();await page.locator('#submit').click();await visible('#receipt');
  assert.equal((await progress()).session.entries[largeEntry.id].first_submission.answer.verdict,'no_explanation');check('no-explanation submission is distinct from empty marks');
  const priorCount=Object.keys((await progress()).session.entries).length;
  await page.locator('#learn').click();await visible('#play');assert.match(await page.locator('#itemKicker').textContent(),/LEARN BY PLAYING/);
  await page.locator('#allSwitches').evaluate(e=>e.open=true);await page.locator('#switchList button').first().click();
  await page.reload();await visible('#welcome');await page.locator('#resume').click();await visible('#play');
  assert.match(await page.locator('#itemKicker').textContent(),/LEARN BY PLAYING/);
  assert.equal(await page.locator('#switchList button').first().getAttribute('aria-pressed'),'true');check('teaching draft resumes separately from current puzzle');
  await page.locator('#clear').click();
  await page.locator('#submit').click();await visible('#receipt');
  saved=await progress();assert.equal(Object.keys(saved.session.entries).length,priorCount);assert(saved.session.lessons.length>0);check('interactive teaching attempts remain separate from puzzle scores');
  await page.locator('#scores').click();await visible('#scoresDialog');
  const download=page.waitForEvent('download');await page.locator('#downloadProgress').click();assert.equal((await download).suggestedFilename(),'trace-practice-progress.json');check('local progress can be downloaded');
  await page.locator('[data-close="scoresDialog"]').click();
  await page.setViewportSize({width:390,height:844});await page.locator('#retry').click();await visible('#play');
  const width=await page.evaluate(()=>({document:document.documentElement.scrollWidth,viewport:window.innerWidth}));assert(width.document<=width.viewport+1,'Page itself should not overflow; board scrolls independently');
  await page.screenshot({path:path.join(output,'mobile-teaching.png'),fullPage:true});
  await page.locator('#allSwitches').evaluate(e=>e.open=true);const switchButton=page.locator('#switchList button').first();await switchButton.focus();await page.keyboard.press('Enter');assert.equal(await switchButton.getAttribute('aria-pressed'),'true');check('mobile layout and keyboard switch selection');
  assert.equal(await page.locator('#error').isVisible(),false);assert.deepEqual(errors,[]);
  assert(requests.every(request=>request.startsWith(url)),'No API or third-party requests');check('no collection API, external network dependency, or browser errors');
  const beforeSecondTab=await progress(),secondTab=await page.context().newPage();await secondTab.goto(url);await secondTab.locator('#welcome').waitFor({state:'visible'});await secondTab.locator('#storageNotice').waitFor({state:'visible'});
  await secondTab.locator('#startPlay').click();await secondTab.locator('#play').waitFor({state:'visible'});await secondTab.locator('#submit').click();await secondTab.locator('#receipt').waitFor({state:'visible'});await secondTab.close();
  assert.deepEqual(await progress(),beforeSecondTab);check('second tab cannot overwrite saved first answers');
  const unavailable=await browser.newPage();await unavailable.addInitScript(()=>{Storage.prototype.setItem=function(){throw new DOMException('Simulated full storage','QuotaExceededError');};});
  await unavailable.goto(url);await unavailable.locator('#welcome').waitFor({state:'visible'});await unavailable.locator('#storageNotice').waitFor({state:'visible'});
  await unavailable.locator('#startPlay').click();await unavailable.locator('#play').waitFor({state:'visible'});await unavailable.locator('#submit').click();await unavailable.locator('#receipt').waitFor({state:'visible'});
  assert.equal(await unavailable.locator('#error').isVisible(),false);await unavailable.close();check('storage failure is visible and does not prevent in-memory play');
  const report={status:'PASS',protocol_version:catalog.protocol_version,package_id:catalog.package_id,build_id:catalog.build_id,checks,scope:'Public demo UI/software checks in Chromium. No claim of participant comprehension, enjoyment, human difficulty, or research data collection.'};
  fs.writeFileSync(path.join(output,'report.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
}finally{if(browser)await browser.close();await new Promise(resolve=>server.close(resolve));}
