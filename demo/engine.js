/* TRACE static demo decision procedure. Tested against the Python grader;
 * this JavaScript adapter is not itself covered by the Lean kernel proof.
 * It reads the complete machine, never an answer key or all-answer inventory.
 */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.TraceDemoEngine = api;
})(typeof globalThis === 'object' ? globalThis : this, function () {
  'use strict';
  const SEMANTICS_VERSION = 'trace.gp.v2';
  const SEMANTICS = {
    version:SEMANTICS_VERSION,
    answer:'one inclusion-minimal set satisfying guarantee and prevention',
    cell_encoding:'cell = step * number_of_inputs + input_index; both zero-based',
    selected_value:'the observed Boolean value, including zero',
    output_timing:'output is emitted by the current-state/current-input transition before changing state',
    effect:'the single output equals 1 at target_step',
    guarantee:'every input assignment agreeing with selected cells preserves the effect',
    prevention:'some input assignment agreeing with every unselected cell makes the effect false',
    minimality:'no proper subset still satisfies both; not minimum cardinality',
    counterfactuals:'all Boolean input assignments through target_step, replayed from the same initial state'
  };
  const own = (value, keys) => value !== null && typeof value === 'object' && !Array.isArray(value) &&
    Object.keys(value).sort().join('|') === [...keys].sort().join('|');
  const integer = Number.isSafeInteger;
  const binary = value => integer(value) && (value === 0 || value === 1);
  const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
  const bit = (valuation, index) => Math.floor(valuation / (2 ** index)) % 2;
  const range = n => Array.from({length:n}, (_, i) => i);
  const count = item => item.machine.inputs.length * (item.target_step + 1);

  function validateMachine(machine) {
    if (!machine || !Array.isArray(machine.inputs) || !machine.inputs.length ||
        machine.inputs.some(x => typeof x !== 'string' || !x) || new Set(machine.inputs).size !== machine.inputs.length)
      throw Error('input names must be distinct nonempty strings');
    if (!integer(machine.states) || machine.states < 1 || !integer(machine.initial) || machine.initial < 0 || machine.initial >= machine.states)
      throw Error('invalid finite state count or initial state');
    if (!Array.isArray(machine.transitions) || machine.transitions.length !== machine.states)
      throw Error('missing state rows');
    for (const row of machine.transitions) {
      if (!Array.isArray(row) || row.length !== 2 ** machine.inputs.length)
        throw Error('input totality: missing or duplicate valuation');
      for (const edge of row) if (!own(edge, ['next', 'output']) || !integer(edge.next) || edge.next < 0 || edge.next >= machine.states || !binary(edge.output))
        throw Error('invalid deterministic transition');
    }
  }
  function simulate(machine, inputs) {
    let state = machine.initial;
    const outputs = [], states = [state];
    if (!Array.isArray(inputs)) throw Error('inputs must be an array');
    for (const row of inputs) {
      if (!Array.isArray(row) || row.length !== machine.inputs.length || !row.every(binary))
        throw Error('input step must contain binary integers');
      // Arithmetic rather than JS bitwise operators: no 32-bit cell mask.
      const valuation = row.reduce((sum, value, index) => sum + value * (2 ** index), 0);
      const edge = machine.transitions[state][valuation];
      outputs.push(edge.output); state = edge.next; states.push(state);
    }
    return {outputs, states};
  }
  function validateItem(item) {
    if (!item || typeof item !== 'object') throw Error('item requires machine, observed and target_step');
    validateMachine(item.machine);
    if (!integer(item.target_step) || item.target_step < 0 || !Array.isArray(item.observed) || item.observed.length !== item.target_step + 1)
      throw Error('observed inputs must end exactly at the nonnegative target step');
    if (!integer(count(item))) throw Error('cell count exceeds exact integer indexing in this JavaScript runtime');
    const replay = simulate(item.machine, item.observed);
    if (replay.outputs[item.target_step] !== 1) throw Error('the selected target must be an observed positive output');
    if (item.observed_outputs !== undefined && !same(item.observed_outputs, replay.outputs)) throw Error('recorded outputs disagree with the machine');
    if (item.observed_states !== undefined && !same(item.observed_states, replay.states)) throw Error('recorded states disagree with the machine');
    if (item.semantics !== undefined && (!own(item.semantics, Object.keys(SEMANTICS)) || Object.entries(SEMANTICS).some(([key, value]) => item.semantics[key] !== value))) throw Error('unsupported semantic contract');
    // The exported board is separately certified/validated at package creation.
    // The decision procedure intentionally grades the source machine.
    return replay;
  }
  function parseCells(answer, n) {
    if (!own(answer, ['cells'])) throw Error('answer must be exactly {"cells": [integer cell IDs]}');
    const cells = answer.cells;
    if (!Array.isArray(cells) || cells.some(c => !integer(c) || c < 0 || c >= n) || new Set(cells).size !== cells.length)
      throw Error('cell IDs must be unique in-window integers');
    return [...cells].sort((a, b) => a - b);
  }
  function noExplanation(answer) { return own(answer, ['verdict']) && answer.verdict === 'no_explanation'; }
  function game(item) {
    validateItem(item);
    const n = count(item), all = range(n), m = item.machine.inputs.length, cache = new Map();
    function complement(selected) { const set = new Set(selected); return all.filter(c => !set.has(c)); }
    function permitted(fixed, t) {
      const checked = range(m).filter(r => fixed.has(t * m + r));
      return range(item.machine.transitions[0].length).filter(v => checked.every(r => bit(v, r) === item.observed[t][r]));
    }
    function recurrence(selected, full = false) {
      const fixed = new Set(selected), layers = full ? new Array(item.target_step + 1) : null;
      let following = null;
      for (let t = item.target_step; t >= 0; t--) {
        const values = permitted(fixed, t);
        const current = item.machine.transitions.map(row => values.some(v =>
          t === item.target_step ? row[v].output === 0 : following[row[v].next]));
        if (full) layers[t] = current;
        following = current;
      }
      return full ? layers : following[item.machine.initial];
    }
    function bad(selected) {
      const key = selected.join(',');
      if (!cache.has(key)) cache.set(key, recurrence(selected));
      return cache.get(key);
    }
    function valid(selected) { return !bad(selected) && bad(complement(selected)); }
    function diagnostics(selected) {
      const guarantee = !bad(selected), prevention = bad(complement(selected));
      const removable = guarantee && prevention ? selected.filter(c => valid(selected.filter(x => x !== c))) : [];
      const minimality = guarantee && prevention && removable.length === 0;
      return {correct:minimality, guarantee, prevention, minimality};
    }
    function witness(selected) {
      const layers = recurrence(selected, true), fixed = new Set(selected);
      let state = item.machine.initial;
      if (!layers[0][state]) return null;
      const inputs = [];
      for (let t = 0; t <= item.target_step; t++) {
        const valuation = permitted(fixed, t).find(v => t === item.target_step ? item.machine.transitions[state][v].output === 0 : layers[t + 1][item.machine.transitions[state][v].next]);
        if (valuation === undefined) throw Error('backward decision failed to supply its witness');
        inputs.push(range(m).map(r => bit(valuation, r)));
        state = item.machine.transitions[state][valuation].next;
      }
      return execution(item, inputs);
    }
    return {n, all, complement, bad, valid, diagnostics, witness};
  }
  function gradeWithGame(g, answer) {
    const empty = {correct:false, valid_format:false, guarantee:false, prevention:false, minimality:false, answer_kind:'invalid'};
    if (noExplanation(answer)) return {...empty, correct:!g.bad([]), valid_format:true, answer_kind:'no_explanation'};
    let selected;
    try { selected = parseCells(answer, g.n); }
    catch (error) { return {...empty, reason:error.message}; }
    return {...g.diagnostics(selected), valid_format:true, answer_kind:'explanation'};
  }
  function grade(item, answer) { return gradeWithGame(game(item), answer); }
  function execution(item, inputs) {
    const replay = simulate(item.machine, inputs), m = item.machine.inputs.length;
    if (inputs.length !== item.target_step + 1) throw Error('execution must cover exactly the target window');
    return {inputs:inputs.map(row => [...row]), ...replay, board_path:null,
      changed_cells:inputs.flatMap((row, t) => row.flatMap((value, r) => value !== item.observed[t][r] ? [t * m + r] : [])),
      target_flashes:replay.outputs[item.target_step] === 1};
  }
  function feedback(item, answer) {
    const g = game(item), result = gradeWithGame(g, answer);
    const response = {...result, selected_cells:null, tests:null};
    if (!result.valid_format || result.answer_kind !== 'explanation') {
      response.message = result.reason || (result.correct ? 'No explanation exists: every permitted setting leaves the target on.' : 'Some permitted setting turns the target off. Try marking switches.');
      return response;
    }
    const selected = parseCells(answer, g.n);
    const removable = selected.filter(c => g.valid(selected.filter(x => x !== c)));
    response.selected_cells = selected;
    response.tests = {
      guarantee:{passed:result.guarantee, witness:result.guarantee ? null : g.witness(selected)},
      prevention:{passed:result.prevention, witness:result.prevention ? g.witness(g.complement(selected)) : null},
      minimality:{passed:result.minimality, removable_cells:removable}
    };
    if (removable.length) {
      const removed = removable[0], flipped = item.observed.map(row => [...row]), m = item.machine.inputs.length;
      flipped[Math.floor(removed / m)][removed % m] = 1 - flipped[Math.floor(removed / m)][removed % m];
      const runs = [execution(item, item.observed), execution(item, flipped)];
      if (runs[0].target_flashes === runs[1].target_flashes) response.tests.minimality.removal_example = {
        removed_cell:removed, remaining_cells:selected.filter(c => c !== removed), runs,
        scope:'illustration_only; the exact grader checks all permitted completions'
      };
    }
    response.message = result.correct ? 'Both tests pass, with no unnecessary marks.' : !result.guarantee ? 'The target can turn off while your marks stay fixed.' : !result.prevention ? 'Changing only your marks cannot turn the target off.' : 'An unnecessary mark can be removed while both tests still pass.';
    return response;
  }
  function solve(item) {
    const g = game(item); let candidate = g.all;
    if (!g.valid(candidate)) return null;
    for (const c of g.all) { const smaller = candidate.filter(x => x !== c); if (g.valid(smaller)) candidate = smaller; }
    return candidate;
  }
  function reveal(item) {
    const selected = solve(item), answer = selected === null ? {verdict:'no_explanation'} : {cells:selected};
    return {answer, feedback:feedback(item, answer), answer_inventory:'one_example_not_exhaustive'};
  }
  return {SEMANTICS_VERSION, validateItem, parseCells, cellCount:count, simulate, execution, grade, feedback, solve, reveal};
});
