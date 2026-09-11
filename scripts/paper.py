#!/usr/bin/env python3
"""Evidence-bound authoring, deterministic assembly and document delivery.

Core auditing uses only the standard library. Document dependencies are lazy.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = 'mm-authoring/v1'
if __package__:
    from . import contracts, native
else:
    import contracts, native


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    tmp.replace(path)


def local(root, relative):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError('path must be nonempty and relative to the project')
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('path escapes project: '+relative)
    return path


def snapshot(root, paths):
    return {str(p.relative_to(root)): digest(p) for p in sorted(set(paths))}


def current(root, hashes):
    errors=[]
    for name, expected in hashes.items():
        p=local(root,name)
        if not p.is_file() or digest(p)!=expected:errors.append('changed or missing: '+name)
    return errors


def doctor():
    modules={name:importlib.util.find_spec(name) is not None for name in ('docx','pypdf','pypdfium2','latex2mathml','lxml')}
    binaries={name:shutil.which(name) for name in ('soffice','xelatex','pdftoppm')}
    return {'python':sys.version.split()[0], 'modules':modules, 'tools':binaries,
            'imagegen':'Use the connected image tool; this CLI does not authenticate or call a service.',
            'installs_performed':False}


def init(root):
    root.mkdir(parents=True,exist_ok=True)
    path=root/'paper-plan.json'
    if path.exists():raise ValueError('refusing to overwrite paper-plan.json')
    write(path,{'schema':SCHEMA,'title':'','language':'zh','profile':{'font':'','font_pt':12,'line_spacing':1.25,'margin_cm':2.5,'min_body_chars':0,'min_pages':0,'max_pages':0,'require_page_review':True},
                'questions':[], 'sections':[], 'evidence':{}, 'claims':{}, 'figures':{}, 'references':{},
                'notes':'Fill from the actual task. Zero page/length limits mean unspecified. No sample results are evidence.'})
    return {'created':'paper-plan.json'}


def audit(root, plan_path='paper-plan.json'):
    """Recompute from inputs. Saved PASS reports are never authoritative."""
    root=root.resolve(); path=local(root,plan_path); plan=read(path)
    errors=[];warnings=[];paths=[path];texts=[];used_figures=set();used_claims=set();used_refs=set()
    if not isinstance(plan,dict):raise ValueError('plan must be an object')
    if plan.get('mode') not in (None,'generated','existing_tex'):raise ValueError('unsupported authoring mode')
    if plan.get('mode')=='existing_tex':
        return native.audit(root,plan,path,sys.modules[__name__])
    def require_file(name,sha=None):
        p=local(root,name)
        if not p.is_file():errors.append('missing file: '+name);return None
        paths.append(p)
        if sha is not None and digest(p)!=sha:errors.append('hash mismatch: '+name)
        return p
    if plan.get('schema')!=SCHEMA:errors.append('unsupported authoring schema')
    if not plan.get('title','').strip():errors.append('title missing')
    profile=plan.get('profile',{})
    for name in ('font_pt','line_spacing','margin_cm'):
        v=profile.get(name)
        if not isinstance(v,(int,float)) or isinstance(v,bool) or not math.isfinite(v) or v<=0:errors.append('invalid profile: '+name)
    if profile.get('max_pages',0) and profile.get('min_pages',0)>profile['max_pages']:errors.append('conflicting page limits')
    evidence=plan.get('evidence',{})
    for eid,item in evidence.items():
        if not item.get('sha256'):errors.append('missing evidence hash: '+eid)
        require_file(item['path'],item.get('sha256'))
        if not item.get('source'):errors.append('missing provenance: '+eid)
    for cid,claim in plan.get('claims',{}).items():
        item=evidence.get(claim.get('evidence'))
        if item is None:errors.append('unknown claim evidence: '+cid);continue
        p=require_file(item['path'],item.get('sha256'))
        if not p:continue
        value=read(p)
        try:
            pointer=claim['pointer']
            if not isinstance(pointer,str) or (pointer and not pointer.startswith('/')):raise ValueError('invalid JSON pointer')
            for part in (pointer.split('/')[1:] if pointer else []):
                value=value[int(part)] if isinstance(value,list) else value[part.replace('~1','/').replace('~0','~')]
        except (KeyError,IndexError,ValueError,TypeError):errors.append('invalid claim pointer: '+cid);continue
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):errors.append('nonfinite or nonnumeric claim: '+cid)
        elif value!=claim.get('value'):errors.append('claim value differs from data: '+cid)
        try:format(value,claim.get('format','.6g'))
        except (ValueError,TypeError):errors.append('invalid claim format: '+cid)
    seen=set();covered=set();body_chars=0
    for section in plan.get('sections',[]):
        sid=section['id']
        if sid in seen:errors.append('duplicate section id: '+sid)
        seen.add(sid); covered.update(section.get('questions',[]))
        p=require_file(section['path'])
        if not p:continue
        text=p.read_text(encoding='utf-8');texts.append((sid,text))
        if not text.strip():errors.append('empty section: '+sid)
        for marker in re.findall(r'\[\[([^]]+)\]\]',text):
            if not re.fullmatch(r'(?:value|figure|cite):[\w-]+',marker):errors.append('unsupported marker: '+marker)
        if re.search(r'\bTODO\b|\bTBD\b|待填写|内容生成中',text):errors.append('placeholder: '+sid)
        if re.search(r'workflow/runs/|paper_output/|本轮修改|初稿中|第二版中',text):warnings.append('possible internal process wording: '+sid)
        # Exclude code, comments and appendices from optional length checks.
        prose=re.sub(r'```.*?```|<!--.*?-->','',text,flags=re.S)
        if section.get('role','body')=='body':body_chars+=len(re.sub(r'\s','',prose))
        for eid in section.get('evidence',[]):
            if eid not in evidence:errors.append('unknown section evidence: '+eid)
        for line in text.splitlines():
            if '[[figure:' in line and not re.fullmatch(r'\s*\[\[figure:[\w-]+\]\]\s*',line):errors.append('figure marker must occupy a separate line: '+sid)
        used_figures.update(re.findall(r'\[\[figure:([\w-]+)\]\]',text))
        used_claims.update(re.findall(r'\[\[value:([\w-]+)\]\]',text))
        used_refs.update(re.findall(r'\[\[cite:([\w-]+)\]\]',text))
        # Direct images bypass the figure ledger, therefore they are not admitted.
        if re.search(r'!\[[^\]]*\]\(',text):errors.append('use figure ledger instead of direct Markdown image: '+sid)
        paragraphs=[re.sub(r'\s+','',x) for x in prose.split('\n\n') if len(x.strip())>=100]
        if len(paragraphs)!=len(set(paragraphs)):errors.append('duplicate paragraph: '+sid)
    if not seen:errors.append('no sections')
    for q in plan.get('questions',[]):
        if q not in covered:errors.append('unanswered question: '+q)
    if body_chars<profile.get('min_body_chars',0):errors.append('body shorter than the declared requirement')
    for cid in used_claims:
        if cid not in plan.get('claims',{}):errors.append('unknown value marker: '+cid)
    for rid in used_refs:
        ref=plan.get('references',{}).get(rid)
        if not ref or not ref.get('text') or not ref.get('source'):errors.append('unresolved citation: '+rid)
    for fid in used_figures:
        fig=plan.get('figures',{}).get(fid)
        if not fig:errors.append('unresolved figure: '+fid);continue
        if fig.get('review')!='passed' or not fig.get('review_note'):errors.append('figure review missing: '+fid)
        if not fig.get('caption') or not fig.get('sha256'):errors.append('figure caption/hash missing: '+fid)
        require_file(fig['path'],fig.get('sha256'))
        if fig.get('kind')=='imagegen':
            for key in ('prompt_path','raw_path'):
                if not fig.get(key) or not fig.get(key+'_sha256'):errors.append('imagegen record missing: '+fid+'/'+key)
                else:require_file(fig[key],fig[key+'_sha256'])
            if not fig.get('tool') or not fig.get('generated_at'):errors.append('imagegen call metadata missing: '+fid)
        elif fig.get('kind')=='quantitative':
            for key in ('data_evidence','code_evidence'):
                if fig.get(key) not in evidence:errors.append('quantitative figure provenance missing: '+fid+'/'+key)
        else:errors.append('unsupported figure kind: '+fid)
    # Exact cross-section duplicates are actionable; semantic repetition still needs a reader.
    paragraphs={}
    for sid,text in texts:
        for para in text.split('\n\n'):
            norm=re.sub(r'\s+','',para)
            if len(norm)>=100:
                if norm in paragraphs and paragraphs[norm]!=sid:errors.append('duplicate prose across sections: '+sid)
                paragraphs[norm]=sid
    extra,more=contracts.audit_contracts(root,plan,local,digest);errors+=extra;paths+=more
    return {'schema':'mm-authoring-audit/v1','status':'FAIL' if errors else 'PASS',
            'errors':errors,'warnings':warnings,'body_chars':body_chars,'inputs':snapshot(root,paths),
            'boundary':'Mechanical coverage and provenance checks do not certify mathematical correctness or human review.'}


def assemble(root, plan):
    refs=list(plan.get('references',{}));figs=list(plan.get('figures',{}))
    parts=['# '+plan['title']]
    for section in plan['sections']:
        text=local(root,section['path']).read_text(encoding='utf-8')
        def value(m):
            item=plan['claims'][m[1]]
            return format(item['value'],item.get('format','.6g'))+item.get('unit','')
        text=re.sub(r'\[\[value:([\w-]+)\]\]',value,text)
        text=re.sub(r'\[\[cite:([\w-]+)\]\]',lambda m:'['+str(refs.index(m[1])+1)+']',text)
        def figure(m):
            item=plan['figures'][m[1]]
            return f"![{item['caption']}]({item['path']})"
        text=re.sub(r'\[\[figure:([\w-]+)\]\]',figure,text)
        parts.append(text.strip())
    used=set(re.findall(r'\[\[cite:([\w-]+)\]\]','\n'.join(local(root,s['path']).read_text() for s in plan['sections'])))
    if used:parts.append('## '+('参考文献' if plan.get('language')=='zh' else 'References')+'\n\n'+'\n\n'.join(f'[{refs.index(r)+1}] '+plan['references'][r]['text'] for r in refs if r in used))
    return '\n\n'.join(parts)+'\n'


def build(root, formats):
    report=audit(root)
    if report['status']!='PASS':raise ValueError('; '.join(report['errors']))
    plan=read(root/'paper-plan.json'); is_native=plan.get('mode')=='existing_tex'
    if is_native and formats!=['latex']:raise ValueError('existing_tex supports latex only')
    text=json.dumps(plan['native'],ensure_ascii=False,indent=2) if is_native else assemble(root,plan)
    out=root/'delivery';out.mkdir(exist_ok=True)
    assembled=out/('native-inputs.json' if is_native else 'paper.md')
    assembled.write_text(text,encoding='utf-8')
    outputs=[assembled];details={}
    # All assets are resolved against root, regardless of the output directory.
    for fmt in ([] if is_native else formats):
        if fmt=='docx':
            if __package__:
                from .documents import make_docx
            else:
                from documents import make_docx
            details['docx']=make_docx(root,text,plan['profile'],out/'paper.docx');outputs.append(out/'paper.docx')
        elif fmt=='latex':
            if __package__:
                from .documents import make_tex
            else:
                from documents import make_tex
            make_tex(root,text,plan['profile'],out/'paper.tex',plan.get('language','zh'));outputs.append(out/'paper.tex')
        else:raise ValueError('unknown format: '+fmt)
    # Record the exact code responsible for the build, including vendored formula conversion.
    tool_hashes={str(p.relative_to(ROOT)):digest(p) for p in (ROOT/'scripts').rglob('*.py')}
    result={'schema':'mm-build/v1','status':'BUILT_REVIEW_REQUIRED','plan':'paper-plan.json','inputs':report['inputs'],
            'outputs':snapshot(root,outputs),'tools':tool_hashes,'formats':formats,'details':details}
    write(out/'build.json',result)
    write(out/'authoring-audit.json',report)
    return result


def render(root,fmt,engine=None):
    build_path=root/'delivery/build.json';build_record=read(build_path)
    errors=current(root,build_record['inputs'])+current(root,build_record['outputs'])+current(ROOT,build_record['tools'])
    if errors:raise ValueError('; '.join(errors))
    plan=read(root/'paper-plan.json')
    if plan.get('mode')=='existing_tex':
        if fmt!='latex':raise ValueError('existing_tex supports latex only')
        output=root/'delivery/paper-latex.pdf'
        log=native.compile_pdf(root,plan,output,engine)
        from pypdf import PdfReader
        n=len(PdfReader(output).pages)
        (root/'delivery/render-latex.log').write_text(log,encoding='utf-8')
        result={'schema':'mm-render/v1','status':'RENDERED_REVIEW_REQUIRED','build_sha256':digest(build_path),'pdf':'delivery/paper-latex.pdf','pdf_sha256':digest(output),'pages':n,'format':'latex'}
        write(root/'delivery/render-latex.json',result)
        return result
    source=root/'delivery'/('paper.docx' if fmt=='docx' else 'paper.tex')
    if str(source.relative_to(root)) not in build_record['outputs']:raise ValueError('format was not built')
    binary=engine or shutil.which('soffice' if fmt=='docx' else 'xelatex')
    if not binary:raise ValueError('render tool not available')
    # Fresh build directories prevent an old PDF from satisfying a failed new run.
    with tempfile.TemporaryDirectory(prefix='mm-render-') as temp:
        tmp=Path(temp)
        if fmt=='docx':
            command=[binary,'-env:UserInstallation='+(tmp/'profile').as_uri(),'--headless','--convert-to','pdf','--outdir',str(tmp),str(source)]
            calls=[command]
        else:
            command=[binary,'-no-shell-escape','-interaction=nonstopmode','-halt-on-error','-output-directory='+str(tmp),str(source)]
            calls=[command,command]
        log=[]
        for command in calls:
            proc=subprocess.run(command,cwd=root,capture_output=True,text=True,timeout=180)
            log.append(proc.stdout+'\n'+proc.stderr)
            if proc.returncode:raise ValueError('render failed: '+log[-1][-3000:])
        pdf=tmp/'paper.pdf'
        if not pdf.is_file() or not pdf.read_bytes().startswith(b'%PDF-'):raise ValueError('renderer did not produce a PDF')
        from pypdf import PdfReader
        reader=PdfReader(pdf)
        if not reader.pages or not any((p.extract_text() or '').strip() for p in reader.pages):raise ValueError('PDF has no extractable content')
        output=root/'delivery'/('paper-'+fmt+'.pdf');shutil.copy2(pdf,output)
        logpath=root/'delivery'/('render-'+fmt+'.log');logpath.write_text('\n'.join(log),encoding='utf-8')
    result={'schema':'mm-render/v1','status':'RENDERED_REVIEW_REQUIRED','build_sha256':digest(build_path),
            'pdf':str(output.relative_to(root)),'pdf_sha256':digest(output),'pages':len(reader.pages),'format':fmt}
    write(root/'delivery'/('render-'+fmt+'.json'),result)
    return result


def verify(root):
    record=read(root/'delivery/build.json');errors=[]
    if record.get('schema')!='mm-build/v1' or not record.get('formats') or not record.get('inputs') or not record.get('outputs') or not record.get('tools'):
        raise ValueError('invalid or incomplete build contract')
    errors+=current(root,record['inputs'])+current(root,record['outputs'])+current(ROOT,record['tools'])
    fresh=audit(root); errors+=fresh['errors']
    profile=read(root/'paper-plan.json')['profile'];pdfs={};pages={}
    for fmt in record['formats']:
        path=root/'delivery'/('render-'+fmt+'.json')
        if not path.is_file():errors.append('render missing: '+fmt);continue
        r=read(path)
        if r.get('build_sha256')!=digest(root/'delivery/build.json'):errors.append('stale rendering: '+fmt)
        pdf=local(root,r['pdf'])
        if not pdf.is_file() or digest(pdf)!=r.get('pdf_sha256'):errors.append('changed PDF: '+fmt);continue
        from pypdf import PdfReader
        reader=PdfReader(pdf); n=len(reader.pages);pages[fmt]=n
        if not n or not any((p.extract_text() or '').strip() for p in reader.pages):errors.append('empty PDF: '+fmt)
        if profile.get('min_pages',0)>n:errors.append('below declared total-page minimum: '+fmt)
        if profile.get('max_pages',0) and n>profile['max_pages']:errors.append('above declared total-page maximum: '+fmt)
        extracted=''.join(p.extract_text() or '' for p in reader.pages)
        try:
            import pypdfium2 as pdfium
            with pdfium.PdfDocument(pdf) as doc:
                extracted=''.join(page.get_textpage().get_text_range() for page in doc)
        except ImportError:
            pass
        title=read(root/'paper-plan.json')['title']
        compact=lambda s:re.sub(r'\s+','',s)
        if compact(title) not in compact(extracted):errors.append('PDF title text mismatch or extraction failure: '+fmt)
        pdfs[r['pdf']]=digest(pdf)
    review=root/'delivery/visual-review.json'
    if not review.is_file():errors.append('visual review missing; inspect actual pages before recording it')
    else:
        rv=read(review)
        if rv.get('status')!='PASS' or not rv.get('reviewer') or not rv.get('notes'):errors.append('visual review incomplete')
        if rv.get('pdfs')!=pdfs:errors.append('visual review is stale or incomplete')
        if rv.get('pages')!=pages:errors.append('visual review does not cover all rendered pages')
        errors+=contracts.page_review(profile,rv,pages)
    return {'schema':'mm-delivery/v1','status':'FAIL' if errors else 'PASS','errors':errors,'pages':pages,
            'inputs':fresh['inputs'],'outputs':pdfs,
            'boundary':'PASS is a file/coverage check plus a recorded visual review, not proof of scientific correctness.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',type=Path,default=Path.cwd())
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('doctor');sub.add_parser('init');sub.add_parser('audit');sub.add_parser('verify')
    b=sub.add_parser('build');b.add_argument('--formats',nargs='+',choices=['docx','latex'],default=['docx'])
    r=sub.add_parser('render');r.add_argument('--format',choices=['docx','latex'],required=True);r.add_argument('--engine')
    args=parser.parse_args();root=args.project.resolve()
    try:
        if args.command=='doctor':result=doctor()
        elif args.command=='init':result=init(root)
        elif args.command=='audit':result=audit(root)
        elif args.command=='build':result=build(root,args.formats)
        elif args.command=='render':result=render(root,args.format,args.engine)
        else:result=verify(root)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 1 if result.get('status')=='FAIL' else 0
    except (ValueError,KeyError,TypeError,OSError,ImportError,subprocess.TimeoutExpired) as exc:
        print(json.dumps({'status':'FAIL','error':str(exc)},ensure_ascii=False),file=sys.stderr);return 1

if __name__=='__main__':raise SystemExit(main())
