// Runtime smoke test for the mode pages: executes each page's script in a DOM
// stub, loads EVERY level, and asserts the recording strip and bench both
// rendered non-empty SVG. Catches render-path crashes that semantic
// verification cannot (the pass-node regression class).
const fs=require("fs");
function freshDom(){
  const elements={};
  function el(id){if(!elements[id])elements[id]={id,_html:"",style:{},
    classList:{add(){},remove(){}},setAttribute(){},appendChild(){},onclick:null,
    get innerHTML(){return this._html},set innerHTML(v){this._html=v},
    get textContent(){return this._t||""},set textContent(v){this._t=v},
    set className(v){this._c=v},get className(){return this._c||""}};
    return elements[id];}
  global.document={getElementById:el,querySelectorAll:()=>[],
    createElementNS:()=>el("ns"+Math.random())};
  return el;
}
let fail=0;
const pages=["stop","pin","credit"];
for(const m of ["auto_stop","auto_pin","auto_credit"])
  if(fs.existsSync(`${__dirname}/../../TRACE_${m}.html`))pages.push(m);
for(const m of pages){
  const el=freshDom();
  const html=fs.readFileSync(`${__dirname}/../../TRACE_${m}.html`,"utf8");
  const js=html.match(/<script>([\s\S]*)<\/script>/)[1];
  try{
    const run=new Function("document",js+"\n;return {load,LEVELS};");
    const {load,LEVELS}=run(global.document);
    for(let i=0;i<LEVELS.length;i++){
      load(i);
      const rec=el("recwrap")._html, bench=el("svgwrap")._html;
      const ok=rec.includes("<svg")&&bench.includes("<svg")&&bench.includes("bulb");
      console.log(`${m} level ${LEVELS[i].name}: render ${ok?"OK":"EMPTY"} (rec ${rec.length}b, bench ${bench.length}b)`);
      if(!ok)fail++;
    }
  }catch(e){console.log(`${m}: RUNTIME ERROR`,e.message);fail++;}
}
console.log(fail?`SMOKE FAIL (${fail})`:"SMOKE PASS: every level of every mode renders");
process.exit(fail?1:0);
