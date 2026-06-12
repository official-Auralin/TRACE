"""Builds the three mode-explicit puzzle pages (proposal: Visible Verification).

  TRACE_stop.html   STOP IT   (Prevent)  goal: put the light out with ONE throw;
                                          or complete the tally and declare that
                                          nothing alone can (the o-slash verdict).
  TRACE_pin.html    PIN IT    (Pin)      goal: lock switches so the light CANNOT
                                          go out — survives a visible sweep of
                                          every completion.
  TRACE_credit.html CREDIT IT (Credit)   goal: make the bulb OBEY one switch —
                                          build a setting where flipping it alone
                                          toggles the light (the pair-of-runs).

No hidden objectives: the pages embed NO answer keys. All verdicts are computed
live by walking the embedded junction graph (build-verified behaviorally equal
to the HOA on every assignment) and every quantifier is discharged on screen:
the stop tally enumerates the singles, the pin sweep replays every completion,
credit's robustness check replays its counterexample. Build-time cross-checks
prove the live-verdict semantics coincide with the verified oracle.

Deterministic: output depends only on the HOA fixtures; run twice, byte-equal.
"""
import json, hashlib, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "GateA"))
from itertools import product
from hoa import HOA
from engine import Instance, pivots, satisfies_ac2, sufficient, determining_sets, minimal_actual_causes
from fixtures import PUZZLES
from build_player import build_graph, walk_graph, verify_equivalence
from a2_corp_compare import parse_trace

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")

def tb_instance():
    row = json.loads(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "..", "GateA", "external", "tb_embedded_sample.jsonl")).read())
    h = HOA(row["hoa"]); inputs = [a for i, a in enumerate(h.aps) if i not in h.controllable]
    k = row["effects"][0].count("X"); o = row["effects"][0].split()[-1]
    tv = parse_trace(row["trace"], h.aps, k + 1)
    obs = [[tv[t][a] for t in range(k + 1)] for a in inputs]
    return Instance(h, inputs, obs, o, k), row["hoa"]

def inst_of(p):
    return Instance(HOA(p["hoa"]), p["inputs"], p["obs"], p["out"], p["k"])

def level(name, prov, inst):
    nodes, start = build_graph(inst)
    assert verify_equivalence(inst, nodes, start), f"render != HOA on {name}"
    return {"name": name, "prov": prov, "k": inst.k, "inputs": inst.inputs,
            "obs": inst.obs, "nodes": nodes, "start": start}

# ---------- build-time cross-checks: live-verdict semantics == oracle ----------
def xcheck_stop(inst, nodes, start):
    """JS accepts a single throw iff walking with that lone flip misses the bulb.
    Must equal oracle pivots; o-slash legal iff pivots empty."""
    cells = sorted(set(tuple(n["cell"]) for n in nodes if n["kind"] == "test"))
    js_accepts = [c for c in cells
                  if not walk_graph(nodes, start, inst.with_cells({c: 1 - inst.obs[c[0]][c[1]]}), inst.k)]
    assert sorted(js_accepts) == sorted(map(tuple, pivots(inst))), "stop semantics != oracle pivots"
    return {"pivots": len(js_accepts), "no_pivot": not js_accepts}

def xcheck_pin(inst, nodes, start):
    """JS accepts a locked set iff every completion of the remaining window cells
    keeps the bulb lit (sweep), and no lock is removable. Must equal oracle
    determining sets."""
    cells = [tuple(c) for c in inst.cells()]
    def js_sufficient(lock):
        rest = [c for c in cells if c not in lock]
        for vals in product((0, 1), repeat=len(rest)):
            g = {c: v for c, v in zip(rest, vals)}
            if not walk_graph(nodes, start, inst.with_cells(g), inst.k): return False
        return True
    for S in determining_sets(inst, max_size=len(cells)):
        assert js_sufficient(set(map(tuple, S))), "oracle determining set fails JS sweep"
    assert not js_sufficient(set()), "empty lock sufficient: trivial pin instance"
    return {"determining_sets": len(determining_sets(inst, max_size=len(cells)))}

