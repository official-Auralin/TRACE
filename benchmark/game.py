"""Backward finite Bad(F) games and locally checkable certificates.

Bad(F)[t][q] means that some continuation from q at round t, keeping every
cell in F at its recorded value, makes the positive target output false.
The G branch is universally safe iff not Bad(C); the P branch is reachable
iff Bad(D\\C). This finite fixed-controller game is not infinite parity N2.
"""
from .core import (cell_count, cells, digest, parse_cells, public_item,
                   simulate, validate_item)

CERTIFICATE_VERSION = 'trace.gp-certificate.v2'


def _fixed(item, selected):
    return parse_cells({'cells':list(selected)}, cell_count(item))


def allowed_values(item, fixed, step):
    ni = len(item['machine']['inputs'])
    return [v for v in range(1 << ni)
            if all(((v >> r) & 1) == item['observed'][step][r]
                   for r in range(ni) if step*ni+r in fixed)]


def bad_query(item, fixed):
    """Return all backward recurrence layers, not a sampled path search."""
    fixed = set(_fixed(item, fixed))
    machine = item['machine']; k = item['target_step']
    layers = [[False]*machine['states'] for _ in range(k+1)]
    for t in range(k, -1, -1):
        permitted = allowed_values(item, fixed, t)
        for q, row in enumerate(machine['transitions']):
            layers[t][q] = any(row[v]['output'] == 0 if t == k
                               else layers[t+1][row[v]['next']]
                               for v in permitted)
    return layers


def bad_root(item, fixed):
    """The same exact recurrence with two rows of working storage.

    Full tables are needed only for optional witnesses/certificates. Candidate
    grading and one-answer search never retain O(h*states) tables per query.
    """
    fixed = set(_fixed(item, fixed))
    machine = item['machine']; k = item['target_step']
    following = None
    for t in range(k, -1, -1):
        permitted = allowed_values(item, fixed, t)
        following = [any(row[v]['output'] == 0 if t == k else following[row[v]['next']]
                         for v in permitted) for row in machine['transitions']]
    return following[machine['initial']]


class Game:
    """Cache only decision bits within one immutable instance, not full tables."""
    def __init__(self, item):
        validate_item(item)
        self.item = item
        self.n = cell_count(item)
        self.universe = (1 << self.n)-1
        self.initial = item['machine']['initial']
        self.cache = {}

    def bad(self, fixed_mask):
        if fixed_mask not in self.cache:
            self.cache[fixed_mask] = bad_root(self.item, cells(fixed_mask,self.n))
        return self.cache[fixed_mask]

    def valid(self, selected_mask):
        return not self.bad(selected_mask) and self.bad(self.universe ^ selected_mask)

    def diagnostics(self, selected_mask):
        guarantee = not self.bad(selected_mask)
        prevention = self.bad(self.universe ^ selected_mask)
        minimal = guarantee and prevention and all(
            not self.valid(selected_mask ^ (1 << c))
            for c in range(self.n) if selected_mask & (1 << c))
        return {'correct':bool(minimal), 'guarantee':guarantee,
                'prevention':prevention, 'minimality':bool(minimal)}


def diagnostics(item, selected):
    selected = _fixed(item, selected)
    return Game(item).diagnostics(sum(1 << c for c in selected))


def solve(item):
    """One inclusion-minimal witness, using at most n+1 validity queries.
    The initial existence test plus one pass suffices by upward closure of G/P.
    No minimum-cardinality or all-answer enumeration claim is made.
    """
    game = Game(item); candidate = game.universe
    if not game.valid(candidate):
        return None
    for c in range(game.n):
        smaller = candidate & ~(1 << c)
        if game.valid(smaller):
            candidate = smaller
    return cells(candidate, game.n)


def minimal_answers(item):
    """Optional exponential all-answer audit; never needed for live grading."""
    game = Game(item)
    valid = [game.valid(s) for s in range(1 << game.n)]
    return [cells(s,game.n) for s in range(1 << game.n)
            if valid[s] and all(not valid[s ^ (1 << c)]
                                for c in range(game.n) if s & (1 << c))]


