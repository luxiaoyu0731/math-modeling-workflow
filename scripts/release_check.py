"""Read-only scans of actual ZIP bytes or Git content; never prints matched secrets."""
import argparse, hashlib, json, posixpath, re, stat, subprocess, zipfile
from urllib.parse import unquote
from pathlib import Path, PurePosixPath

RULES={
    'personal_path': re.compile(r'(?:/(?:Users|home)/[A-Za-z0-9_.-]+/|[A-Za-z]:\\Users\\[^\\\s]+\\)'),
    'private_key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'credential': re.compile(r'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|sk-[A-Za-z0-9_-]{30,}|AKIA[0-9A-Z]{16})'),
}
TEXT={'.md','.txt','.py','.json','.csv','.tsv','.tex','.yml','.yaml','.toml','.xml','.svg','.mjs','.js','.bib','.sty','.cls','.ini','.cfg'}
MAX=64*1024*1024

def inspect(name,data,terms=()):
    findings=[];manual=[]
    p=PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts or '\\' in name:findings.append({'file':name,'rule':'unsafe_path'})
    if any(x in p.parts for x in ('.git','private','node_modules','__pycache__')) or p.name in ('.env','id_rsa','id_ed25519'):
        findings.append({'file':name,'rule':'private_or_runtime_file'})
    for term in terms:
        if term and term in name:findings.append({'file':name,'rule':'excluded_task_term'})
    if p.suffix=='.zip':manual.append({'file':name,'reason':'nested archive requires separate scan'});return findings,manual
    if len(data)>MAX:findings.append({'file':name,'rule':'oversized_unscanned_file'});return findings,manual
    try:text=data.decode('utf-8')
    except UnicodeDecodeError:manual.append({'file':name,'reason':'binary content requires inspection'});return findings,manual
    for rule,pattern in RULES.items():
        for match in pattern.finditer(text):findings.append({'file':name,'line':text.count('\n',0,match.start())+1,'rule':rule})
    for term in terms:
        if term and term in text:findings.append({'file':name,'rule':'excluded_task_term'})
    return findings,manual


def summarize(items,terms=()):
    items=list(items)
    findings=[];manual=[];hashes={}
    for name,data in items:
        a,b=inspect(name,data,terms);findings+=a;manual+=b;hashes[name]=hashlib.sha256(data).hexdigest()
    reviews={}
    for name,data in items:
        if PurePosixPath(name).name!='asset-review.json':continue
        try:record=json.loads(data)
        except (ValueError,UnicodeDecodeError):continue
        if not isinstance(record,dict) or record.get('schema')!='mm-public-assets/v1' or not record.get('reviewer') or not record.get('reviewed_at'):continue
        if not isinstance(record.get('assets'),dict):continue
        for relative,review in record['assets'].items():
            if not isinstance(review,dict):continue
            target=posixpath.normpath(posixpath.join(posixpath.dirname(name),relative))
            if review.get('status')=='passed' and review.get('notes') and review.get('sha256')==hashes.get(target):reviews[target]=name
    manual=[m for m in manual if not (m['reason']=='binary content requires inspection' and m['file'] in reviews)]
    return {'reviewed_assets':reviews,'status':'FAIL' if findings else ('REVIEW_REQUIRED' if manual else 'PASS'),
            'findings':findings,'manual_review':manual,'files':hashes,
            'boundary':'Pattern coverage only; review task material, copyright and Git author metadata separately. No secret excerpts are emitted.'}