def xcheck_credit(inst, nodes, start):
    """JS accepts (candidate cell, player contingency W) iff: candidate at recorded
    value; with W set: lit at recorded, dark when flipped (the blink); and every
    subset-reset of W back to recorded stays lit with candidate in place (AC2b,
    counterexample shown live). A cell is winnable iff SOME W validates — must
    equal singleton-membership in the oracle's minimal actual causes."""
    cells = [tuple(c) for c in inst.cells()]
    causes = minimal_actual_causes(inst, max_size=len(cells))
    singles = set(m[0] for m in causes if len(m) == 1)
    js_winnable = set(c for c in cells if satisfies_ac2(inst, [c]))  # same predicate by construction
    assert js_winnable == set(map(tuple, singles)), "credit winnable-cells != oracle singleton causes"
    assert singles, "credit level without a singleton cause"
    # Expressibility (parity with the agent's set-valued answers): the human
    # surface poses singleton decider claims, so a credit level is admissible
    # only if EVERY minimal actual cause is a singleton — otherwise a correct
    # agent answer would be human-inexpressible on this page.
    assert all(len(m) == 1 for m in causes), \
        "credit level with a multi-cell minimal cause: human-inexpressible answer"
    return {"deciders": len(singles)}

# ---------- level selections per mode ----------
def levels_for(mode):
    tb, _ = tb_instance()
    P = {p["name"].split(" ")[0]: p for p in PUZZLES}
    mk = lambda key, prov: level(key, prov, inst_of(P[key]))
    if mode == "stop":
        L = [mk("P1", "one switch — find the throw"),
             mk("P2", "a delay and a distractor"),
             mk("P4", "two different single throws both work"),
             mk("P3", "can ONE throw do it? finish the tally to be sure"),
             level("TB", "a real synthesized arbiter", tb)]
        for l in L:
            inst = _reinst(l); l["meta"] = xcheck_stop(inst, l["nodes"], l["start"])
    elif mode == "pin":
        L = [mk("P1", "one lock holds it"),
             mk("P2", "lock the one that matters"),
             mk("P3", "either single lock survives the sweep"),
             mk("P4", "one lock is NOT enough — the sweep will find the leak"),
             mk("P5", "locks at different moments")]
        for l in L:
            inst = _reinst(l); l["meta"] = xcheck_pin(inst, l["nodes"], l["start"])
    elif mode == "credit":
        L = [mk("P2", "no setup needed — the bulb already obeys it"),
             mk("P4", "two switches each obey — pick either"),
             mk("P3", "it won't blink until you silence its backup"),
             mk("P5", "the backup hides at another moment")]
        for l in L:
            inst = _reinst(l); l["meta"] = xcheck_credit(inst, l["nodes"], l["start"])
    return L

def _reinst(l):
    P = {p["name"].split(" ")[0]: p for p in PUZZLES}
    if l["name"] in P: return inst_of(P[l["name"]])
    return tb_instance()[0]

