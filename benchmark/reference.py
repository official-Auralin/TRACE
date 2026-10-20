"""Independent checks: source recurrences and direct finite G/P quantifiers.
Does not import production simulation, minimal-falsifier or hitting-set code.
"""
from itertools import combinations, product

def source_execute(recipe, sequence, return_states=False):
    """Independent route interpreter; never imports the compiler or board walker."""
    phase=0;lane=recipe['initial_lane'];outputs=[];states=[lane]
    for inputs in sequence:
        if lane in (0,1):
            channel=recipe.get('channels',[[0,1]]*recipe['horizon'])[phase][lane]
            pair=recipe['edges'][phase][lane]
            lane=pair[1] if inputs[channel] else pair[0]
        outputs.append(1 if lane==2 else 0)
        phase=min(phase+1,recipe['horizon']-1)
        states.append(4*phase+lane)
    return {'outputs':outputs,'states':states} if return_states else outputs

def all_subsets(values):
    values = list(values)
    for size in range(len(values)+1):
        yield from combinations(values,size)

def direct_predicates(f, selected):
    """Literal quantifiers, no hitting sets, backward tables or production helpers."""
    n = len(f).bit_length()-1
    if n < 0 or len(f) != 2**n or f[0] != 1:
        raise ValueError('true actual effect and full truth table required')
    chosen = sum(2**j for j in set(selected))
    outside = (2**n-1) ^ chosen
    guarantee = True; prevention = False
    # Integer indices enumerate the same complete Boolean change words. This
    # avoids rebuilding Python tuples for each candidate; no recurrence, winning
    # table, source compiler, hitting set, or production helper is used here.
    for changes,value in enumerate(f):
        if value:continue
        if changes & chosen == 0:guarantee=False
        if changes & outside == 0:prevention=True
    return guarantee, prevention

def direct_key(f):
    n = len(f).bit_length()-1
    candidates = list(all_subsets(range(n)))
    valid = [set(S) for S in candidates if all(direct_predicates(f,S))]
    accepted = [sorted(S) for S in valid if not any(T < S for T in valid)]
    return {'explanation':sorted(accepted,key=lambda S:sum(2**c for c in S))}

def table_execute(machine, sequence):
    """Independent table interpreter: no production imports or bitmask helpers."""
    state = machine['initial']; states = [state]; outputs = []
    for row in sequence:
        index = sum(value * (2**j) for j,value in enumerate(row))
        edge = machine['transitions'][state][index]
        outputs.append(edge['output']); state = edge['next']; states.append(state)
    return {'outputs':outputs,'states':states}

def direct_item_table(item):
    n = len(item['observed'])*len(item['machine']['inputs'])
    ni = len(item['machine']['inputs']); result = [None]*(2**n)
    for bits in product((0,1),repeat=n):
        inputs = [[item['observed'][t][r] ^ bits[t*ni+r] for r in range(ni)]
                  for t in range(item['target_step']+1)]
        result[sum(b*2**j for j,b in enumerate(bits))] = table_execute(item['machine'],inputs)['outputs'][item['target_step']]
    return result


def replay_visible_links(item, inputs):
    """Independent small interpreter for the public picture, not its compiler.

    Each displayed switch reads its labelled time/input cell and follows exactly
    one displayed edge. A lamp/drain is absorbing. This intentionally does not
    call boards.board_execute, a source recurrence, or the machine interpreter.
    """
    board=item['board'];width=len(item['machine']['inputs']);length=item['target_step']+1
    nodes={node['id']:node for node in board['nodes'] if node['kind']=='switch'}
    terminals={node['id']:node for node in board['nodes'] if node['kind'] in ('lamp','drain')}
    if len(nodes)+len(terminals)!=len(board['nodes']) or nodes.keys()&terminals.keys():
        raise ValueError('Displayed graph IDs must be unique')
    if len(inputs)!=length or any(len(row)!=width or any(type(value) is not int or value not in (0,1) for value in row) for row in inputs):
        raise ValueError('Invalid visual input word')
    current=board['start'];path=[current];outputs=[]
    for step in range(length):
        if current in nodes:
            node=nodes[current];cell=node['cell']
            if type(cell) is not int or cell//width!=step:
                raise ValueError('Displayed switch does not belong to its chronological round')
            current=node['one'] if inputs[step][cell%width] else node['zero']
            if current not in nodes and current not in terminals:
                raise ValueError('Displayed wire has an unknown destination')
            path.append(current)
        if current in terminals:
            if terminals[current]['kind'] not in ('lamp','drain'):
                raise ValueError('Unknown displayed terminal')
            outputs.append(int(terminals[current]['kind']=='lamp'))
        else:
            outputs.append(0)
    if current not in terminals:
        raise ValueError('Displayed signal did not terminate by the target round')
    return {'outputs':outputs,'path':path}

