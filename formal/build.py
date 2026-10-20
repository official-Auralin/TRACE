"""Clean Lean kernel build and complete named-theorem axiom inventory."""
from pathlib import Path
import hashlib,json,os,re,shutil,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
FORMAL=ROOT/'formal'
BUILD=FORMAL/'.build'
MODULES=[('vendor/TraceReview.lean','TraceReview','vendor'),('vendor/Mealy.lean','Mealy','vendor')]+[
    ('Trace2/'+name+'.lean','Trace2.'+name,'.')
    for name in ('Semantics','Deletion','Layered','Binding','Game','Certificates',
                 'Compiler','QueryLookup','Runtime','CompilerRuntime')]

def main():
    start=time.time()
    configured=os.environ.get('LEAN_BIN')
    compiler=Path(configured)/'lean' if configured else Path('/private/tmp/lean-4.24.0-darwin_aarch64/bin/lean')
    if not compiler.is_file():
        found=shutil.which('lean')
        if not found:raise SystemExit('Lean 4.24.0 unavailable; install the pinned toolchain or set LEAN_BIN. No proof check was skipped.')
        compiler=Path(found)
    version=subprocess.check_output([str(compiler),'--version'],cwd=ROOT,text=True).strip()
    if 'version 4.24.0,' not in version:raise SystemExit('Wrong Lean version: '+version)
    if BUILD.is_symlink():raise SystemExit('Refusing to replace a symlink at formal/.build')
    if BUILD.exists():shutil.rmtree(BUILD)
    (BUILD/'Trace2').mkdir(parents=True)
    env=dict(os.environ,LEAN_PATH=str(BUILD))
    source_hashes={};theorems=[];logs=[];c_sources=[]
    for relative,module,root in MODULES:
        source=FORMAL/relative;text=source.read_text()
        if re.search(r'\b(sorry|admit|axiom|native_decide)\b',text):
            raise SystemExit('Forbidden proof admission/custom axiom/compiler-trust tactic in '+relative)
        source_hashes[relative]=hashlib.sha256(source.read_bytes()).hexdigest()
        target=BUILD/(module.replace('.','/')+'.olean')
        c_target=target.with_suffix('.c');c_sources.append(c_target)
        command=[str(compiler),'-DwarningAsError=true','--root='+str(FORMAL/root),'-o',str(target),'-c',str(c_target),str(source)]
        p=subprocess.run(command,cwd=ROOT,env=env,text=True,capture_output=True)
        logs.append(p.stdout+p.stderr)
        if p.returncode:
            print(p.stdout+p.stderr,file=sys.stderr);raise SystemExit(p.returncode)
        namespace='TraceReview' if root=='vendor' else ('Trace2.Runtime' if module in ('Trace2.Runtime','Trace2.QueryLookup') else 'Trace2')
        theorems.extend(namespace+'.'+name for name in re.findall(r'^theorem\s+([A-Za-z0-9_]+)',text,re.M))
        print('Checked '+module,flush=True)
    binaries={}
    for cli_name,executable in [('CheckCertificates','trace-check'),('CompileLevel','trace-compile')]:
        cli=FORMAL/(cli_name+'.lean');cli_c=BUILD/(cli_name+'.c')
        source_hashes[cli.name]=hashlib.sha256(cli.read_bytes()).hexdigest()
        p=subprocess.run([str(compiler),'-DwarningAsError=true','--root='+str(FORMAL),'-c',str(cli_c),str(cli)],cwd=ROOT,env=env,text=True,capture_output=True)
        if p.returncode:
            print(p.stdout+p.stderr,file=sys.stderr);raise SystemExit(p.returncode)
        binary=BUILD/executable
        p=subprocess.run([str(compiler.with_name('leanc')),'-O2','-o',str(binary),str(cli_c),
            *map(str,c_sources)],cwd=ROOT,env=env,text=True,capture_output=True)
        if p.returncode:
            print(p.stdout+p.stderr,file=sys.stderr);raise SystemExit(p.returncode)
        binaries[executable]=hashlib.sha256(binary.read_bytes()).hexdigest()
    audit=BUILD/'AxiomAudit.lean'
    audit.write_text('\n'.join('import '+m for _,m,_ in MODULES)+'\n\n'+
      '\n'.join('#print axioms '+name for name in theorems)+'\n')
    p=subprocess.run([str(compiler),'-DwarningAsError=true','--root='+str(BUILD),str(audit)],cwd=ROOT,env=env,text=True,capture_output=True)
    (BUILD/'axiom-report.txt').write_text(p.stdout+p.stderr)
    if p.returncode or re.search(r'sorryAx|Lean\.ofReduceBool|Lean\.trustCompiler',p.stdout+p.stderr):
        print(p.stdout+p.stderr,file=sys.stderr);raise SystemExit('Axiom audit failed')
    dependencies=set()
    for dependency_list in re.findall(r'depends on axioms: \[(.*?)\]',p.stdout):
        dependencies.update(x.strip() for x in dependency_list.split(',') if x.strip())
    if not dependencies <= {'propext','Classical.choice','Quot.sound'}:
        raise SystemExit('Unexpected axiom dependencies: '+repr(sorted(dependencies)))
    audited=p.stdout.count('depends on axioms')+p.stdout.count('does not depend on any axioms')
    if audited!=len(theorems):raise SystemExit('The theorem inventory and printed dependency inventory disagree')
    result={'status':'PASS','clean_build':True,'lean_version':version,'compiler_sha256':hashlib.sha256(compiler.read_bytes()).hexdigest(),
      'axiom_dependencies':sorted(dependencies),'modules':len(MODULES),'named_theorems':len(theorems),'new_trace2_theorems':sum(n.startswith('Trace2.') for n in theorems),
      'source_sha256':source_hashes,'executable_sha256':binaries,'axiom_report_sha256':hashlib.sha256((BUILD/'axiom-report.txt').read_bytes()).hexdigest(),
      'elapsed_seconds':time.time()-start,
      'scope':'Finite G/P semantics, inclusion-minimal deletion, complete Boolean alphabet, local recurrence checking, sparse checked-query binding and coverage, finite verification game, general executable Mealy-to-switch-tree construction and equality reduction, all-round output and semantic-state preservation, output-only terminal display projection and target/minimal-explanation preservation. JSON decoding/serialization, executable runtime, Python, browser, and full synthesis-strategy N2 remain outside the kernel proof.'}
    (FORMAL/'proof_checks.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,sort_keys=True))
if __name__=='__main__':main()