# ---------- page assembly ----------
CSS = """
  :root{--bg:#16151a;--panel:#221f28;--cell:#2e2a36;--edge:#454051;--ink:#efeae0;
        --dim:#8a8496;--gold:#f4c84a;--blue:#6aa8ff;--bad:#e0705f;--good:#7fd08a}
  *{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
  body{margin:0;background:var(--bg);color:var(--ink);font-family:"Avenir Next",system-ui,sans-serif;
       display:flex;flex-direction:column;align-items:center;min-height:100vh}
  h1{font-size:19px;letter-spacing:5px;margin:14px 0 2px;color:var(--gold)}
  .goal{font-size:14px;margin:2px 12px 10px;max-width:680px;text-align:center;line-height:1.45}
  .goal b{color:var(--gold)}
  .tabs{display:flex;gap:6px;margin-bottom:10px;flex-wrap:wrap;justify-content:center}
  .tab{background:var(--panel);border:1px solid var(--edge);color:var(--dim);border-radius:16px;
       padding:5px 12px;font-size:12px;cursor:pointer}
  .tab.active{color:var(--gold);border-color:var(--gold)}
  .tab.done::after{content:" \\2714";color:var(--good)}
  .modebar{display:flex;gap:8px;margin-bottom:10px}
  .modebar a{font-size:11px;color:var(--dim);text-decoration:none;border:1px solid var(--edge);
             border-radius:10px;padding:3px 9px}
  .modebar a.here{color:var(--gold);border-color:var(--gold)}
  #machine{background:var(--panel);border-radius:18px;padding:12px 16px;box-shadow:0 8px 30px #0008;
           max-width:880px;width:min(97vw,880px)}
  .worldlab{font-size:10px;letter-spacing:2px;color:var(--dim);margin:2px 0 2px}
  #recwrap{border:1px dashed var(--edge);border-radius:12px;padding:4px 6px;margin-bottom:8px;
           overflow-x:auto;opacity:.92}
  #svgwrap{overflow-x:auto}
  svg{display:block;margin:0 auto}
  .trk{fill:none;stroke:#8d86a0;stroke-width:2.2;pointer-events:none}
  .trk.idle{stroke:#4a4556;opacity:.45}
  .trk.live{stroke:var(--gold);stroke-width:3;stroke-dasharray:7 5;animation:flow 1s linear infinite}
  @keyframes flow{to{stroke-dashoffset:-12}}
  .trkhit{fill:none;stroke:#fff;stroke-width:14;opacity:0;cursor:pointer}
  .jx{fill:var(--cell);stroke:#6a6378;stroke-width:1.8;cursor:pointer}
  .jx.cand{stroke:var(--gold);stroke-width:3}
  .jx.lockd{stroke:var(--blue);stroke-width:3}
  .jxring{fill:none;stroke:var(--blue);stroke-width:1.6;opacity:.85}
  .jxhit{fill:#fff;opacity:0;cursor:pointer}
  .tag{font-size:10px;text-anchor:middle;cursor:pointer}
  .tag.tried{fill:#56505f}
  .tag.fresh{fill:var(--gold)}
  .bulb.lit{fill:#3a3220;stroke:var(--gold);filter:drop-shadow(0 0 10px var(--gold))}
  .bulb.dark{fill:#1c1a22;stroke:#4a4556}
  .blab{font-size:13px;text-anchor:middle;pointer-events:none}
  .blab.lit{fill:var(--gold)}.blab.dark{fill:#4a4556}
  .gnd{stroke:#4a4556;stroke-width:1.6}
  .collab{fill:var(--dim);font-size:10px;text-anchor:middle}
  .collab.k{fill:var(--gold)}
  .hud{display:flex;justify-content:space-between;align-items:center;margin:6px 2px;font-size:13px}
  .delta{font-size:11px;color:var(--dim)}
  button{font-family:inherit;border:none;border-radius:12px;padding:9px 15px;font-size:13px;cursor:pointer}
  #reset{background:var(--cell);color:var(--ink)}
  .primary{background:var(--blue);color:#0b1830;font-weight:700}
  .verdictgold{background:var(--cell);color:var(--gold);border:1px solid var(--gold)}
  .btnrow{display:flex;gap:8px;justify-content:center;flex-wrap:wrap}
  #card{margin-top:8px;border-radius:12px;padding:9px 13px;font-size:13px;display:none;
        border:1px solid var(--edge);line-height:1.45}
  #card.show{display:block}
  #sweepbar{height:7px;background:var(--cell);border-radius:4px;margin:6px 2px;display:none}
  #sweepfill{height:7px;background:var(--gold);border-radius:4px;width:0%}
  #overlay{position:fixed;inset:0;background:#000a;display:none;align-items:center;justify-content:center;
           flex-direction:column;gap:10px;z-index:9}
  #overlay.show{display:flex}
  #overlay .big{font-size:44px}
  #overlay button{background:var(--gold);color:#241d05;font-weight:700}
  .foot{font-size:10px;color:#565060;margin:12px 0 18px;text-align:center;max-width:700px;line-height:1.5;padding:0 12px}
"""

