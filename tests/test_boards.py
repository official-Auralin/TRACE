import copy,json,unittest
from itertools import product
from benchmark.boards import compile_machine,make_board,trace_board,public_board,validate_board,demo_items
from benchmark.core import assignment,grade,simulate
from benchmark.reference import source_execute

class SwitchBoardTests(unittest.TestCase):
    def test_demonstrations_are_exact_under_all_assignments(self):
        demos=demo_items()
        self.assertEqual([i['id'] for i in demos],['demo-direct','demo-and','demo-or','demo-xor','demo-choice'])
        for item in demos:
            self.assertTrue(validate_board(item['board'],item['observed']))
            for mask in range(1<<(2*len(item['observed']))):
                word=assignment(mask,2,len(item['observed']))
                self.assertEqual(trace_board(item['board'],word)['outputs'],simulate(item['machine'],word)['outputs'])
            for answer in item['key']['explanation']:
                self.assertTrue(grade(item,{'cells':answer})['correct'])
        xor=demos[3]
        self.assertEqual(xor['key']['explanation'],[[0,2]])
        both=copy.deepcopy(xor['observed']);both[0][0]^=1;both[1][0]^=1
        self.assertEqual(trace_board(xor['board'],both)['target'],1)
        only=copy.deepcopy(xor['observed']);only[0][0]^=1
        self.assertEqual(trace_board(xor['board'],only)['target'],0)
        choice=demos[4]
        self.assertEqual(choice['key']['explanation'],[[0,3],[2,3]])
        self.assertFalse(grade(choice,{'cells':[0,2,3]})['correct'])

    def test_early_lamp_and_drain_latch_at_every_later_round(self):
        recipe={'version':'trace.switch-network.v1','family':'fixture','horizon':3,'initial_lane':0,
                'edges':[[[2,3],[0,1]],[[0,1],[1,0]],[[2,3],[3,2]]]}
        machine=compile_machine(recipe);observed=[[0,0],[1,1],[0,1]];board=make_board(recipe,observed)
        for mask in range(64):
            word=assignment(mask,2,3);output=simulate(machine,word)
            self.assertEqual(output,source_execute(recipe,word,return_states=True))
            self.assertEqual(output['outputs'],trace_board(board,word)['outputs'])
            self.assertEqual(output['outputs'],[1-word[0][0]]*3)
        self.assertEqual(len(board['switches']),1)

    def test_public_projection_discards_private_metadata_at_every_level(self):
        board=copy.deepcopy(demo_items()[0]['board']);expected=copy.deepcopy(board)
        board['answer']=[0]
        for collection in ('nodes','switches','columns'):
            for row in board[collection]:row['secret_recipe']='not public'
        self.assertEqual(public_board(board),expected)

    def test_malformed_display_metadata_is_rejected(self):
        item=demo_items()[1]
        mutations=[lambda b:b['nodes'].append(copy.deepcopy(b['nodes'][0])),
                   lambda b:b['nodes'][0].update(zero=999),
                   lambda b:b['nodes'][1].update(one=b['start']),
                   lambda b:b['nodes'][0].update(cell=99),
                   lambda b:b['nodes'][0].update(kind='answer'),
                   lambda b:b['switches'][0].update(value=0),
                   lambda b:b.update(recorded_path=[b['start']]),
                   lambda b:b.update(start=True)]
        for mutate in mutations:
            board=copy.deepcopy(item['board']);mutate(board)
            with self.assertRaises(ValueError):validate_board(board,item['observed'])

if __name__=='__main__':unittest.main()
