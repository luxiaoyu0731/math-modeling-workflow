"""Synthetic negative cases: no test is a real paper or human visual sign-off."""
import hashlib, json, subprocess, sys, tempfile, unittest, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT/'examples'))
import paper, contracts, native, release_check
from create_demo import create

class NativeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=create(Path(self.tmp.name)/'p','existing_tex')
    def tearDown(self):self.tmp.cleanup()
    def test_native_audit_preserves_original_and_tracks_sources(self):
        old=(self.root/'main.tex').read_bytes();a=paper.audit(self.root)
        self.assertEqual(a['status'],'PASS');self.assertIn('main.tex',a['inputs'])
        paper.build(self.root,['latex']);self.assertEqual((self.root/'main.tex').read_bytes(),old)
    def test_package_import_in_clean_process(self):
        code="from scripts.paper import audit;from pathlib import Path;import sys;assert audit(Path(sys.argv[1]))['status']=='PASS'"
        subprocess.run([sys.executable,'-I','-c',"import sys;sys.path.insert(0,sys.argv[1]);"+code.replace('sys.argv[1]','sys.argv[2]'),str(ROOT),str(self.root)],check=True)
    def test_modified_main_rejected(self):
        (self.root/'main.tex').write_text('changed')
        self.assertIn('native input hash mismatch: main.tex',paper.audit(self.root)['errors'])
    def test_missing_contract_rejected(self):
        p=paper.read(self.root/'paper-plan.json');del p['model_review'];paper.write(self.root/'paper-plan.json',p)
        self.assertEqual(paper.audit(self.root)['status'],'FAIL')
    def test_wrong_schema_rejected(self):
        p=paper.read(self.root/'paper-plan.json');p['schema']='invalid';paper.write(self.root/'paper-plan.json',p)
        self.assertEqual(paper.audit(self.root)['status'],'FAIL')
    def test_failed_build_cannot_reuse_old_pdf(self):
        p=paper.read(self.root/'paper-plan.json');p['native']['command']=[sys.executable,'-c','import sys;sys.exit(1)']
        (self.root/'main.pdf').write_bytes(b'%PDF-old')
        with self.assertRaises(ValueError):native.compile_pdf(self.root,p,self.root/'output.pdf')
        self.assertFalse((self.root/'output.pdf').exists())
    def test_isolation_does_not_copy_unregistered_dependency(self):
        p=paper.read(self.root/'paper-plan.json');(self.root/'hidden.txt').write_text('not registered')
        p['native']['command']=[sys.executable,'-c',"from pathlib import Path;Path('hidden.txt').read_text()"]
        with self.assertRaises(ValueError):native.compile_pdf(self.root,p,self.root/'output.pdf')
    def test_generated_demo_values_and_no_overwrite(self):
        with self.assertRaises(ValueError):create(self.root,'generated')
        p=create(Path(self.tmp.name)/'generated','generated');self.assertEqual(paper.audit(p)['status'],'PASS')
        self.assertIn('2.0',paper.assemble(p,paper.read(p/'paper-plan.json')))

class ContractTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=create(Path(self.tmp.name)/'p','generated')
    def tearDown(self):self.tmp.cleanup()
    def test_model_modification_requires_comparison_or_limitation(self):
        p=paper.read(self.root/'model-review.json');p['relations'][0]['choice']='modified';paper.write(self.root/'model-review.json',p)
        self.assertEqual(paper.audit(self.root)['status'],'FAIL')
        p['relations'][0]['limitation']='Synthetic comparison not performed';paper.write(self.root/'model-review.json',p)
        self.assertEqual(paper.audit(self.root)['status'],'PASS')
    def test_execution_level_cannot_be_claimed_from_hash_only(self):
        p={'checks':[{'id':'x','level':'recomputed','status':'passed','scope':'test','limitations':'arithmetic only','artifacts':{'result.json':paper.digest(self.root/'result.json')}}]}
        paper.write(self.root/'validation-ledger.json',p);self.assertEqual(paper.audit(self.root)['status'],'FAIL')
        p['checks'][0]['level']='historical_hash';paper.write(self.root/'validation-ledger.json',p)
        self.assertEqual(paper.audit(self.root)['status'],'PASS')
    def test_validation_log_must_be_bound_and_current(self):
        (self.root/'run.log').write_text('synthetic log')
        p={'checks':[{'id':'x','level':'recomputed','status':'passed','scope':'test','limitations':'test only','command':['test'],'environment':{'python':'test'},'log':'run.log','artifacts':{'run.log':paper.digest(self.root/'run.log')}}]}
        paper.write(self.root/'validation-ledger.json',p);self.assertEqual(paper.audit(self.root)['status'],'PASS')
        (self.root/'run.log').write_text('changed');self.assertEqual(paper.audit(self.root)['status'],'FAIL')
    def test_impact_compatibility_evidence_expires(self):
        p=paper.read(self.root/'paper-plan.json');p['change_impact']='impact.json';paper.write(self.root/'paper-plan.json',p)
        (self.root/'comparison.txt').write_text('synthetic comparison')
        change={'changes':[{'path':'section.md','before_sha256':'a'*64,'after_sha256':paper.digest(self.root/'section.md'),'effect':'sampling change','affected_outputs':['table'],'decision':'compatible','evidence':{'comparison.txt':paper.digest(self.root/'comparison.txt')}}]}
        paper.write(self.root/'impact.json',change);self.assertEqual(paper.audit(self.root)['status'],'PASS')
        (self.root/'comparison.txt').write_text('changed');self.assertEqual(paper.audit(self.root)['status'],'FAIL')
    def test_page_parts_count_body_independently(self):
        profile={'page_parts':{'latex':[{'role':'abstract','start':1,'end':1,'max_pages':1},{'role':'body','start':2,'end':3,'max_pages':2},{'role':'appendix','start':4,'end':8}]}}
        self.assertEqual(contracts.page_review(profile,{}, {'latex':8}),[])
        profile['page_parts']['latex'][1]['max_pages']=1;self.assertTrue(contracts.page_review(profile,{}, {'latex':8}))
    def test_overlapping_and_incomplete_parts_rejected(self):
        p={'page_parts':{'latex':[{'start':1,'end':2},{'start':2,'end':2}]}}
        errors=contracts.page_review(p,{}, {'latex':3});self.assertTrue(any('overlapping' in e for e in errors));self.assertTrue(any('incomplete' in e for e in errors))
    def test_per_page_coverage_and_unresolved_findings(self):
        review={'schema':'mm-visual/v2','page_reviews':{'latex':[{'page':1,'method':'zoomed','status':'passed','notes':'synthetic test only'}]}}
        self.assertTrue(contracts.page_review({},review,{'latex':2}))
        self.assertEqual(contracts.page_review({},review,{'latex':1}),[])
        review['page_reviews']['latex'][0]['status']='failed';self.assertTrue(contracts.page_review({},review,{'latex':1}))