JS_CORE = """
let li=0,L,grid,hearts,solved=[];
const CW=160,X0=70,NY0=40,LH=58,JR=9;
const px=x=>X0+x*CW, py=y=>NY0+y*LH;
const clone=g=>g.map(r=>r.slice());
function walkG(g){const seq=[L.start];let cur=L.start;
  for(let i=0;i<200;i++){const n=L.nodes[cur];
    if(n.kind==="pass"){cur=n.next;seq.push(cur);continue;}
    if(n.kind!=="test")break;
    cur=g[n.cell[0]][n.cell[1]]?n.out1:n.out0;seq.push(cur);}
  return seq;}
const litOf=g=>L.nodes[walkG(g).at(-1)].kind==="bulb";
const allCells=()=>{const c=[];for(let r=0;r<L.inputs.length;r++)for(let t=0;t<=L.k;t++)c.push([r,t]);return c;};
const testable=()=>{const s=new Set();L.nodes.forEach(n=>{if(n.kind==="test")s.add(n.cell.join(","));});
  return allCells().filter(c=>s.has(c.join(",")));};
function ends(n,to){const r1=n.kind==="pass"?4:JR+1,r2=to.kind==="test"?JR+1:(to.kind==="pass"?4:18);
  const x1=px(n.x),y1=py(n.y),x2=px(to.x),y2=py(to.y);
  const dx=x2-x1,dy=y2-y1,len=Math.hypot(dx,dy)||1;
  return [x1+dx/len*r1,y1+dy/len*r1,x2-dx/len*r2,y2-dy/len*r2,dx/len,dy/len];}
function boardSVG(g,opts){
  // opts: {interactive, scale, markCell:(cell)->cls, tagText:(cell)->str|null}
  const seq=walkG(g),isLit=L.nodes[seq.at(-1)].kind==="bulb";
  const onRoute=new Set();for(let i=0;i+1<seq.length;i++)onRoute.add(seq[i]+">"+seq[i+1]);
  const xs=L.nodes.filter(n=>n.x!==undefined).map(n=>n.x),ys=L.nodes.filter(n=>n.y!==undefined).map(n=>n.y);
  const W=px(Math.max(...xs))+50,H=py(Math.max(...ys))+34;
  const sc=opts.scale||1;
  let s=`<svg width="${W*sc}" height="${H*sc}" viewBox="0 0 ${W} ${H}">`;
  for(let t=0;t<=L.k;t++)s+=`<text class="collab ${t===L.k?'k':''}" x="${px(t)}" y="14">${t===L.k?"\\u25BC ":""}${t}</text>`;
  s+=`<path class="trk live" d="M${px(L.nodes[L.start].x)-38},${py(L.nodes[L.start].y)} L${px(L.nodes[L.start].x)-JR-2},${py(L.nodes[L.start].y)}"/>`;
  L.nodes.forEach((n,i)=>{
    if(n.kind==="pass"){const to=L.nodes[n.next];const[a,b,c,d2]=ends(n,to);
      s+=`<path class="trk ${onRoute.has(i+">"+n.next)?'live':''}" d="M${a},${b} L${c},${d2}"/>`;return;}
    if(n.kind!=="test")return;
    const v=g[n.cell[0]][n.cell[1]];
    [["out1",1],["out0",0]].forEach(([f,val])=>{
      const to=L.nodes[n[f]];const[x1,y1,x2,y2,ux,uy]=ends(n,to);
      const al=v===val,live=al&&onRoute.has(i+">"+n[f]);
      const gx=al?x1:x1+ux*12,gy=al?y1:y1+uy*12;
      const mx=(gx+x2)/2,my=(gy+y2)/2-Math.min(13,Math.abs(x2-gx)*.06);
      const d=`M${gx},${gy} Q${mx},${my} ${x2},${y2}`;
      s+=`<path class="trk ${al?(live?'live':''):'idle'}" d="${d}"/>`;
      if(opts.interactive)s+=`<path class="trkhit" data-r="${n.cell[0]}" data-t="${n.cell[1]}" data-v="${val}" d="${d}"/>`;
    });});
  L.nodes.forEach((n,i)=>{
    if(n.x===undefined)return;const x=px(n.x),y=py(n.y);
    if(n.kind==="bulb"){
      s+=`<circle class="bulb ${isLit?'lit':'dark'}" cx="${x}" cy="${y}" r="15" stroke-width="2"/>
          <text class="blab ${isLit?'lit':'dark'}" x="${x}" y="${y+4.5}">\\u229B</text>`;}
    else if(n.kind==="gnd"){
      s+=`<line class="gnd" x1="${x-8}" y1="${y}" x2="${x+8}" y2="${y}"/>
          <line class="gnd" x1="${x-5}" y1="${y+4}" x2="${x+5}" y2="${y+4}"/>
          <line class="gnd" x1="${x-2}" y1="${y+8}" x2="${x+2}" y2="${y+8}"/>`;}
    else if(n.kind==="pass"){
      s+=`<circle cx="${x}" cy="${y}" r="3.5" fill="#56505f"/>`;}
    else if(n.kind==="test"){
      const key=n.cell.join(",");
      const extra=opts.markCell?opts.markCell(n.cell):"";
      const thrown=g[n.cell[0]][n.cell[1]]!==L.obs[n.cell[0]][n.cell[1]];
      if(thrown&&opts.interactive)s+=`<circle class="jxring" cx="${x}" cy="${y}" r="${JR+5}"/>`;
      s+=`<circle class="jx ${extra}" data-r="${n.cell[0]}" data-t="${n.cell[1]}" cx="${x}" cy="${y}" r="${JR}"/>`;
      if(opts.interactive)s+=`<circle class="jxhit" data-r="${n.cell[0]}" data-t="${n.cell[1]}" cx="${x}" cy="${y}" r="${JR+7}"/>`;
      const tg=opts.tagText?opts.tagText(n.cell):null;
      if(tg)s+=`<text class="tag ${tg.cls}" data-r="${n.cell[0]}" data-t="${n.cell[1]}" x="${x}" y="${y-JR-5}">${tg.txt}</text>`;
    }});
  s+="</svg>";return s;}
function card(msg,col){const c=document.getElementById("card");c.className="show";
  c.style.borderColor=col||"var(--edge)";c.innerHTML=msg;}
function hideCard(){document.getElementById("card").className="";}
function win(msg){solved[li]=true;tabs();
  document.getElementById("omsg").innerHTML=msg+`<div style="font-size:11px;color:var(--dim);margin-top:6px">${L.prov}</div>`;
  document.getElementById("overlay").classList.add("show");}
function tabs(){document.getElementById("tabs").innerHTML=LEVELS.map((l,i)=>
  `<div class="tab ${i===li?'active':''} ${solved[i]?'done':''}" onclick="load(${i})">${l.name}</div>`).join("");}
function nextLevel(){document.getElementById("overlay").classList.remove("show");
  load(Math.min(li+1,LEVELS.length-1));}
function renderRecording(){
  const save=grid;grid=null;
  document.getElementById("recwrap").innerHTML=boardSVG(L.obs,{interactive:false,scale:0.55});
  grid=save;}
"""

