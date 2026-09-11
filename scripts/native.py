"""Existing TeX projects: declared inputs, isolated build, unchanged authoring sources."""
from pathlib import Path
import json, math, shutil, subprocess, tempfile

def audit(root,plan,path,api):
    errors=[];paths=[path];native=plan.get('native',{})
    if plan.get('schema')!=api.SCHEMA:errors.append('unsupported authoring schema')
    if not plan.get('title'):errors.append('title missing')
    inputs=native.get('inputs',{})
    if not inputs or native.get('main') not in inputs:errors.append('native main must be a declared input')
    for name,sha in inputs.items():
        p=api.local(root,name)
        if name.startswith('delivery/'):errors.append('native inputs must not be generated delivery files')
        if not p.is_file():errors.append('missing native input: '+name);continue
        paths.append(p)
        if not sha or api.digest(p)!=sha:errors.append('native input hash mismatch: '+name)
    if not plan.get('model_review'):errors.append('existing project needs model_review')
    if not plan.get('validation_ledger'):errors.append('existing project needs validation_ledger')
    command=native.get('command')
    if not isinstance(command,list) or not command or not all(isinstance(x,str) and x for x in command):errors.append('native command must be an argv list')
    if native.get('pdf'):
        api.local(root,native['pdf'])
        if native['pdf'] in inputs:errors.append('native output cannot also be an input')
    else:errors.append('native output PDF missing')
    if type(native.get('passes',2))!=int or not 1<=native.get('passes',2)<=5:errors.append('native passes must be 1..5')
    for k in ('font_pt','line_spacing','margin_cm'):
        if type(plan.get('profile',{}).get(k)) not in (int,float) or not math.isfinite(plan['profile'][k]) or plan['profile'][k]<=0:errors.append('invalid profile: '+k)
    profile=plan.get('profile',{})
    if profile.get('max_pages',0) and profile.get('min_pages',0)>profile['max_pages']:errors.append('conflicting page limits')
    extra,more=api.contracts.audit_contracts(root,plan,api.local,api.digest);errors+=extra;paths+=more
    return {'schema':'mm-authoring-audit/v1','status':'FAIL' if errors else 'PASS','errors':errors,
        'warnings':['Native TeX prose, unregistered values and citations require human review.'],
        'inputs':api.snapshot(root,[p for p in paths if p.is_file()]),'body_chars':None,
        'boundary':'Declared-file freshness and review records do not prove scientific correctness.'}

def compile_pdf(root,plan,destination,engine=None):
    native=plan['native'];logs=[]
    with tempfile.TemporaryDirectory(prefix='mm-native-') as td:
        temp=Path(td)
        for name in native['inputs']:
            target=temp/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/name,target)
        command=[x.replace('{main}',native['main']) for x in native['command']]
        if engine:command[0]=engine
        for _ in range(native.get('passes',2)):
            p=subprocess.run(command,cwd=temp,capture_output=True,text=True,timeout=180)
            logs.append(p.stdout+'\n'+p.stderr)
            if p.returncode:raise ValueError('native build failed: '+logs[-1][-3000:])
        pdf=temp/native['pdf']
        if not pdf.is_file() or not pdf.read_bytes().startswith(b'%PDF-'):raise ValueError('native build produced no PDF')
        shutil.copy2(pdf,destination)
    return '\n'.join(logs)
