from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'examples'))
from create_showcase import create_showcase
import paper

class ShowcaseTests(unittest.TestCase):
    def test_computed_results_are_bound_and_existing_directory_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            root=create_showcase(Path(temp)/'showcase')
            result=paper.read(root/'result.json')
            self.assertEqual(result['forecast'],result['heldout'])
            self.assertEqual(result['model_mae'],0)
            self.assertEqual(result['baseline_mae'],3)
            self.assertEqual(paper.audit(root)['status'],'PASS')
            with self.assertRaises(ValueError):create_showcase(root)
