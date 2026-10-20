"""Public practice feedback. Never attached to scored-item receipts.

A defeating run is a witness for failed HOLD or successful CHANGE. Absence of
such a run is decided by the backward game; no single animation proves absence.
"""
from functools import lru_cache
from itertools import product
from .core import cell_count, cells, grade, parse_cells, public_item, simulate
from .game import Game, allowed_values, bad_query, solve
from .instructions import TUTORIAL_EXPLANATION


def execution(item, inputs):
    result = simulate(item['machine'], inputs)
    ni = len(item['machine']['inputs'])
    from .boards import trace_board
    board_path=trace_board(item['board'],inputs)['path'] if 'board' in item else None
    return {'inputs':inputs, **result, 'board_path':board_path,
            'changed_cells':[t*ni+r for t,row in enumerate(inputs)
                             for r,value in enumerate(row) if value != item['observed'][t][r]],
            'target_flashes':bool(result['outputs'][item['target_step']])}


def defeating_execution(item, fixed):
    layers = bad_query(item, fixed)
    state = item['machine']['initial']
    if not layers[0][state]:
        return None
    ni = len(item['machine']['inputs']); inputs = []
    for t in range(item['target_step']+1):
        for valuation in allowed_values(item, set(fixed), t):
            edge = item['machine']['transitions'][state][valuation]
            if edge['output'] == 0 if t == item['target_step'] else layers[t+1][edge['next']]:
                inputs.append([(valuation >> r) & 1 for r in range(ni)])
                state = edge['next']
                break
        else:
            raise ValueError('Backward game did not supply its claimed witness')
    return execution(item, inputs)


def practice_solution(item):
    """One example answer, not an exhaustive family or a stored-key lookup."""
    selected = solve(item)
    return {'answer':{'verdict':'no_explanation'} if selected is None else {'cells':selected},
            'accepted_explanations':[] if selected is None else [selected],
            'answer_inventory':'one_example_not_exhaustive'}


def practice_feedback(item, answer):
    """Explain the submitted set without revealing any other scored item."""
    result = grade(item, answer)
    game = Game(item)
    solution = practice_solution(item)
    answers = solution['accepted_explanations']
    # Keep the participant's alternative visible when it is also correct.
    if result['correct'] and result.get('answer_kind') == 'explanation':
        selected = parse_cells(answer, game.n)
        if selected not in answers:answers.append(selected)
    feedback = {'correct':result['correct'], 'item':public_item(item),
                'correct_cells':answers[0] if answers else [],
                'accepted_explanations':answers, 'answer':solution['answer'],
                'answer_inventory':'examples_not_exhaustive', 'explanation':TUTORIAL_EXPLANATION}
    if not result['valid_format'] or result['answer_kind'] != 'explanation':
        feedback.update(selected_cells=None, tests=None,
                        message=result.get('reason', 'No explanation exists.' if result['correct']
                                           else 'Some setting can turn this light off. Try marking switches.'))
        return feedback
    selected = parse_cells(answer, game.n)
    mask = sum(1 << c for c in selected)
    removable = [c for c in selected if game.valid(mask ^ (1 << c))]
    feedback.update(selected_cells=selected, tests={
        'guarantee':{'passed':result['guarantee'],
                     'witness':None if result['guarantee'] else defeating_execution(item, selected)},
        'prevention':{'passed':result['prevention'],
                      'witness':defeating_execution(item, sorted(set(range(game.n))-set(selected)))
                                if result['prevention'] else None},
        'minimality':{'passed':result['minimality'], 'removable_cells':removable}})
    if removable:
        removed=removable[0]
        flipped=[list(row) for row in item['observed']]
        m=len(item['machine']['inputs']);flipped[removed//m][removed%m]^=1
        runs=[execution(item,item['observed']),execution(item,flipped)]
        # This pair illustrates one deletion; the exact grader establishes both
        # quantified conditions for the remaining set. It does not establish
        # that the removed input is irrelevant under all other assignments.
        if runs[0]['target_flashes']==runs[1]['target_flashes']:
            feedback['tests']['minimality']['removal_example']={
                'removed_cell':removed,'remaining_cells':[c for c in selected if c!=removed],
                'runs':runs,
                'scope':'illustration_only; the exact grader checks all permitted completions'}
    return feedback


def completions(item, selected, stage):
    """All assignments to the visible free switches, with omitted dummy cells fixed.

    Board construction checks establish that input cells absent from the board
    cannot change the route. The declared count includes those duplicate words.
    """
    n = cell_count(item); ni = len(item['machine']['inputs'])
    visible = sorted({node['cell'] for node in item['board']['nodes'] if node['kind'] == 'switch'})
    free = sorted(set(visible)-set(selected)) if stage == 'hold' else sorted(set(visible)&set(selected))
    invisible_free = (n-len(selected)-len(free)) if stage == 'hold' else (len(selected)-len(free))
    paths = []
    for values in product((0,1), repeat=len(free)):
        inputs = [list(row) for row in item['observed']]
        for cell,value in zip(free,values):inputs[cell//ni][cell%ni] = value
        paths.append(execution(item,inputs))
    return {'stage':stage, 'free_cells':free, 'runs':paths,
            'complete_visible_assignments':True, 'input_words_covered':len(paths)*(1 << invisible_free)}


@lru_cache(maxsize=1)
def demonstrations():
    """Fixed public examples shared by humans and agents before any item clock."""
    from .boards import demo_items
    examples = []
    for item in demo_items():
        visible = sorted({node['cell'] for node in item['board']['nodes'] if node['kind'] == 'switch'})
        candidates = [[visible[0]]]
        accepted=item.get('key', {}).get('explanation', [])
        if accepted and accepted[0] not in candidates:candidates.append(accepted[0])
        # A visible branch can be unnecessary for this explanation, even if the switch
        # changes the outcome under other assignments.
        game = Game(item)
        for mask in range(1 << game.n):
            selected = cells(mask, game.n)
            if selected and set(selected) <= set(visible) and game.valid(mask) and not game.diagnostics(mask)['minimality']:
                if selected not in candidates:candidates.append(selected)
                break
        cases = []
        for selected in candidates:
            feedback = practice_feedback(item, {'cells':selected})
            label='One mark' if len(selected)==1 else ('An extra mark' if feedback['tests']['minimality']['removable_cells'] else 'These marks')
            cases.append({'label':label,'selected_cells':selected, 'correct':feedback['correct'], 'tests':feedback['tests'],
                          'completions':{stage:completions(item,selected,stage) for stage in ('hold','change-marked')}})
        titles={'demo-direct':'Follow the pulse','demo-or':'Two ways to the light','demo-and':'Both switches matter','demo-xor':'Linked switches','demo-choice':'Leave no extra marks'}
        captions={'demo-direct':'Mark the switch that holds the light on and can turn it off.',
                  'demo-or':'One path can keep the light on while the other changes.',
                  'demo-and':'A break anywhere along this route turns the light off.',
                  'demo-xor':'Copies with the identical full label are one switch; they move together.'}
        examples.append({'id':item['id'], 'title':titles.get(item['id'],'Leave no extra marks'),
                         'caption':captions.get(item['id'],'Remove marks that neither test needs.'),
                         'item':public_item(item), 'cases':cases})
    return examples
