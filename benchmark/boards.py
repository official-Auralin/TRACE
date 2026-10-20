"""Visible, finite switch-and-light networks and their Mealy compilation.

A pulse starts at one junction. At each time column the current junction reads
one switch and sends the pulse along its 0/1 wire. Lamp/drain destinations latch.
All alternatives remain visible, including junctions outside the recorded route.
"""
from copy import deepcopy

BOARD_VERSION='trace.board.v1'
SOURCE_VERSION='trace.switch-network.v1'

def compile_machine(recipe):
    h=recipe['horizon']
    rows=[]
    for t in range(h):
        for lane in range(4):
            edges=[]
            for valuation in range(4):
                if lane>=2: destination=lane
                else:
                    channel=recipe.get('channels',[[0,1]]*h)[t][lane]
                    destination=recipe['edges'][t][lane][(valuation>>channel)&1]
                nt=min(t+1,h-1)
                edges.append({'next':4*nt+destination,'output':int(destination==2)})
            rows.append(edges)
    return {'inputs':['upper','lower'],'states':4*h,'initial':recipe['initial_lane'], 'transitions':rows}

def make_board(recipe,observed):
    h=recipe['horizon'];lamp=2*h;drain=lamp+1
    reachable={(0,recipe['initial_lane'])};nodes=[]
    for t in range(h):
        for lane in range(2):
            if (t,lane) not in reachable:continue
            channel=recipe.get('channels',[[0,1]]*h)[t][lane]
            dest=[]
            for route in recipe['edges'][t][lane]:
                if route<2:
                    if t==h-1:raise ValueError('last column must terminate')
                    reachable.add((t+1,route));dest.append(2*(t+1)+route)
                else:dest.append(lamp if route==2 else drain)
            nodes.append({'id':2*t+lane,'kind':'switch','cell':2*t+channel,'zero':dest[0],'one':dest[1],'x':t,'y':2*lane})
    nodes.extend([{'id':lamp,'kind':'lamp','x':h,'y':0},{'id':drain,'kind':'drain','x':h,'y':2}])
    visible=sorted({n['cell'] for n in nodes if n['kind']=='switch'})
    board={'version':BOARD_VERSION,'nodes':nodes,'start':recipe['initial_lane'],'width':h+1,'height':3,
           'columns':[{'step':t,'label':str(t+1)} for t in range(h)],
           'switches':[{'cell':c,'label':chr(65+j),'step':c//2,'channel':c%2,'value':observed[c//2][c%2]} for j,c in enumerate(visible)]}
    board['recorded_path']=trace_board(board,observed)['path']
    return board

def trace_board(board,inputs):
    if board.get('version') == 'trace.board.v2':
        from .level import execute
        return execute(board,inputs)
    nodes={n['id']:n for n in board['nodes']};current=board['start'];path=[current];outputs=[]
    for t,row in enumerate(inputs):
        node=nodes[current]
        if node['kind']=='switch':
            if node['cell']//2!=t:raise ValueError('route/time disagreement')
            current=node['one' if row[node['cell']%2] else 'zero'];path.append(current)
            node=nodes[current]
        outputs.append(int(node['kind']=='lamp'))
    if nodes[current]['kind']=='switch':raise ValueError('unfinished route')
    return {'path':path,'outputs':outputs,'target':outputs[-1]}

board_execute=trace_board

def public_board(board):
    """Copy only participant-safe graph fields, never arbitrary source metadata."""
    if board.get('version') == 'trace.board.v2':
        from .level import public_board as project_general
        return project_general(board)
    def project(obj,fields):return {name:deepcopy(obj[name]) for name in fields}
    return {'version':board['version'],'start':board['start'],'width':board['width'],'height':board['height'],
            'nodes':[project(n,('id','kind','cell','zero','one','x','y') if n['kind']=='switch' else ('id','kind','x','y')) for n in board['nodes']],
            'columns':[project(c,('step','label')) for c in board['columns']],
            'switches':[project(s,('cell','label','step','channel','value')) for s in board['switches']],
            'recorded_path':list(board['recorded_path'])}

def demo_items():
    from .core import SEMANTICS,compute_key,simulate
    examples=[
      ('direct',[[[3,2],[3,2]]],[[1,0]],None),
      ('and',[[[3,0],[3,2]],[[3,2],[3,2]]],[[1,0],[1,0]],None),
      ('or',[[[0,2],[3,2]],[[3,2],[3,2]]],[[1,0],[1,0]],None),
      ('xor',[[[0,1],[3,2]],[[3,2],[2,3]]],[[1,0],[0,0]],[[0,1],[0,0]]),
      ('choice',[[[0,1],[3,2]],[[3,2],[3,2]]],[[1,0],[1,1]],None),
    ]
    result=[]
    for name,edges,observed,channels in examples:
        recipe={'version':SOURCE_VERSION,'family':name,'horizon':len(edges),'initial_lane':0,'edges':edges}
        if channels:recipe['channels']=channels
        machine=compile_machine(recipe);execution=simulate(machine,observed)
        item={'id':'demo-'+name,'machine':machine,'observed':observed,'observed_outputs':execution['outputs'],
              'observed_states':execution['states'],'target_step':len(edges)-1,'semantics':dict(SEMANTICS),'board':make_board(recipe,observed)}
        item['key']=compute_key(item);result.append(item)
    return result


def validate_board(board,observed,machine=None):
    """Validate visible graph shape and recording, not its Mealy correspondence.

    Full compiler correspondence is checked independently for every release word.
    This parser check prevents malformed display metadata from reaching a player.
    """
    if board.get('version') == 'trace.board.v2':
        from .level import validate_board as validate_general
        return validate_general(board,observed,machine)
    if not observed or any(not isinstance(row,list) or len(row)!=2 for row in observed):
        raise ValueError('switch boards require exactly two input channels')
    h=len(observed)
    if board.get('version')!=BOARD_VERSION or board.get('width')!=h+1 or board.get('height')!=3:
        raise ValueError('unsupported board dimensions/version')
    nodes=board.get('nodes');metadata=board.get('switches');columns=board.get('columns')
    if not isinstance(nodes,list) or not isinstance(metadata,list) or not isinstance(columns,list) or len(columns)!=h:
        raise ValueError('board arrays missing')
    if columns!=[{'step':t,'label':str(t+1)} for t in range(h)]:raise ValueError('board columns disagree with time')
    byid={};cells=set();terminals={}
    for node in nodes:
        if type(node.get('id')) is not int or node['id'] in byid:raise ValueError('duplicate/invalid board ID')
        byid[node['id']]=node
        if node.get('kind')=='switch':
            c=node.get('cell')
            if type(c) is not int or not 0<=c<2*h:raise ValueError('invalid switch cell')
            if node.get('x')!=c//2 or node.get('y') not in (0,2):raise ValueError('invalid switch position')
            cells.add(c)
        elif node.get('kind') in ('lamp','drain'):
            if node['kind'] in terminals or node.get('x')!=h or node.get('y')!=(0 if node['kind']=='lamp' else 2):
                raise ValueError('invalid terminal position')
            terminals[node['kind']]=node['id']
        else:raise ValueError('unknown board node kind')
    if set(terminals)!={'lamp','drain'}:raise ValueError('missing board terminals')
    if type(board.get('start')) is not int or board['start'] not in byid or byid[board['start']]['kind']!='switch' or byid[board['start']]['x']!=0:
        raise ValueError('invalid board start')
    for node in nodes:
        if node['kind']!='switch':continue
        for branch in ('zero','one'):
            target=node.get(branch)
            if type(target) is not int or target not in byid:raise ValueError('dangling route')
            nxt=byid[target]
            if nxt['kind']=='switch' and nxt['x']!=node['x']+1:raise ValueError('route must advance one time column')
    seen=set();pending=[board['start']]
    while pending:
        ident=pending.pop()
        if ident in seen:continue
        seen.add(ident);node=byid[ident]
        if node['kind']=='switch':pending.extend([node['zero'],node['one']])
    if any(n['kind']=='switch' and n['id'] not in seen for n in nodes):raise ValueError('unreachable displayed switch')
    expected=[{'cell':c,'label':chr(65+j),'step':c//2,'channel':c%2,'value':observed[c//2][c%2]} for j,c in enumerate(sorted(cells))]
    if metadata!=expected:raise ValueError('switch labels/values disagree with recording')
    if board.get('recorded_path')!=trace_board(board,observed)['path']:raise ValueError('incorrect recorded route')
    return True
