"""Shared visual teaching and practice-only causal feedback contracts."""
import tempfile
import unittest
from pathlib import Path
from benchmark.core import cell_count, grade, simulate
from benchmark.boards import demo_items, trace_board
from benchmark.runtime import StudyStore
from benchmark.teaching import demonstrations, practice_feedback


class VisualTeachingTests(unittest.TestCase):
    def test_demonstrations_are_complete_and_correct(self):
        originals={item['id']:item for item in demo_items()}
        demos=demonstrations()
        self.assertGreaterEqual(len(demos),4)
        for demo in demos:
            item=originals[demo['id']]
            for case in demo['cases']:
                chosen=set(case['selected_cells'])
                expected=grade(item,{'cells':list(chosen)})
                self.assertEqual(case['correct'],expected['correct'])
                for test in ('guarantee','prevention','minimality'):
                    self.assertEqual(case['tests'][test]['passed'],expected[test])
                for stage,sequence in case['completions'].items():
                    count=cell_count(item)-len(chosen) if stage=='hold' else len(chosen)
                    self.assertEqual(sequence['input_words_covered'],1 << count)
                    self.assertEqual(len(sequence['runs']),1 << len(sequence['free_cells']))
                    assignments=set()
                    for run in sequence['runs']:
                        flat=[v for row in run['inputs'] for v in row]
                        assignments.add(tuple(flat[c] for c in sequence['free_cells']))
                        changed=set(run['changed_cells'])
                        self.assertFalse(changed & chosen if stage=='hold' else changed-chosen)
                        replay=simulate(item['machine'],run['inputs'])
                        self.assertEqual(run['outputs'],replay['outputs'])
                        self.assertEqual(run['states'],replay['states'])
                        self.assertEqual(run['board_path'],trace_board(item['board'],run['inputs'])['path'])
                    self.assertEqual(len(assignments),len(sequence['runs']))
                    verdict=all(run['target_flashes'] for run in sequence['runs']) if stage=='hold' else any(not run['target_flashes'] for run in sequence['runs'])
                    self.assertEqual(verdict,expected['guarantee' if stage=='hold' else 'prevention'])

    def test_practice_witnesses_obey_the_two_different_constraints(self):
        for item in demo_items():
            n=cell_count(item)
            for mask in range(1 << n):
                selected=[c for c in range(n) if mask & (1 << c)]
                feedback=practice_feedback(item,{'cells':selected})
                for name,test in feedback['tests'].items():
                    if name=='minimality':
                        for removed in test['removable_cells']:
                            reduced=[c for c in selected if c!=removed]
                            score=grade(item,{'cells':reduced})
                            self.assertTrue(score['guarantee'] and score['prevention'])
                        continue
                    witness=test['witness']
                    needed=(not test['passed']) if name=='guarantee' else test['passed']
                    self.assertEqual(witness is not None,needed)
                    if witness:
                        self.assertFalse(witness['target_flashes'])
                        changes=set(witness['changed_cells'])
                        self.assertFalse(changes & set(selected) if name=='guarantee' else changes-set(selected))
                        self.assertEqual(simulate(item['machine'],witness['inputs'])['outputs'][-1],0)

    def test_linked_xor_can_prevent_without_flipping_every_mark(self):
        item=next(item for item in demo_items() if item['id']=='demo-xor')
        answer=item['key']['explanation'][0]
        feedback=practice_feedback(item,{'cells':answer})
        self.assertTrue(feedback['correct'])
        self.assertLess(len(feedback['tests']['prevention']['witness']['changed_cells']),len(answer))
        flipped=[list(row) for row in item['observed']]
        for cell in answer:flipped[cell//2][cell%2]^=1
        self.assertEqual(simulate(item['machine'],flipped)['outputs'][-1],1)

    def test_no_extra_marks_is_demonstrated_with_visible_switches(self):
        nonminimal=[]
        for demo in demonstrations():
            visible={switch['cell'] for switch in demo['item']['board']['switches']}
            for case in demo['cases']:
                if case['tests']['minimality']['removable_cells']:
                    self.assertTrue(set(case['selected_cells'])<=visible)
                    nonminimal.append(case)
        self.assertTrue(nonminimal)

    def test_curriculum_available_before_timer_and_identical_for_modalities(self):
        with tempfile.TemporaryDirectory() as temp:
            store=StudyStore(Path(temp)/'study.sqlite3')
            observations=[]
            for cohort in ('human','agent'):
                token=store.create(cohort,cohort,'pilot','pilot-01')['token']
                obs=store.act(token,'state')
                self.assertFalse(obs['active']);self.assertNotIn('deadline',obs)
                self.assertIn('Mark the switches',obs['instruction_brief'])
                observations.append(obs)
            self.assertEqual(observations[0]['demonstrations'],observations[1]['demonstrations'])
            self.assertEqual(observations[0]['instructions'],observations[1]['instructions'])

    def test_scored_receipts_withhold_all_practice_diagnostics(self):
        with tempfile.TemporaryDirectory() as temp:
            store=StudyStore(Path(temp)/'study.sqlite3')
            token=store.create('human','feedback','pilot','pilot-01')['token']
            for index in range(3):
                obs=store.act(token,'next')
                receipt=store.act(token,'submit',{'request_id':str(index),'item_id':obs['item']['id'],'answer':{'cells':[]}})
                if index<2:
                    self.assertIn('tests',receipt['feedback'])
                    self.assertEqual(receipt['feedback']['item'],obs['item'])
                else:
                    self.assertEqual(set(receipt),{'received','status','item_id','next_available'})
                    self.assertNotIn('feedback',store.act(token,'state')['last_receipt'])


if __name__=='__main__':unittest.main()
