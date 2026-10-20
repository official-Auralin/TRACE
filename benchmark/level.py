"""Public switch/light interpretation and validation of Lean-constructed levels.

The constructor lives in formal/Trace2/Compiler.lean. This independent adapter
checks every switch and leaf, including counterfactual paths, against the input
machine. It does not construct a substitute machine or select a new trace.
"""
from copy import deepcopy

VERSION = 'trace.board.v2'
DISPLAY_VERSION = 'trace.display.v1'
CORE_FIELDS = ('version','initial','states','inputs','horizon','layers')


def project_terminal(node):
    """Independent reference for the proved terminal-output projection.

    The state after the target has no influence on the scored event. Earlier
    semantic layers retain that state, even when their current outputs agree.
    """
    if node['kind'] == 'output':
        return {'kind':'outcome','value':node['value']}
    zero = project_terminal(node['zero']); one = project_terminal(node['one'])
    return zero if zero == one else {'kind':'switch','cell':node['cell'],
                                    'zero':zero,'one':one}


def terminal_display(board):
    return {'version':DISPLAY_VERSION,
            'terminal':[project_terminal(root) for root in board['layers'][-1]]}


def switches(observed, names):
    m = len(names)
    return [{'cell':t*m+r,'label':f'{names[r]} · {t+1}', 'step':t,
             'channel':r,'value':value}
            for t,row in enumerate(observed) for r,value in enumerate(row)]


def decorate(board, observed, names):
    board = deepcopy(board)
    # Directly constructed test fixtures may use this independent reference.
    # Production compile_item requires the Lean-emitted display before decorating.
    if 'display' not in board:board['display'] = terminal_display(board)
    board['switches'] = switches(observed,names)
    board['recorded_path'] = execute(board,observed)['path']
    return board


def execute(board, inputs):
    m = board['inputs']; h = board['horizon']
    if len(inputs) != h or any(not isinstance(row,list) or len(row)!=m or
            any(type(v) is not int or v not in (0,1) for v in row) for row in inputs):
        raise ValueError('level input word has incorrect dimensions or values')
    q = board['initial']; states = [q]; outputs = []; path = []
    for t,row in enumerate(inputs):
        node = board['layers'][t][q]; prefix = ''
        while node['kind'] == 'switch':
            path.append(f'{t}:{q}:{prefix}')
            r = node['cell']-t*m
            if not 0 <= r < m:raise ValueError('switch does not belong to its round')
            bit = row[r]; prefix += str(bit)
            node = node['one' if bit else 'zero']
        if node['kind'] != 'output':raise ValueError('round does not end in an output')
        path.append(f'{t}:{q}:{prefix}')
        outputs.append(node['value']);q = node['next'];states.append(q)
    return {'path':path,'outputs':outputs,'states':states,'target':outputs[-1]}


