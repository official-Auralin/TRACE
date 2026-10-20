"""TRACE2 finite combined guarantee/prevention explanations.
Cells denote recorded Boolean values; accepted sets are inclusion-minimal G and P.
The live grader uses backward reachability, never a stored canonical answer.
"""
from itertools import product
import hashlib
import json

PROTOCOL_VERSION = 'trace-study-v5'
DATA_VERSION = 'trace-mealy-v5'
MODES = ('explanation',)
SEMANTICS = {
    'version': 'trace.gp.v2', 'answer': 'one inclusion-minimal set satisfying guarantee and prevention',
    'cell_encoding': 'cell = step * number_of_inputs + input_index; both zero-based',
    'selected_value': 'the observed Boolean value, including zero',
    'output_timing': 'output is emitted by the current-state/current-input transition before changing state',
    'effect': 'the single output equals 1 at target_step',
    'guarantee': 'every input assignment agreeing with selected cells preserves the effect',
    'prevention': 'some input assignment agreeing with every unselected cell makes the effect false',
    'minimality': 'no proper subset still satisfies both; not minimum cardinality',
    'counterfactuals': 'all Boolean input assignments through target_step, replayed from the same initial state',
}

def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=True)

def digest(obj):
    return hashlib.sha256(canonical(obj).encode()).hexdigest()

def submasks(mask):
    sub = mask
    while True:
        yield sub
        if not sub:
            break
        sub = (sub - 1) & mask

def cells(mask, n):
    return [i for i in range(n) if mask & (1 << i)]

def validate_machine(m):
    if not isinstance(m, dict):
        raise ValueError('machine must be an object')
    if not isinstance(m.get('inputs'),list) or any(not isinstance(x,str) or not x for x in m['inputs']):
        raise ValueError('input names must be nonempty strings')
    ni = len(m['inputs'])
    ns = m.get('states')
    if ni < 1 or type(ns) is not int or ns < 1:
        raise ValueError('machine requires positive finite state and input counts')
    if len(set(m['inputs'])) != ni:
        raise ValueError('invalid input names')
    if type(m.get('initial')) is not int or not 0 <= m['initial'] < ns:
        raise ValueError('invalid initial state')
    if not isinstance(m.get('transitions'),list) or len(m['transitions']) != ns:
        raise ValueError('missing state rows')
    for row in m['transitions']:
        if not isinstance(row,list) or len(row) != 1 << ni:
            raise ValueError('input totality: missing or duplicate valuation')
        for edge in row:
            if not isinstance(edge,dict) or set(edge) != {'next','output'} or type(edge['next']) is not int or not 0 <= edge['next'] < ns or type(edge['output']) is not int or edge['output'] not in (0,1):
                raise ValueError('invalid deterministic transition')
    return True

def simulate(machine, inputs):
    state = machine['initial']
    outputs, states = [], [state]
    ni = len(machine['inputs'])
    for step in inputs:
        if not isinstance(step,list) or len(step) != ni or any(type(v) is not int or v not in (0,1) for v in step):
            raise ValueError('input step must contain binary integers')
        iv = sum(v << j for j,v in enumerate(step))
        edge = machine['transitions'][state][iv]
        outputs.append(edge['output'])
        state = edge['next']
        states.append(state)
    return {'outputs':outputs, 'states':states}

def assignment(mask, ni, length):
    return [[(mask >> (t*ni+r)) & 1 for r in range(ni)] for t in range(length)]

def input_mask(observed):
    return sum(v << (t*len(step)+r) for t,step in enumerate(observed) for r,v in enumerate(step))

def truth_table(item):
    ni, length = len(item['machine']['inputs']), item['target_step']+1
    return [simulate(item['machine'], assignment(a,ni,length))['outputs'][-1] for a in range(1 << (ni*length))]

def relative_table(item, absolute=None):
    absolute = truth_table(item) if absolute is None else absolute
    actual = input_mask(item['observed'])
    return [absolute[actual ^ d] for d in range(len(absolute))]

def minimal_false_supports(f):
    """Finite hypergraph helper for independent cross-checks and declared selection."""
    n = len(f).bit_length()-1
    if n < 0 or len(f) != 1 << n or not f[0] or any(type(v) not in (int,bool) or v not in (0,1) for v in f):
        raise ValueError('a true actual effect and Boolean power-of-two truth table are required')
    minimal = []
    for mask in sorted((m for m in range(1 << n) if not f[m]), key=lambda m:(m.bit_count(),m)):
        if not any(h & mask == h for h in minimal):
            minimal.append(mask)
    return minimal

