// Independent execution of the shipped browser interpreter. Small instances are
// exhaustive; larger inputs use stated deterministic probes, not an exhaustion claim.
import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const source=fs.readFileSync(new URL('../web/board.js',import.meta.url),'utf8');
const sandbox={window:{}};vm.runInNewContext(source,sandbox);
const items=JSON.parse(fs.readFileSync(0,'utf8'));
let exhaustiveWords=0,sampledWords=0;
for(const item of items){
  const board=item.board,m=board.inputs,h=board.horizon,n=m*h;
  assert.equal(board.version,'trace.board.v2');
  const exhaustive=n<=12;
  const wordAt=number=>Array.from({length:h},(_,t)=>Array.from({length:m},(_,r)=>Math.floor(number/2**(t*m+r))%2));
  const words=exhaustive?Array.from({length:2**n},(_,i)=>wordAt(i)):
    [item.observed,Array.from({length:h},()=>Array(m).fill(0)),Array.from({length:h},()=>Array(m).fill(1)),Array.from({length:h},(_,t)=>Array.from({length:m},(_,r)=>(t+r)%2))];
  for(const word of words){
    let q=item.machine.initial;const states=[q],outputs=[];
    for(const row of word.slice(0,h)){const valuation=row.reduce((sum,bit,r)=>sum+bit*2**r,0),edge=item.machine.transitions[q][valuation];outputs.push(edge.output);q=edge.next;states.push(q);}
    const result=JSON.parse(JSON.stringify(sandbox.window.TRACEBoard.execute(board,word)));
    assert.deepEqual(result.outputs,outputs,item.id+' output correspondence');
    assert.deepEqual(result.states,states,item.id+' state correspondence');
    const display=JSON.parse(JSON.stringify(sandbox.window.TRACEBoard.displayExecute(board,word)));
    assert.deepEqual(display.outputs,outputs,item.id+' projected display outputs');
    assert.equal(display.outcome,outputs.at(-1),item.id+' projected target');
    assert.equal(display.path.at(-1),outputs.at(-1)?'target-lamp':'dark-exit',item.id+' shared destination');
    assert.deepEqual(display.path.filter(id=>!id.startsWith((h-1)+':')).slice(0,-1),result.path.filter(id=>!id.startsWith((h-1)+':')),item.id+' earlier paths are unchanged');
    assert(result.path.length>=h&&result.path.length<=h*(m+1));
    if(exhaustive)exhaustiveWords++;else sampledWords++;
  }
  assert.deepEqual(JSON.parse(JSON.stringify(sandbox.window.TRACEBoard.walk(board,item.observed))),board.recorded_path);
}
console.log(JSON.stringify({status:'PASS',items:items.length,exhaustive_words:exhaustiveWords,sampled_words:sampledWords,scope:'Browser semantic and terminal-display interpreters versus independent Mealy execution; no claim about rendering or human comprehension.'}));
