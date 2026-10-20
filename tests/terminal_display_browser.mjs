// Reproduce the reported two-switch ambiguity against a natively compiled public
// fixture. Only semantic inputs enter the page; expected outcomes stay in QA.
import fs from 'node:fs';
import path from 'node:path';
import {createRequire} from 'node:module';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
const require=createRequire(import.meta.url);
const {chromium}=require(process.env.TRACE_PLAYWRIGHT_MODULE||'playwright');
const item=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const output=process.argv[3]||'artifacts/terminal-display-v5/target-regression';
fs.mkdirSync(output,{recursive:true});
assert.equal(item.board.states,2);assert.equal(item.board.inputs,1);assert.equal(item.board.horizon,2);
assert.deepEqual(item.board.display.terminal[1],{kind:'outcome',value:1});
const browser=await chromium.launch({headless:true,...(process.env.TRACE_CHROME?{executablePath:process.env.TRACE_CHROME}:{})});
try{
  const page=await browser.newPage({viewport:{width:1280,height:1000}}),errors=[];
  page.on('pageerror',e=>errors.push(String(e)));
  await page.setContent('<main><h1>Which switches matter?</h1><div class="workbench"><div id="board" class="board-host"></div></div></main>');
  await page.addStyleTag({content:fs.readFileSync(new URL('../web/style.css',import.meta.url),'utf8')});
  await page.addScriptTag({content:fs.readFileSync(new URL('../web/board.js',import.meta.url),'utf8')});
  let destination=null;
  for(const [a,b,expected] of [[0,0,1],[0,1,1],[1,0,0],[1,1,1]]){
    const observed=await page.evaluate(({item,a,b})=>{window.fixture=item;const result=TRACEBoard.render(document.getElementById('board'),item,{inputs:[[a],[b]],selected:new Set([0]),animate:false});return{path:result.path,semantic:TRACEBoard.execute(item.board,[[a],[b]]),display:TRACEBoard.displayExecute(item.board,[[a],[b]])};},{item,a,b});
    await page.getByRole('button',{name:'Overview',exact:true}).click();
    assert.equal(await page.locator('[data-target-lamp]').count(),1);
    assert.equal(await page.locator('[data-dark-exit]').count(),1);
    assert.equal(await page.locator('.lamp-glass').count(),1,'No transition output is an additional lamp');
    assert.equal(await page.locator('[data-target-lamp]').getAttribute('data-target-on'),String(Boolean(expected)));
    assert.equal(observed.display.outcome,expected);
    assert.equal(observed.path.at(-1),expected?'target-lamp':'dark-exit');
    assert.equal(await page.locator('.switch-node[data-node^="1:1:"]').count(),0,'Constant final route has no switch');
    assert.equal(await page.locator('.switch-node[data-node^="1:0:"][data-cell="1"]').count(),1,'Conditional relevance remains visible');
    assert.equal(await page.locator('[data-output-node^="0:1:"]').count(),2,'Earlier equal-output transitions remain distinct');
    const geometry=await page.locator('[data-target-lamp] .lamp-glass').evaluate(e=>[e.getAttribute('cx'),e.getAttribute('cy')]);
    if(destination)assert.deepEqual(geometry,destination,'Target identity and position stay fixed across runs');else destination=geometry;
    for(const wire of await page.locator('[data-final-outcome="1"]').all())assert.equal(await wire.getAttribute('data-destination'),'target-lamp');
    for(const wire of await page.locator('[data-final-outcome="0"]').all())assert.equal(await wire.getAttribute('data-destination'),'dark-exit');
    assert.equal(await page.locator('[data-final-outcome].live').count(),1);
    assert.equal(await page.locator('[data-final-outcome].live').getAttribute('data-final-outcome'),String(expected));
    const labels=await page.locator('.switch-node .switch-label').allTextContents();
    assert(labels.includes('A · 1')&&labels.includes('A · 2'));
    const selected=await page.locator('.switch-node.selected').evaluateAll(nodes=>nodes.map(e=>Number(e.dataset.cell)));
    assert(selected.every(cell=>cell===0),'Marking moment 1 must not alias moment 2');
    await page.screenshot({path:path.join(output,`setting-${a}${b}.png`),fullPage:true});
  }
  assert.deepEqual(errors,[]);
  const report={status:'PASS',fixture:item.id,fixture_sha256:createHash('sha256').update(fs.readFileSync(process.argv[2])).digest('hex'),board_source_sha256:createHash('sha256').update(fs.readFileSync(new URL('../web/board.js',import.meta.url))).digest('hex'),test_source_sha256:createHash('sha256').update(fs.readFileSync(new URL(import.meta.url))).digest('hex'),settings:4,checks:['one persistent target lamp','one distinct dark exit','all successful branches converge on the same lamp','all failed branches converge on the dark exit','gold trail agrees with target result for every input setting','constant final route has no irrelevant switch','conditionally relevant final switch remains','earlier equal outputs retain next-state distinctions','moment labels and selections do not alias','no browser errors'],scope:'Rendered target semantics for the reported regression; not evidence of participant comprehension.'};
  fs.writeFileSync(path.join(output,'report.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
}finally{await browser.close();}
