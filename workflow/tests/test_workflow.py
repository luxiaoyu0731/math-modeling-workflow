"""Control-plane acceptance regressions; synthetic files are not contest evidence."""
import argparse
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest

MODULE_ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('workflow', MODULE_ROOT / 'workflow.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)


class WorkflowTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.old_root = w.ROOT
        w.ROOT = self.base
        shutil.copytree(MODULE_ROOT / 'templates', self.base / 'templates')
        shutil.copytree(MODULE_ROOT / 'prompts', self.base / 'prompts')
        self.state_path = self.base / 'runs/test/state/workflow_state.json'
        self.run_root = self.base / 'runs/test'
        self.run_root.mkdir(parents=True)
        w.dump(self.state_path, w.new_state('test', 'runs/test'))
        self.capture = io.StringIO()
        self.redirect = contextlib.redirect_stdout(self.capture)
        self.redirect.__enter__()

    def tearDown(self):
        self.redirect.__exit__(None, None, None)
        w.ROOT = self.old_root
        self.tmp.cleanup()

    def args(self, **kw):
        return argparse.Namespace(state=str(self.state_path), **kw)

    def state(self):
        return w.load(self.state_path)

    def register(self, aid, deps=None, path=None):
        path = path or f'evidence/{aid}.md'
        target = self.run_root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('Synthetic acceptance fixture for ' + aid)
        w.register_artifact(self.args(id=aid, path=path, source='test fixture', status='usable', depends_on=','.join(deps if deps is not None else w.ARTIFACT_REQUIRED_DEPENDENCIES.get(aid, [])), allowed_next_gate='G1'))

    def fill_gate(self, gate):
        for aid in self.state()['gates'][gate]['required_output_ids']:
            self.register(aid)

    def accept(self, gate):
        w.accept_gate(self.args(gate=gate, outputs=','.join(self.state()['gates'][gate]['required_output_ids']), note='Synthetic mechanical review only'))

    def advance_to(self, gate):
        while self.state()['active_gate'] != gate:
            current = self.state()['active_gate']
            self.fill_gate(current)
            self.accept(current)

    def test_missing_unregistered_requirements_and_read_only_check(self):
        before = self.state_path.read_bytes()
        result = w.check_state(self.state_path)
        self.assertEqual(set(result['missing_artifacts']), {'input_audit', 'contest_profile'})
        self.assertEqual(before, self.state_path.read_bytes())

    def test_cannot_skip_gate(self):
        with self.assertRaises(SystemExit):
            self.accept('G1')

    def test_missing_outputs_rejected(self):
        self.register('input_audit')
        with self.assertRaises(SystemExit):
            self.accept('G0')

    def test_hash_drift_blocks_acceptance(self):
        self.fill_gate('G0')
        (self.run_root / 'evidence/input_audit.md').write_text('Changed after registration')
        with self.assertRaises(SystemExit):
            self.accept('G0')
        self.assertEqual(self.state()['active_gate'], 'G0')

    def test_deleted_evidence_blocks_acceptance(self):
        self.fill_gate('G0')
        (self.run_root / 'evidence/contest_profile.md').unlink()
        with self.assertRaises(SystemExit):
            self.accept('G0')

    def test_global_blocker_blocks_acceptance(self):
        self.fill_gate('G0')
        s = self.state();s['open_blockers'] = ['B-EXTERNAL: unresolved rule'];w.dump(self.state_path,s)
        with self.assertRaises(SystemExit):
            self.accept('G0')

    def test_dangling_dependency_rejected(self):
        with self.assertRaises(SystemExit):
            self.register('child', ['nonexistent'])

    def test_invalidated_dependency_rejected(self):
        self.register('parent')
        w.invalidate(self.args(artifact='parent', reason='test'))
        with self.assertRaises(SystemExit):
            self.register('child',['parent'])

    def test_self_dependency_rejected(self):
        with self.assertRaises(SystemExit):
            self.register('self',['self'])

    def test_templates_cannot_be_accepted(self):
        self.register('input_audit',path='evidence/templates/input_audit.md')
        self.register('contest_profile')
        with self.assertRaises(SystemExit):
            self.accept('G0')

    def test_complete_gate_sequence_and_v7_requirements(self):
        for gate in w.GATES:
            self.fill_gate(gate)
            self.accept(gate)
        s = self.state()
        self.assertTrue(all(g['status'] == 'passed' for g in s['gates'].values()))
        self.assertEqual(s['schema'],'mm-workflow/v7')
        self.assertIn('human_review_record',s['gates']['G8']['output_artifacts'])

    def test_invalidation_cascades_and_preserves_other_blockers(self):
        self.advance_to('G3')
        self.fill_gate('G3');self.accept('G3')
        self.register('draft',deps=['model_card'])
        s=self.state();s['open_blockers']=['B-OTHER: keep'];w.dump(self.state_path,s)
        w.invalidate(self.args(artifact='input_audit',reason='input changed'))
        s=self.state()
        self.assertEqual(s['active_gate'],'G0')
        self.assertIn('B-OTHER: keep',s['open_blockers'])
        self.assertEqual(s['gates']['G3']['status'],'invalidated')
        self.assertEqual(s['artifacts']['draft']['status'],'invalidated')
        self.assertTrue((self.run_root/'evidence/input_audit.md').is_file())

    def test_recovery_requires_fresh_downstream_evidence(self):
        self.advance_to('G2')
        w.invalidate(self.args(artifact='input_audit',reason='input changed'))
        self.fill_gate('G0')
        blocker=self.state()['gates']['G0']['blocker'][0]
        w.resolve_blocker(self.args(gate='G0',blocker=blocker))
        self.accept('G0')
        self.assertEqual(self.state()['active_gate'],'G1')
        with self.assertRaises(SystemExit):
            self.accept('G1')
        self.fill_gate('G1');self.accept('G1')
        self.assertEqual(self.state()['active_gate'],'G2')

    def test_meta_prompt_follows_gate_and_is_read_only(self):
        before=self.state_path.read_bytes()
        w.meta_prompt(self.args(task='prepare kickoff'))
        self.assertIn('"meta_stage": "kickoff"',self.capture.getvalue())
        self.assertEqual(before,self.state_path.read_bytes())
        self.advance_to('G7')
        self.capture.seek(0);self.capture.truncate(0)
        w.meta_prompt(self.args(task='write only certified results'))
        self.assertIn('Part2 论文适配',self.capture.getvalue())
        self.assertNotIn('UNRELATED_PRIOR_CASE_RESULT',self.capture.getvalue())

    def test_duplicate_run_refused(self):
        w.new_run(argparse.Namespace(slug='new'))
        with self.assertRaises(SystemExit):
            w.new_run(argparse.Namespace(slug='new'))

    def test_path_traversal_rejected(self):
        with self.assertRaises(SystemExit):
            w.checked_relative('../outside')
        with self.assertRaises(SystemExit):
            w.checked_relative('/absolute')

    def test_legacy_state_requirements_not_migrated(self):
        s=self.state();s['schema']='mm-workflow/v6';s['gates']['G0']['required_output_ids']=['input_audit'];w.dump(self.state_path,s)
        self.register('input_audit');self.accept('G0')
        self.assertEqual(self.state()['schema'],'mm-workflow/v6')


if __name__ == '__main__':
    unittest.main()
