import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import paper
import package
import documents


def fixture(root):
    root.mkdir(parents=True,exist_ok=True)
    (root/'result.json').write_text('{"value": 2}')
    (root/'section.md').write_text('## 合成验证\n\n这是软件验收材料，不是实际题目或论文结论。校验值为 [[value:V1]]。\n\n$$\nx=\\frac{4}{2}\n$$\n\n| 项目 | 内容 |\n| --- | --- |\n| 用途 | 软件验证 |\n',encoding='utf-8')
    plan={'schema':paper.SCHEMA,'title':'合成交付验证','language':'zh',
          'profile':{'font':'Noto Serif CJK SC','font_pt':12,'line_spacing':1.25,'margin_cm':2.5,'min_body_chars':0,'min_pages':0,'max_pages':0},
          'questions':['Q'], 'sections':[{'id':'analysis','path':'section.md','questions':['Q'],'evidence':['E']}],
          'evidence':{'E':{'path':'result.json','sha256':paper.digest(root/'result.json'),'source':'explicit synthetic software fixture'}},
          'claims':{'V1':{'evidence':'E','pointer':'/value','value':2,'format':'.1f'}},'figures':{},'references':{}}
    paper.write(root/'paper-plan.json',plan);return plan


class AuthoringTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.plan=fixture(self.root)
    def tearDown(self):self.tmp.cleanup()
    def save(self):paper.write(self.root/'paper-plan.json',self.plan)
    def test_actual_result_value_substitution(self):
        self.assertEqual(paper.audit(self.root)['status'],'PASS')
        self.assertIn('2.0',paper.assemble(self.root,self.plan))
    def test_changed_data_rejected(self):
        (self.root/'result.json').write_text('{"value":3}')
        self.assertEqual(paper.audit(self.root)['status'],'FAIL')
    def test_wrong_value_rejected_even_when_hash_current(self):
        self.plan['claims']['V1']['value']=4;self.save()
        self.assertIn('claim value differs from data: V1',paper.audit(self.root)['errors'])
    def test_missing_question_coverage(self):
        self.plan['questions'].append('other');self.save()
        self.assertEqual(paper.audit(self.root)['status'],'FAIL')
    def test_no_global_page_floor(self):
        self.assertEqual(paper.audit(self.root)['status'],'PASS')
    def test_unknown_citation_rejected(self):
        with (self.root/'section.md').open('a') as f:f.write('\n[[cite:missing]]\n')
        self.assertEqual(paper.audit(self.root)['status'],'FAIL')
    def test_path_escape_rejected(self):
        with self.assertRaises(ValueError):paper.local(self.root,'../outside')
    def test_symlink_escape_rejected(self):
        with tempfile.TemporaryDirectory() as outside_dir:
            outside=Path(outside_dir)/'outside-file';outside.write_text('synthetic')
            try:(self.root/'escape').symlink_to(outside)
            except OSError as exc:self.skipTest('symlink capability unavailable: '+str(exc))
            with self.assertRaises(ValueError):paper.local(self.root,'escape')
    def test_direct_image_cannot_bypass_ledger(self):
        (self.root/'section.md').write_text('![untracked](fake.png)')
        self.assertEqual(paper.audit(self.root)['status'],'FAIL')
    def test_imagegen_missing_call_record_rejected(self):
        (self.root/'section.md').write_text('[[figure:F]]')
        (self.root/'image.png').write_bytes(b'synthetic-not-an-image')
        self.plan['figures']={'F':{'path':'image.png','sha256':paper.digest(self.root/'image.png'),'kind':'imagegen','caption':'test','review':'passed','review_note':'synthetic test'}};self.save()
        self.assertEqual(paper.audit(self.root)['status'],'FAIL')
    def test_changed_imagegen_raw_asset_invalidates(self):
        (self.root/'section.md').write_text('[[figure:F]]')
        for name in ('image.png','raw.png','prompt.txt'):(self.root/name).write_text('synthetic fixture')
        self.plan['figures']={'F':{'path':'image.png','sha256':paper.digest(self.root/'image.png'),'kind':'imagegen','caption':'test','review':'passed','review_note':'software test only','tool':'synthetic-fixture','generated_at':'test',
             'raw_path':'raw.png','raw_path_sha256':paper.digest(self.root/'raw.png'),'prompt_path':'prompt.txt','prompt_path_sha256':paper.digest(self.root/'prompt.txt')}};self.save()
        self.assertEqual(paper.audit(self.root)['status'],'PASS')
        (self.root/'raw.png').write_text('changed')
        self.assertEqual(paper.audit(self.root)['status'],'FAIL')
    def test_repeat_prose_rejected(self):
        para='本段文字用于检查重复内容是否能够在实际正文里被发现。'*10
        (self.root/'section.md').write_text(para+'\n\n'+para,encoding='utf-8')
        self.assertEqual(paper.audit(self.root)['status'],'FAIL')
    def test_tex_build_and_staleness(self):
        r=paper.build(self.root,['latex'])
        self.assertEqual(r['status'],'BUILT_REVIEW_REQUIRED')
        (self.root/'section.md').write_text('changed source')
        self.assertTrue(paper.current(self.root,r['inputs']))
        with self.assertRaises(ValueError):paper.render(self.root,'latex',engine='missing-binary')
    def test_unsupported_math_not_silently_dropped(self):
        with self.assertRaises(ValueError):list(documents.blocks('$$\nx=2'))
    @unittest.skipUnless(importlib.util.find_spec('docx') and importlib.util.find_spec('latex2mathml'),'optional document dependencies absent')
    def test_word_contains_native_formula_and_configured_spacing(self):
        self.plan['profile']['line_spacing']=1.6;self.save()
        r=paper.build(self.root,['docx'])
        with zipfile.ZipFile(self.root/'delivery/paper.docx') as z:
            doc=z.read('word/document.xml').decode();style=z.read('word/styles.xml').decode()
        self.assertIn('oMath',doc);self.assertIn('w:line="384"',style)
        self.assertEqual(r['details']['docx']['display_equations'],1)


class PackageTests(unittest.TestCase):
    def test_archive_is_deterministic(self):
        with tempfile.TemporaryDirectory() as temp:
            a=Path(temp)/'a.zip';b=Path(temp)/'b.zip';package.archive(a);package.archive(b)
            self.assertEqual(a.read_bytes(),b.read_bytes())
            with zipfile.ZipFile(a) as z:
                self.assertFalse(any('/runs/' in n or '/.git/' in n for n in z.namelist()))
    def test_install_preserves_unrelated_files_and_refuses_collisions(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'AGENTS.md').write_text('existing rules')
            result=package.install(root,'codex')
            self.assertEqual(len(result['installed_skills']),9)
            self.assertTrue((root/'.math-modeling/scripts/paper.py').is_file())
            self.assertEqual((root/'AGENTS.md').read_text(),'existing rules')
            with self.assertRaises(ValueError):package.install(root,'codex')


class GateTests(unittest.TestCase):
    def test_new_runs_require_current_paper_content(self):
        spec=importlib.util.spec_from_file_location('gate_workflow',ROOT/'workflow/workflow.py');w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
        with tempfile.TemporaryDirectory() as temp:
            w.ROOT=Path(temp);state=w.new_state('test','runs/test')
            state['artifacts']={};state['active_gate']='G7'
            for i in range(7):state['gates']['G'+str(i)]['status']='passed'
            p=Path(temp)/'state.json';paper.write(p,state)
            self.assertTrue(any('B-PAPER-CONTRACT' in x for x in w.check_state(p)['blockers']))

if __name__=='__main__':unittest.main()
