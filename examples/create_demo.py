"""Create explicitly synthetic examples in new directories; never overwrite user projects."""
import argparse, hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import paper

def create(root,mode):
    if root.exists():raise ValueError('choose a new destination')
    root.mkdir(parents=True)
    (root/'result.json').write_text('{"value": 2}\n')
    (root/'section.md').write_text('## Synthetic analysis\n\nSynthetic software example, not a real problem or research finding. Computed value: [[value:V1]].\n\n$$\nx=\\frac{4}{2}\n$$\n',encoding='utf-8')
    profile={'font':'Noto Serif CJK SC','font_pt':12,'line_spacing':1.25,'margin_cm':2.5,'min_pages':0,'max_pages':0,'require_page_review':True}
    plan={'schema':paper.SCHEMA,'title':'Synthetic Workflow Example','language':'en','profile':profile,
      'questions':['Q1'],'sections':[{'id':'analysis','path':'section.md','questions':['Q1'],'evidence':['E1']}],
      'evidence':{'E1':{'path':'result.json','sha256':paper.digest(root/'result.json'),'source':'Explicit synthetic arithmetic fixture'}},
      'claims':{'V1':{'evidence':'E1','pointer':'/value','value':2,'format':'.1f'}},'figures':{},'references':{},
      'model_review':'model-review.json','validation_ledger':'validation-ledger.json'}
    paper.write(root/'model-review.json',{'reviewer':'synthetic fixture author','notes':'Checks an arithmetic fixture only, not scientific validity.',
       'relations':[{'id':'R1','given':'4 divided by 2','interpretation':'ordinary arithmetic','choice':'as_given','reason':'definition of division','status':'accepted'}]})
    paper.write(root/'validation-ledger.json',{'checks':[{'id':'full-run','level':'cold_start','status':'not_run','scope':'Synthetic example has no physical solver.'}]})
    if mode=='existing_tex':
        (root/'main.tex').write_text('\\documentclass{article}\n\\begin{document}\n\\section*{Synthetic Workflow Example}\nSynthetic fixture only. $x=4/2=2$.\n\\end{document}\n')
        plan['mode']='existing_tex';plan['native']={'main':'main.tex','inputs':{'main.tex':paper.digest(root/'main.tex'),'result.json':paper.digest(root/'result.json')},
            'command':['xelatex','-no-shell-escape','-interaction=nonstopmode','-halt-on-error','{main}'],'pdf':'main.pdf','passes':2}
    paper.write(root/'paper-plan.json',plan)
    # This is a blank checklist, deliberately unable to pass verify.
    paper.write(root/'visual-review.template.json',{'schema':'mm-visual/v2','status':'NOT_REVIEWED','reviewer':'','notes':'','pdfs':{},'pages':{},'page_reviews':{}})
    return root

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--destination',type=Path,required=True);p.add_argument('--mode',choices=['generated','existing_tex'],default='generated');a=p.parse_args()
    try:print(create(a.destination,a.mode))
    except ValueError as e:p.exit(1,str(e)+'\n')
