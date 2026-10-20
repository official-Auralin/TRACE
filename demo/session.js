/* Browser-local demonstration sessions. This is an editable personal record,
 * not an authenticated research log. First submissions are append-only within
 * the API; all retries, disclosures and prior exposure remain explicit.
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(require('./engine.js'));
  else root.TraceDemoSession = factory(root.TraceDemoEngine);
})(typeof globalThis === 'object' ? globalThis : this, function (engine) {
  'use strict';
  const PROTOCOL_VERSION = 'trace.demo.v1', SCHEMA_VERSION = 'trace.demo.session.v1';
  const catalogs = new WeakMap();
  const clone = value => JSON.parse(JSON.stringify(value));
  const freeze = value => {
    if (value && typeof value === 'object' && !Object.isFrozen(value)) {
      Object.values(value).forEach(freeze); Object.freeze(value);
    }
    return value;
  };
  function clock(options = {}) {
    const value = options.now === undefined ? Date.now() : options.now;
    if (!Number.isFinite(value) || value < 0) throw Error('now must be nonnegative milliseconds');
    return value;
  }
  function validateCatalog(catalog) {
    if (!catalog || catalog.schema_version !== 'trace.demo.catalog.v1' || catalog.protocol_version !== PROTOCOL_VERSION ||
        catalog.semantics_version !== engine.SEMANTICS_VERSION || typeof catalog.package_id !== 'string' || !catalog.package_id ||
        !Array.isArray(catalog.items) || !catalog.items.length || catalog.items.some(x => !x || typeof x.id !== 'string' || !x.id || typeof x.band !== 'string') ||
        new Set(catalog.items.map(x => x.id)).size !== catalog.items.length) throw Error('invalid or incompatible demo catalog');
  }
  function catalogOf(state) {
    const catalog = catalogs.get(state);
    if (!catalog) throw Error('session must be created or restored with this API');
    return catalog;
  }
  function entryFor(state, id) {
    const entry = catalogOf(state).items.find(x => x.id === id);
    if (!entry) throw Error('unknown puzzle ID');
    return entry;
  }
  function event(state, type, detail, now) {
    state.events.push(freeze({sequence:state.events.length, type, at:now, ...clone(detail)}));
    state.updated_at = now;
  }
  function create(catalog, options = {}) {
    validateCatalog(catalog); const now = clock(options);
    const sessionId = options.sessionId || (typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : 'local-' + now + '-' + Math.random().toString(36).slice(2));
    if (typeof sessionId !== 'string' || !sessionId) throw Error('invalid local session ID');
    const state = {schema_version:SCHEMA_VERSION, protocol_version:PROTOCOL_VERSION,
      semantics_version:engine.SEMANTICS_VERSION, package_id:catalog.package_id,
      record_scope:'editable_local_demo_not_research_data', session_id:sessionId,
      created_at:now, updated_at:now, selected_band:'all', current_item_id:null,
      current_visit:null, draft:{cells:[]}, entries:Object.create(null), events:[], lessons:[]};
    catalogs.set(state, freeze(clone(catalog)));
    return state;
  }
  function restore(catalog, raw) {
    validateCatalog(catalog); const state = clone(raw);
    if (!state || state.schema_version !== SCHEMA_VERSION || state.protocol_version !== PROTOCOL_VERSION ||
        state.semantics_version !== engine.SEMANTICS_VERSION || state.package_id !== catalog.package_id ||
        state.record_scope !== 'editable_local_demo_not_research_data' || !Array.isArray(state.events) || !Array.isArray(state.lessons) ||
        !state.entries || typeof state.entries !== 'object' || Array.isArray(state.entries) || typeof state.session_id !== 'string')
      throw Error('saved session belongs to another package/protocol or is malformed');
    catalogs.set(state, freeze(clone(catalog)));
    state.entries = Object.assign(Object.create(null), state.entries);
    for (const [id, entry] of Object.entries(state.entries)) {
      entryFor(state, id);
      if (!entry || !Number.isSafeInteger(entry.exposures) || entry.exposures < 1 || !Array.isArray(entry.submissions) || !Array.isArray(entry.reveals) || !Array.isArray(entry.visits))
        throw Error('invalid saved item progress');
      if (new Set(entry.submissions.map(s => s.id)).size !== entry.submissions.length ||
          entry.submissions.some(s => s.item_id !== id || typeof s.id !== 'string' || !s.result || !s.feedback))
        throw Error('invalid saved submissions');
      if (entry.submissions.length) {
        if (!entry.first_submission || JSON.stringify(entry.first_submission) !== JSON.stringify(entry.submissions[0])) throw Error('first submission does not match append-only history');
        entry.submissions = entry.submissions.map(freeze);
        entry.first_submission = entry.submissions[0];
      } else if (entry.first_submission !== null) throw Error('first submission without an attempt');
      entry.reveals = entry.reveals.map(freeze);
    }
    if (state.current_item_id !== null) {
      entryFor(state, state.current_item_id);
      if (!state.entries[state.current_item_id] || !state.current_visit || state.current_visit.item_id !== state.current_item_id) throw Error('invalid saved current visit');
    }
    state.events = state.events.map(freeze); state.lessons = state.lessons.map(freeze);
    return state;
  }
  function start(state, id, options = {}) {
    const catalogEntry = entryFor(state, id), now = clock(options);
    if (state.current_item_id === id && !options.replay) return catalogEntry;
    let progress = state.entries[id];
    if (progress && !options.replay) throw Error('previously seen puzzles require explicit replay');
    const priorExposure = progress ? progress.exposures : 0;
    if (!progress) progress = state.entries[id] = {exposures:0, first_submission:null, submissions:[], reveals:[], visits:[], completed:false, draft:{cells:[]}};
    progress.exposures++;
    const visit = {id:id + ':visit:' + progress.exposures, item_id:id, started_at:now,
      prior_exposure:priorExposure, prior_items_seen:Object.keys(state.entries).length - (priorExposure ? 0 : 1),
      locked:false, submission_id:null, attempt_index:0};
    progress.visits.push({...visit});
    state.current_item_id = id; state.current_visit = visit; state.draft = clone(progress.draft);
    event(state, 'start', {item_id:id, visit_id:visit.id, prior_exposure:priorExposure, replay:priorExposure > 0}, now);
    return catalogEntry;
  }
  function next(state, options = {}) {
    const catalog = catalogOf(state), band = options.band === undefined ? state.selected_band : options.band;
    if (band !== 'all' && !catalog.items.some(x => x.band === band)) throw Error('unknown structural band');
    state.selected_band = band;
    const available = catalog.items.find(x => (band === 'all' || x.band === band) && !state.entries[x.id]);
    if (!available) return null;
    return start(state, available.id, options);
  }
  function current(state) { return state.current_item_id === null ? null : entryFor(state, state.current_item_id); }
  function active(state, item) {
    catalogOf(state);
    if (!state.current_visit || !state.current_item_id) throw Error('start a puzzle first');
    if (item && item.id !== state.current_item_id) throw Error('answer item does not match the active puzzle');
    return state.entries[state.current_item_id];
  }
  function saveDraft(state, answer) {
    const progress = active(state);
    if (state.current_visit.locked) throw Error('choose retry before changing a submitted answer');
    if (!(answer && Object.keys(answer).length === 1 &&
          ((answer.verdict === 'no_explanation') || (Array.isArray(answer.cells) && answer.cells.every(Number.isSafeInteger))))) throw Error('invalid draft answer');
    state.draft = clone(answer); progress.draft = clone(answer);
    return clone(state.draft);
  }
  function submit(state, item, answer, options = {}) {
    const progress = active(state, item), visit = state.current_visit;
    const id = options.submissionId || visit.id + ':answer:' + visit.attempt_index;
    if (typeof id !== 'string' || !id) throw Error('invalid submission ID');
    const prior = progress.submissions.find(s => s.id === id);
    if (prior) {
      if (JSON.stringify(prior.answer) !== JSON.stringify(answer)) throw Error('duplicate submission ID has a different answer');
      return prior;
    }
    if (visit.locked) {
      const last = progress.submissions.find(s => s.id === visit.submission_id);
      if (last && JSON.stringify(last.answer) === JSON.stringify(answer)) return last;
      throw Error('choose retry before submitting again');
    }
    const now = clock(options), elapsed = options.elapsedMs === undefined ? Math.max(0, now - visit.started_at) : options.elapsedMs;
    if (!Number.isFinite(elapsed) || elapsed < 0) throw Error('elapsedMs must be nonnegative');
    const feedback = engine.feedback(item, answer), result = {};
    for (const key of ['correct','valid_format','guarantee','prevention','minimality','answer_kind','reason']) if (key in feedback) result[key] = feedback[key];
    const record = freeze({id, item_id:item.id, visit_id:visit.id, at:now, elapsed_ms:elapsed,
      timing_scope:'client_reported_wall_time_for_current_attempt', answer:clone(answer), result, feedback,
      first_submission:progress.submissions.length === 0,
      assisted:progress.reveals.length > 0 || progress.submissions.length > 0,
      assistance:{solution_revealed:progress.reveals.length > 0, prior_feedback_count:progress.submissions.length},
      replay:visit.prior_exposure > 0, prior_exposure:visit.prior_exposure,
      prior_items_seen:visit.prior_items_seen});
    progress.submissions.push(record);
    if (!progress.first_submission) progress.first_submission = record;
    if (result.correct) progress.completed = true;
    visit.locked = true; visit.submission_id = id;
    state.draft = clone(answer); progress.draft = clone(answer);
    event(state, 'submit', {item_id:item.id, submission_id:id, first_submission:record.first_submission}, now);
    return record;
  }
  function retry(state, options = {}) {
    const progress = active(state), visit = state.current_visit, now = clock(options);
    if (!visit.locked) return clone(state.draft);
    visit.locked = false; visit.submission_id = null; visit.attempt_index++; visit.started_at = now;
    event(state, 'retry', {item_id:state.current_item_id, visit_id:visit.id, attempt_index:visit.attempt_index}, now);
    progress.draft = clone(state.draft);
    return clone(state.draft);
  }
  function reveal(state, item, options = {}) {
    const progress = active(state, item), visit = state.current_visit;
    const submitted = progress.submissions.find(record => record.id === visit.submission_id && record.visit_id === visit.id);
    if (!visit.locked || !submitted || submitted.result.correct !== false)
      throw Error('a solution is available only after an incorrect submission for the current attempt');
    const now = clock(options), solution = engine.reveal(item);
    const record = freeze({at:now, item_id:item.id, visit_id:state.current_visit.id, before_first_submission:!progress.first_submission, ...solution});
    progress.reveals.push(record);
    // The answer remains a disclosure, never an automatically scored attempt.
    state.current_visit.locked = true;
    event(state, 'reveal', {item_id:item.id, before_first_submission:record.before_first_submission}, now);
    return record;
  }
  function recordLesson(state, id, result, options = {}) {
    catalogOf(state); const now = clock(options);
    if (typeof id !== 'string' || !id) throw Error('invalid lesson ID');
    if (result.kind === 'reveal') {
      const submitted = state.lessons.filter(record => record.id === id && record.kind === 'submit').at(-1);
      if (!submitted || (submitted.feedback?.correct ?? submitted.correct) !== false)
        throw Error('a lesson solution is available only after its latest submission is incorrect');
    }
    const record = freeze({id, at:now, ...clone(result)}); state.lessons.push(record);
    event(state, 'lesson', {id}, now); return record;
  }
  function stats(state) {
    const catalog = catalogOf(state), progress = Object.values(state.entries);
    const submitted = progress.filter(x => x.first_submission), firstCorrect = submitted.filter(x => x.first_submission.result.correct).length;
    const unaided = submitted.filter(x => !x.first_submission.assisted);
    const attempts = progress.reduce((sum, x) => sum + x.submissions.length, 0);
    return {assistance_scope:'same_item_feedback_or_solution; lessons and other puzzles remain prior learning',
      total:catalog.items.length, exposed:progress.length, remaining:catalog.items.length - progress.length,
      submitted:submitted.length, first_correct:firstCorrect, first_accuracy:submitted.length ? firstCorrect / submitted.length : null,
      unaided_first_submitted:unaided.length, unaided_first_correct:unaided.filter(x => x.first_submission.result.correct).length,
      assisted_first:submitted.length - unaided.length, completed:progress.filter(x => x.completed).length,
      revealed:progress.filter(x => x.reveals.length).length, attempts, retries:attempts - submitted.length,
      bands: [...new Set(catalog.items.map(x => x.band))].map(band => ({id:band,
        total:catalog.items.filter(x => x.band === band).length,
        remaining:catalog.items.filter(x => x.band === band && !state.entries[x.id]).length}))};
  }
  function snapshot(state) { catalogOf(state); return clone(state); }
  return {PROTOCOL_VERSION, SCHEMA_VERSION, create, restore, start, next, current, saveDraft, submit, retry, reveal, recordLesson, stats, snapshot};
});