def _failure_path(item, fixed, layers):
    q = item['machine']['initial']
    if not layers[0][q]:
        return None
    path = []; k = item['target_step']; ni = len(item['machine']['inputs'])
    for t in range(k+1):
        for v in allowed_values(item,set(fixed),t):
            edge = item['machine']['transitions'][q][v]
            if (edge['output'] == 0 if t == k else layers[t+1][edge['next']]):
                path.append([(v >> r) & 1 for r in range(ni)])
                q = edge['next']; break
        else:
            raise ValueError('inconsistent bad table')
    return path


def _required_masks(n, candidate):
    universe = (1 << n)-1
    # Full-free query additionally certifies existence / no-explanation verdicts.
    masks = {0}
    if candidate is not None:
        masks.update((candidate, universe ^ candidate))
        for c in range(n):
            if candidate & (1 << c):
                child = candidate ^ (1 << c)
                masks.update((child, universe ^ child))
    return sorted(masks)


def make_certificate(item, selected=None):
    """Bind actual execution and G/P/deletion proofs to the canonical public input.
    selected=None means construct the deterministic solver's answer or no-answer.
    """
    actual = validate_item(item)
    if selected is None:
        selected = solve(item)
    n = cell_count(item)
    mask = None if selected is None else sum(1 << c for c in _fixed(item,selected))
    proofs = []
    for fixed_mask in _required_masks(n,mask):
        fixed = cells(fixed_mask,n); table = bad_query(item,fixed)
        proofs.append({'fixed_cells':fixed,'bad_layers':table,
                       'failure_inputs':_failure_path(item,fixed,table)})
    return {'schema_version':CERTIFICATE_VERSION,
            'instance_sha256':digest(public_item(item)),
            'answer':{'verdict':'no_explanation'} if selected is None else {'cells':sorted(selected)},
            'actual_execution':actual,'queries':proofs}


