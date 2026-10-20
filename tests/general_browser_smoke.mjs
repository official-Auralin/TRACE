// Renderer/interactions only. Supply an independently compiled public item JSON.
// No answer key or private certificate is injected into the page.
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import {createRequire} from 'node:module';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
const require=createRequire(import.meta.url);
const {chromium}=require(process.env.TRACE_PLAYWRIGHT_MODULE||'playwright');
const item=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const output=process.argv[3]||fs.mkdtempSync(path.join(os.tmpdir(),'trace-general-ui-'));
fs.mkdirSync(output,{recursive:true});
const browser=await chromium.launch({headless:true,...(process.env.TRACE_CHROME?{executablePath:process.env.TRACE_CHROME}:{})});
try{
  const page=await browser.newPage({viewport:{width:1280,height:1050}}),errors=[];
  page.on('pageerror',e=>errors.push(String(e)));
  await page.setContent('<main><h1>Which switches matter?</h1><div class="workbench"><div id="board" class="board-host"></div></div></main>');
  await page.addStyleTag({content:fs.readFileSync(new URL('../web/style.css',import.meta.url),'utf8')});
  await page.addScriptTag({content:fs.readFileSync(new URL('../web/board.js',import.meta.url),'utf8')});
  await page.evaluate(item=>{window.fixture=item;window.selected=new Set();window.navigation=[];window.draw=()=>TRACEBoard.render(document.getElementById('board'),fixture,{interactive:true,selected,onNavigate:event=>navigation.push(event),onSelect:cell=>{selected.has(cell)?selected.delete(cell):selected.add(cell);draw();}});draw();},item);
  assert.deepEqual(await page.evaluate(()=>TRACEBoard.walk(fixture.board,fixture.observed)),item.board.recorded_path);
  assert.equal(await page.locator('[data-target-lamp]').count(),1);
  assert.equal(await page.locator('[data-dark-exit]').count(),1);
  assert.equal(await page.locator('.lamp-glass').count(),1);
  const first=page.locator('#board .switch-node').first();
  const hasVisibleSwitch=(await first.count())>0;
  if(hasVisibleSwitch){
    const cell=await first.getAttribute('data-cell');await first.focus();await page.keyboard.press('Space');
    assert.equal(await page.locator('.switch-node:focus').getAttribute('data-cell'),cell);
    await page.setViewportSize({width:1260,height:1050});await page.waitForTimeout(100);
    assert.equal(await page.locator('.switch-node:focus').getAttribute('data-cell'),cell,'Resize redraw preserves keyboard focus');
    const copies=page.locator('.switch-node[data-cell="'+cell+'"]');
    for(let i=0;i<await copies.count();i++)assert.equal(await copies.nth(i).getAttribute('aria-pressed'),'true');
    await page.keyboard.press('Enter');assert.equal(await page.locator('.switch-node:focus').getAttribute('aria-pressed'),'false');
  }
  await page.getByRole('spinbutton',{name:'Go to moment',exact:true}).fill(String(item.board.horizon));
  await page.getByRole('spinbutton',{name:'Go to route',exact:true}).fill(String(item.board.states));
  await page.getByRole('button',{name:'Go',exact:true}).click();
  // Even a cell omitted by decision-tree reduction remains a valid selectable input.
  assert.equal(await page.locator('[data-inventory-cell="'+((item.board.horizon-1)*item.board.inputs)+'"]').count(),1);
  await page.locator('.circuit-switches button').first().click();
  assert.equal(await page.locator('.circuit-switches button').first().getAttribute('aria-pressed'),'true');
  await page.getByRole('button',{name:'Overview',exact:true}).click();
  await page.screenshot({path:path.join(output,'general-overview.png'),fullPage:true});
  await page.getByRole('button',{name:'Target',exact:true}).click();
  const targetBox=await page.locator('[data-target-lamp] .lamp-glass').boundingBox(),viewBox=await page.locator('.circuit-viewport').boundingBox();
  assert(targetBox.width>=40&&targetBox.x>=viewBox.x&&targetBox.x+targetBox.width<=viewBox.x+viewBox.width);
  assert(targetBox.y>=viewBox.y&&targetBox.y+targetBox.height<=viewBox.y+viewBox.height);
  await page.screenshot({path:path.join(output,'general-target.png'),fullPage:true});
  await page.getByRole('button',{name:'Start',exact:true}).click();
  const before=await page.locator('.general-board-svg').getAttribute('viewBox');
  await page.getByRole('button',{name:'−',exact:true}).click();
  assert.notEqual(await page.locator('.general-board-svg').getAttribute('viewBox'),before);
  await page.screenshot({path:path.join(output,'general-desktop.png'),fullPage:true});
  await page.setViewportSize({width:390,height:844});
  await page.waitForTimeout(100);
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await page.getByRole('button',{name:'Start',exact:true}).click();
  await page.screenshot({path:path.join(output,'general-mobile.png'),fullPage:true});
  // Drag and keyboard movement navigate the same semantic board.
  const viewport=page.locator('.circuit-viewport');await page.getByRole('button',{name:'+',exact:true}).click();await viewport.focus();
  const initial=await page.locator('.general-board-svg').getAttribute('viewBox');await page.keyboard.press('ArrowRight');
  if(item.board.horizon>1)assert.notEqual(await page.locator('.general-board-svg').getAttribute('viewBox'),initial);
  await page.evaluate(()=>document.getElementById('board').replay());
  await page.waitForTimeout(600);assert(await page.locator('.signal-dot').count());
  const events=await page.evaluate(()=>navigation);
  for(const kind of ['jump','overview','start','zoom','pan','replay'])assert(events.some(event=>event.kind===kind),'Navigation callback '+kind);
  for(const event of events){assert(event.view.x>=0&&event.view.y>=0&&event.view.zoom>0);assert(event.view.moment>=0&&event.view.moment<item.board.horizon);assert(event.view.route>=0&&event.view.route<item.board.states);}
  assert.equal(errors.length,0,errors.join('\n'));
  const report={status:'PASS',item:item.id,fixture_sha256:createHash('sha256').update(fs.readFileSync(process.argv[2])).digest('hex'),board_source_sha256:createHash('sha256').update(fs.readFileSync(new URL('../web/board.js',import.meta.url))).digest('hex'),style_source_sha256:createHash('sha256').update(fs.readFileSync(new URL('../web/style.css',import.meta.url))).digest('hex'),test_source_sha256:createHash('sha256').update(fs.readFileSync(new URL(import.meta.url))).digest('hex'),screenshots:output,not_applicable:hasVisibleSwitch?[]:['keyboard switch-node selection: constant fixture has no switch nodes'],checks:['browser/source path agreement','one fixed target lamp and distinct dark exit','intermediate outputs are not lamps',...(hasVisibleSwitch?['keyboard selection and focus','resize redraw preserves keyboard focus','linked visual copies']:[]),'all input cells selectable after reduction','navigation to final moment and route','overview','target navigation restores readable scale','zoom','mobile page width','keyboard pan','recorded replay','navigation telemetry callbacks','no page errors'],scope:'Synthetic renderer fixture; not participant comprehension, enjoyment, server behavior, or live agent performance.'};
  fs.writeFileSync(path.join(output,'report.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
}finally{await browser.close();}
