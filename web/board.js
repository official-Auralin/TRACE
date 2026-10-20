'use strict';
// The public routing graph is the puzzle. This module draws/replays a supplied
// input word only; it contains no causal solver, answer key, or grading routine.
window.TRACEBoard = (() => {
  const ns='http://www.w3.org/2000/svg';
  function walk(board,inputs){
    if(board.version==='trace.board.v2')return execute(board,inputs).path;
    const nodes=new Map(board.nodes.map(n=>[n.id,n])),values=inputs.flat(),path=[];
    let node=nodes.get(board.start);
    while(node&&path.length<=board.nodes.length){path.push(node.id);if(node.kind!=='switch')break;node=nodes.get(values[node.cell]?node.one:node.zero);}
    return path;
  }
  function render(host,item,options={}){
    if(host._animation)cancelAnimationFrame(host._animation);
    if(item.board.version==='trace.board.v2')return renderGeneral(host,item,options);
    host._dispose?.();host._dispose=null;
    const board=item.board,inputs=options.inputs||item.observed,values=inputs.flat(),selected=options.selected||new Set();
    const path=options.path||walk(board,inputs),nodes=new Map(board.nodes.map(n=>[n.id,n]));
    const labels=new Map(board.switches.map(s=>[s.cell,s.label]));
    const maxX=board.nodes.reduce((maximum,node)=>Math.max(maximum,node.x),0),width=Math.max(480,160*maxX+160),height=320;
    const px=x=>80+x*((width-160)/Math.max(1,maxX)),py=y=>98+y*72;
    const svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox','0 0 '+width+' '+height);svg.setAttribute('class','board-svg');svg.setAttribute('role','group');svg.setAttribute('aria-label','Switch and light puzzle. Follow routes from left to right.');
    const add=(tag,attrs,text,parent=svg)=>{const e=document.createElementNS(ns,tag);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,v);if(text!==undefined)e.textContent=text;parent.append(e);return e;};
    const title=add('title',{},'Recorded switches route a signal toward the light or the dark exit. Marking holds their recorded direction.');
    for(const column of board.columns){const x=px(column.step);add('line',{x1:x,y1:45,x2:x,y2:285,class:'step-rule'});add('text',{x,y:25,'text-anchor':'middle',class:'column-label'},'MOMENT '+(column.step+1));}
    const edges=new Map();
    for(const node of board.nodes){if(node.kind!=='switch')continue;const x=px(node.x),y=py(node.y);
      for(const value of [0,1]){const next=nodes.get(value?node.one:node.zero);const x2=px(next.x)-23,y2=py(next.y),startX=x+21,startY=y+(value?13:-13),dx=x2-startX;
        // Ports encode directions consistently: 0 is the upper fork, 1 lower.
        // Long wires take a separate outside lane instead of crossing switch bodies.
        let d;
        if(next.x-node.x>1.05){const lane=value?284-node.x*9:53+node.x*9;d='M '+startX+' '+startY+' C '+(startX+45)+' '+startY+' '+(startX+38)+' '+lane+' '+(startX+64)+' '+lane+' L '+(x2-53)+' '+lane+' C '+(x2-20)+' '+lane+' '+(x2-40)+' '+y2+' '+x2+' '+y2;}
        else d='M '+startX+' '+startY+' C '+(startX+dx*.45)+' '+startY+' '+(x2-dx*.45)+' '+y2+' '+x2+' '+y2;
        add('path',{d,class:'rail-under'});
        const index=path.indexOf(node.id),live=index>=0&&values[node.cell]===value&&path[index+1]===next.id;
        const edge=add('path',{d,class:'rail'+(live?' live':values[node.cell]!==value?' closed':'')});edges.set(node.id+':'+value,edge);
      }
    }
    const first=nodes.get(board.start),entryY=py(first.y),entryX=px(first.x);
    add('path',{d:'M '+(entryX-55)+' '+entryY+' L '+(entryX-25)+' '+entryY,class:'rail live'});
    add('path',{d:'M '+(entryX-46)+' '+(entryY-5)+' L '+(entryX-38)+' '+entryY+' L '+(entryX-46)+' '+(entryY+5),fill:'none',stroke:'#f6ce74','stroke-width':2});
    add('text',{x:entryX-40,y:entryY+28,'text-anchor':'middle',class:'entry-text'},'START');
    for(const node of board.nodes){const x=px(node.x),y=py(node.y);
      if(node.kind==='switch'){
        const marked=selected.has(node.cell),group=add('g',{class:'switch-node'+(marked?' selected':''),'data-cell':node.cell,'data-node':node.id,role:'button',tabindex:options.interactive?0:-1,'aria-pressed':String(marked),'aria-label':'Switch '+labels.get(node.cell)+', moment '+(Math.floor(node.cell/item.machine.inputs.length)+1)+', displayed direction '+(values[node.cell]?'lower':'upper')+', recorded direction '+(item.observed.flat()[node.cell]?'lower':'upper')+(marked?', marked':'')});
        add('circle',{cx:x,cy:y,r:24,class:'switch-body'},undefined,group);
        add('circle',{cx:x+20,cy:y-13,r:3,class:'port'},undefined,group);add('circle',{cx:x+20,cy:y+13,r:3,class:'port'},undefined,group);
        add('path',{d:'M '+(x-13)+' '+y+' L '+(x+17)+' '+(y+(values[node.cell]?12:-12)),class:'switch-lever'},undefined,group);add('circle',{cx:x-13,cy:y,r:3.5,class:'switch-hub'},undefined,group);
        add('text',{x,y:y+45,'text-anchor':'middle',class:'switch-label'},labels.get(node.cell),group);
        if(marked)add('path',{d:'M '+x+' '+(y-40)+' l 5 5 -5 5 -5 -5 Z',class:'pin-symbol'},undefined,group);
        if(options.interactive){group.onclick=()=>options.onSelect?.(node.cell);group.onkeydown=e=>{if(e.key===' '||e.key==='Enter'){e.preventDefault();options.onSelect?.(node.cell);host.querySelector('[data-node="'+node.id+'"]')?.focus();}};}
      }else if(node.kind==='lamp'){
        const on=path.at(-1)===node.id;
        add('rect',{x:x-49,y:y-64,width:98,height:131,rx:16,class:'goal-frame','data-target-lamp':'true','data-target-on':String(on)});
        add('text',{x,y:y-45,'text-anchor':'middle',class:'target-name'},'TARGET');
        add('circle',{cx:x,cy:y-2,r:25,class:'lamp-glass'+(on?' on':'')});
        add('path',{d:'M '+(x-8)+' '+(y+18)+' L '+(x-8)+' '+(y+31)+' L '+(x+8)+' '+(y+31)+' L '+(x+8)+' '+(y+18)+' M '+(x-7)+' '+y+' L '+(x-4)+' '+(y-7)+' L '+x+' '+(y+3)+' L '+(x+4)+' '+(y-7)+' L '+(x+7)+' '+y,class:'lamp-filament'+(on?' on':'')});
        if(on)for(let i=0;i<7;i++){const a=Math.PI*(.85+i*.215);add('line',{x1:x+33*Math.cos(a),y1:y-2+33*Math.sin(a),x2:x+39*Math.cos(a),y2:y-2+39*Math.sin(a),class:'light-rays'});}
        add('text',{x,y:y+52,'text-anchor':'middle',class:'terminal-label'},on?'LIGHT ON':'LIGHT OFF');
      }else{
        const active=path.at(-1)===node.id;
        add('path',{d:'M '+(x-18)+' '+y+' L '+(x+18)+' '+y+' M '+(x-12)+' '+(y+7)+' L '+(x+12)+' '+(y+7)+' M '+(x-5)+' '+(y+14)+' L '+(x+5)+' '+(y+14),class:'drain-lines'+(active?' off-target':''),'data-dark-exit':'true'});
        add('text',{x,y:y+42,'text-anchor':'middle',class:'terminal-label'},'DARK EXIT');
      }
    }
    const dot=add('circle',{r:4.5,class:'signal-dot',visibility:'hidden'});
    host.replaceChildren(svg);const note=document.createElement('p');note.className='scroll-note';note.textContent='Slide the board sideways to follow every wire →';host.append(note);
    function animate(){if(host._animation)cancelAnimationFrame(host._animation);const tracks=path.slice(0,-1).map(id=>edges.get(id+':'+values[nodes.get(id).cell])).filter(Boolean);if(!tracks.length||matchMedia('(prefers-reduced-motion: reduce)').matches)return;
      const lengths=tracks.map(e=>e.getTotalLength()),total=lengths.reduce((a,b)=>a+b,0),duration=Math.max(1400,path.length*470);let start;
      function tick(time){if(!host.contains(svg))return;start??=time;let d=Math.min(1,(time-start)/duration)*total,index=0;while(index<lengths.length-1&&d>lengths[index])d-=lengths[index++];const p=tracks[index].getPointAtLength(d);dot.setAttribute('cx',p.x);dot.setAttribute('cy',p.y);dot.setAttribute('visibility','visible');if(time-start<duration)host._animation=requestAnimationFrame(tick);else dot.setAttribute('visibility','hidden');}
      host._animation=requestAnimationFrame(tick);
    }
    host.replay=animate;if(options.animate!==false)animate();return {path,svg};
  }
  // Independent interpreter for the general compiler's public decision trees.
  // Each tree consumes one round; its routing decisions are not extra time steps.
  // No integer bit masks: cell identifiers remain ordinary safe JSON integers.
  function execute(board,inputs){
    if(board.version!=='trace.board.v2')throw Error('General execution requires board v2.');
    if(inputs.length<board.horizon)throw Error('The supplied recording is too short.');
    const path=[],outputs=[],states=[board.initial];let state=board.initial;
    for(let t=0;t<board.horizon;t++){
      if(inputs[t].length!==board.inputs||inputs[t].some(value=>value!==0&&value!==1))throw Error('Input channel count or values differ.');
      let node=board.layers[t][state],prefix='';
      while(node.kind==='switch'){
        path.push(t+':'+state+':'+prefix);
        const channel=node.cell-t*board.inputs,value=inputs[t][channel];
        if(channel<0||channel>=board.inputs||(value!==0&&value!==1))throw Error('Invalid switch input.');
        prefix+=String(value);node=value?node.one:node.zero;
      }
      if(node.kind!=='output')throw Error('Invalid circuit output.');
      path.push(t+':'+state+':'+prefix);outputs.push(node.value);state=node.next;states.push(state);
    }
    return {path,outputs,states};
  }

  // The final display observes only the target output; post-target states have
  // no visual identity. Earlier state transitions remain exact. This evaluator
  // provides projected path IDs while execute() retains semantic replay IDs.
  function displayExecute(board,inputs){
    if(board.display?.version!=='trace.display.v1')throw Error('A certified terminal display is required.');
    const semantic=execute(board,inputs),path=[];
    for(let t=0;t<board.horizon;t++){
      const q=semantic.states[t];let node=t===board.horizon-1?board.display.terminal[q]:board.layers[t][q],prefix='';
      while(node.kind==='switch'){
        path.push(t+':'+q+':'+prefix);const value=inputs[t][node.cell-t*board.inputs];
        prefix+=String(value);node=value?node.one:node.zero;
      }
      path.push(t+':'+q+':'+prefix);
      if(node.value!==semantic.outputs[t])throw Error('Terminal display and execution disagree.');
    }
    const outcome=semantic.outputs.at(-1);path.push(outcome?'target-lamp':'dark-exit');
    return {...semantic,path,outcome};
  }

  function renderGeneral(host,item,options){
    const board=item.board,word=options.inputs||item.observed,recording=displayExecute(board,word);
    const displayLayers=board.layers.map((layer,t)=>t===board.horizon-1?board.display.terminal:layer);
    const selected=options.selected||new Set(),actual=item.observed.flat(),values=word.flat();
    const labels=new Map(board.switches.map(s=>[s.cell,s.label])),live=new Set(recording.path);
    const sizes=new WeakMap();let leaves=1;
    for(const layer of displayLayers)for(const root of layer){
      const pending=[[root,false]];
      while(pending.length){const[node,visited]=pending.pop();if(sizes.has(node))continue;
        if(node.kind!=='switch')sizes.set(node,1);
        else if(visited)sizes.set(node,sizes.get(node.zero)+sizes.get(node.one));
        else pending.push([node,true],[node.one,false],[node.zero,false]);
      }
      leaves=Math.max(leaves,sizes.get(root));
    }
    const leafPitch=58,routeHeight=leaves*leafPitch+90;
    const columnWidth=board.inputs*108+235,worldWidth=board.horizon*columnWidth+195,worldHeight=board.states*routeHeight+70;
    const terminals={ 'target-lamp':{x:worldWidth-100,y:Math.max(120,worldHeight/2-68)},'dark-exit':{x:worldWidth-100,y:Math.max(240,worldHeight/2+68)} };
    const previous=host._generalView?.id===item.id?host._generalView:null;
    host._dispose?.();
    const view=previous||{id:item.id,x:0,y:0,zoom:Math.min(1,800/columnWidth),inventoryMoment:0};
    host._generalView=view;
    const toolbar=document.createElement('div');toolbar.className='board-navigation';
    const viewport=document.createElement('div');viewport.className='circuit-viewport';
    viewport.tabIndex=0;viewport.setAttribute('aria-label','Puzzle board. Drag or scroll to pan; use plus and minus to zoom. Arrow keys move the view.');
    const svg=document.createElementNS(ns,'svg');svg.setAttribute('class','general-board-svg');svg.setAttribute('role','group');
    svg.setAttribute('aria-label','Switch circuits across time lead to one target lamp or one dark exit. Identical full labels are linked; different moments are separate switches.');
    viewport.append(svg);
    const note=document.createElement('p');note.className='circuit-note';
    note.textContent='One target lamp. Every successful route joins it; the other exit leaves it dark. Gold shows this run. Identical full switch labels move together.';
    const inventory=document.createElement('div');inventory.className='circuit-switches';inventory.setAttribute('aria-label','Recorded input switches');
    // Keep every original input cell selectable, including cells skipped by a
    // reduced routing tree. This inventory is shared with the agent task.
    let inventoryMoment=-1;
    function showInventory(t){if(!options.interactive||inventoryMoment===t)return;inventoryMoment=t;inventory.replaceChildren();const label=document.createElement('span');label.textContent='Moment '+(t+1);inventory.append(label);
      for(let channel=0;channel<board.inputs;channel++){const cell=t*board.inputs+channel,b=document.createElement('button');b.type='button';b.textContent=labels.get(cell)+' '+(values[cell]?'↘':'↗');b.dataset.inventoryCell=cell;b.setAttribute('aria-pressed',String(selected.has(cell)));b.setAttribute('aria-label','Switch '+labels.get(cell)+', moment '+(t+1)+', '+(values[cell]?'lower':'upper'));b.onclick=()=>options.onSelect?.(cell);inventory.append(b);}
    }
    host.replaceChildren(toolbar,viewport,inventory,note);
    viewport.style.height=Math.min(570,Math.max(330,worldHeight*Math.min(1,(viewport.clientWidth||800)/worldWidth)))+'px';
    const initialZoom=()=>Math.min(1,Math.max(.35,Math.min((viewport.clientWidth||800)/worldWidth,(viewport.clientHeight||570)/worldHeight)));
    if(!previous)view.zoom=initialZoom();
    const controls=[];
    function control(label,action){const b=document.createElement('button');b.type='button';b.textContent=label;b.onclick=action;toolbar.append(b);controls.push(b);return b;}
    const scale=document.createElement('output');scale.className='zoom-level';
    control('−',()=>zoomAt(.8));control('+',()=>zoomAt(1.25));toolbar.append(scale);
    control('Start',()=>{view.x=0;view.y=0;view.inventoryMoment=0;view.zoom=initialZoom();draw();notifyNavigation('start');});
    control('Target',()=>{view.zoom=Math.max(view.zoom,.85);view.x=terminals['target-lamp'].x-viewport.clientWidth/(2*view.zoom);view.y=terminals['target-lamp'].y-viewport.clientHeight/(2*view.zoom);view.inventoryMoment=board.horizon-1;draw();notifyNavigation('jump');});
    control('Overview',()=>{view.x=0;view.y=0;view.zoom=Math.min(viewport.clientWidth/worldWidth,viewport.clientHeight/worldHeight);draw();notifyNavigation('overview');});
    function locationInput(label,value,max){const wrapper=document.createElement('label');wrapper.textContent=label+' ';const input=document.createElement('input');input.type='number';input.min='1';input.max=String(max);input.value=String(value);input.setAttribute('aria-label','Go to '+label.toLowerCase());wrapper.append(input);toolbar.append(wrapper);return input;}
    const moment=locationInput('Moment',1,board.horizon),route=locationInput('Route',board.initial+1,board.states);
    control('Go',()=>{const t=Number(moment.value)-1,q=Number(route.value)-1;if(!Number.isSafeInteger(t)||!Number.isSafeInteger(q)||t<0||t>=board.horizon||q<0||q>=board.states)return;view.x=t*columnWidth;view.y=q*routeHeight;view.inventoryMoment=t;view.zoom=Math.min(1,800/columnWidth);draw();notifyNavigation('jump');});
    let frame=null,drag=null,animation=null;
    const position=(t,q,node,firstLeaf=0)=>({x:t*columnWidth+65+(node.kind==='switch'?node.cell%board.inputs:board.inputs)*108,y:65+q*routeHeight+((leaves-sizes.get(displayLayers[t][q]))/2+firstLeaf+sizes.get(node)/2)*leafPitch});
    const rootPosition=(t,q)=>position(t,q,displayLayers[t][q]);
    const rootEntry=(t,q)=>{const p=rootPosition(t,q);return {x:p.x-(displayLayers[t][q].kind==='switch'?23:0),y:p.y};};
    const livePoints=new Map();
    for(let t=0;t<board.horizon;t++){const q=recording.states[t];let node=displayLayers[t][q],prefix='',firstLeaf=0;while(true){livePoints.set(t+':'+q+':'+prefix,position(t,q,node,firstLeaf));if(node.kind!=='switch')break;const value=values[node.cell];if(value)firstLeaf+=sizes.get(node.zero);node=value?node.one:node.zero;prefix+=String(value);}}
    const pointFor=id=>livePoints.get(id)||terminals[id];
    function bounds(){return {left:view.x,top:view.y,right:view.x+viewport.clientWidth/view.zoom,bottom:view.y+viewport.clientHeight/view.zoom};}
    function notifyNavigation(kind){options.onNavigate?.({kind,view:{moment:view.inventoryMoment||0,route:Math.min(board.states-1,Math.max(0,Math.floor(view.y/routeHeight))),zoom:view.zoom,x:Math.max(0,view.x),y:Math.max(0,view.y)}});}
    function zoomAt(factor,x=viewport.clientWidth/2,y=viewport.clientHeight/2){const old=view.zoom;view.zoom=Math.min(4,Math.max(Math.min(viewport.clientWidth/worldWidth,viewport.clientHeight/worldHeight)/2,old*factor));view.x+=x/old-x/view.zoom;view.y+=y/old-y/view.zoom;draw();notifyNavigation('zoom');}
    function draw(){
      if(!host.contains(svg))return;
      const w=viewport.clientWidth||800,h=viewport.clientHeight||560;
      view.x=Math.max(0,Math.min(view.x,Math.max(0,worldWidth-w/view.zoom)));
      view.y=Math.max(0,Math.min(view.y,Math.max(0,worldHeight-h/view.zoom)));
      const focusedId=svg.contains(document.activeElement)?document.activeElement.dataset.node:null;
      svg.setAttribute('viewBox',[view.x,view.y,w/view.zoom,h/view.zoom].join(' '));svg.replaceChildren();
      scale.textContent=Math.round(view.zoom*100)+'%';
      showInventory(view.inventoryMoment||0);
      const box=bounds(),visible=(x,y,pad=38)=>x+pad>=box.left&&x-pad<=box.right&&y+pad>=box.top&&y-pad<=box.bottom;
      const add=(tag,attrs,text,parent=svg)=>{const e=document.createElementNS(ns,tag);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,v);if(text!==undefined)e.textContent=text;parent.append(e);return e;};
      const edgeLayer=add('g',{}),nodeLayer=add('g',{});
      function wire(a,b,active=false,closed=false,metadata={}){
        if(Math.max(a.x,b.x)<box.left-30||Math.min(a.x,b.x)>box.right+30||Math.max(a.y,b.y)<box.top-30||Math.min(a.y,b.y)>box.bottom+30)return;
        const bend=Math.max(32,(b.x-a.x)*.45),d='M '+a.x+' '+a.y+' C '+(a.x+bend)+' '+a.y+' '+(b.x-bend)+' '+b.y+' '+b.x+' '+b.y;
        add('path',{d,class:'rail-under'},undefined,edgeLayer);add('path',{d,class:'rail'+(active?' live':closed?' closed':''),...metadata},undefined,edgeLayer);
      }
      function targetObjects(){
        const p=terminals['target-lamp'],on=recording.outcome===1;
        const goal=add('g',{'data-target-lamp':'true','data-target-on':String(on),'aria-label':'Target lamp, '+(on?'ON':'OFF')},undefined,nodeLayer);
        add('rect',{x:p.x-58,y:p.y-71,width:116,height:135,rx:18,class:'goal-frame'},undefined,goal);
        add('text',{x:p.x,y:p.y-48,'text-anchor':'middle',class:'target-name'},'TARGET',goal);
        add('circle',{cx:p.x,cy:p.y-2,r:25,class:'lamp-glass'+(on?' on':'')},undefined,goal);
        add('path',{d:'M '+(p.x-8)+' '+(p.y+18)+' v 13 h 16 v -13 M '+(p.x-7)+' '+p.y+' l 3 -7 4 10 4 -10 3 7',class:'lamp-filament'+(on?' on':'')},undefined,goal);
        add('text',{x:p.x,y:p.y+50,'text-anchor':'middle',class:'terminal-label'},on?'LIGHT ON':'LIGHT OFF',goal);
        const d=terminals['dark-exit'],dark=add('g',{'data-dark-exit':'true','aria-label':'Dark exit; target remains off'},undefined,nodeLayer);
        add('path',{d:'M '+(d.x-20)+' '+d.y+' h 40 M '+(d.x-13)+' '+(d.y+8)+' h 26 M '+(d.x-5)+' '+(d.y+16)+' h 10',class:'drain-lines'+(!on?' off-target':'')},undefined,dark);
        add('text',{x:d.x,y:d.y+40,'text-anchor':'middle',class:'terminal-label'},'DARK EXIT',dark);
      }
      targetObjects();
      const firstT=Math.max(0,Math.floor(box.left/columnWidth)-1),lastT=Math.min(board.horizon-1,Math.floor(box.right/columnWidth));
      const firstQ=Math.max(0,Math.floor((box.top-65)/routeHeight)),lastQ=Math.min(board.states-1,Math.floor(box.bottom/routeHeight));
      // At overview scale use circuit tiles, not millions of illegible SVG nodes.
      // Every tile remains reachable with Go or zoom, without deleting any route.
      if(view.zoom<.16){
        const tStride=Math.max(1,Math.ceil(4/(columnWidth*view.zoom))),qStride=Math.max(1,Math.ceil(4/(routeHeight*view.zoom)));
        for(let t=firstT;t<=lastT;t+=tStride)for(let q=firstQ;q<=lastQ;q+=qStride)add('rect',{x:t*columnWidth+10,y:q*routeHeight+40,width:columnWidth*tStride-20,height:routeHeight*qStride-20,rx:10,class:'circuit-tile'+(t===board.horizon-1?' target-tile':'')},undefined,nodeLayer);
        const p=rootPosition(0,board.initial);add('circle',{cx:p.x,cy:p.y,r:6/view.zoom,fill:'#f6ce74'},undefined,nodeLayer);
        return;
      }
      for(let t=firstT;t<=lastT;t++){
        const left=t*columnWidth;
        add('rect',{x:left+9,y:Math.max(14,box.top+5),width:columnWidth-20,height:28,rx:6,class:t===board.horizon-1?'target-heading':'moment-heading'},undefined,nodeLayer);
        add('text',{x:left+25,y:Math.max(33,box.top+24),class:'column-label','font-size':Math.max(10,9/view.zoom),style:'font-size:'+Math.max(10,9/view.zoom)+'px'},'MOMENT '+(t+1)+(t===board.horizon-1?' · TARGET':''),nodeLayer);
        if(t<board.horizon-1)add('text',{x:left+columnWidth-24,y:Math.max(33,box.top+24),'text-anchor':'end',class:'output-value','data-recorded-output':t},'OUTPUT '+(recording.outputs[t]?'ON':'OFF'),nodeLayer);
        // Connections from off-screen source routes may enter a visible route.
        // Traverse one time column at a time; no whole-board DOM is allocated.
        for(let q=0;q<board.states;q++){
          if(q>=firstQ&&q<=lastQ){add('rect',{x:left+15,y:q*routeHeight+48,width:columnWidth-30,height:routeHeight-15,rx:12,class:'circuit-tile'+(t===board.horizon-1?' target-tile':'')},undefined,edgeLayer);add('text',{x:left+28,y:q*routeHeight+66,class:'route-label',style:'font-size:'+Math.max(9,8/view.zoom)+'px'},'ROUTE '+(q+1),nodeLayer);}
          const stack=[{node:displayLayers[t][q],firstLeaf:0,prefix:''}];
          while(stack.length){
            const {node,firstLeaf,prefix}=stack.pop(),p=position(t,q,node,firstLeaf),id=t+':'+q+':'+prefix;
            if(node.kind==='switch'){
              for(const value of [0,1]){const child=value?node.one:node.zero,childFirst=firstLeaf+(value?sizes.get(node.zero):0),c=position(t,q,child,childFirst);wire({x:p.x+22,y:p.y+(value?12:-12)},{x:c.x-(child.kind==='switch'?23:child.kind==='output'?20:0),y:c.y},live.has(id)&&values[node.cell]===value,values[node.cell]!==value);stack.push({node:child,firstLeaf:childFirst,prefix:prefix+value});}
              if(!visible(p.x,p.y,50))continue;
              const marked=selected.has(node.cell),group=add('g',{class:'switch-node'+(marked?' selected':''),'data-cell':node.cell,'data-node':id,role:'button',tabindex:options.interactive?0:-1,'aria-pressed':String(marked),'aria-label':'Switch '+labels.get(node.cell)+', moment '+(t+1)+', route '+(q+1)+', displayed '+(values[node.cell]?'lower':'upper')+', recorded '+(actual[node.cell]?'lower':'upper')},undefined,nodeLayer);
              add('circle',{cx:p.x,cy:p.y,r:23,class:'switch-body'},undefined,group);
              add('circle',{cx:p.x+20,cy:p.y-12,r:3,class:'port'},undefined,group);add('circle',{cx:p.x+20,cy:p.y+12,r:3,class:'port'},undefined,group);
              add('path',{d:'M '+(p.x-13)+' '+p.y+' L '+(p.x+17)+' '+(p.y+(values[node.cell]?12:-12)),class:'switch-lever'},undefined,group);
              add('circle',{cx:p.x-13,cy:p.y,r:3.5,class:'switch-hub'},undefined,group);
              add('text',{x:p.x,y:p.y+40,'text-anchor':'middle',class:'switch-label',style:'font-size:'+Math.max(10,8/view.zoom)+'px'},labels.get(node.cell),group);
              if(marked)add('path',{d:'M '+p.x+' '+(p.y-37)+' l 5 5 -5 5 -5 -5 Z',class:'pin-symbol'},undefined,group);
              if(options.interactive){group.onclick=()=>options.onSelect?.(node.cell);group.onkeydown=e=>{if(e.key===' '||e.key==='Enter'){e.preventDefault();options.onSelect?.(node.cell);host.querySelector('[data-node="'+id+'"]')?.focus();}};}
            }else if(node.kind==='outcome'){
              const target=node.value?'target-lamp':'dark-exit',end=terminals[target];
              wire(p,{x:end.x-(node.value?26:20),y:end.y},live.has(id),false,{'data-final-outcome':node.value,'data-destination':target,'data-from-node':id});
            }else{
              const next=rootEntry(t+1,node.next);wire({x:p.x+20,y:p.y},next,live.has(id));
              if(!visible(p.x,p.y,38))continue;
              const g=add('g',{'data-output-node':id,'aria-label':'Moment '+(t+1)+' output '+node.value+', then route '+(node.next+1)},undefined,nodeLayer);
              // Intermediate output is a status chip, never a goal lamp. Its
              // outgoing wire preserves the consequential next-state identity.
              add('rect',{x:p.x-20,y:p.y-13,width:40,height:26,rx:5,class:'output-chip'+(live.has(id)?' traversed':'')},undefined,g);
              add('text',{x:p.x,y:p.y+4,'text-anchor':'middle',class:'output-value'},node.value?'ON':'OFF',g);
            }
          }
        }
      }
      const start=rootPosition(0,board.initial);
      if(visible(start.x,start.y)){wire({x:start.x-48,y:start.y},rootEntry(0,board.initial),true);add('text',{x:start.x-28,y:start.y-14,'text-anchor':'end',class:'entry-text'},'START',nodeLayer);}
      if(animation){const p=pointFor(recording.path[animation.index]);add('circle',{cx:p.x,cy:p.y,r:7,class:'signal-dot'},undefined,nodeLayer);}
      if(focusedId)svg.querySelector('[data-node="'+focusedId+'"]')?.focus({preventScroll:true});
    }
    function schedule(kind){if(frame!==null)cancelAnimationFrame(frame);frame=requestAnimationFrame(()=>{frame=null;draw();if(typeof kind==='string')notifyNavigation(kind);});}
    viewport.addEventListener('wheel',e=>{e.preventDefault();if(e.ctrlKey||e.metaKey){const r=viewport.getBoundingClientRect();zoomAt(Math.exp(-e.deltaY*.005),e.clientX-r.left,e.clientY-r.top);}else{view.x+=(e.shiftKey?e.deltaY:e.deltaX)/view.zoom;view.y+=(e.shiftKey?0:e.deltaY)/view.zoom;schedule('pan');}},{passive:false});
    viewport.addEventListener('pointerdown',e=>{if(e.target.closest('.switch-node'))return;drag={x:e.clientX,y:e.clientY};viewport.setPointerCapture(e.pointerId);});
    viewport.addEventListener('pointermove',e=>{if(!drag)return;view.x-=(e.clientX-drag.x)/view.zoom;view.y-=(e.clientY-drag.y)/view.zoom;drag={x:e.clientX,y:e.clientY};schedule('pan');});
    viewport.addEventListener('pointerup',()=>{drag=null;});viewport.addEventListener('pointercancel',()=>{drag=null;});
    viewport.addEventListener('keydown',e=>{if(e.target!==viewport)return;const moves={ArrowLeft:[-120,0],ArrowRight:[120,0],ArrowUp:[0,-120],ArrowDown:[0,120]};if(moves[e.key]){e.preventDefault();view.x+=moves[e.key][0]/view.zoom;view.y+=moves[e.key][1]/view.zoom;draw();notifyNavigation('pan');}else if(e.key==='+'||e.key==='='){e.preventDefault();zoomAt(1.25);}else if(e.key==='-'){e.preventDefault();zoomAt(.8);}else if(e.key==='Home'){e.preventDefault();view.x=0;view.y=board.initial*routeHeight;draw();notifyNavigation('start');}});
    const resize=new ResizeObserver(schedule);resize.observe(viewport);
    host._dispose=()=>{resize.disconnect();if(frame!==null)cancelAnimationFrame(frame);if(animation)clearInterval(animation.timer);};
    host.replay=()=>{if(animation)clearInterval(animation.timer);animation={index:0,timer:null};const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;const advance=()=>{if(!host.contains(svg)||animation.index>=recording.path.length){clearInterval(animation.timer);animation=null;draw();return;}const p=pointFor(recording.path[animation.index]);view.x=p.x-viewport.clientWidth/(2*view.zoom);view.y=p.y-viewport.clientHeight/(2*view.zoom);draw();animation.index++;};advance();notifyNavigation('replay');if(!reduced)animation.timer=setInterval(advance,480);else{animation=null;draw();}};
    draw();return {path:recording.path,outputs:recording.outputs,svg};
  }
  return {render,walk,execute,displayExecute};
})();
