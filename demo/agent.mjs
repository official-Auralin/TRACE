#!/usr/bin/env node
/** Local JSONL transport for the same feedback-rich demo as the Pages UI.
 * Usage: node demo/agent.mjs artifacts/demo-site/catalog.json
 * Each input line: {"action":"next"}, {"action":"submit","answer":{"cells":[0]}},
 * {"action":"retry"}, {"action":"reveal"}, {"action":"snapshot"}, or
 * {"action":"restore","snapshot":...}. No provider calls or isolated sandbox.
 * All output records are locally editable demo records, not research results.
 */
import fs from 'node:fs';
import path from 'node:path';
import readline from 'node:readline';
import {createHash} from 'node:crypto';
import session from './session.js';
import engine from './engine.js';
const catalogPath = process.argv[2];
if (!catalogPath || process.argv.includes('--help')) {
  process.stdout.write('Usage: node demo/agent.mjs <exported catalog.json>\nJSONL actions: next {band?}, start {id,replay?}, submit {answer,submissionId?}, retry, reveal, draft {answer}, lesson {id,answer}, lesson_reveal {id}, snapshot, restore {snapshot}, observe.\n');
  process.exit(catalogPath ? 0 : 2);
}
const root = path.dirname(path.resolve(catalogPath));
const catalog = JSON.parse(fs.readFileSync(catalogPath,'utf8'));
function readVerified(relative, expectedHash) {
  const filename = path.resolve(root,relative);
  if (!filename.startsWith(root + path.sep)) throw Error('asset path leaves the exported package');
  const bytes = fs.readFileSync(filename);
  if (typeof expectedHash !== 'string' || createHash('sha256').update(bytes).digest('hex') !== expectedHash)
    throw Error('public package asset hash mismatch: ' + relative);
  return JSON.parse(bytes.toString('utf8'));
}
const lessons = readVerified(catalog.lessons_path || 'lessons.json',catalog.lessons_sha256)
  .map(({id,title,caption,item}) => ({id,title,caption,item}));
for (const lesson of lessons) engine.validateItem(lesson.item);
let state = session.create(catalog);
let currentItem = null;
function loadCurrent() {
  const entry = session.current(state);
  if (!entry) { currentItem = null; return; }
  const item = readVerified(entry.path,entry.sha256);
  if (item.id !== entry.id) throw Error('catalog and item IDs disagree');
  engine.validateItem(item); currentItem = item;
}
function observation(extra = {}) {
  return {protocol_version:session.PROTOCOL_VERSION, semantics_version:catalog.semantics_version,
    package_id:catalog.package_id, scope:'editable_local_demo_not_research_data',
    session_id:state.session_id, catalog, lessons, current:currentItem,
    draft:state.draft, locked:state.current_visit?.locked || false,
    history:session.snapshot(state), stats:session.stats(state), ...extra};
}
function emit(value) { process.stdout.write(JSON.stringify(value) + '\n'); }
emit(observation({status:'ready', instruction:'Mark any inclusion-minimal set that guarantees the recorded target when fixed and permits prevention by changing only marked cells. An explicit reveal is assistance. All actions and feedback remain in history; this local transport provides no participant isolation.'}));
const lines = readline.createInterface({input:process.stdin,crlfDelay:Infinity});
for await (const line of lines) {
  let before = null; const previousItem = currentItem;
  try {
    const request = JSON.parse(line); let result;
    if (['next','start','restore'].includes(request.action)) before = session.snapshot(state);
    switch (request.action) {
      case 'next': result = session.next(state,{band:request.band}); loadCurrent(); break;
      case 'start': result = session.start(state,request.id,{replay:request.replay === true}); loadCurrent(); break;
      case 'submit': case 'answer':
        if (!currentItem) throw Error('start a puzzle first');
        result = session.submit(state,currentItem,request.answer,{submissionId:request.submissionId}); break;
      case 'draft': result = session.saveDraft(state,request.answer); break;
      case 'lesson': {
        const lesson = lessons.find(value => value.id === request.id);
        if (!lesson) throw Error('unknown lesson ID');
        const feedback = engine.feedback(lesson.item,request.answer);
        const assisted = state.lessons.some(record => record.id === lesson.id && record.kind === 'reveal');
        result = session.recordLesson(state,lesson.id,{kind:'submit',answer:request.answer,feedback,correct:feedback.correct,assisted}); break;
      }
      case 'lesson_reveal': {
        const lesson = lessons.find(value => value.id === request.id);
        if (!lesson) throw Error('unknown lesson ID');
        result = session.recordLesson(state,lesson.id,{kind:'reveal',...engine.reveal(lesson.item)}); break;
      }
      case 'retry': result = session.retry(state); break;
      case 'reveal':
        if (!currentItem) throw Error('start a puzzle first');
        result = session.reveal(state,currentItem); break;
      case 'snapshot': result = session.snapshot(state); break;
      case 'restore': state = session.restore(catalog,request.snapshot); loadCurrent(); result = {restored:true}; break;
      case 'observe': break;
      default: throw Error('unknown action');
    }
    emit(observation({status:'ok',action:request.action,...(result === undefined ? {} : {result})}));
  } catch (error) {
    if (before) { state = session.restore(catalog,before); currentItem = previousItem; }
    emit({status:'error',error:error.message,protocol_version:session.PROTOCOL_VERSION});
  }
}
