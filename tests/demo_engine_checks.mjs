// JSON batch runner used by the Python differential tests. No browser globals.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import engine from '../demo/engine.js';
const payload = JSON.parse(fs.readFileSync(0, 'utf8'));
let checks = 0;
for (const fixture of payload.fixtures || []) {
  for (const candidate of fixture.candidates) {
    assert.deepEqual(engine.grade(fixture.item, candidate.answer), candidate.expected,
      `grade differs for ${fixture.item.id} and ${JSON.stringify(candidate.answer)}`);
    if (candidate.tests !== undefined) {
      const feedback = engine.feedback(fixture.item, candidate.answer);
      assert.deepEqual(feedback.tests, candidate.tests, `feedback differs for ${fixture.item.id}`);
      assert.equal('answer' in feedback, false, 'normal feedback leaked a solution');
      assert.equal('correct_cells' in feedback, false, 'normal feedback leaked canonical cells');
      if (feedback.tests) for (const name of ['guarantee', 'prevention']) {
        const witness = feedback.tests[name].witness;
        if (witness) {
          assert.equal(engine.execution(fixture.item, witness.inputs).target_flashes, false);
          const selected = new Set(candidate.answer.cells);
          const changed = witness.changed_cells;
          assert(changed.every(c => name === 'guarantee' ? !selected.has(c) : selected.has(c)), 'illegal intervention witness');
        }
      }
    }
    checks++;
  }
  if ('solution' in fixture) {
    assert.deepEqual(engine.solve(fixture.item), fixture.solution);
    const revealed = engine.reveal(fixture.item);
    assert.equal(engine.grade(fixture.item, revealed.answer).correct, true);
    checks++;
  }
}
for (const item of payload.invalid_items || []) { assert.throws(() => engine.validateItem(item)); checks++; }
console.log(JSON.stringify({checks}));