def validate_board(board, observed, machine=None):
    if not isinstance(board,dict) or board.get('version') != VERSION:
        raise ValueError('unsupported general level version')
    m=board.get('inputs');ns=board.get('states');h=board.get('horizon')
    if any(type(v) is not int or v<1 for v in (m,ns,h)):
        raise ValueError('positive finite board dimensions required')
    if type(board.get('initial')) is not int or not 0<=board['initial']<ns:
        raise ValueError('invalid board initial state')
    if len(observed)!=h or any(len(row)!=m for row in observed):
        raise ValueError('board/trace dimension mismatch')
    layers=board.get('layers')
    if not isinstance(layers,list) or len(layers)!=h:
        raise ValueError('missing time layers')
    if machine is not None and (m!=len(machine['inputs']) or ns!=machine['states'] or board['initial']!=machine['initial']):
        raise ValueError('board/machine dimension or initial-state mismatch')
    for t,layer in enumerate(layers):
        if not isinstance(layer,list) or len(layer)!=ns:raise ValueError('missing state roots')
        for q,root in enumerate(layer):
            pending=[(root,-1)]
            while pending:
                node,previous=pending.pop()
                if not isinstance(node,dict):raise ValueError('invalid decision node')
                if node.get('kind')=='switch':
                    if set(node)!={'kind','cell','zero','one'} or type(node['cell']) is not int or not t*m+previous<node['cell']<(t+1)*m:
                        raise ValueError('switch cell/decision order mismatch')
                    r=node['cell']-t*m
                    pending.extend(((node['zero'],r),(node['one'],r)))
                else:
                    if set(node)!={'kind','value','next'} or node['kind']!='output' or type(node['value']) is not int or node['value'] not in (0,1) or type(node['next']) is not int or not 0<=node['next']<ns:
                        raise ValueError('invalid output leaf')
            if machine is not None:
                # Reduced trees omit irrelevant tests. Check every valuation of
                # one transition, not every word through the entire horizon.
                for valuation,edge in enumerate(machine['transitions'][q]):
                    node=root
                    while node['kind']=='switch':
                        node=node['one' if (valuation>>(node['cell']-t*m))&1 else 'zero']
                    if (node['value'],node['next'])!=(edge['output'],edge['next']):
                        raise ValueError('compiled counterfactual transition disagrees with machine')
    display=board.get('display')
    if not isinstance(display,dict) or set(display)!={'version','terminal'} or display.get('version')!=DISPLAY_VERSION:
        raise ValueError('missing or unsupported terminal display')
    terminal=display['terminal']
    if not isinstance(terminal,list) or len(terminal)!=ns:
        raise ValueError('missing terminal display state roots')
    t=h-1
    for q,root in enumerate(terminal):
        pending=[(root,-1)]
        while pending:
            node,previous=pending.pop()
            if not isinstance(node,dict):raise ValueError('invalid terminal display node')
            if node.get('kind')=='switch':
                if set(node)!={'kind','cell','zero','one'} or type(node['cell']) is not int or not t*m+previous<node['cell']<(t+1)*m:
                    raise ValueError('terminal display cell/decision order mismatch')
                r=node['cell']-t*m
                pending.extend(((node['zero'],r),(node['one'],r)))
            elif set(node)!={'kind','value'} or node.get('kind')!='outcome' or type(node.get('value')) is not int or node['value'] not in (0,1):
                raise ValueError('invalid terminal display outcome')
        if root!=project_terminal(layers[-1][q]):
            raise ValueError('terminal display is not the canonical target projection')
        if machine is not None:
            for valuation,edge in enumerate(machine['transitions'][q]):
                node=root
                while node['kind']=='switch':
                    node=node['one' if (valuation>>(node['cell']-t*m))&1 else 'zero']
                if node['value']!=edge['output']:
                    raise ValueError('terminal display outcome disagrees with machine target')
    metadata=board.get('switches')
    if not isinstance(metadata,list) or len(metadata)!=h*m:
        raise ValueError('all original input cells require a selectable control')
    for c,s in enumerate(metadata):
        if not isinstance(s,dict) or any(type(s.get(k)) is not int for k in ('cell','step','channel','value')) or s.get('cell')!=c or s.get('step')!=c//m or s.get('channel')!=c%m or s.get('value')!=observed[c//m][c%m] or not isinstance(s.get('label'),str):
            raise ValueError('switch metadata disagrees with original input cell')
    if len({s['label'] for s in metadata})!=h*m:
        raise ValueError('distinct input cells require unambiguous labels')
    if machine is not None:
        expected=switches(observed,machine['inputs'])
        if any(s['label']!=e['label'] for s,e in zip(metadata,expected)):
            raise ValueError('switch label disagrees with original input identity')
    if board.get('recorded_path')!=execute(board,observed)['path']:
        raise ValueError('recorded path disagrees with level execution')
    return True


def public_board(board):
    # The semantic tree schema is strict; no arbitrary metadata passes through.
    def tree(node):
        if node['kind']=='switch':
            return {'kind':'switch','cell':node['cell'],'zero':tree(node['zero']),'one':tree(node['one'])}
        return {'kind':'output','value':node['value'],'next':node['next']}
    result={k:deepcopy(board[k]) for k in CORE_FIELDS if k!='layers'}
    result['layers']=[[tree(root) for root in layer] for layer in board['layers']]
    def outcome_tree(node):
        if node['kind']=='switch':
            return {'kind':'switch','cell':node['cell'],'zero':outcome_tree(node['zero']),
                    'one':outcome_tree(node['one'])}
        return {'kind':'outcome','value':node['value']}
    result['display']={'version':board['display']['version'],
                       'terminal':[outcome_tree(root) for root in board['display']['terminal']]}
    result['switches']=[{k:s[k] for k in ('cell','label','step','channel','value')} for s in board['switches']]
    result['recorded_path']=list(board['recorded_path'])
    return result
