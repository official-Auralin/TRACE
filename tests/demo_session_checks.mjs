import assert from 'node:assert/strict';
import session from '../demo/session.js';
const machine = {inputs:['A'],states:1,initial:0,transitions:[[{next:0,output:0},{next:0,output:1}]]};
const a = {id:'a',machine,observed:[[1]],target_step:0};
const b = {...a,id:'b'};
const c = {...a,id:'c'};
const catalog = {schema_version:'trace.demo.catalog.v1',protocol_version:'trace.demo.v1',semantics_version:'trace.gp.v2',package_id:'test-bound-package',items:[{id:'a',band:'small'},{id:'b',band:'small'},{id:'c',band:'large'}]};
let state = session.create(catalog,{now:0,sessionId:'test-session'});
assert.equal(session.next(state,{now:1}).id,'a');
session.saveDraft(state,{cells:[0]});
state = session.restore(catalog,session.snapshot(state));
assert.deepEqual(state.draft,{cells:[0]});
const wrong = session.submit(state,a,{cells:[]},{submissionId:'first',now:100});
assert.equal(wrong.result.correct,false);
assert(Object.isFrozen(wrong.answer.cells));
assert.throws(()=>wrong.answer.cells.push(0));
assert.strictEqual(session.submit(state,a,{cells:[]},{submissionId:'first',now:101}),wrong);
assert.equal(state.entries.a.submissions.length,1);
assert.throws(()=>session.submit(state,a,{cells:[0]},{submissionId:'first'}));
assert.throws(()=>session.submit(state,a,{cells:[0]}));
session.retry(state,{now:102});
assert.throws(()=>session.reveal(state,a)); // No disclosure during an unanswered retry.
const correct = session.submit(state,a,{cells:[0]},{submissionId:'retry',now:120});
assert.equal(correct.result.correct,true);assert.equal(correct.assisted,true);
assert.throws(()=>session.reveal(state,a)); // Success cannot unlock a canonical alternative.
assert.strictEqual(state.entries.a.first_submission,wrong);
assert.deepEqual(session.stats(state),{assistance_scope:'same_item_feedback_or_solution; lessons and other puzzles remain prior learning',total:3,exposed:1,remaining:2,submitted:1,first_correct:0,first_accuracy:0,unaided_first_submitted:1,unaided_first_correct:0,assisted_first:0,completed:1,revealed:0,attempts:2,retries:1,bands:[{id:'small',total:2,remaining:1},{id:'large',total:1,remaining:1}]});
state = session.restore(catalog,session.snapshot(state));
assert.equal(state.entries.a.first_submission.result.correct,false);
assert.strictEqual(state.entries.a.first_submission,state.entries.a.submissions[0]);
assert.equal(state.current_visit.locked,true);
assert.equal(session.next(state,{band:'large',now:200}).id,'c');
const beforeReveal = session.snapshot(state);
assert.throws(()=>session.reveal(state,c,{now:201}));
assert.deepEqual(session.snapshot(state),beforeReveal); // Rejection changes no exposure or history.
session.submit(state,c,{cells:[]},{now:201});
const disclosed = session.reveal(state,c,{now:201});
assert.deepEqual(disclosed.answer,{cells:[0]});
assert.equal(state.entries.c.first_submission.result.correct,false); // Reveal never manufactures success.
assert.equal(disclosed.before_first_submission,false);
assert.deepEqual(session.reveal(state,c,{now:201}).answer,disclosed.answer); // Repetition adds no new information.
assert.equal(state.entries.c.completed,false);
session.retry(state,{now:202});
const assisted = session.submit(state,c,{cells:[0]},{now:210});
assert.equal(assisted.assisted,true);assert.equal(assisted.assistance.solution_revealed,true);
assert.equal(session.next(state,{band:'large'}),null); // No fictional unseen repetitions.
assert.equal(session.next(state,{band:'small',now:220}).id,'b');
assert.throws(()=>session.start(state,'a'));
session.start(state,'a',{replay:true,now:230});
assert.equal(state.current_visit.prior_exposure,1);
assert.throws(()=>session.reveal(state,a)); // Old wrong submissions cannot unlock a new visit.
session.submit(state,a,{cells:[0]},{now:240});
assert.equal(state.entries.a.first_submission.result.correct,false);
assert.equal(state.entries.a.submissions.at(-1).replay,true);
assert.equal(session.next(state,{band:'all'}),null);
assert.throws(()=>session.next(state,{band:'absent'}));
assert.throws(()=>session.restore({...catalog,package_id:'other'},session.snapshot(state)));
const bad = session.snapshot(state);bad.entries.a.first_submission.result.correct=true;
assert.throws(()=>session.restore(catalog,bad));
session.recordLesson(state,'hold',{answer:{cells:[0]},correct:true},{now:250});
assert.equal(session.restore(catalog,session.snapshot(state)).lessons[0].id,'hold');
const constant = {id:'a',machine:{...machine,transitions:[[{next:0,output:1},{next:0,output:1}]]},observed:[[1]],target_step:0};
state = session.create(catalog,{now:0});session.next(state,{now:1});
assert.equal(session.submit(state,constant,{verdict:'no_explanation'},{now:2}).result.correct,true);
// IDs come from external imported data, including ordinary Object property names.
const namedCatalog = {...catalog,items:['__proto__','constructor','toString'].map(id => ({id,band:'small'}))};
state = session.create(namedCatalog,{now:0});
for (const entry of namedCatalog.items) {
  assert.equal(session.next(state,{now:1}).id,entry.id);
  session.saveDraft(state,{cells:[0]});
  state = session.restore(namedCatalog,session.snapshot(state));
  assert.deepEqual(state.draft,{cells:[0]});
  session.submit(state,{...a,id:entry.id},{cells:[0]},{now:2});
}
assert.equal(session.next(state),null);
assert.equal(session.stats(state).first_correct,3);
session.start(state,'__proto__',{replay:true,now:3});
assert.deepEqual(state.draft,{cells:[0]});
const lessonSnapshot = session.snapshot(state);
assert.throws(()=>session.recordLesson(state,'new-lesson',{kind:'reveal'}));
assert.deepEqual(session.snapshot(state),lessonSnapshot);
session.recordLesson(state,'new-lesson',{kind:'submit',correct:false,feedback:{correct:false}});
session.recordLesson(state,'new-lesson',{kind:'reveal',answer:{cells:[0]}});
session.recordLesson(state,'new-lesson',{kind:'submit',correct:true,feedback:{correct:true}});
assert.throws(()=>session.recordLesson(state,'new-lesson',{kind:'reveal'}));
console.log(JSON.stringify({checks:60}));
