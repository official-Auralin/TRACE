// Researcher-only browser QA. Answers are held by this fixture process, never
// injected into participant observations. These are synthetic baseline sessions.
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import os from 'node:os';
import path from 'node:path';
import {spawn,spawnSync} from 'node:child_process';
import {createRequire} from 'node:module';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
const require=createRequire(import.meta.url);
const {chromium}=require(process.env.TRACE_PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const temp=fs.mkdtempSync(path.join(os.tmpdir(),'trace-visual-browser-'));
const python=process.env.TRACE_PYTHON||'python3';
const database=path.join(temp,'study.sqlite3');
const databaseEvidence=path.join(root,'artifacts/terminal-display-v5/session','synthetic-'+Date.now()+'.sqlite3');
const setup=`import json,sys
from benchmark.runtime import StudyStore
from benchmark.server import Handler
from benchmark.game import solve
from http.server import ThreadingHTTPServer
s=StudyStore(sys.argv[1])
form=next((name for name,f in s.forms.items() if f['split']=='pilot' and len(solve(s.items[f['item_ids'][0]]) or [])>1),'pilot-01')
sessions={condition:s.create('baseline','browser-'+condition,'pilot',form,condition,metadata={'system_id':'browser-fixture'}) for condition in ('probe','reasoning')}
ids=set(s.forms[form]['item_ids']) | set(s.forms[form].get('tutorial_ids',s.manifest.get('tutorial_ids',s.forms.get('tutorial-01',{}).get('item_ids',[])[:2])))
v=ThreadingHTTPServer(('127.0.0.1',0),Handler);v.store=s
print(json.dumps({'port':v.server_port,'sessions':sessions,'dataset_sha256':s.manifest['dataset_sha256'],'source_provenance':s.provenance,'answers':{i:[solve(s.items[i])] for i in ids}}),flush=True)
v.serve_forever()`;
const server=spawn(python,['-B','-u','-c',setup,database],{cwd:root,env:{...process.env,PYTHONDONTWRITEBYTECODE:'1'},stdio:['ignore','pipe','pipe']});
let browser;let serverErrors='';server.stderr.on('data',chunk=>{serverErrors+=chunk});
try{
  const info=await new Promise((resolve,reject)=>{let text='';server.on('error',reject);server.stdout.on('data',chunk=>{text+=chunk;if(text.includes('\n'))resolve(JSON.parse(text.split('\n')[0]));});server.on('exit',code=>reject(new Error('Study server exited '+code+' '+serverErrors)));});
  browser=await chromium.launch({headless:true,...(process.env.TRACE_CHROME?{executablePath:process.env.TRACE_CHROME}:{})});
  const page=await browser.newPage({viewport:{width:1440,height:1100}});page.setDefaultTimeout(15000);const errors=[];page.on('pageerror',error=>errors.push(String(error)));
  fs.mkdirSync(path.join(root,'artifacts/terminal-display-v5/session'),{recursive:true});
  async function state(){return page.evaluate(async()=>{const response=await fetch('/api/state',{headers:{'X-Trace-Token':new URLSearchParams(location.hash.slice(1)).get('token')}});if(!response.ok)throw Error(await response.text());return response.json()})}
  async function select(cells){for(const cell of cells)await page.locator(`#board .switch-node[data-cell="${cell}"]`).first().click()}
  async function tutorials(condition){
    await page.goto(`http://127.0.0.1:${info.port}/#token=${info.sessions[condition].token}`);
    await page.locator('#demoBoard svg').waitFor();const intro=await state();assert.equal(intro.active,false);assert(!('deadline' in intro));
    assert.equal(await page.locator('#demoTabs button').count(),intro.demonstrations.length);
    // Onboarding uses the same public examples/frames as the agent observation.
    for(const [index,demo] of intro.demonstrations.entries()){
      await page.locator('#demoTabs button').nth(index).click();assert.equal(await page.locator('#demoBoard .switch-node').count(),demo.item.board.nodes.filter(node=>node.kind==='switch').length);
      await page.locator('#demoChange').click();assert.match(await page.locator('#demoCount').textContent(),/\d/);await page.locator('#demoHold').click();
      if(demo.id==='demo-and'){
        assert((await page.locator('#demoBadge').getAttribute('class')).includes('fail'));
        if(condition==='probe'){
          await page.setViewportSize({width:1440,height:1600});
          await page.locator('#demoCases button').nth(demo.cases.findIndex(example=>example.correct)).click();
          await page.locator('#demoHold').click();
          await page.evaluate(()=>{window.scrollTo(0,0);document.getElementById('demoBoard').scrollTop=0;});
          await page.screenshot({path:path.join(root,'artifacts/terminal-display-v5/session/demo-hold.png'),clip:await page.locator('#demoBoard').boundingBox()});
          await page.locator('#demoChange').click();assert.match(await page.locator('#demoCount').textContent(),/light off/);
          await page.evaluate(()=>{window.scrollTo(0,0);document.getElementById('demoBoard').scrollTop=0;});
          await page.screenshot({path:path.join(root,'artifacts/terminal-display-v5/session/demo-change.png'),clip:await page.locator('#demoBoard').boundingBox()});
          await page.locator('#demoCases button').first().click();await page.locator('#demoHold').click();
          await page.setViewportSize({width:1440,height:1100});
        }
      }
      if(demo.id==='demo-or'){await page.locator('#demoChange').click();assert((await page.locator('#demoBadge').getAttribute('class')).includes('fail'));await page.locator('#demoHold').click();}
      if(demo.id==='demo-choice'){await page.locator('#demoCases button').last().click();assert.match(await page.locator('#demoCaption').textContent(),/extra mark/);}
      if(demo.id==='demo-xor'){
        const copies=page.locator('#demoBoard .switch-node[data-cell="2"]');assert.equal(await copies.count(),2);assert.equal(await copies.nth(0).getAttribute('aria-pressed'),await copies.nth(1).getAttribute('aria-pressed'));
      }
    }
    await page.locator('#demoTabs button').first().click();
    if(condition==='probe')await page.screenshot({path:path.join(root,'artifacts/terminal-display-v5/session/browser-onboarding.png'),fullPage:true});
    await page.locator('#next').click();
    for(let i=0;i<2;i++){
      await page.locator('#task').waitFor({state:'visible'});const obs=await state();assert(obs.practice);
      // First practice response is deliberately wrong, to verify a concrete HOLD
      // counterexample. The second uses a valid solution from the private fixture.
      if(i===0&&condition==='reasoning')await select([0,1]);
      if(i===1)await select(info.answers[obs.item.id][0]);
      await page.locator('#submit').click();await page.locator('#feedback').waitFor({state:'visible'});
      const done=await state();const feedback=done.last_receipt.feedback;
      assert.equal(feedback.correct,i===1);assert.deepEqual(feedback.item,obs.item);assert.deepEqual(feedback.accepted_explanations,info.answers[obs.item.id]);
      assert(await page.locator('#feedbackBoard .switch-node').count()>0);
      assert.equal(await page.locator('#feedbackTests button').count(),3);
      if(i===0&&condition==='probe'){assert(feedback.tests.guarantee.witness);assert.equal(feedback.tests.guarantee.witness.target_flashes,false);}
      if(i===0&&condition==='reasoning'){
        assert(feedback.tests.guarantee.passed&&feedback.tests.prevention.passed);
        assert.equal(feedback.tests.minimality.passed,false);
        assert.equal(await page.locator('#feedbackRuns button').count(),2);
        assert.equal(await page.locator('#feedbackBoard [data-target-lamp]').count(),1);
        assert.equal(await page.locator('#feedbackBoard [data-target-lamp]').getAttribute('data-target-on'),'true');
        await page.locator('#feedbackRuns button').last().click();
        assert.equal(await page.locator('#feedbackBoard [data-target-lamp]').getAttribute('data-target-on'),'true');
        assert.match(await page.locator('#feedbackCaption').textContent(),/Only A · 2 is flipped/);
        assert.equal((await state()).probes_used,undefined);
        await page.screenshot({path:path.join(root,'artifacts/terminal-display-v5/session/redundant-mark-flipped.png'),fullPage:true});
      }
      await page.locator('#continue').click();
    }
    await page.locator('#task').waitFor({state:'visible'});assert.equal((await state()).practice,false);
  }
  await tutorials('probe');const before=await state();assert.equal(before.protocol_version,'trace-study-v5');assert.equal(before.training_examples.length,2);
  assert.deepEqual(Object.keys(before.item).sort(),['id','machine','observed','observed_outputs','observed_states','semantics','target_step','board'].sort());
  for(const example of before.training_examples){assert(Array.isArray(example.accepted_explanations));assert(example.feedback);assert(!('key' in example.item));}
  await page.locator('#showLesson').click();await page.locator('#lessonDialog').waitFor({state:'visible'});
  assert.equal(await page.locator('#lessonDialog .practice-reference').count(),before.training_examples.length);
  assert.equal(await page.locator('#lessonDialog .dialog-demo').count(),before.demonstrations.length+before.training_examples.length);
  await page.locator('#lessonDialog .practice-reference').first().getByRole('button',{name:'Your hold test'}).click();
  assert.match(await page.locator('#lessonDialog .practice-reference').first().textContent(),/Hold failed/);
  await page.locator('#closeLesson').click();
  assert(await page.locator('#board .switch-node').count()>0);
  await page.waitForFunction(()=>/^\d+:\d{2}$/.test(document.getElementById('timer').textContent));assert(await page.locator('#timer').isVisible());
  assert.equal(await page.locator('#task table').count(),0);assert(await page.locator('#machine').isHidden());
  const navigationResponse=page.waitForResponse(response=>response.url().endsWith('/api/navigate')&&response.request().postDataJSON().kind==='zoom');
  await page.locator('#board').getByRole('button',{name:'+',exact:true}).click();assert.equal((await navigationResponse).status(),200);
  const navigated=await state();assert.equal(navigated.deadline,before.deadline);assert.equal(navigated.probes_used,before.probes_used);
  await page.locator('#board').getByRole('button',{name:'Overview',exact:true}).click();
  const observedPath=await page.evaluate(item=>TRACEBoard.walk(item.board,item.observed),before.item);assert.deepEqual(observedPath,before.item.board.recorded_path);
  await page.locator('#replay').click();assert.equal((await state()).probes_used,0);
  const firstCell=Number(await page.locator('#board .switch-node').first().getAttribute('data-cell'));
  const first=page.locator(`#board .switch-node[data-cell="${firstCell}"]`).first();await first.focus();await page.keyboard.press('Space');assert.equal(await first.getAttribute('aria-pressed'),'true');
  assert.equal(await first.evaluate(element=>document.activeElement===element),true);
  await page.keyboard.press('Enter');assert.equal(await first.getAttribute('aria-pressed'),'false');
  await page.locator('details.technical > summary').click();await page.locator('#noExplanation').check();assert.match(await page.locator('#selected').textContent(),/No switch|cannot|No explanation/i);
  await first.click();assert(!(await page.locator('#noExplanation').isChecked()));await first.click();await page.locator('details.technical > summary').click();
  await page.locator('#probePanel > summary').click();
  await page.locator(`[data-probe="${firstCell}"]`).selectOption(String(1-before.item.observed.flat()[firstCell]));
  for(let i=0;i<8;i++){await page.locator('#probe').click();await page.waitForFunction(n=>document.getElementById('probeCount').textContent.startsWith(n+' /'),i+1);}
  assert(await page.locator('#probe').isDisabled());const probed=await state();assert.equal(probed.probes_used,8);assert.equal(probed.probe_history[0].result.switches_changed,1);
  assert.deepEqual(probed.probe_history[0].result.board_path,await page.evaluate(({item,inputs})=>TRACEBoard.walk(item.board,inputs),{item:probed.item,inputs:probed.probe_history[0].result.inputs}));
  await page.reload();await page.locator('#task').waitFor({state:'visible'});const after=await state();
  assert.equal(before.deadline,after.deadline);assert.equal(after.probes_used,8);assert.equal(after.probe_history.length,8);
  const selectedAnswer=info.answers[after.item.id].at(-1);await select(selectedAnswer);
  await page.screenshot({path:path.join(root,'artifacts/terminal-display-v5/session/browser-desktop.png'),fullPage:true});
  await page.setViewportSize({width:390,height:844});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth));
  await page.screenshot({path:path.join(root,'artifacts/terminal-display-v5/session/browser-mobile.png'),fullPage:true});
  await page.locator('#board').getByRole('button',{name:'Overview',exact:true}).click();
  assert.equal(await page.locator('#board [data-target-lamp]').count(),1);
  await page.screenshot({path:path.join(root,'artifacts/terminal-display-v5/session/browser-mobile-target.png'),fullPage:true});
  await page.locator('#submit').click();await page.locator('#receipt').waitFor({state:'visible'});assert(await page.locator('#feedback').isHidden());
  const received=await state();assert(!('feedback' in received.last_receipt));assert(!('correct' in received.last_receipt));
  await page.setViewportSize({width:1440,height:1100});await tutorials('reasoning');assert(await page.locator('#probePanel').isHidden());
  await page.locator('#replay').click();assert.equal((await state()).probes_used,0);
  await page.locator('details.technical > summary').click();await page.locator('#noExplanation').check();await page.locator('#submit').click();await page.locator('#receipt').waitFor({state:'visible'});assert(await page.locator('#feedback').isHidden());
  for(const privatePath of ['/data/corpus.json','/data/certificates.json','/benchmark/core.py','/.git/config','/archive/v2-textbook/README.md'])assert.equal((await page.request.get(`http://127.0.0.1:${info.port}${privatePath}`)).status(),404);
  const inspect=`import sqlite3,json,sys
c=sqlite3.connect('file:'+sys.argv[1]+'?mode=ro',uri=True)
print(json.dumps([json.loads(row[0]) for row in c.execute('SELECT payload FROM events') if json.loads(row[0]).get('record_type') in ('trial','navigation')]))`;
  const inspected=spawnSync(python,['-B','-c',inspect,database],{cwd:root,encoding:'utf8'});assert.equal(inspected.status,0,inspected.stderr);const events=JSON.parse(inspected.stdout),trials=events.filter(e=>e.record_type==='trial'&&e.split==='pilot'),navigation=events.filter(e=>e.record_type==='navigation');
  const accepted=trials.find(t=>t.session_id===info.sessions.probe.session_id);assert(accepted.correct);assert.deepEqual(accepted.response,{cells:[...selectedAnswer].sort((a,b)=>a-b)});assert.equal(accepted.probes_used,8);assert.equal(accepted.attempts_used,1);assert.equal(accepted.deadline,before.deadline);assert(navigation.some(e=>e.session_id===info.sessions.probe.session_id&&e.item_id===before.item.id&&e.kind==='zoom'));
  const noAnswer=trials.find(t=>t.session_id===info.sessions.reasoning.session_id);assert.deepEqual(noAnswer.response,{verdict:'no_explanation'});assert.equal(noAnswer.correct,false);assert.equal(noAnswer.probes_used,0);
  assert.equal(errors.length,0,errors.join('\n'));assert.equal(serverErrors,'');
  const report={status:'PASS',scope:'Synthetic browser fixture only; no participant comprehension, enjoyment, human ease, or live model inference is established.',dataset_sha256:info.dataset_sha256,source_provenance:info.source_provenance,browser_test_sha256:createHash('sha256').update(fs.readFileSync(fileURLToPath(import.meta.url))).digest('hex'),browser:await browser.version(),checks:['five visual examples available before timer','HOLD and CHANGE demonstration frames including failed guarantee/prevention and extra marks','linked switches share selection','wrong practice has concrete counterexample','correct practice answer accepted','practice feedback persists in shared agent context','human reference dialog exposes the same practice feedback','explicit public board allowlist','visible route agrees with public graph','primary puzzle has no transition table','recorded replay costs zero probes','navigation recorded without changing deadline, probes, or attempts','keyboard switch selection','exclusive typed no-explanation answer','solver-produced minimal explanation accepted','eight charged probes and visual paths','visible countdown, unchanged deadline and history after reload','scored correctness withheld','reasoning arm hides simulator','private and archived routes denied','desktop and 390px mobile without page overflow','mobile overview exposes the single target lamp','extra-mark practice pair reaches the same target without experiments','no browser or server errors'],raw_session_database:databaseEvidence,canonical_answers_tested:info.answers[after.item.id].length,navigation_records:navigation.length};
  fs.writeFileSync(path.join(root,'artifacts/terminal-display-v5/session/report.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
}finally{
  if(browser)await browser.close();
  if(fs.existsSync(database)){
    fs.mkdirSync(path.dirname(databaseEvidence),{recursive:true});
    const backup=spawnSync(python,['-B','-c','import sqlite3,sys; source=sqlite3.connect("file:"+sys.argv[1]+"?mode=ro",uri=True); target=sqlite3.connect(sys.argv[2]); source.backup(target); target.close(); source.close()',database,databaseEvidence],{cwd:root,encoding:'utf8'});
    if(backup.status!==0)console.error('Could not preserve synthetic session database:',backup.stderr);
  }
  server.kill();fs.rmSync(temp,{recursive:true,force:true});
}