class ReleaseTests(unittest.TestCase):
    def test_redacts_sensitive_matches(self):
        secret='ghp_'+'x'*36;path='/'+'Users/'+'synthetic-user'+'/workspace'
        result=release_check.summarize([('sample.txt',(secret+' '+path).encode())])
        self.assertEqual(result['status'],'FAIL');self.assertNotIn(secret,json.dumps(result));self.assertNotIn('synthetic-user',json.dumps(result))
    def test_binary_requires_human_review(self):
        self.assertEqual(release_check.summarize([('image.png',b'\x89\xff')])['status'],'REVIEW_REQUIRED')
    def test_reviewed_asset_only_approves_exact_binary(self):
        data=bytes([137,255]);review={'schema':'mm-public-assets/v1','reviewer':'synthetic test','reviewed_at':'test','assets':{'a.png':{'status':'passed','notes':'Synthetic test, not actual visual review','sha256':hashlib.sha256(data).hexdigest()}}}
        items=[('docs/assets/a.png',data),('docs/assets/asset-review.json',json.dumps(review).encode())]
        self.assertEqual(release_check.summarize(items)['status'],'PASS')
        self.assertEqual(release_check.summarize(items+[('docs/assets/b.png',data)])['status'],'REVIEW_REQUIRED')
        items[0]=('docs/assets/a.png',data+b'changed')
        self.assertEqual(release_check.summarize(items)['status'],'REVIEW_REQUIRED')
    def test_terms_detect_task_material(self):
        self.assertEqual(release_check.summarize([('notes.md',b'SYNTHETIC-PRIVATE-TASK')],['SYNTHETIC-PRIVATE-TASK'])['status'],'FAIL')
    def test_tampered_zip_manifest_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'test.zip'
            with zipfile.ZipFile(p,'w') as z:z.writestr('p/a.txt','changed');z.writestr('p/MANIFEST.json',json.dumps({'a.txt':'a'*64}))
            self.assertEqual(release_check.scan_zip(p)['status'],'FAIL')
    def test_zip_local_links_checked_against_actual_entries(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'test.zip'
            with zipfile.ZipFile(p,'w') as z:z.writestr('p/README.md','[guide](docs/absent.md)')
            self.assertEqual(release_check.scan_zip(p)['status'],'FAIL')
    def test_zip_traversal_and_symlinks_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'test.zip'
            with zipfile.ZipFile(p,'w') as z:
                z.writestr('../escape','test');i=zipfile.ZipInfo('link');i.external_attr=0o120777<<16;z.writestr(i,'target')
            result=release_check.scan_zip(p);self.assertEqual(result['status'],'FAIL')
    def test_index_scan_uses_staged_bytes_not_worktree(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);subprocess.run(['git','init',str(root)],capture_output=True,check=True)
            (root/'data.txt').write_text('ghp_'+'x'*36)
            subprocess.run(['git','-C',t,'add','data.txt'],check=True)
            (root/'data.txt').write_text('clean')
            self.assertEqual(release_check.scan_git(root,'tracked')['status'],'PASS')
            self.assertEqual(release_check.scan_git(root,'index')['status'],'FAIL')

if __name__=='__main__':unittest.main()
