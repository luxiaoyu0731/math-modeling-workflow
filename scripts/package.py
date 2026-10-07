#!/usr/bin/env python3
"""Install a complete local skill package or make a deterministic sharing ZIP."""
import argparse
import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ALLOW=('README.en.md','README.md','LICENSE','CHANGELOG.md','VERSION','examples','THIRD_PARTY_NOTICES.md','requirements-documents.txt','docs','prompts','skills','workflow','scripts','tests','.gitignore','.github')
DENY={'__pycache__','runs','state','.git','delivery','dist'}


def sources():
    paths=[]
    for name in ALLOW:
        p=ROOT/name
        for item in ([p] if p.is_file() else sorted(p.rglob('*'))):
            if item.is_symlink():raise ValueError('symlinks cannot be packaged')
            if item.is_file() and not DENY.intersection(item.relative_to(ROOT).parts) and item.suffix!='.pyc':paths.append(item)
    return sorted(set(paths))


def install(target,platform):
    target=target.resolve();tool=target/'.math-modeling'
    dest=target/{'codex':'.agents','claude':'.claude','trae':'.trae'}[platform]/'skills'
    skill_names=[p.name for p in (ROOT/'skills').iterdir() if (p/'SKILL.md').is_file()]
    # Validate all collisions before writing anything; never overwrite existing skills.
    if tool.exists() or any((dest/name).exists() for name in skill_names):raise ValueError('installation already exists or a skill name conflicts; choose a clean target')
    with tempfile.TemporaryDirectory(prefix='mm-install-') as temp:
        tmp=Path(temp)/'runtime';tmp.mkdir()
        for path in sources():
            out=tmp/path.relative_to(ROOT);out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,out)
        target.mkdir(parents=True,exist_ok=True)
        shutil.copytree(tmp,tool)
    for name in skill_names:
        shutil.copytree(ROOT/'skills'/name,dest/name)
        entry=dest/name/'SKILL.md'
        with entry.open('a',encoding='utf-8') as f:
            f.write('\n## Installed runtime\n\nRun project commands from the project root. Complete runtime and shared references are in `.math-modeling/`; invoke `python3 .math-modeling/scripts/paper.py --project <run-directory> doctor` before document work. Do not write task evidence into the installed skill directories.\n')
    return {'installed_skills':skill_names,'runtime':'.math-modeling','platform':platform}


def archive(output):
    if output.exists():raise ValueError('refusing to overwrite archive')
    manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources()}
    output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for p in sources():
            info=zipfile.ZipInfo('math-modeling-workflow/'+str(p.relative_to(ROOT)),date_time=(2020,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o100644<<16;z.writestr(info,p.read_bytes())
        info=zipfile.ZipInfo('math-modeling-workflow/MANIFEST.json',date_time=(2020,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
        z.writestr(info,json.dumps(manifest,sort_keys=True,indent=2)+'\n')
    if __package__:
        from .release_check import scan_zip
    else:
        from release_check import scan_zip
    inspection=scan_zip(output)
    if inspection['status']!='PASS':raise ValueError('archive requires release review; run release_check.py --zip on the retained archive')
    return {'files':len(manifest),'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'release_scan':inspection['status']}


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('install');a.add_argument('--target',type=Path,required=True);a.add_argument('--platform',choices=['codex','claude','trae'],required=True)
    a=sub.add_parser('archive');a.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    try:result=install(args.target,args.platform) if args.cmd=='install' else archive(args.output)
    except (ValueError,OSError) as e:p.exit(1,str(e)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