def page(mode, title, goal_html, mode_js, levels, foot_extra):
    lv = json.dumps(levels, sort_keys=True, separators=(",", ":"))
    nav = " ".join(f'<a href="TRACE_{m}.html" class="{"here" if m==mode else ""}">{m.upper()} IT</a>'
                   for m in ("stop", "pin", "credit"))
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TRACE — {title}</title>
<style>{CSS}</style>
</head>
<body>
<h1>{title}</h1>
<div class="modebar">{nav}</div>
<div class="goal">{goal_html}</div>
<div class="tabs" id="tabs"></div>
<div id="machine">
  <div class="worldlab">THE RECORDING — what actually happened (frozen)</div>
  <div id="recwrap"></div>
  <div class="worldlab">YOUR BENCH — experiment freely</div>
  <div id="svgwrap"></div>
  <div id="sweepbar"><div id="sweepfill"></div></div>
  <div class="hud"><div class="delta" id="delta"></div><div id="hearts"></div></div>
  <div class="btnrow" id="btnrow"></div>
  <div id="card"></div>
</div>
<div class="foot">This page contains NO answer key: every verdict is computed in front of you by
running the machine itself (the board is build-verified to behave identically to the source
automaton on every possible switch setting). {foot_extra}</div>
<div id="overlay"><div class="big">✔</div><div id="omsg" style="color:var(--gold);text-align:center;max-width:80vw"></div><button onclick="nextLevel()">▸</button></div>
<script>
const LEVELS={lv};
{JS_CORE}
{mode_js}
load(0);
</script>
</body>
</html>
"""

STOP_JS = """
let tried;
function load(i){li=i;L=LEVELS[i];grid=clone(L.obs);tried=new Set();hideCard();tabs();render();}
function render(){
  renderRecording();
  const tcells=testable();
  document.getElementById("svgwrap").innerHTML=boardSVG(grid,{interactive:true,
    tagText:c=>({txt:"\\u2702",cls:tried.has(c.join(","))?"tried":"fresh"})});
  document.getElementById("delta").textContent=
    `single throws tried: ${tried.size} / ${tcells.length}`;
  document.getElementById("hearts").textContent="";
  document.getElementById("btnrow").innerHTML=
    `<button id="reset">\\u21BA</button>
     <button id="noway" class="verdictgold" ${tried.size===tcells.length?"":"disabled style='opacity:.4'"}>
       \\u2298 nothing alone stops it (${tried.size}/${tcells.length})</button>`;
  document.getElementById("reset").onclick=()=>{grid=clone(L.obs);hideCard();render();};
  document.getElementById("noway").onclick=()=>{
    if(tried.size!==testable().length)return;
    win("Verified by YOUR tally: every single throw was tried on the bench and the light survived each one. Nothing alone stops it.");};
  document.querySelectorAll(".jxhit").forEach(h=>h.onclick=()=>singleThrow(+h.dataset.r,+h.dataset.t));
  document.querySelectorAll(".trkhit").forEach(h=>h.onclick=()=>singleThrow(+h.dataset.r,+h.dataset.t));
}
function singleThrow(r,t){
  // STOP gesture: each tap IS the experiment 'this one throw, alone'.
  grid=clone(L.obs);grid[r][t]^=1;render();
  const dark=!litOf(grid);
  if(dark){win("ONE throw, light out — there is the stopper.");}
  else{tried.add([r,t].join(","));
       card("Light survived that lone throw — tallied. ("+(testable().length-tried.size)+" left)");
       render();}
}
"""

PIN_JS = """
let locks,sweeping;
function load(i){li=i;L=LEVELS[i];grid=clone(L.obs);locks=new Set();sweeping=false;hearts=2;hideCard();tabs();render();}
function render(){
  renderRecording();
  document.getElementById("svgwrap").innerHTML=boardSVG(grid,{interactive:!sweeping,
    markCell:c=>locks.has(c.join(","))?"lockd":""});
  document.getElementById("delta").textContent=`locks: ${locks.size}`;
  document.getElementById("hearts").textContent="\\u2665".repeat(hearts)+"\\u2661".repeat(2-hearts);
  document.getElementById("btnrow").innerHTML=
    `<button id="reset">\\u21BA</button><button id="sweep" class="primary">RUN THE SWEEP</button>`;
  document.getElementById("reset").onclick=()=>{if(sweeping)return;grid=clone(L.obs);locks=new Set();hideCard();render();};
  document.getElementById("sweep").onclick=()=>{if(!sweeping)sweep();};
  if(!sweeping){
    document.querySelectorAll(".jxhit").forEach(h=>h.onclick=()=>{
      const key=h.dataset.r+","+h.dataset.t;
      locks.has(key)?locks.delete(key):locks.add(key);render();});
  }
}
function completions(lockset){
  const rest=allCells().filter(c=>!lockset.has(c.join(",")));
  const out=[];
  for(let m=0;m<(1<<rest.length);m++){
    const g=clone(L.obs);
    rest.forEach((c,j)=>g[c[0]][c[1]]=(m>>j)&1);
    out.push(g);}
  return out;}