def scan_zip(path,terms=()):
    items=[];extra=[]
    with zipfile.ZipFile(path) as z:
        names=z.namelist()
        if len(names)!=len(set(names)):extra.append({'file':path.name,'rule':'duplicate_archive_entries'})
        if sum(i.file_size for i in z.infolist())>MAX*4:raise ValueError('archive expanded size exceeds inspection limit')
        for entry in z.infolist():
            if entry.is_dir():continue
            if stat.S_ISLNK(entry.external_attr>>16):extra.append({'file':entry.filename,'rule':'archive_symlink'})
            if entry.file_size>MAX:raise ValueError('archive member exceeds inspection limit')
            items.append((entry.filename,z.read(entry)))
    result=summarize(items,terms)
    available={name for name,data in items}
    directories={str(parent) for name in available for parent in PurePosixPath(name).parents}
    for name,data in items:
        if not name.endswith('.md'):continue
        for target in re.findall(r'\]\(([^)]+)\)',data.decode('utf-8',errors='replace')):
            target=target.strip().strip('<>').split('#',1)[0]
            if not target or re.match(r'^[A-Za-z][A-Za-z0-9+.-]*:',target):continue
            resolved=posixpath.normpath(posixpath.join(posixpath.dirname(name),unquote(target)))
            if resolved not in available and resolved not in directories:extra.append({'file':name,'rule':'missing_local_link'})
    # Package manifests bind the exact entry set as well as bytes.
    for name,data in items:
        if PurePosixPath(name).name=='MANIFEST.json':
            base=name[:-len('MANIFEST.json')];manifest=json.loads(data)
            actual={n[len(base):]:hashlib.sha256(d).hexdigest() for n,d in items if n.startswith(base) and n!=name}
            if actual!=manifest or any(not n.startswith(base) for n,d in items):extra.append({'file':name,'rule':'manifest_mismatch'})
    result['findings']+=extra
    if extra:result['status']='FAIL'
    result['archive_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def git(root,*args):
    return subprocess.check_output(['git','-C',str(root),*args])


def scan_git(root,mode,terms=()):
    items=[]
    if mode=='history':
        ids=set()
        for commit in git(root,'rev-list','--all').decode().splitlines():
            for entry in git(root,'ls-tree','-rz',commit).split(b'\0'):
                if not entry:continue
                meta,name=entry.split(b'\t',1);perm,kind,oid=meta.split()
                if kind!=b'blob' or (oid,name) in ids:continue
                ids.add((oid,name));label=commit[:12]+'/'+name.decode('utf-8')
                if perm==b'120000':items.append((label,b'archive_symlink'))
                else:items.append((label,git(root,'cat-file','blob',oid.decode())))
        result=summarize(items,terms)
        # Symlink targets alone cannot establish archive portability.
        for name,data in items:
            if data==b'archive_symlink':result['findings'].append({'file':name,'rule':'git_symlink'})
    else:
        entries=git(root,'ls-files','--stage','-z').split(b'\0');links=[]
        for entry in entries:
            if not entry:continue
            meta,name=entry.split(b'\t',1);perm,oid,stage=meta.split();name=name.decode('utf-8')
            if stage!=b'0':raise ValueError('unmerged index')
            if perm==b'120000':links.append({'file':name,'rule':'git_symlink'});continue
            if mode=='index':data=git(root,'cat-file','blob',oid.decode())
            else:
                p=root/name
                if not p.is_file():links.append({'file':name,'rule':'missing_tracked_file'});continue
                if p.is_symlink():links.append({'file':name,'rule':'git_symlink'});continue
                data=p.read_bytes()
            items.append((name,data))
        result=summarize(items,terms);result['findings']+=links
    if result['findings']:result['status']='FAIL'
    result['git_scope']=mode
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--zip',type=Path);g.add_argument('--git',type=Path)
    p.add_argument('--mode',choices=['tracked','index','history'],default='tracked');p.add_argument('--terms',type=Path)
    a=p.parse_args();terms=a.terms.read_text().splitlines() if a.terms else []
    try:r=scan_zip(a.zip,terms) if a.zip else scan_git(a.git,a.mode,terms)
    except (ValueError,OSError,zipfile.BadZipFile,subprocess.CalledProcessError) as e:p.exit(1,str(e)+'\n')
    print(json.dumps(r,ensure_ascii=False,indent=2));return 0 if r['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
