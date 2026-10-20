'use strict';
// Public practice UI. All scoring/progress stays local; no participant API is used.
(() => {
  const $ = id => document.getElementById(id), E = window.TraceDemoEngine, S = window.TraceDemoSession;
  const clone = value => JSON.parse(JSON.stringify(value));
  const storagePrefix = 'trace.demo.progress.';
  let catalog, lessons, state, item, entry, storageKey, saved = {}, screen = 'welcome';
  let mode = 'puzzle', lessonIndex = 0, lessonMarks = new Set(), chosen = new Set(), busy = false;
  let selectedBand = '', catalogPage = 0, latestRecord = null, lessonFeedback = null;
  let lessonsProgress = {}, lessonResume = null, startedAt = 0, storageAvailable = true, lastStored = null;
  const itemCache = new Map();
  const screens = ['welcome', 'play', 'receipt', 'exhausted'];
  const button = (parent, label, action, className = '') => {
    const b = document.createElement('button'); b.type = 'button'; b.textContent = label;
    b.className = className; b.onclick = () => run(action); parent.append(b); return b;
  };
  function fail(error) {
    $('error').hidden = false;
    $('error').textContent = 'Could not finish that action. ' + (error?.message || String(error)) + ' Your earlier progress has been kept.';
  }
  async function run(action) {
    if (busy) return;
    busy = true; document.body.setAttribute('aria-busy', 'true');
    for (const id of ['submit', 'next', 'retry', 'reveal', 'startPlay', 'startLearning', 'resume']) $(id).disabled = true;
    $('error').hidden = true;
    try { await new Promise(resolve => setTimeout(resolve, 0)); await action(); }
    catch (error) { fail(error); }
    finally {
      busy = false; document.body.removeAttribute('aria-busy');
      for (const id of ['submit', 'next', 'retry', 'reveal', 'startPlay', 'startLearning', 'resume']) $(id).disabled = false;
    }
  }
  async function json(path, expectedHash) {
    const response = await fetch(path);
    if (!response.ok) throw Error('A game file could not be loaded (' + response.status + '). Refresh to try again.');
    const bytes = await response.arrayBuffer();
    if (expectedHash) {
      const hash = [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))].map(n => n.toString(16).padStart(2,'0')).join('');
      if (hash !== expectedHash) throw Error('A puzzle file belongs to a different release. Refresh the page before continuing.');
    }
    return JSON.parse(new TextDecoder().decode(bytes));
  }
  function notifyStorage(message) {
    storageAvailable = false; $('storageNotice').hidden = false;
    $('storageNotice').textContent = message || 'This browser could not save progress. You can keep playing now, but download your progress before closing the page.';
  }
  async function claimStorage() {
    if (!navigator.locks) return; // The value comparison below detects conflicts in older browsers.
    await new Promise(resolve => {
      navigator.locks.request(storageKey, {ifAvailable:true}, async lock => {
        if (!lock) { notifyStorage('Another TRACE tab is saving progress. This tab can play without saving. Download this tab’s progress, or close the other tab and refresh.'); resolve(); return; }
        resolve(); await new Promise(() => {}); // Browser releases this lock when the tab closes.
      }).catch(() => resolve());
    });
  }
  function snapshot() {
    return {schema_version:'trace.demo.ui.v1', session:S.snapshot(state), lessons:lessonsProgress,
      selected_band:selectedBand, screen, mode, lesson_resume:lessonResume};
  }
  function persist() {
    if (!state) return;
    saved = snapshot();
    if (storageAvailable) try {
      if (localStorage.getItem(storageKey) !== lastStored) { notifyStorage('Progress changed in another tab. This tab has stopped saving to protect those answers. Download this tab’s progress before refreshing.'); return; }
      lastStored = JSON.stringify(saved); localStorage.setItem(storageKey, lastStored);
    } catch (_) { notifyStorage(); }
  }
  function show(name, focus = false) {
    screen = name; screens.forEach(id => { $(id).hidden = id !== name; });
    persist();
    if (focus) {
      window.scrollTo({top:0, behavior:matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth'});
      const title = name === 'play' ? $('itemTitle') : name === 'receipt' ? $('resultTitle') : null;
      title?.focus({preventScroll:true});
    }
  }
  function labels(current, cells) {
    const names = new Map(current.board.switches.map(s => [s.cell, s.label]));
    return cells.map(c => names.get(c) || current.machine.inputs[c % current.machine.inputs.length] + ' · ' + (Math.floor(c / current.machine.inputs.length) + 1)).join(', ');
  }
  function answer() { return $('noExplanation').checked ? {verdict:'no_explanation'} : {cells:[...chosen].sort((a,b) => a-b)}; }
  function setAnswer(value) {
    chosen = new Set(value?.cells || []); $('noExplanation').checked = value?.verdict === 'no_explanation';
  }
  function counts() {
    const entries = Object.values(state.entries || {}), submitted = entries.filter(e => e.first_submission);
    return {
      attempted:submitted.length,
      correct:submitted.filter(e => e.first_submission.result.correct).length,
      assistedFirst:submitted.filter(e => e.first_submission.assisted).length,
      completed:entries.filter(e => e.completed).length,
      retries:entries.reduce((n,e) => n + Math.max(0, e.submissions.length - 1), 0),
      reveals:entries.reduce((n,e) => n + e.reveals.length, 0)
    };
  }
  function scoreLine() { const c = counts(); return c.correct + '/' + c.attempted + ' first answers correct · ' + c.completed + ' completed' + (c.assistedFirst ? ' · '+c.assistedFirst+' first answers after assistance' : ''); }
  async function loadItem(currentEntry) {
    if (!itemCache.has(currentEntry.id)) {
      const value = await json(currentEntry.path, currentEntry.sha256); E.validateItem(value);
      if (value.id !== currentEntry.id) throw Error('This puzzle does not match the catalog. Refresh the page.');
      itemCache.set(currentEntry.id, value);
      if (itemCache.size > 8) itemCache.delete(itemCache.keys().next().value);
    }
    return itemCache.get(currentEntry.id);
  }
  function drawBoard(host, current, marks, inputs, interactive = false) {
    window.TRACEBoard.render(host, current, {selected:new Set(marks), inputs, interactive,
      onSelect:toggle, animate:false});
  }
  function updateMarks(save = true) {
    if (mode === 'lesson') { lessonMarks = new Set(chosen); lessonResume = {...lessonResume,index:lessonIndex,answer:answer(),screen:'play',record:null}; }
    else if (save) S.saveDraft(state, answer());
    $('selected').textContent = $('noExplanation').checked ? 'No switch setting can turn the light off' : chosen.size ? labels(item, [...chosen].sort((a,b) => a-b)) : 'Choose switches on the board';
    document.querySelectorAll('#switchList button').forEach(b => b.setAttribute('aria-pressed', String(chosen.has(Number(b.dataset.cell)))));
    drawBoard($('board'), item, chosen, undefined, true);
    persist();
  }
  function toggle(cell) {
    if (busy || screen !== 'play') return;
    $('noExplanation').checked = false;
    chosen.has(cell) ? chosen.delete(cell) : chosen.add(cell); updateMarks();
  }
  function fullSwitchList() {
    $('switchList').replaceChildren(); const m = item.machine.inputs.length, metadata = new Map(item.board.switches.map(s => [s.cell,s]));
    for (let t = 0; t <= item.target_step; t++) {
      const group = document.createElement('div'); group.className = 'moment-group';
      const label = document.createElement('span'); label.textContent = 'Moment ' + (t+1); group.append(label);
      for (let r = 0; r < m; r++) {
        const cell = t*m+r, name = metadata.get(cell)?.label || item.machine.inputs[r] + ' · ' + (t+1);
        const b = document.createElement('button'); b.type = 'button'; b.textContent = name + (item.observed[t][r] ? ' ↘' : ' ↗'); b.dataset.cell = cell;
        b.setAttribute('aria-label', name + ', recorded ' + (item.observed[t][r] ? 'lower' : 'upper') + ' fork');
        b.setAttribute('aria-pressed', String(chosen.has(cell))); b.onclick = () => toggle(cell); group.append(b);
      }
      $('switchList').append(group);
    }
  }
  function lessonNote() {
    const notes = {
      'demo-direct':'There is one target lamp. Try marking the switch that keeps its route open and can also close it.',
      'demo-and':'HOLD fixes your marks. Unmarked switches are allowed to move, even if the recorded route passed through them.',
      'demo-or':'CHANGE only needs one way to turn the target off. You may change some or all of your marked switches.',
      'demo-xor':'Both appearances of a full label are the same switch. They move together. Changing every marked switch at once is not required.',
      'demo-choice':'A set can pass HOLD and CHANGE yet include an extra mark. Keep removing marks while both tests still pass.'
    };
    return notes[item.id] || 'Find marks that pass HOLD and CHANGE, with no extras.';
  }
  function renderPlay(focus = true) {
    show('play', focus); fullSwitchList();
    $('board').classList.toggle('lesson-board', mode === 'lesson');
    $('itemKicker').textContent = mode === 'lesson' ? 'LEARN BY PLAYING · ' + (lessonIndex+1) + ' / ' + lessons.length : entry.practice ? 'WARM-UP · FEEDBACK AFTER EVERY ANSWER' : 'PUZZLE · FEEDBACK AFTER EVERY ANSWER';
    $('itemTitle').textContent = mode === 'lesson' ? lessons[lessonIndex].title : 'Mark what matters.';
    $('itemDimensions').textContent = (item.target_step+1) + ' moment' + (item.target_step?'s':'') + (item.board.version==='trace.board.v2' ? ' · ' + item.machine.states + ' routes · ' + item.machine.inputs.length + ' input' + (item.machine.inputs.length===1?'':'s') + ' per moment' : ' · identical labels are linked');
    const history = mode === 'puzzle' ? state.entries[item.id] : null;
    $('visitLabel').textContent = mode === 'lesson' ? 'GUIDED EXAMPLE' : state.current_visit?.prior_exposure ? 'REPLAY · ' + item.id : history?.first_submission ? 'RETRY · ' + item.id : item.id;
    $('lessonNote').hidden = mode !== 'lesson'; $('lessonNote').textContent = mode === 'lesson' ? lessonNote() : '';
    $('skip').textContent = mode === 'lesson' ? 'Skip this example' : 'Leave this puzzle for later';
    $('technicalEncoding').open = false; $('machine').textContent = '';
    $('playScore').textContent = scoreLine(); updateMarks(false); startedAt = performance.now();
  }
  async function openEntry(currentEntry, replay = false) {
    const loaded = await loadItem(currentEntry);
    S.start(state, currentEntry.id, {replay}); entry = currentEntry; item = loaded; mode = 'puzzle'; latestRecord = null;
    setAnswer(state.draft); renderPlay();
  }
  async function nextPuzzle() {
    const nextEntry = catalog.items.find(e => (!selectedBand || e.band === selectedBand) && !state.entries[e.id]);
    if (!nextEntry) { renderExhausted(); return; }
    const loaded = await loadItem(nextEntry);
    S.start(state,nextEntry.id); state.selected_band = selectedBand || 'all';
    mode = 'puzzle'; entry = nextEntry; item = loaded; latestRecord = null; setAnswer(state.draft); renderPlay();
  }
  function renderExhausted() {
    const hasBand = !!selectedBand;
    $('exhaustedTitle').textContent = hasBand ? 'You have explored this board size.' : 'You have explored the current collection.';
    $('exhaustedText').textContent = hasBand ? 'Choose another size, or replay a puzzle. Previously seen puzzles stay available, with their first answers preserved.' : 'Every puzzle is still available to revisit. Replays keep their own attempts and never replace your first answers. More certified puzzle packs can extend this collection.';
    show('exhausted', true);
  }
  function startLesson(index = 0) {
    mode = 'lesson'; lessonIndex = index; item = lessons[index].item; entry = null; latestRecord = null;
    lessonMarks = new Set(); lessonResume = {index,answer:{cells:[]},screen:'play',record:null}; setAnswer({cells:[]}); renderPlay();
  }
  function nextLesson() {
    if (lessonIndex+1 < lessons.length) startLesson(lessonIndex+1);
    else return nextPuzzle();
  }
  function feedbackView(feedback, revealed = false) {
    $('feedbackTests').replaceChildren(); $('feedbackRuns').replaceChildren();
    const tests = feedback.tests, selected = feedback.selected_cells || [];
    function showTest(kind) {
      for (const b of $('feedbackTests').children) b.setAttribute('aria-pressed', String(b.dataset.test === kind));
      $('feedbackRuns').replaceChildren(); const test = tests[kind]; let marks = selected, inputs, caption;
      if (kind === 'guarantee') {
        inputs = test.witness?.inputs;
        caption = test.passed ? 'HOLD passes: every setting of the unmarked switches leaves the target on. The board shows the recorded run.' : 'HOLD fails: here your marked switches stay recorded, but changing unmarked switches turns the target off.';
      } else if (kind === 'prevention') {
        inputs = test.witness?.inputs;
        caption = test.passed ? 'CHANGE passes: this setting changes only marked switches and turns the target off.' : 'CHANGE fails: no setting of only your marked switches can turn the target off.';
      } else if (test.removable_cells.length) {
        const example = test.removal_example, removed = test.removable_cells[0];
        marks = selected.filter(c => c !== removed);
        caption = 'The mark on ' + labels(item,[removed]) + ' is extra: remove it and both tests still pass. The board shows those reduced marks.';
        if (example) {
          const draw = index => {
            drawBoard($('feedbackBoard'), item, example.remaining_cells, example.runs[index].inputs);
            for (const [i,b] of [...$('feedbackRuns').children].entries()) b.setAttribute('aria-pressed', String(i===index));
            $('feedbackCaption').textContent = 'Remove ' + labels(item,[example.removed_cell]) + ': HOLD and CHANGE still pass. ' + (index===0 ? 'This is the recorded setting.' : 'Here only that removed switch is flipped.') + ' These two runs illustrate the removal; the checker verifies the complete conditions.';
          };
          button($('feedbackRuns'),'Recorded setting',()=>draw(0)); button($('feedbackRuns'),'Flip '+labels(item,[example.removed_cell]),()=>draw(1));
          draw(0); return;
        }
      } else caption = test.passed ? 'No extras: removing any one mark breaks HOLD or CHANGE. Another valid explanation may use a different number of marks.' : 'First make HOLD and CHANGE pass. Then check whether any mark can be removed.';
      drawBoard($('feedbackBoard'), item, marks, inputs); $('feedbackCaption').textContent = caption;
    }
    if (tests) {
      for (const [key,label] of [['guarantee','Hold'],['prevention','Change'],['minimality','No extras']]) {
        const b = button($('feedbackTests'),(tests[key].passed?'✓ ':'× ')+label,()=>showTest(key));
        b.dataset.test = key; b.classList.toggle('failed',!tests[key].passed);
      }
      showTest(!tests.guarantee.passed?'guarantee':!tests.prevention.passed?'prevention':!tests.minimality.passed?'minimality':'prevention');
    } else { drawBoard($('feedbackBoard'),item,selected); $('feedbackCaption').textContent = feedback.message; }
    $('revealNote').hidden = !revealed;
    if (revealed) $('revealNote').textContent = 'One accepted answer is shown. Other minimal answers may also work. A solution reveal is recorded as assistance.';
  }
  function renderReceipt(record, focus = true) {
    latestRecord = record; const feedback = record.feedback, correct = feedback.correct;
    if(mode==='lesson')lessonResume={index:lessonIndex,answer:record.answer,screen:'receipt',record};
    show('receipt', focus);
    $('resultIcon').textContent = correct ? '✓' : '↗'; $('resultIcon').classList.toggle('review',!correct);
    $('receiptKicker').textContent = mode === 'lesson' ? 'LEARN BY PLAYING · ' + (lessonIndex+1) + ' / ' + lessons.length : record.replay ? 'REPLAY RESULT' : record.first_submission ? 'FIRST ANSWER SAVED' : 'RETRY RESULT';
    $('resultTitle').textContent = correct ? feedback.answer_kind==='no_explanation' ? 'The light cannot be stopped.' : 'Those marks work.' : 'Follow what happened.';
    $('resultText').textContent = feedback.message || (correct ? 'Both tests pass, and every mark is needed.' : 'Review what the tests found about your marks.');
    $('scoreNote').textContent = mode === 'lesson' ? 'These examples are for learning and stay separate from your puzzle scores.' : scoreLine() + (record.assistance?.solution_revealed ? ' · solution-assisted attempt' : record.assisted ? ' · retry after feedback' : '');
    $('retry').textContent = correct ? 'Try another answer' : 'Try again';
    $('next').innerHTML = (mode === 'lesson' ? lessonIndex+1 < lessons.length ? 'Next example' : 'Start puzzles' : 'Next puzzle') + ' <span aria-hidden="true">→</span>';
    $('reveal').hidden = correct; feedbackView(feedback);
  }
  function submit() {
    const submitted = answer();
    if (mode === 'lesson') {
      const feedback = E.feedback(item,submitted); lessonFeedback = feedback;
      const history = lessonsProgress[item.id] ||= {attempts:[],reveals:0};
      const record = {answer:clone(submitted),feedback,elapsed_ms:Math.round(performance.now()-startedAt),assisted:history.reveals>0};
      history.attempts.push({answer:clone(submitted),correct:feedback.correct,assisted:record.assisted,elapsed_ms:record.elapsed_ms});
      S.recordLesson(state,item.id,{kind:'submit',answer:submitted,correct:feedback.correct,assisted:record.assisted,elapsed_ms:record.elapsed_ms});
      renderReceipt(record);
    } else {
      const record = S.submit(state,item,submitted); persist(); renderReceipt(record);
    }
  }
  function retry() {
    if (mode === 'lesson') { setAnswer(latestRecord.answer); renderPlay(); return; }
    S.retry(state); setAnswer(state.draft); renderPlay();
  }
  function reveal() {
    let revealed;
    if (mode === 'lesson') {
      const history = lessonsProgress[item.id] ||= {attempts:[],reveals:0}; history.reveals++; revealed = E.reveal(item); S.recordLesson(state,item.id,{kind:'reveal'});
    } else revealed = S.reveal(state,item);
    if(mode==='lesson')lessonResume.revealed=revealed;
    persist(); showRevealed(revealed);
  }
  function showRevealed(revealed) {
    if(mode==='lesson'){lessonResume.revealed=revealed;persist();}
    $('resultTitle').textContent = 'One way to explain the light.';
    $('resultText').textContent = revealed.answer.cells ? 'Accepted marks: ' + labels(item,revealed.answer.cells) + '.' : 'No switch setting can prevent this target.';
    feedbackView(revealed.feedback,true); $('reveal').hidden = true;
  }
  function renderWelcome() {
    $('welcomeProgress').textContent = catalog.items.length.toLocaleString() + ' puzzles · ' + scoreLine();
    $('resume').hidden = !(mode==='lesson'&&lessonResume) && !S.current(state);
    $('resume').textContent=mode==='lesson'&&lessonResume?'Resume your example':'Resume your puzzle'; show('welcome');
  }
  async function resume() {
    if(mode==='lesson'&&lessonResume){
      lessonIndex=lessonResume.index;item=lessons[lessonIndex].item;entry=null;
      setAnswer(lessonResume.answer);
      if(lessonResume.screen==='receipt'&&lessonResume.record){const revealed=lessonResume.revealed;renderReceipt(lessonResume.record);if(revealed)showRevealed(revealed);}else renderPlay();
      return;
    }
    const current = S.current(state); if (!current) return nextPuzzle();
    mode = 'puzzle'; entry = current; item = await loadItem(entry);
    setAnswer(state.draft);
    const history = state.entries[item.id], last = history.submissions.at(-1);
    if (state.current_visit?.locked && last) {renderReceipt(last);const revealed=history.reveals.at(-1);if(revealed&&revealed.at>=last.at)showRevealed(revealed);} else renderPlay();
  }
  function openCatalog() {
    catalogPage = 0; $('bandSelect').value = selectedBand; renderCatalog(); $('catalogDialog').showModal();
  }
  function renderCatalog() {
    const items = catalog.items.filter(e => !selectedBand || e.band === selectedBand), pages = Math.max(1,Math.ceil(items.length/12));
    catalogPage = Math.min(catalogPage,pages-1); $('catalogItems').replaceChildren();
    const seen = items.filter(e => state.entries[e.id]);
    $('catalogSummary').textContent = items.length.toLocaleString() + ' puzzles · ' + (items.length-seen.length).toLocaleString() + ' unseen. Opening a seen puzzle is a replay; its first answer is kept.';
    for (const current of items.slice(catalogPage*12,(catalogPage+1)*12)) {
      const history = state.entries[current.id], b = button($('catalogItems'),'',async()=>{ $('catalogDialog').close(); await openEntry(current,!!history); },'catalog-item');
      const name = document.createElement('span'); name.textContent = current.id;
      const dimensions = document.createElement('small'); dimensions.textContent = (current.practice?'Warm-up · ':'') + current.dimensions.horizon+' moments · '+current.dimensions.states+' routes · '+current.dimensions.inputs+' inputs'; name.append(dimensions);
      const status = document.createElement('span'); status.className='status'; status.textContent=history?.completed?'✓ Replay':history?'Revisit':'Unseen'; b.append(name,status);
    }
    $('pageLabel').textContent = (catalogPage+1) + ' / ' + pages; $('previousPage').disabled = catalogPage===0; $('nextPage').disabled = catalogPage===pages-1;
  }
  function openScores() {
    const c=counts(); $('scoreCards').replaceChildren();
    const values = [[c.correct+'/'+c.attempted,'First answers correct',c.assistedFirst+' first answers followed same-item assistance'],[String(c.completed),'Puzzles completed','At least one correct submitted answer'],[String(c.retries),'Additional submissions',c.reveals+' solution reveal'+(c.reveals===1?'':'s')]];
    for(const [value,label,detail] of values){const card=document.createElement('div');card.className='score-card';const strong=document.createElement('strong');strong.textContent=value;const text=document.createElement('span');text.textContent=label;const small=document.createElement('small');small.textContent=detail;card.append(strong,text,small);$('scoreCards').append(card);}
    const learned=Object.values(lessonsProgress).filter(h=>h.attempts.some(a=>a.correct)).length;
    $('lessonProgress').textContent=learned+' / '+lessons.length+' teaching examples solved. Teaching attempts are separate from puzzle totals. Prior practice can improve later first answers; these totals do not measure untrained ability.';
    $('scoresDialog').showModal();
  }
  function download() {
    const blob=new Blob([JSON.stringify(snapshot(),null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),link=document.createElement('a');
    link.href=url;link.download='trace-practice-progress.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  $('home').onclick=e=>{e.preventDefault();if(!busy&&state)renderWelcome();};
  $('learn').onclick=()=>run(()=>startLesson(0)); $('startLearning').onclick=()=>run(()=>startLesson(0));
  $('startPlay').onclick=()=>run(nextPuzzle); $('resume').onclick=()=>run(resume);
  $('levels').onclick=()=>{if(state&&!busy)openCatalog();}; $('chooseMore').onclick=openCatalog;
  $('scores').onclick=()=>{if(state&&!busy)openScores();};
  $('clear').onclick=()=>{if(busy)return;chosen.clear();$('noExplanation').checked=false;updateMarks();};
  $('noExplanation').onchange=()=>{if(busy)return;if($('noExplanation').checked)chosen.clear();updateMarks();};
  $('submit').onclick=()=>run(submit); $('retry').onclick=()=>run(retry); $('reveal').onclick=()=>run(reveal);
  $('next').onclick=()=>run(mode==='lesson'?nextLesson:nextPuzzle); $('skip').onclick=()=>run(mode==='lesson'?nextLesson:nextPuzzle);
  $('replaySignal').onclick=()=>{if(!busy)$('board').replay?.();};
  $('technicalEncoding').ontoggle=()=>{if($('technicalEncoding').open&&item)$('machine').textContent=JSON.stringify({machine:item.machine,observed:item.observed,target_step:item.target_step},null,2);};
  $('bandSelect').onchange=()=>{selectedBand=$('bandSelect').value;catalogPage=0;persist();renderCatalog();};
  $('nextInBand').onclick=()=>run(async()=>{$('catalogDialog').close();await nextPuzzle();});
  $('previousPage').onclick=()=>{catalogPage--;renderCatalog();}; $('nextPage').onclick=()=>{catalogPage++;renderCatalog();};
  $('downloadProgress').onclick=download;
  document.querySelectorAll('[data-close]').forEach(b=>{b.onclick=()=>$(b.dataset.close).close();});
  window.addEventListener('beforeunload',persist);
  window.addEventListener('storage',event=>{
    if(state&&storageAvailable&&event.key===storageKey&&event.newValue!==lastStored)
      notifyStorage('Progress changed in another tab. This tab has stopped saving to protect those answers. Download this tab’s progress before refreshing.');
  });
  async function init() {
    if(!E||!S||!window.TRACEBoard)throw Error('The game scripts did not load. Refresh this page.');
    catalog=await json('catalog.json');lessons=await json(catalog.lessons_path||'lessons.json',catalog.lessons_sha256);
    if(!Array.isArray(catalog.items)||!catalog.items.length||!Array.isArray(lessons)||!lessons.length)throw Error('The public puzzle collection is empty.');
    storageKey=storagePrefix+catalog.package_id;
    await claimStorage();
    try { lastStored=localStorage.getItem(storageKey);if(lastStored)saved=JSON.parse(lastStored); }
    catch(_){notifyStorage();}
    if(saved.session){try{state=S.restore(catalog,saved.session);}catch(error){throw Error('Saved progress could not be restored: '+error.message+' The saved record has not been overwritten.');}}
    else state=S.create(catalog);
    lessonsProgress=saved.lessons||{};selectedBand=catalog.bands.some(b=>b.id===saved.selected_band)?saved.selected_band:'';
    lessonResume=saved.lesson_resume||null;mode=saved.mode==='lesson'&&lessonResume?'lesson':'puzzle';
    const all=document.createElement('option');all.value='';all.textContent='All sizes · suggested order';$('bandSelect').append(all);
    for(const band of catalog.bands){const option=document.createElement('option');option.value=band.id;option.textContent=band.label+' · '+band.count+' puzzles';$('bandSelect').append(option);}
    $('version').textContent=catalog.protocol_version+' · '+catalog.dataset_version;
    $('loading').hidden=true;renderWelcome();
  }
  init().catch(error=>{$('loading').hidden=true;fail(error);});
})();
