"""Finite semantics regressions, exhaustive Boolean cases, and hostile certificates."""
import copy
import unittest
from benchmark.core import (grade,key_from_table,parse_cells,public_item,simulate,
                            validate_machine,validate_item)
from benchmark.game import (Game,bad_query,diagnostics,make_certificate,
                            minimal_answers,solve,verify_certificate,build_verification_game,verification_game_winner)
from benchmark.reference import direct_key,direct_item_table,direct_predicates
from benchmark.reference import replay_visible_links


def table_item(f):
    """Realize any <=4-variable table as a tiny total Mealy machine.
    This fixture does not use the production compiler or simulator to build rows.
    """
    n=len(f).bit_length()-1
    if n in (1,2):
        ni=n;length=1;states=1
        transitions=[[{'next':0,'output':v} for v in f]]
    elif n==3:
        ni=1;length=3;states=4
        transitions=[[{'next':(q//2)+2*v,'output':f[q+4*v]} for v in range(2)] for q in range(4)]
    elif n==4:
        ni=2;length=2;states=4
        transitions=[[{'next':v,'output':f[q+4*v]} for v in range(4)] for q in range(4)]
    else:
        raise ValueError(n)
    return {'id':'boolean-fixture','machine':{'inputs':['x'+str(i) for i in range(ni)],
            'states':states,'initial':0,'transitions':transitions},
            'observed':[[0]*ni for _ in range(length)],'target_step':length-1}


class FiniteGameTests(unittest.TestCase):
    def test_all_32907_true_actual_boolean_functions_through_four_cells(self):
        checked=0
        for n in range(5):
            for suffix in range(1 << ((1 << n)-1)):
                f=[1]+[(suffix >> i)&1 for i in range((1 << n)-1)]
                ref=direct_key(f)
                self.assertEqual(key_from_table(f),ref)
                if n:
                    item=table_item(f)
                    self.assertEqual(direct_item_table(item),f)
                    self.assertEqual(minimal_answers(item),ref['explanation'])
                    witness=solve(item)
                    self.assertTrue(witness in ref['explanation'] if witness is not None else not ref['explanation'])
                checked+=1
        self.assertEqual(checked,32907)

    def test_combined_or_and_xor_and_nonmonotone(self):
        for f in ([1,1,1,0],[1,0,0,0],[1,0,0,1]):
            item=table_item(f)
            self.assertEqual(minimal_answers(item),[[0,1]])
            self.assertTrue(grade(item,{'cells':[0,1]})['correct'])
            self.assertFalse(grade(item,{'cells':[0]})['correct'])
            self.assertFalse(grade(item,{'cells':[]})['correct'])
        # XOR preserves the effect after toggling all selected cells; P is existential.
        self.assertEqual(direct_predicates([1,0,0,1],[0,1]),(True,True))

    def test_dummy_cells_and_multiple_accepted_answers(self):
        item=table_item([1,1,1,0,0,0,0,0])
        accepted=minimal_answers(item)
        self.assertEqual(accepted,[[0,2],[1,2]])
        for answer in accepted:self.assertTrue(grade(item,{'cells':answer})['correct'])
        bigger=grade(item,{'cells':[0,1,2]})
        self.assertTrue(bigger['guarantee'] and bigger['prevention'])
        self.assertFalse(bigger['minimality'])
        self.assertEqual(minimal_answers(table_item([1,0,1,0])),[[0]])

    def test_minimal_does_not_mean_minimum_cardinality(self):
        # Failures have minimal supports {0,1} and {2,3,4}.
        f=[int(not((s&3)==3 or (s&28)==28)) for s in range(32)]
        family=key_from_table(f)['explanation']
        self.assertEqual({len(s) for s in family},{3,4})
        self.assertEqual(direct_key(f)['explanation'],family)

    def test_invariant_typed_no_explanation(self):
        item=table_item([1]*8)
        self.assertIsNone(solve(item));self.assertEqual(minimal_answers(item),[])
        self.assertTrue(grade(item,{'verdict':'no_explanation'})['correct'])
        self.assertFalse(grade(item,{'cells':[]})['correct'])
        self.assertFalse(grade(table_item([1,0]),{'verdict':'no_explanation'})['correct'])
        self.assertTrue(verify_certificate(item,make_certificate(item)))
        self.assertEqual(key_from_table([1]),{'explanation':[]})

    def test_valid_certificates_and_mutations(self):
        item=table_item([1,1,1,0,0,0,0,0]);cert=make_certificate(item)
        self.assertTrue(verify_certificate(item,cert))
        variants=[]
        c=copy.deepcopy(cert);c['instance_sha256']='wrong';variants.append(c)
        c=copy.deepcopy(cert);c['actual_execution']['outputs'][-1]=0;variants.append(c)
        c=copy.deepcopy(cert);c['queries'].pop();variants.append(c)
        c=copy.deepcopy(cert);c['queries'][0]['bad_layers'][0][0]=not c['queries'][0]['bad_layers'][0][0];variants.append(c)
        c=copy.deepcopy(cert);c['queries'][0]['bad_layers'][0][0]=1;variants.append(c)
        c=copy.deepcopy(cert);c['queries'][-1]['bad_layers'][-1][-1]=not c['queries'][-1]['bad_layers'][-1][-1];variants.append(c)
        c=copy.deepcopy(cert);c['answer']={'cells':[0,1,2]};variants.append(c)
        c=copy.deepcopy(cert);c['answer']={'verdict':'no_explanation'};variants.append(c)
        c=copy.deepcopy(cert)
        for q in c['queries']:
            if q['failure_inputs'] is not None:q['failure_inputs']=None;break
        variants.append(c)
        for forged in variants:
            with self.assertRaises((ValueError,TypeError)):verify_certificate(item,forged)
        changed=copy.deepcopy(item);changed['machine']['initial']=1
        with self.assertRaises(ValueError):verify_certificate(changed,cert)

    def test_explicit_parity_game_all_candidates_through_three_cells(self):
        for n in range(1,4):
            for suffix in range(1<<((1<<n)-1)):
                f=[1]+[(suffix>>i)&1 for i in range((1<<n)-1)]
                item=table_item(f)
                for mask in range(1<<n):
                    chosen=[c for c in range(n) if mask&(1<<c)]
                    explicit=build_verification_game(item,chosen)
                    self.assertEqual(verification_game_winner(explicit),all(direct_predicates(f,chosen)))
        corrupted=build_verification_game(table_item([1,0]),[0])
        corrupted['nodes']['root']['edges']=[{'to':'root'}]
        with self.assertRaises(ValueError):verification_game_winner(corrupted)

    def test_false_recording_and_target_rejected(self):
        with self.assertRaises(ValueError):validate_item(table_item([0,1]))
        item=table_item([1,0]);item['observed_outputs']=[0]
        with self.assertRaises(ValueError):validate_item(item)
        item=table_item([1,0]);item['observed'].append([0])
        with self.assertRaises(ValueError):validate_item(item)

    def test_strict_answer_formats_and_private_key_not_trusted(self):
        item=table_item([1,0,0,1])
        for answer in ({'cells':[True]},{'cells':[0,0]},{'cells':[-1]},
                       {'cells':[2]},{'cells':[],'extra':0},[],None):
            self.assertFalse(grade(item,answer)['valid_format'])
        self.assertTrue(grade(item,{'cells':[0,1]},key={'explanation':[[]]})['correct'])
        with self.assertRaises(ValueError):grade(item,{'cells':[0]},'credit_union')

    def test_public_timing_encoding_and_allowlist(self):
        item=table_item([1,0,1,0]);item.update(recipe={'private':1},key={'private':1},family='private')
        item['machine']['private_annotation']={'key':'researcher-only'}
        public=public_item(item)
        self.assertFalse({'key','certificate','recipe','family'} & public.keys())
        self.assertEqual(set(public['machine']),{'inputs','states','initial','transitions'})
        self.assertNotIn('private_annotation',public['machine'])
        public['machine']['transitions'][0][0]['output']=0
        self.assertEqual(item['machine']['transitions'][0][0]['output'],1)
        self.assertEqual(len(public['observed_states']),item['target_step']+2)
        self.assertIn('before changing state',public['semantics']['output_timing'])
        self.assertEqual(simulate(item['machine'],[[1,0]])['outputs'],[0])

    def test_invalid_machines(self):
        good=table_item([1,0])['machine']
        self.assertTrue(validate_machine(good))
        for changes in ({'initial':True},{'transitions':[good['transitions'][0][:1]]},{'inputs':['a','a']}):
            with self.assertRaises(ValueError):validate_machine({**good,**changes})

class VisibleBoardContractTests(unittest.TestCase):
    def test_visual_cell_encoding_rejects_non_two_channel_machines(self):
        from benchmark.boards import demo_items
        item=demo_items()[1]
        item['machine']['inputs']=['a']
        item['machine']['transitions']=[row[:2] for row in item['machine']['transitions']]
        item['observed']=[[row[0]] for row in item['observed']]
        replay=simulate(item['machine'],item['observed'])
        item['observed_outputs']=replay['outputs'];item['observed_states']=replay['states']
        # The board labels its later switch cell 2; a one-input machine has only 0,1.
        with self.assertRaisesRegex(ValueError,'exactly two input channels'):validate_item(item)

    def test_chance_and_all_switch_baselines_use_only_displayed_controls(self):
        import random
        from benchmark.boards import demo_items
        from benchmark.evaluate import baseline_answer
        item=demo_items()[3]
        visible={switch['cell'] for switch in item['board']['switches']}
        self.assertEqual(visible,{0,2})
        self.assertEqual(set(baseline_answer(item,'all',random.Random(0))['cells']),visible)
        self.assertEqual(baseline_answer(item,'latest',random.Random(0))['cells'],[2])
        for seed in range(32):
            self.assertLessEqual(set(baseline_answer(item,'random',random.Random(seed))['cells']),visible)

    def test_visible_metadata_allowlist_and_certificate_binding(self):
        from benchmark.boards import demo_items,public_board
        item=demo_items()[3]
        item['board']['private_answer']='SECRET-RESEARCHER-ANSWER'
        for entry in item['board']['nodes']:entry['private_answer']='SECRET-RESEARCHER-ANSWER'
        public=public_item(item)
        self.assertNotIn('SECRET-RESEARCHER-ANSWER',str(public))
        self.assertEqual(set(public['board']),{'version','start','width','height','nodes','columns','switches','recorded_path'})
        cert=make_certificate(item)
        self.assertTrue(verify_certificate(public,cert))
        metadata=copy.deepcopy(item['board'])
        for field in ('switches','columns'):
            for entry in metadata[field]:entry['private_answer']='SECRET-RESEARCHER-ANSWER'
        self.assertNotIn('SECRET-RESEARCHER-ANSWER',str(public_board(metadata)))
        public['board']['nodes'][0]['y']=2
        self.assertNotEqual(public['board']['nodes'][0]['y'],item['board']['nodes'][0]['y'])
        validate_item(public) # The mutation is well formed; the identity binding must reject it.
        with self.assertRaisesRegex(ValueError,'certificate instance/version mismatch'):verify_certificate(public,cert)

    def test_early_lamp_and_drain_are_absorbing(self):
        # The second round is irrelevant after either terminal is reached.
        item={'machine':{'inputs':['a'],'states':3,'initial':0,
              'transitions':[[{'next':1,'output':0},{'next':2,'output':1}],
                             [{'next':1,'output':0}]*2,[{'next':2,'output':1}]*2]},
              'observed':[[1],[0]],'target_step':1,
              'board':{'start':0,'nodes':[{'id':0,'kind':'switch','cell':0,'zero':1,'one':2},
                                        {'id':1,'kind':'drain'},{'id':2,'kind':'lamp'}]}}
        for a in (0,1):
            for b in (0,1):
                rows=[[a],[b]];visual=replay_visible_links(item,rows)
                self.assertEqual(visual['outputs'],simulate(item['machine'],rows)['outputs'])
                self.assertEqual(visual['path'],[0,2 if a else 1])
        self.assertEqual(minimal_answers({k:v for k,v in item.items() if k!='board'}),[[0]])

    def test_linked_visual_copies_read_the_same_cell_and_xor_is_existential(self):
        # The two second-column nodes are copies of the SAME switch (cell 2).
        # They must not become two independently editable inputs in the picture.
        item={'id':'visual-xor-fixture','machine':{'inputs':['a','unused'],'states':4,'initial':0,
              'transitions':[[{'next':1+(v&1),'output':0} for v in range(4)],
                             [{'next':3,'output':v&1} for v in range(4)],
                             [{'next':3,'output':1-(v&1)} for v in range(4)],
                             [{'next':3,'output':0} for _ in range(4)]]},
              'observed':[[0,0],[1,0]],'target_step':1,
              'board':{'start':0,'nodes':[{'id':0,'kind':'switch','cell':0,'zero':1,'one':2},
                                        {'id':1,'kind':'switch','cell':2,'zero':4,'one':3},
                                        {'id':2,'kind':'switch','cell':2,'zero':3,'one':4},
                                        {'id':3,'kind':'lamp'},{'id':4,'kind':'drain'}]}}
        for mask in range(16):
            rows=[[(mask>>(2*t+r))&1 for r in range(2)] for t in range(2)]
            self.assertEqual(replay_visible_links(item,rows)['outputs'],simulate(item['machine'],rows)['outputs'])
        self.assertEqual(minimal_answers({k:v for k,v in item.items() if k!='board'}),[[0,2]])
        self.assertEqual(replay_visible_links(item,[[1,0],[0,0]])['outputs'][-1],1)
        self.assertEqual(replay_visible_links(item,[[1,0],[1,0]])['outputs'][-1],0)
        broken=copy.deepcopy(item);broken['board']['nodes'][1]['cell']=0
        with self.assertRaises(ValueError):replay_visible_links(broken,broken['observed'])
        broken=copy.deepcopy(item);broken['board']['nodes'][0]['zero']=99
        with self.assertRaises(ValueError):replay_visible_links(broken,broken['observed'])

if __name__=='__main__':unittest.main()
