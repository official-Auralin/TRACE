"""The visible terminal event must be exactly the event used by G/P grading."""
import copy
import unittest

from benchmark.compile import LeanProcess, compile_item, normalize
from benchmark.core import grade, public_item, simulate, validate_item
from benchmark.level import execute, public_board, terminal_display
from benchmark.teaching import practice_feedback


def screenshot_record():
    # Exact two-round machine behind the reported A · 2 ambiguity.
    return {'id':'terminal-target-regression','split':'tutorial',
            'machine':{'initial':0,'inputs':['A'],'states':2,'transitions':[
                [{'next':1,'output':0},{'next':0,'output':1}],
                [{'next':1,'output':1},{'next':0,'output':1}]]},
            'observed':[[0],[0]],'target_step':1}


class TerminalDisplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=screenshot_record()
        with LeanProcess('CompileLevel.lean') as compiler:
            cls.item=compile_item(cls.source,compiler)

    def test_reported_four_cases_and_all_candidate_grades_are_unchanged(self):
        source=normalize(self.source)
        for first,second,target in ((0,0,1),(0,1,1),(1,0,0),(1,1,1)):
            word=[[first],[second]]
            replay=execute(self.item['board'],word)
            self.assertEqual(replay['outputs'],simulate(source['machine'],word)['outputs'])
            self.assertEqual(replay['target'],target)
            root=self.item['board']['display']['terminal'][replay['states'][-2]]
            while root['kind']=='switch':root=root['one' if word[1][0] else 'zero']
            self.assertEqual(root['value'],target)
        for mask in range(4):
            answer={'cells':[c for c in range(2) if mask & (1<<c)]}
            self.assertEqual(grade(self.item,answer),grade(source,answer))
            self.assertEqual(grade(self.item,answer)['correct'],mask==1)

    def test_final_route_collapses_only_when_target_is_constant(self):
        display=self.item['board']['display']
        self.assertEqual(display,{'version':'trace.display.v1','terminal':[
            {'kind':'switch','cell':1,'zero':{'kind':'outcome','value':0},
             'one':{'kind':'outcome','value':1}},
            {'kind':'outcome','value':1}]})
        self.assertEqual([control['cell'] for control in self.item['board']['switches']],[0,1])

    def test_earlier_equal_outputs_with_different_successors_are_preserved(self):
        board=self.item['board']
        first=board['layers'][0][1]
        self.assertEqual(first['kind'],'switch')
        self.assertEqual(first['zero']['value'],first['one']['value'])
        self.assertNotEqual(first['zero']['next'],first['one']['next'])
        self.assertEqual(board['layers'][-1][1]['kind'],'switch')
        self.assertEqual(board['display']['terminal'][1],{'kind':'outcome','value':1})

    def test_missing_forged_or_noncanonical_displays_are_rejected(self):
        mutations=[]
        missing=copy.deepcopy(self.item);missing['board'].pop('display');mutations.append(missing)
        unknown=copy.deepcopy(self.item);unknown['board']['display']['goal']='node';mutations.append(unknown)
        wrong=copy.deepcopy(self.item);wrong['board']['display']['terminal'][1]['value']=0;mutations.append(wrong)
        future=copy.deepcopy(self.item);future['board']['display']['terminal'][1]['next']=1;mutations.append(future)
        boolean=copy.deepcopy(self.item);boolean['board']['display']['terminal'][1]['value']=True;mutations.append(boolean)
        wrong_cell=copy.deepcopy(self.item);wrong_cell['board']['display']['terminal'][0]['cell']=0;mutations.append(wrong_cell)
        unreduced=copy.deepcopy(self.item);leaf={'kind':'outcome','value':1}
        unreduced['board']['display']['terminal'][1]={'kind':'switch','cell':1,'zero':leaf,'one':leaf}
        mutations.append(unreduced)
        for malformed in mutations:
            with self.subTest(display=malformed['board'].get('display')):
                with self.assertRaisesRegex(ValueError,'terminal display'):validate_item(malformed)

    def test_native_constructor_cannot_silently_use_reference_display(self):
        old=copy.deepcopy(self.item['board']);old.pop('display')
        class StaleCompiler:
            def request(self, item):return old
        with self.assertRaisesRegex(ValueError,'Lean constructor must emit'):
            compile_item(self.source,StaleCompiler())

    def test_native_projection_matches_independent_reference_and_public_contract(self):
        board=self.item['board']
        self.assertEqual(board['display'],terminal_display(board))
        exposed=public_item(self.item)
        self.assertEqual(exposed['board']['display'],board['display'])
        self.assertEqual(exposed['machine'],self.source['machine'])
        self.assertEqual(exposed['observed'],self.source['observed'])
        # The public allowlist does not expose arbitrary private board metadata.
        private=copy.deepcopy(board);private['certificate']={'secret':True}
        private['display']['private_note']='do not expose'
        private['display']['terminal'][1]['private_note']='do not expose'
        self.assertEqual(public_board(private),public_board(board))

    def test_practice_removal_pair_illustrates_conditional_not_global_irrelevance(self):
        feedback=practice_feedback(self.item,{'cells':[0,1]})
        example=feedback['tests']['minimality']['removal_example']
        self.assertEqual(example['removed_cell'],1)
        self.assertEqual(example['remaining_cells'],[0])
        self.assertEqual([run['inputs'] for run in example['runs']],[[[0],[0]],[[0],[1]]])
        self.assertEqual([run['target_flashes'] for run in example['runs']],[True,True])
        self.assertIn('illustration_only',example['scope'])
        self.assertNotEqual(simulate(self.source['machine'],[[1],[0]])['outputs'][-1],
                            simulate(self.source['machine'],[[1],[1]])['outputs'][-1])
        self.assertNotIn('removal_example',practice_feedback(self.item,{'cells':[0]})['tests']['minimality'])


if __name__=='__main__':unittest.main()