def key_from_table(f):
    """Hypergraph cross-check: min unions of a minimal transversal and bad support.
    This is separate from the production backward-game implementation.
    """
    n = len(f).bit_length()-1
    joints = minimal_false_supports(f)
    pins = []
    for mask in sorted(range(1 << n), key=lambda m:(m.bit_count(),m)):
        if all(mask & h for h in joints) and not any(p & mask == p for p in pins):
            pins.append(mask)
    unions = {p | h for p in pins for h in joints}
    accepted = [s for s in unions if not any(t != s and t & s == t for t in unions)]
    return {'explanation':[cells(mask,n) for mask in sorted(accepted)]}

def cell_count(item):
    return len(item['machine']['inputs']) * (item['target_step']+1)

def validate_item(item):
    if not isinstance(item,dict) or not {'machine','observed','target_step'} <= item.keys():
        raise ValueError('item requires machine, observed and target_step')
    validate_machine(item['machine'])
    k = item['target_step']
    if type(k) is not int or k < 0 or not isinstance(item['observed'],list) or len(item['observed']) != k+1:
        raise ValueError('observed inputs must end exactly at the nonnegative target step')
    replay = simulate(item['machine'], item['observed'])
    if replay['outputs'][k] != 1:
        raise ValueError('the selected target must be an observed positive output')
    if 'observed_outputs' in item and item['observed_outputs'] != replay['outputs']:
        raise ValueError('recorded outputs disagree with the machine')
    if 'observed_states' in item and item['observed_states'] != replay['states']:
        raise ValueError('recorded states disagree with the machine')
    if 'semantics' in item and item['semantics'] != SEMANTICS:
        raise ValueError('unsupported semantic contract')
    if 'board' in item:
        from .boards import validate_board
        validate_board(item['board'],item['observed'],machine=item['machine'])
    return replay

def compute_key(item):
    from .game import minimal_answers
    return {'explanation':minimal_answers(item)}

def parse_cells(answer, n):
    if not isinstance(answer,dict) or set(answer) != {'cells'}:
        raise ValueError('answer must be exactly {"cells": [integer cell IDs]}')
    selected = answer['cells']
    if not isinstance(selected,list) or any(type(c) is not int or not 0 <= c < n for c in selected) or len(selected) != len(set(selected)):
        raise ValueError('cell IDs must be unique in-window integers')
    return sorted(selected)

def grade(item, answer, mode='explanation', key=None):
    """Accept any minimal G/P explanation. key is never trusted for grading."""
    if mode not in MODES:
        raise ValueError('unknown mode')
    from .game import diagnostics, bad_root
    validate_item(item)
    empty = {'correct':False,'valid_format':False,'guarantee':False,'prevention':False,'minimality':False,'answer_kind':'invalid'}
    if isinstance(answer,dict) and answer == {'verdict':'no_explanation'}:
        return {**empty,'correct':not bad_root(item,[]), 'valid_format':True,'answer_kind':'no_explanation'}
    try:
        selected = parse_cells(answer,cell_count(item))
    except ValueError as e:
        return {**empty,'reason':str(e)}
    return {**diagnostics(item,selected),'valid_format':True,'answer_kind':'explanation'}

def public_item(item):
    # Explicit allowlist; operator keys, recipes, families and certificates stay private.
    replay = validate_item(item)
    source=item['machine']
    machine={'inputs':list(source['inputs']),'states':source['states'],'initial':source['initial'],
             'transitions':[[{'next':edge['next'],'output':edge['output']} for edge in row]
                            for row in source['transitions']]}
    result = {'id':item['id'],'machine':machine,'observed':[list(row) for row in item['observed']],
              'observed_outputs':replay['outputs'],'observed_states':replay['states'],
              'target_step':item['target_step'],'semantics':dict(SEMANTICS)}
    if 'board' in item:
        from .boards import public_board
        result['board'] = public_board(item['board'])
    return result

def probe(item, changes):
    n = len(item['machine']['inputs'])*(item['target_step']+1)
    if not isinstance(changes,dict):
        raise ValueError('changes must map string cell IDs to 0 or 1')
    observed = [list(s) for s in item['observed']]
    ni = len(item['machine']['inputs'])
    for c,v in changes.items():
        if not isinstance(c,str) or not c.isdigit() or str(int(c)) != c or not 0 <= int(c)<n or type(v) is not int or v not in (0,1):
            raise ValueError('invalid probe assignment')
        observed[int(c)//ni][int(c)%ni] = v
    result = simulate(item['machine'],observed)
    from .boards import trace_board
    board_path=trace_board(item['board'],observed)['path'] if 'board' in item else None
    return {'inputs':observed,'outputs':result['outputs'],'states':result['states'],'board_path':board_path,
            'target_flashes':bool(result['outputs'][item['target_step']]),
            'switches_changed':sum(a!=b for old,new in zip(item['observed'],observed) for a,b in zip(old,new))}
