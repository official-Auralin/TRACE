'use strict';
const $=id=>document.getElementById(id),token=new URLSearchParams(location.hash.slice(1)).get('token');
let state=null,chosen=new Set(),busy=false,pending=null,pendingProbe=null,offset=0,demoIndex=0,demoCase=0,demoPhase='hold',demoTimer=null,probeChanges={};
let navigationTimer=null,navigationPending=null;
window.addEventListener('hashchange',()=>{if(new URLSearchParams(location.hash.slice(1)).get('token')!==token)location.reload();});
$('brand').onclick=e=>e.preventDefault();
function error(e){$('error').hidden=false;$('error').textContent=e.message||String(e);}
async function api(action,body){const options={headers:{'X-Trace-Token':token||''}};if(body!==undefined){options.method='POST';options.headers['Content-Type']='application/json';options.body=JSON.stringify(body);}const r=await fetch('/api/'+action,options),s=await r.json();if(!r.ok)throw Error(s.error||'The request could not be completed.');return s;}
function flushNavigation(){clearTimeout(navigationTimer);const payload=navigationPending;navigationPending=null;if(payload)api('navigate',payload).catch(e=>console.warn('Navigation telemetry was not saved:',e.message));}
function recordNavigation(event){if(!state?.active||pending)return;navigationPending={item_id:state.item.id,...event};clearTimeout(navigationTimer);navigationTimer=setTimeout(flushNavigation,200);}
function button(parent,label,action,active=false){const b=document.createElement('button');b.type='button';b.textContent=label;b.classList.toggle('active',active);b.onclick=action;parent.append(b);return b;}
function labels(item,cells){const names=new Map(item.board.switches.map(s=>[s.cell,s.label]));return cells.map(c=>names.get(c)||String(c)).join(' · ');}
function drawDemo(){
 clearInterval(demoTimer);if(!state?.demonstrations?.length)return;$('lesson').hidden=false;
 const demos=state.demonstrations,demo=demos[demoIndex],example=demo.cases[demoCase],stage=example.completions[demoPhase],runs=stage.runs;
 $('demoTabs').replaceChildren();demos.forEach((d,i)=>button($('demoTabs'),String(i+1)+' · '+d.title,()=>{demoIndex=i;demoCase=0;demoPhase='hold';drawDemo();},i===demoIndex));
 $('demoCases').replaceChildren();demo.cases.forEach((c,i)=>button($('demoCases'),c.label,()=>{demoCase=i;drawDemo();},i===demoCase));
 $('demoHold').classList.toggle('active',demoPhase==='hold');$('demoChange').classList.toggle('active',demoPhase!=='hold');
 const passed=example.tests[demoPhase==='hold'?'guarantee':'prevention'].passed;
 $('demoBadge').classList.toggle('fail',!passed);$('demoBadge').textContent=passed?'✓':'×';
 let caption=demoPhase==='hold'?(passed?'Keep the blue marks fixed. The light survives every setting of the other switches.':'Keep the blue marks fixed. An unmarked switch can still send the light out.'):(passed?'Keep unmarked switches recorded. Changing only blue marks can send the light out.':'Even changing the blue marks cannot put the light out. Another route still lights it.');
 if(example.tests.minimality.removable_cells.length)caption+=' Both tests pass, but '+labels(demo.item,example.tests.minimality.removable_cells)+' is an extra mark.';
 if(demo.id==='demo-xor')caption+=' Identical full labels move together; changing just one marked switch can be enough.';
 $('demoCaption').textContent=caption;
 let index=0;const show=()=>{const run=runs[index];TRACEBoard.render($('demoBoard'),demo.item,{selected:new Set(example.selected_cells),inputs:run.inputs,path:run.board_path});$('demoCount').textContent='Setting '+(index+1)+' / '+runs.length+' · '+(run.target_flashes?'light on':'light off');index=(index+1)%runs.length;};show();
 if(runs.length>1)demoTimer=setInterval(show,2400);
}
$('demoHold').onclick=()=>{demoPhase='hold';drawDemo();};$('demoChange').onclick=()=>{demoPhase='change-marked';drawDemo();};
function updateMarks(){
 $('selected').textContent=$('noExplanation').checked?'No switch setting can turn it off':chosen.size?labels(state.item,[...chosen].sort((a,b)=>a-b)):'Choose switches on the board';
 document.querySelectorAll('#switchList button').forEach(b=>b.setAttribute('aria-pressed',String(chosen.has(Number(b.dataset.answerCell)))));
 TRACEBoard.render($('board'),state.item,{selected:chosen,interactive:true,onSelect:toggle,onNavigate:recordNavigation,animate:false});
}
function toggle(cell){if(busy||pending)return;$('noExplanation').checked=false;chosen.has(cell)?chosen.delete(cell):chosen.add(cell);updateMarks();}
$('clear').onclick=()=>{if(busy||pending)return;chosen.clear();$('noExplanation').checked=false;updateMarks();};
$('noExplanation').onchange=()=>{if(busy||pending)return;if($('noExplanation').checked)chosen.clear();updateMarks();};
function render(s){
 state=s;offset=s.server_time-Date.now()/1000;$('error').hidden=true;$('rules').textContent=s.instructions;
 $('progress').textContent=s.active?(s.practice?'Warm-up':'Puzzle')+' '+s.position+' / '+s.total_items:s.complete?'Session complete':'';
 $('timer').hidden=!s.active;
 if(s.limits)$('welcome').textContent='Watch the examples, then play. '+Math.round(s.limits.seconds/60*10)/10+' minutes and one answer per puzzle. Practice puzzles give feedback.';
 if(!s.active){$('task').hidden=true;if(s.last_receipt){receipt(s.last_receipt);if(s.complete)$('continue').hidden=true;}else if(s.complete){$('intro').hidden=true;$('receipt').hidden=false;$('receiptTitle').textContent='Session ended.';$('receiptText').textContent='Your session is closed.';$('continue').hidden=true;$('feedback').hidden=true;}else{$('intro').hidden=false;$('receipt').hidden=true;$('next').disabled=false;drawDemo();}return;}
 clearInterval(demoTimer);$('intro').hidden=true;$('receipt').hidden=true;$('task').hidden=false;
 $('itemlabel').textContent=s.practice?'WARM-UP · TRY YOUR MARKS':'PUZZLE · ONE FINAL ANSWER';$('condition').textContent=s.condition==='probe'?'Up to '+s.limits.probes+' experiments':'Use the visible routes';
 $('submit').innerHTML=(s.practice?'Check my marks':'Submit my marks')+' <span>→</span>';$('submit').disabled=false;$('noExplanation').disabled=false;$('noExplanation').checked=false;
 TRACEBoard.render($('board'),s.item,{selected:chosen,interactive:true,onSelect:toggle,onNavigate:recordNavigation});
 $('selected').textContent='Choose switches on the board';$('machine').textContent='';$('machine').parentElement.ontoggle=()=>{if($('machine').parentElement.open)$('machine').textContent=JSON.stringify(state.item.machine,null,2);};
 $('switchList').replaceChildren();if(s.item.board.version==='trace.board.v2')$('switchList').textContent='The switch strip below the board includes every input at the chosen moment. Use Moment and Go to reach any round, including switches skipped by the routes.';else s.item.board.switches.forEach(sw=>{const b=button($('switchList'),sw.label+' · moment '+(sw.step+1),()=>toggle(sw.cell));b.dataset.answerCell=sw.cell;b.setAttribute('aria-pressed','false');});
 $('probePanel').hidden=s.condition!=='probe';$('probePanel').open=false;$('probeInputs').replaceChildren();$('probeBoard').hidden=true;
 probeChanges={};
 function probeFields(host,switches){host.replaceChildren();switches.forEach(sw=>{const label=document.createElement('label');label.className='probe-field';label.append(document.createTextNode(sw.label));const select=document.createElement('select');select.dataset.probe=sw.cell;select.setAttribute('aria-label','Experiment switch '+sw.label);for(const[v,l]of[['','Recorded'],['0','Upper fork'],['1','Lower fork']]){const o=document.createElement('option');o.value=v;o.textContent=l;select.append(o);}select.value=sw.cell in probeChanges?String(probeChanges[sw.cell]):'';select.onchange=()=>{if(select.value==='')delete probeChanges[sw.cell];else probeChanges[sw.cell]=Number(select.value);};label.append(select);host.append(label);});}
 if(s.item.board.version==='trace.board.v2'){
  const moment=document.createElement('input');moment.type='number';moment.min='1';moment.max=String(s.item.board.horizon);moment.value='1';moment.setAttribute('aria-label','Experiment moment');const fields=document.createElement('div');fields.className='probe-inputs';$('probeInputs').append(moment,fields);
  const show=()=>{const t=Number(moment.value)-1;if(Number.isSafeInteger(t)&&t>=0&&t<s.item.board.horizon)probeFields(fields,s.item.board.switches.slice(t*s.item.board.inputs,(t+1)*s.item.board.inputs));};moment.onchange=show;show();
 }else probeFields($('probeInputs'),s.item.board.switches);
 showProbeHistory();
}
function showProbeHistory(){
 const history=state.probe_history||[];$('probeCount').textContent=state.probes_used+' / '+state.limits.probes+' used';$('probe').disabled=state.probes_used>=state.limits.probes;
 $('probeResult').textContent=history.map((p,i)=>'Experiment '+(i+1)+': '+(p.result.target_flashes?'light on':'light off')+' · changed '+(labels(state.item,Object.keys(p.changes).map(Number))||'nothing')).join('\n');
 if(history.length){const p=history.at(-1),inputs=state.item.observed.map(r=>[...r]),ni=state.item.machine.inputs.length;Object.entries(p.changes).forEach(([c,v])=>inputs[Math.floor(c/ni)][c%ni]=v);$('probeBoard').hidden=false;TRACEBoard.render($('probeBoard'),state.item,{inputs,path:p.result.board_path,selected:new Set()});}
}
function removalIllustration(boardHost,captionHost,controlsHost,item,test){
 const example=test?.removal_example;if(!example)return false;
 const removed=labels(item,[example.removed_cell]);
 function show(index){
  const run=example.runs[index];TRACEBoard.render(boardHost,item,{selected:new Set(example.remaining_cells),inputs:run.inputs,path:run.board_path});
  [...controlsHost.children].forEach((b,i)=>b.classList.toggle('active',i===index));
  captionHost.textContent='Remove the mark on '+removed+': both tests still pass. '+(index===0?'This is the recorded setting.':'Only '+removed+' is flipped here.')+' Both settings reach the same target lamp. This pair illustrates the extra mark; the checker tests every permitted setting.';
 }
 example.runs.forEach((run,index)=>button(controlsHost,index===0?'Recorded setting':'Flip '+removed,()=>show(index)));show(0);return true;
}
function feedbackView(feedback){
 const item=feedback.item,selected=feedback.selected_cells||[],tests=feedback.tests;$('feedbackTests').replaceChildren();$('feedbackChoices').replaceChildren();$('feedbackRuns').replaceChildren();
 function show(kind){
  document.querySelectorAll('#feedbackTests button').forEach(b=>b.classList.toggle('active',b.dataset.test===kind));
  $('feedbackRuns').replaceChildren();const test=tests?.[kind],witness=test?.witness;let marks=selected,caption='';
  if(kind==='minimality'&&removalIllustration($('feedbackBoard'),$('feedbackCaption'),$('feedbackRuns'),item,test))return;
  if(kind==='guarantee')caption=test.passed?'HOLD passed: all settings of the unmarked switches leave the light on. This is the recorded route.':'HOLD failed: this setting of the unmarked switches puts the light out while your marks stay fixed.';
  if(kind==='prevention')caption=test.passed?'CHANGE passed: this setting changes only your marks and puts the light out.':'CHANGE failed: no setting of only your marked switches can turn the light off.';
  if(kind==='minimality'){if(test.removable_cells.length){marks=selected.filter(c=>c!==test.removable_cells[0]);caption='An extra mark: remove '+labels(item,[test.removable_cells[0]])+' and both tests still pass. The recorded setting is unchanged; only the blue marks have been reduced.';}else caption=test.passed?'No spare marks: removing any mark breaks at least one test.':'Pass both tests first; then check for extra marks.';}
  TRACEBoard.render($('feedbackBoard'),item,{selected:new Set(marks),inputs:witness?.inputs,path:witness?.board_path});$('feedbackCaption').textContent=caption;
 }
 if(tests){for(const[k,l]of[['guarantee','Hold'],['prevention','Change'],['minimality','No extras']]){const b=button($('feedbackTests'),'',()=>show(k));b.dataset.test=k;b.classList.toggle('failed',!tests[k].passed);const mark=document.createElement('span');mark.textContent=tests[k].passed?'✓':'×';b.append(mark,document.createTextNode(l));}show(!tests.guarantee.passed?'guarantee':!tests.prevention.passed?'prevention':!tests.minimality.passed?'minimality':'prevention');}
 else{TRACEBoard.render($('feedbackBoard'),item,{selected:new Set(selected)});$('feedbackCaption').textContent=feedback.message||'Review one accepted set of marks below.';}
 (feedback.accepted_explanations||[]).forEach((cells,i)=>button($('feedbackChoices'),'Show an answer '+(i+1)+' · '+labels(item,cells),()=>{$('feedbackRuns').replaceChildren();TRACEBoard.render($('feedbackBoard'),item,{selected:new Set(cells)});$('feedbackCaption').textContent='These marks pass both tests, with no extras. This is one accepted answer.';}));
}
function receipt(r){
 clearInterval(demoTimer);$('task').hidden=true;$('intro').hidden=true;$('receipt').hidden=false;$('timer').hidden=true;$('feedback').hidden=!r.feedback;
 $('receiptKicker').textContent=r.feedback?'WARM-UP':'RESPONSE SAVED';$('receiptIcon').textContent=r.feedback?(r.feedback.correct?'✓':'↗'):'✓';$('receiptIcon').classList.toggle('review',!!r.feedback&&!r.feedback.correct);
 $('receiptTitle').textContent=r.status==='timeout'?'Time is up.':r.feedback?(r.feedback.correct?'Those marks work.':'Follow what happened.'):'Your marks are saved.';
 $('receiptText').textContent=r.feedback?(r.feedback.correct?'Both tests pass, and every mark is needed.':'Review what the two tests found about your marks.'):r.next_available?'Take a breath. Start the next puzzle when you are ready.':'You have reached the end. Thank you for playing.';
 if(r.feedback)feedbackView(r.feedback);$('continue').hidden=!r.next_available;
}
async function next(){if(busy)return;busy=true;try{chosen=new Set();pending=null;pendingProbe=null;render(await api('next',{}));window.scrollTo({top:0,behavior:'smooth'});}catch(e){error(e);}finally{busy=false;}}
$('next').onclick=next;$('continue').onclick=next;$('replay').onclick=()=>{if(state?.active&&!busy)$('board').replay?.();};
$('submit').onclick=async()=>{if(busy||!state?.active)return;flushNavigation();busy=true;$('submit').disabled=true;$('noExplanation').disabled=true;pending=pending||{request_id:crypto.randomUUID(),item_id:state.item.id,answer:$('noExplanation').checked?{verdict:'no_explanation'}:{cells:[...chosen].sort((a,b)=>a-b)}};try{const r=await api('submit',pending);state.active=false;receipt(r);window.scrollTo({top:0,behavior:'smooth'});}catch(e){error(e);$('submit').disabled=false;$('submit').textContent='Retry same submission';}finally{busy=false;}};
$('probe').onclick=async()=>{if(busy)return;busy=true;try{const changes={...probeChanges};document.querySelectorAll('[data-probe]').forEach(e=>{if(e.value!=='')changes[e.dataset.probe]=Number(e.value);});pendingProbe=pendingProbe||{request_id:crypto.randomUUID(),item_id:state.item.id,changes};const r=await api('probe',pendingProbe);state.probe_history=state.probe_history||[];state.probe_history.push({changes:pendingProbe.changes,result:r});pendingProbe=null;state.probes_used=r.probes_used;showProbeHistory();}catch(e){error(e);}finally{busy=false;}};
$('withdraw').onclick=async()=>{if(!token)return;try{await api('withdraw',{});render(await api('state'));}catch(e){error(e);}};
$('showLesson').onclick=()=>{
 const host=$('lessonDialogContent');host.replaceChildren();
 (state.demonstrations||[]).forEach(d=>{const example=d.cases.find(c=>c.correct)||d.cases[0],section=document.createElement('section');section.className='dialog-demo';const title=document.createElement('h3');title.textContent=d.title;const board=document.createElement('div');board.className='board-host compact-board';const caption=document.createElement('p');caption.textContent=d.caption;const choices=document.createElement('div');choices.className='pill-tabs';section.append(title,board,caption,choices);host.append(section);
  const show=(c,phase,run)=>{TRACEBoard.render(board,d.item,{selected:new Set(c.selected_cells),inputs:run?.inputs,path:run?.board_path});caption.textContent=c.label+' · '+(phase==='hold'?'Hold marked switches; change the others.':'Change only marked switches.')+' '+(run?.target_flashes?'Light on.':'Light off.')+' Hold '+(c.tests.guarantee.passed?'passes':'fails')+'; change '+(c.tests.prevention.passed?'passes':'fails')+'; '+(c.tests.minimality.passed?'no extra marks.':c.tests.minimality.removable_cells.length?'extra marks: '+labels(d.item,c.tests.minimality.removable_cells):'both tests must pass first.');};
  TRACEBoard.render(board,d.item,{selected:new Set(example.selected_cells),animate:false});
  for(const c of d.cases)for(const phase of ['hold','change-marked'])c.completions[phase].runs.forEach((run,i)=>button(choices,c.label+' · '+(phase==='hold'?'hold':'change')+' '+(i+1),()=>show(c,phase,run)));
 });
 (state.training_examples||[]).forEach((example,index)=>{const section=document.createElement('section');section.className='dialog-demo practice-reference';const title=document.createElement('h3');title.textContent='Your warm-up '+(index+1);const board=document.createElement('div');board.className='board-host compact-board';const caption=document.createElement('p'),choices=document.createElement('div'),runs=document.createElement('div');choices.className='pill-tabs';runs.className='feedback-runs';section.append(title,board,caption,runs,choices);host.append(section);
  function showAnswer(cells){runs.replaceChildren();TRACEBoard.render(board,example.item,{selected:new Set(cells)});caption.textContent='Accepted marks: '+labels(example.item,cells)+'. Both tests pass, with no extras.';}
  (example.accepted_explanations||[]).forEach((cells,i)=>button(choices,'Answer '+(i+1)+' · '+labels(example.item,cells),()=>showAnswer(cells)));
  const feedback=example.feedback;
  if(feedback?.tests)for(const[k,l]of[['guarantee','Hold'],['prevention','Change'],['minimality','No extras']])button(choices,'Your '+l.toLowerCase()+' test',()=>{runs.replaceChildren();const t=feedback.tests[k];if(k==='minimality'&&removalIllustration(board,caption,runs,example.item,t))return;TRACEBoard.render(board,example.item,{selected:new Set(feedback.selected_cells||[]),inputs:t.witness?.inputs,path:t.witness?.board_path});caption.textContent='Your marks: '+labels(example.item,feedback.selected_cells||[])+'. '+l+' '+(t.passed?'passed.':'failed.')+(t.removable_cells?.length?' Removable marks: '+labels(example.item,t.removable_cells)+'.':'')+(t.witness?' The board shows its counterfactual setting.':'');});
  if(example.answer.cells)showAnswer(example.answer.cells);else{TRACEBoard.render(board,example.item,{selected:new Set()});caption.textContent='No switch setting can prevent this target light.';}
 });
 $('lessonDialog').showModal();
};
$('closeLesson').onclick=()=>$('lessonDialog').close();
setInterval(async()=>{if(!state?.active)return;const seconds=Math.max(0,Math.ceil(state.deadline-Date.now()/1000-offset));$('timer').textContent=Math.floor(seconds/60)+':'+String(seconds%60).padStart(2,'0');if(!seconds&&!busy){busy=true;try{render(await api('state'));}catch(e){error(e);}finally{busy=false;}}},500);
if(token)api('state').then(render).catch(error);else{$('next').disabled=true;$('welcome').textContent='Open the private play link created by the local TRACE server.';}
