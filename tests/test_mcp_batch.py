"""Validate page batch plans; no PowerPoint execution or visual QA claims."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/agent4ppt-skill/scripts'))
from agent4ppt.mcp_batch import plan_batch


class MCPBatchPlan(unittest.TestCase):
    def spec(self):
        return {'session_id': 'session', 'slide_index': 1,
                'objects': {'p1-title': {'shape_index': 2},
                            'p1-body': {'shape_index': 3}},
                'edits': [{'id': 'p1-title', 'position': {'left': 0, 'top': 30},
                           'size': {'width': 600, 'height': 70}, 'font_size': 32,
                           'font_name': 'Microsoft YaHei', 'bold': True,
                           'color': '#01aBff', 'alignment': 'center'},
                          {'id': 'p1-body', 'font_size': 18.1}]}

    def test_plan_preflights_each_name_and_preserves_sequence(self):
        spec = self.spec(); before = copy.deepcopy(spec)
        plan = plan_batch(spec)
        self.assertEqual(spec, before)
        self.assertFalse(plan['executed'])
        self.assertEqual([p['expected_name'] for p in plan['preflight']], ['p1-title', 'p1-body'])
        self.assertTrue(all(p['arguments']['action'] == 'get-name' for p in plan['preflight']))
        self.assertEqual([p['arguments']['action'] for p in plan['calls']],
                         ['set-position', 'set-size', 'set-font-size', 'set-font-name',
                          'set-bold', 'set-font-color', 'set-alignment', 'set-font-size'])
        color = plan['calls'][5]['arguments']
        self.assertEqual((color['red'], color['green'], color['blue']), (1, 171, 255))

    def test_rejects_invalid_later_edit_instead_of_returning_partial_plan(self):
        for invalid in ({'id': 'missing', 'font_size': 10}, {'id': 'p1-title', 'font_size': 10},
                        {'id': 'p1-body', 'delete': True}, {'id': 'p1-body', 'font_size': 0},
                        {'id': 'p1-body', 'font_size': float('nan')},
                        {'id': 'p1-body', 'color': 'blue'}, {'id': 'p1-body', 'bold': 1},
                        {'id': 'p1-body', 'position': {'left': 3}},
                        {'id': 'p1-body', 'size': {'width': 4, 'height': -2}},
                        {'id': 'p1-body', 'alignment': 'bad'}, {'id': 'p1-body'}):
            with self.subTest(invalid=invalid):
                spec = self.spec(); spec['edits'][1] = invalid
                with self.assertRaises(ValueError):
                    plan_batch(spec)

    def test_mixed_runs_geometry_only(self):
        spec = self.spec(); spec['objects']['p1-title']['mixed_runs'] = True
        with self.assertRaisesRegex(ValueError, 'mixed_runs'):
            plan_batch(spec)
        spec['edits'][0] = {'id': 'p1-title', 'position': {'left': 1, 'top': 2}}
        self.assertEqual(len(plan_batch(spec)['calls']), 2)

    def test_rejects_ambiguous_indices_and_noninteger_slide(self):
        spec = self.spec(); spec['objects']['p1-body']['shape_index'] = 2
        with self.assertRaisesRegex(ValueError, 'duplicate shape_index'):
            plan_batch(spec)
        for value in (True, 0, 1.5, float('inf')):
            spec = self.spec(); spec['slide_index'] = value
            with self.assertRaises(ValueError):
                plan_batch(spec)


if __name__ == '__main__':
    unittest.main()