def verify_certificate(item, certificate):
    """Check shape, binding, each local recurrence and paths without calling solve.
    All states/layers are checked, including unreachable states, so missing or
    falsely safe successor rows cannot justify an answer. Raises ValueError.
    """
    actual = validate_item(item)
    if not isinstance(certificate,dict) or set(certificate) != {
            'schema_version','instance_sha256','answer','actual_execution','queries'}:
        raise ValueError('invalid certificate shape')
    if certificate['schema_version'] != CERTIFICATE_VERSION or certificate['instance_sha256'] != digest(public_item(item)):
        raise ValueError('certificate instance/version mismatch')
    if certificate['actual_execution'] != actual:
        raise ValueError('certificate actual execution mismatch')
    answer = certificate['answer']; n = cell_count(item); universe = (1 << n)-1
    mask = None if answer == {'verdict':'no_explanation'} else sum(1 << c for c in parse_cells(answer,n))
    proofs = certificate['queries']
    if not isinstance(proofs,list):
        raise ValueError('certificate queries must be a list')
    by_mask = {}; k = item['target_step']; machine = item['machine']; ni = len(machine['inputs'])
    for proof in proofs:
        if not isinstance(proof,dict) or set(proof) != {'fixed_cells','bad_layers','failure_inputs'}:
            raise ValueError('invalid local proof shape')
        fixed = _fixed(item,proof['fixed_cells']); fixed_mask = sum(1 << c for c in fixed)
        if fixed_mask in by_mask:
            raise ValueError('duplicate subgame proof')
        table = proof['bad_layers']
        if not isinstance(table,list) or len(table) != k+1 or any(
                not isinstance(row,list) or len(row) != machine['states'] or any(type(v) is not bool for v in row)
                for row in table):
            raise ValueError('invalid backward table shape/types')
        # Verify the declared recurrence locally rather than recomputing a solver answer.
        for t,row in enumerate(table):
            for q,value in enumerate(row):
                expected = False
                for valuation in range(1 << ni):
                    if any(((valuation >> r) & 1) != item['observed'][t][r]
                           for r in range(ni) if t*ni+r in fixed):
                        continue
                    edge = machine['transitions'][q][valuation]
                    expected |= edge['output'] == 0 if t == k else table[t+1][edge['next']]
                if value != expected:
                    raise ValueError('invalid local backward recurrence')
        bad = table[0][machine['initial']]; path = proof['failure_inputs']
        if bad:
            if not isinstance(path,list) or len(path) != k+1:
                raise ValueError('missing prevention/counterexample path')
            replay = simulate(machine,path)
            if replay['outputs'][k] != 0 or any(path[c//ni][c%ni] != item['observed'][c//ni][c%ni] for c in fixed):
                raise ValueError('illegal or non-failing witness path')
        elif path is not None:
            raise ValueError('safe subgame must not claim a failure path')
        by_mask[fixed_mask] = bad
    if sorted(by_mask) != _required_masks(n,mask):
        raise ValueError('missing or surplus subgame proof')
    if mask is None:
        if by_mask[0]:
            raise ValueError('false no-explanation verdict')
    else:
        valid = lambda s:not by_mask[s] and by_mask[universe ^ s]
        if not valid(mask) or any(valid(mask ^ (1 << c)) for c in range(n) if mask & (1 << c)):
            raise ValueError('certificate answer is not inclusion-minimal G and P')
    return True

def build_verification_game(item, selected):
    """Explicit two-branch finite parity verification game for a candidate.

    Player 1 chooses the root branch. In G, player 1 chooses completions with C
    fixed and player 0 wins iff the target is 1. In P, player 0 chooses a
    completion with the complement fixed and wins iff the target is 0. Every
    play reaches an absorbing 0/1 sink after finitely many rounds. The min-even
    convention gives player 0 a win exactly when G(C) and P(C) hold. This is a
    finite verification game, not reopened controller choices or N2 liveness.
    """
    validate_item(item);selected=set(_fixed(item,selected));n=cell_count(item)
    machine=item['machine'];ni=len(machine['inputs']);k=item['target_step']
    nodes={
        'win':{'owner':0,'priority':0,'edges':[{'to':'win'}]},
        'lose':{'owner':0,'priority':1,'edges':[{'to':'lose'}]},
        'root':{'owner':1,'priority':2,'edges':[
            {'to':f'G:0:{machine["initial"]}'}, {'to':f'P:0:{machine["initial"]}'}]}}
    for branch,owner,fixed in [('G',1,selected),('P',0,set(range(n))-selected)]:
        for t in range(k+1):
            for q in range(machine['states']):
                edges=[]
                for v in allowed_values(item,fixed,t):
                    edge=machine['transitions'][q][v]
                    if t==k:
                        success=edge['output']==(1 if branch=='G' else 0)
                        target='win' if success else 'lose'
                    else:target=f'{branch}:{t+1}:{edge["next"]}'
                    edges.append({'to':target,'input':[(v>>r)&1 for r in range(ni)],'output':edge['output']})
                nodes[f'{branch}:{t}:{q}']={'owner':owner,'priority':2,'edges':edges}
    return {'schema_version':'trace.finite-verification-game.v2',
            'instance_sha256':digest(public_item(item)),'selected_cells':sorted(selected),
            'initial':'root','parity_convention':'least priority occurring infinitely often is even',
            'players':{'0':'explainer','1':'adversary'},'nodes':nodes}


def verification_game_winner(game):
    """Solve an explicit finite-prefix/sink game; reject all other cycles.
    Returns True iff player 0 wins. This is not a general parity-game solver.
    """
    nodes=game['nodes']
    if nodes.get('win')!={'owner':0,'priority':0,'edges':[{'to':'win'}]} or nodes.get('lose')!={'owner':0,'priority':1,'edges':[{'to':'lose'}]}:
        raise ValueError('invalid absorbing parity sinks')
    if game.get('parity_convention')!='least priority occurring infinitely often is even':
        raise ValueError('unsupported parity convention')
    memo={'win':True,'lose':False};visiting=set()
    def visit(name):
        if name in memo:return memo[name]
        if name in visiting:raise ValueError('nonterminal cycle: outside finite verification-game scope')
        if name not in nodes:raise ValueError('missing game vertex')
        node=nodes[name]
        if type(node.get('owner')) is not int or node['owner'] not in (0,1) or node.get('priority')!=2 or not node.get('edges'):
            raise ValueError('invalid nonterminal vertex')
        visiting.add(name)
        successors=[visit(edge['to']) for edge in node['edges']]
        visiting.remove(name)
        memo[name]=any(successors) if node['owner']==0 else all(successors)
        return memo[name]
    for name in nodes:
        visit(name)
    return visit(game['initial'])