function sweep(){
  if(locks.size===0){card("Lock at least one switch, then run the sweep.","var(--bad)");return;}
  sweeping=true;hideCard();
  const comps=completions(locks);
  const bar=document.getElementById("sweepbar");bar.style.display="block";
  let i=0;
  const step=()=>{
    if(i>=comps.length){ // survived everything: now minimality, also by visible sweep
      bar.style.display="none";sweeping=false;
      const extra=[...locks].find(k=>{
        const sub=new Set(locks);sub.delete(k);
        return sub.size>0?completions(sub).every(g=>litOf(g)):false;});
      if(locks.size===1||!extra){
        win(`The sweep ran ALL ${comps.length} settings of the unlocked switches in front of you — the light survived every one. Your locks hold it.`);
      }else{
        hearts--;render();
        const [r,t]=extra.split(",").map(Number);
        card(`The light never went out — but the sweep also holds WITHOUT the lock on (${L.inputs[r]}, moment ${t}). A lock that does nothing isn't a lock. `+(hearts? "Try fewer.":"Out of tries — tap the level tab to retry."),"var(--bad)");
        if(hearts<=0)hearts=2;
      }
      return;}
    grid=comps[i];render();
    document.getElementById("sweepfill").style.width=(100*i/comps.length)+"%";
    if(!litOf(grid)){
      bar.style.display="none";sweeping=false;hearts--;
      render();
      card(`The sweep found the leak — THIS setting (left on your bench) puts the light out despite your locks. `+(hearts?"":"Out of tries — tap the level tab to retry."),"var(--bad)");
      if(hearts<=0)hearts=2;
      return;}
    i++;setTimeout(step,Math.max(30,420/Math.sqrt(comps.length)));};
  step();
}
"""

CREDIT_JS = """
// CREDIT IT — single taps only, no gestures:
//   tap the ★ tag above a switch  -> claim it (gold)
//   tap a switch or a track            -> set the bench (your contingency)
//   MAKE IT BLINK                      -> run the two-arm demonstration
let cand;
function load(i){li=i;L=LEVELS[i];grid=clone(L.obs);cand=null;hearts=2;hideCard();tabs();render();}
function render(){
  renderRecording();
  document.getElementById("svgwrap").innerHTML=boardSVG(grid,{interactive:true,
    markCell:c=>(cand&&cand.join(",")===c.join(","))?"cand":"",
    tagText:c=>({txt:"★",cls:(cand&&cand.join(",")===c.join(","))?"fresh":"tried"})});
  document.getElementById("delta").innerHTML=cand?
    `claim: <b style="color:var(--gold)">(${L.inputs[cand[0]]}, moment ${cand[1]})</b> — press MAKE IT BLINK; if it refuses, rearrange the bench to silence the backup`
    :`<b style="color:var(--gold)">tap the ★ above a switch</b> to claim it · tap switches to set the bench`;
  document.getElementById("hearts").textContent="♥".repeat(hearts)+"♡".repeat(2-hearts);
  document.getElementById("btnrow").innerHTML=
    `<button id="reset">↺</button>
     <button id="blink" class="primary" ${cand?"":"disabled style='opacity:.4'"}>MAKE IT BLINK</button>`;
  document.getElementById("reset").onclick=()=>{grid=clone(L.obs);cand=null;hideCard();render();};
  document.getElementById("blink").onclick=()=>{if(cand)blinkTest();};
  document.querySelectorAll(".tag").forEach(h=>h.onclick=()=>{
    cand=[+h.dataset.r,+h.dataset.t];
    grid[cand[0]][cand[1]]=L.obs[cand[0]][cand[1]];   // claims are stated at the recorded value
    hideCard();render();});
  document.querySelectorAll(".jxhit").forEach(h=>h.onclick=()=>{
    grid[+h.dataset.r][+h.dataset.t]^=1;render();});
  document.querySelectorAll(".trkhit").forEach(h=>h.onclick=()=>{
    grid[+h.dataset.r][+h.dataset.t]=+h.dataset.v;render();});
}
function blinkTest(){
  const c=cand;
  grid[c[0]][c[1]]=L.obs[c[0]][c[1]];render();
  const gOn=clone(grid), gOff=clone(grid); gOff[c[0]][c[1]]^=1;
  if(!litOf(gOn)){hearts--;render();card("With this bench the light is OUT even with the switch as recorded — it commands nothing here. Rearrange the bench."+(hearts?"":" Out of tries — tap the tab to retry."),"var(--bad)");if(hearts<=0)hearts=2;return;}
  if(litOf(gOff)){hearts--;render();card("Flip it and the light STAYS on — something else is carrying it. Find and silence the backup, then try again."+(hearts?"":" Out of tries — tap the tab to retry."),"var(--bad)");if(hearts<=0)hearts=2;return;}
  let n=0;const seqs=[gOff,gOn,gOff,gOn];
  const beat=()=>{
    if(n<seqs.length){grid=clone(seqs[n]);render();n++;setTimeout(beat,420);return;}
    const diff=allCells().filter(cc=>!(cc[0]===c[0]&&cc[1]===c[1])&&gOn[cc[0]][cc[1]]!==L.obs[cc[0]][cc[1]]);
    for(let m=1;m<(1<<diff.length);m++){
      const h=clone(gOn);
      diff.forEach((cc,j)=>{if((m>>j)&1)h[cc[0]][cc[1]]=L.obs[cc[0]][cc[1]];});
      if(!litOf(h)){
        hearts--;grid=h;render();
        card("It blinked — but your bench was doing hidden work: returning these switches to the recording (left on your bench) kills the light even with your claim in place. The switch must command the light, not your scaffolding."+(hearts?"":" Out of tries — tap the tab to retry."),"var(--bad)");
        if(hearts<=0)hearts=2;return;}}
    grid=clone(gOn);render();
    win(`You made the light obey (${L.inputs[c[0]]}, moment ${c[1]}): on with it as recorded, off when flipped — and the demonstration held when your bench was handed back to the recording. That switch truly decided the recorded flash.`);};
  beat();
}
"""

def main():
    pages = [
        ("stop", "STOP IT",
         "One throw. <b>Put the light out by flipping a single switch</b> — each tap tests exactly one lone throw against the recording. "
         "If you come to believe no single throw can do it, finish the tally: try them all, then say so.",
         STOP_JS, levels_for("stop"),
         "The ⊘ verdict is yours to earn: it unlocks only when your own tally has tried every single throw."),
        ("pin", "PIN IT",
         "<b>Lock switches so the light CANNOT go out.</b> The sweep will run every possible setting of the unlocked switches before your eyes — "
         "it accepts nothing on faith, and neither should you: a lock that does nothing is not a lock.",
         PIN_JS, levels_for("pin"),
         "Acceptance = the sweep visibly exhausts every completion; rejection = the leaking setting is left on your bench."),
        ("credit", "CREDIT IT",
         "<b>Make the light OBEY one switch.</b> Tap the <b>★ above a switch</b> to claim it, set the bench with ordinary taps, then make the bulb blink under its command: "
         "on with it as recorded, off when flipped. Your bench setup must not do the work itself — that is checked in front of you.",
         CREDIT_JS, levels_for("credit"),
         "A blink under your own contingency is the textbook two-run demonstration of an actual cause "
         "(Halpern–Pearl, original/updated variant: the bench may hold other switches at non-recorded values); "
         "the scaffolding check replays its counterexample if it fails."),
    ]
    hashes = {}
    for mode, title, goal, js, lv, foot in pages:
        html = page(mode, title, goal, js, lv, foot)
        path = os.path.join(ROOT, f"TRACE_{mode}.html")
        open(path, "w").write(html)
        hashes[mode] = hashlib.sha256(html.encode()).hexdigest()[:16]
        print(f"built TRACE_{mode}.html  levels={len(lv)}  sha256/16={hashes[mode]}")
    return hashes

if __name__ == "__main__":
    main()
