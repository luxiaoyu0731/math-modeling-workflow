"""Integration smoke test using synthetic prose, never a paper-quality claim."""
import argparse
import sys
import tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from test_delivery import fixture
import paper
p=argparse.ArgumentParser();p.add_argument('--format',choices=['docx','latex'],default='docx');p.add_argument('--engine');p.add_argument('--output',type=Path);args=p.parse_args()
with tempfile.TemporaryDirectory() as temp:
    root=args.output or Path(temp)
    fixture(root)
    paper.build(root,[args.format])
    result=paper.render(root,args.format,args.engine)
    assert result['pages']>0
    verdict=paper.verify(root)
    assert verdict['status']=='FAIL' and any('visual review missing' in x for x in verdict['errors'])
    print('PASS: actual PDF rendered; absent visual review correctly blocks delivery')
