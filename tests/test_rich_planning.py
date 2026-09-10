import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/agent4ppt-skill/scripts'))
from PIL import Image
from agent4ppt.project import Project
from agent4ppt.styles import catalog, save
from agent4ppt.planning import preview, api_job, template
from agent4ppt.imaging import generate, batch
from agent4ppt.package import export_project


class RichPlanning(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        env = patch.dict(os.environ, {'AGENT4PPT_HOME': str(self.root / 'home')})
        env.start()
        self.addCleanup(env.stop)
        self.source = self.root / 'source figure.png'
        Image.new('RGB', (160, 90), 'white').save(self.source)

    def create(self, **extra):
        brief = {'title': '实际项目', 'pages': [{'title': '证据', 'bullets': ['观察 A']}, {'title': '解释'}]}
        brief.update(extra)
        return Project.create(self.root / 'project', brief, self.root)

    def test_each_complete_style_reaches_request(self):
        for name, recipe in catalog().items():
            with self.subTest(style=name):
                project = Project.create(self.root / recipe['id'],
                                         {'title': name, 'style_name': name, 'pages': [{'title': '真实内容'}]})
                request = project.claim('reader')
                self.assertIn(recipe['blueprints'][0]['arrangement'], request['prompt'])
                self.assertIn(recipe['imagery']['charts'], request['prompt'])
                self.assertIn(recipe['typography']['title'], request['prompt'])

    def test_personal_style_is_frozen_for_existing_project(self):
        save('个人方案', {'guidance': 'before', 'canvas': {'density': 'medium'}})
        project = self.create(style_name='个人方案')
        save('个人方案', {'guidance': 'after'}, overwrite=True)
        request = project.claim('reader')
        self.assertIn('before', request['prompt'])
        self.assertNotIn('after', request['prompt'])

    def test_structured_page_and_markdown_asset_survive_planning(self):
        project = self.create(context={'terms': ['完整概念']},
                              pages=[{'title': '图', 'layout': {'intent': '比较真实数据'},
                                      'text': {'caption': '准确图注'},
                                      'visual_elements': {'main': '主证据'},
                                      'references': ['保持原始数据 ![结果](<source figure.png>)']}])
        request = project.claim('reader')
        self.assertEqual(request['references'][0]['path'], str(self.source.resolve()))
        for value in ('完整概念', '比较真实数据', '准确图注', '主证据', '保持原始数据'):
            self.assertIn(value, request['prompt'])
        self.assertTrue(request['requires_images'])

    def test_method_contract_rejects_wrong_and_missing_evidence(self):
        project = self.create()
        first = project.claim('one', 1)
        method = {'tool': 'test-tool', 'mode': 'edit', 'quality': 'high'}
        project.complete(1, first['token'], self.source, 'builtin', 'test fixture', True, method)
        second = project.claim('two', 2)
        self.assertEqual(second['generation_method']['quality'], 'high')
        with self.assertRaises(ValueError):
            project.complete(2, second['token'], self.source, 'builtin', 'test fixture')
        with self.assertRaises(ValueError):
            project.complete(2, second['token'], self.source, 'builtin', 'test fixture',
                             generation_method=dict(method, tool='other'))
        project.complete(2, second['token'], self.source, 'builtin', 'test fixture', generation_method=method)
        from pptx import Presentation
        self.assertEqual(len(Presentation(export_project(project)['path']).slides), 2)

    def test_preparation_does_not_claim_or_complete_work(self):
        project = self.create()
        prepared = preview(project)
        self.assertEqual(prepared['pages'], 2)
        self.assertTrue(all(p['state'] == 'pending' for p in project.status()['pages']))
        data = json.loads(Path(prepared['requests'][0]).read_text(encoding='utf-8'))
        self.assertTrue(data['planning_only'])
        self.assertNotIn('token', data)

    def test_api_bridge_keeps_all_images_and_options(self):
        project = self.create(backend='openai', image_options={'quality': 'high'},
                              pages=[{'title': '图片', 'references': [{'path': str(self.source), 'role': 'evidence'}]}])
        project.claim('worker')
        target = self.root / 'job.json'
        api_job(project.root / 'requests/page-001.json', self.root / 'candidate.png', target)
        job = json.loads(target.read_text(encoding='utf-8'))
        result = generate(job, dry_run=True)
        self.assertEqual(result['images'], [str(self.source.resolve())])
        self.assertEqual(result['request']['quality'], 'high')
        self.source.write_bytes(b'changed')
        with self.assertRaises(ValueError):
            api_job(project.root / 'requests/page-001.json', self.root / 'candidate.png', target)

    def test_builtin_request_cannot_be_silently_converted_to_api(self):
        project = self.create()
        project.claim('worker')
        with self.assertRaises(ValueError):
            api_job(project.root / 'requests/page-001.json', self.root / 'candidate.png', self.root / 'job.json')

    def test_template_initializes_and_preserves_existing_file(self):
        path = self.root / 'brief.json'
        template(path)
        before = path.read_bytes()
        with self.assertRaises(FileExistsError):
            template(path)
        self.assertEqual(path.read_bytes(), before)
        project = Project.create(self.root / 'from-template', json.loads(before))
        self.assertEqual(len(project.status()['pages']), 1)

    def test_batch_short_prompts_and_shared_options(self):
        results = batch(['first image', {'prompt': 'second image', 'options': {'quality': 'low'}}],
                        dry_run=True, defaults={'out_dir': str(self.root), 'options': {'quality': 'high'}})
        self.assertTrue(all(item['ok'] for item in results))
        self.assertEqual(results[0]['request']['quality'], 'high')
        self.assertEqual(results[1]['request']['quality'], 'low')
        self.assertNotEqual(results[0]['outputs'], results[1]['outputs'])

    def test_custom_preview_suffix_writes_actual_reduced_image(self):
        data = self.source.read_bytes()
        class LocalFixture:
            def run(self, fields, images, mask):
                return [data]
        result = generate({'prompt': 'fixture', 'out': str(self.root / 'full.png'),
                           'downscale_max_dim': 80, 'downscale_suffix': '-small'},
                          provider=LocalFixture(), settings={'model': 'gpt-image-2'})
        with Image.open(self.root / 'full-small.png') as image:
            self.assertEqual(image.size, (80, 45))
        self.assertEqual(Path(result['outputs'][0]).read_bytes(), data)


if __name__ == '__main__':
    unittest.main()
