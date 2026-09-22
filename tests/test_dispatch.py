"""Host scheduling advice must respect capacity without acquiring leases."""
import concurrent.futures
import contextlib
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/agent4ppt-skill/scripts'))
from PIL import Image
from agent4ppt.project import Project
from agent4ppt.planning import template
from agent4ppt.plan import validate


class Dispatch(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.image = self.root / 'sample.png'
        Image.new('RGB', (160, 90), 'navy').save(self.image)

    def project(self, count=12, **kwargs):
        return Project.create(self.root / 'deck', {
            'title': 'Dispatch test',
            'pages': [{'title': f'Page {i}'} for i in range(1, count + 1)],
            **kwargs,
        })

    def finish(self, project, page, sample=False):
        job = project.claim('coordinator', page)
        project.complete(page, job['token'], self.image, 'builtin', 'Reviewed', sample)

    def database_state(self, project):
        with contextlib.closing(sqlite3.connect(project.db)) as db:
            return {table: db.execute(f'SELECT * FROM {table}').fetchall()
                    for table in ('settings', 'pages', 'events')}

    def test_sample_first_is_read_only_and_waits_for_acceptance(self):
        project = self.project()
        before = self.database_state(project)
        plan = project.dispatch_plan(20)
        self.assertEqual(plan['phase'], 'sample')
        self.assertEqual(plan['pages'], [2])
        self.assertEqual(plan['launch_count'], 1)
        self.assertTrue(plan['requires_sample_acceptance'])
        self.assertEqual(self.database_state(project), before)
        self.assertEqual(list((project.root / 'requests').iterdir()), [])
        job = project.claim('sample-worker', 2)
        self.assertEqual(project.dispatch_plan(20)['launch_count'], 0)
        self.assertEqual(project.dispatch_plan(20)['active_workers'][0]['number'], 2)
        project.complete(2, job['token'], self.image, 'builtin', 'Reviewed', False)
        self.assertEqual(project.dispatch_plan(20)['phase'], 'sample')
        self.assertEqual(project.dispatch_plan(20)['launch_count'], 1)

    def test_explicit_sample_and_invalid_arguments(self):
        project = self.project()
        self.assertEqual(project.dispatch_plan(10, sample_page=7)['pages'], [7])
        for slots in (-1, True, False, 1.5, '3', None):
            with self.subTest(slots=slots), self.assertRaises(ValueError):
                project.dispatch_plan(slots)
        for page in (0, -1, True, 1.5, '2', 99):
            with self.subTest(page=page), self.assertRaises(ValueError):
                project.dispatch_plan(10, sample_page=page)
        self.assertEqual(project.dispatch_plan(0)['pages'], [])
        self.finish(project, 7)
        with self.assertRaises(ValueError):
            project.dispatch_plan(10, sample_page=7)

    def test_single_page_can_be_sample(self):
        project = self.project(1)
        self.assertEqual(project.dispatch_plan(10)['pages'], [1])
        self.finish(project, 1, sample=True)
        self.assertEqual(project.dispatch_plan(10)['pages'], [])

    def test_production_uses_maximum_available_capacity(self):
        project = self.project()
        self.finish(project, 2, sample=True)
        plan = project.dispatch_plan(50)
        self.assertEqual(plan['phase'], 'production')
        self.assertFalse(plan['requires_sample_acceptance'])
        self.assertEqual(plan['launch_count'], 10)
        self.assertNotIn(2, plan['pages'])
        self.assertEqual(project.dispatch_plan(3)['launch_count'], 3)
        self.assertEqual(project.dispatch_plan(0)['launch_count'], 0)
        self.assertEqual(project.dispatch_plan(3)['max_page_workers'], 10)

    def test_project_slots_and_pending_pages_bound_dispatch(self):
        project = self.project(6, parallelism=3)
        self.finish(project, 2, sample=True)
        project.claim('existing', 1)
        self.assertEqual(project.dispatch_plan(10)['pages'], [3, 4])
        self.assertEqual(project.dispatch_plan(1)['pages'], [3])
        self.finish(project, 3)
        self.finish(project, 4)
        self.finish(project, 5)
        self.assertEqual(project.dispatch_plan(10)['pages'], [6])
        project.claim('last', 6)
        self.assertEqual(project.dispatch_plan(10)['pages'], [])

    def test_replenishment_and_racing_claims_cannot_duplicate_work(self):
        project = self.project(12)
        self.finish(project, 2, sample=True)
        plan = project.dispatch_plan(3)
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            jobs = list(pool.map(lambda n: Project(project.root).claim(f'worker-{n}', n), plan['pages']))
        self.assertEqual(len({job['page'] for job in jobs}), 3)
        next_plan = project.dispatch_plan(10)
        self.assertEqual(next_plan['launch_count'], 7)
        self.assertTrue(set(next_plan['pages']).isdisjoint(plan['pages']))
        # Two hosts can receive identical advisory plans; claim remains authoritative.
        page = next_plan['pages'][0]
        def race(worker):
            try:
                return Project(project.root).claim(worker, page)['page']
            except ValueError:
                return None
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(race, ['race-a', 'race-b']))
        self.assertEqual(outcomes.count(page), 1)
        self.assertEqual(outcomes.count(None), 1)
        project.complete(jobs[0]['page'], jobs[0]['token'], self.image, 'builtin', 'Reviewed')
        self.assertNotIn(page, project.dispatch_plan(10)['pages'])
        self.assertEqual(project.dispatch_plan(10)['launch_count'], 7)

    def test_failed_excluded_and_expired_leases_only_planned(self):
        project = self.project(5)
        self.finish(project, 2, sample=True)
        failed = project.claim('failure', 1)
        project.fail(1, failed['token'], 'Provider error')
        expired = project.claim('expired', 3, lease=60)
        before = self.database_state(project)
        with patch('agent4ppt.project.time.time', return_value=expired['deadline'] + 1):
            plan = project.dispatch_plan(10)
            self.assertEqual(plan['pages'], [3, 4, 5])
            self.assertEqual(plan['active_workers'], [])
            self.assertEqual(self.database_state(project), before)
            reclaimed = project.claim('replacement', 3)
        self.assertNotEqual(reclaimed['token'], expired['token'])

    def test_default_and_template_limits_are_ten(self):
        self.assertEqual(self.project().status()['parallelism'], 10)
        for mode in ('full_slide', 'editable'):
            output = self.root / f'{mode}.json'
            template(output, mode)
            self.assertEqual(json.loads(output.read_text(encoding='utf-8'))['parallelism'], 10)
        for value in (0, 11, -1, True, 2.5, '10'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate({'title': 'Bad limit', 'pages': [{'title': 'One'}], 'parallelism': value}, '.')
        for value in (1, 10):
            self.assertEqual(validate({'title': 'Limit', 'pages': [{'title': 'One'}],
                                       'parallelism': value}, '.')['parallelism'], value)


if __name__ == '__main__':
    unittest.main()
