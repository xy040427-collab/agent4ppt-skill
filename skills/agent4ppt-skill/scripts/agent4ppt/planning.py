"""Inspectable planning artifacts and an explicit bridge to image API jobs."""
import json
from pathlib import Path
from .files import digest, read, write
from .plan import compile_request


def preview(project):
    """Publish planning snapshots without acquiring or fabricating work leases."""
    with project.transaction() as db:
        brief = project.settings(db)
        sample = db.execute("SELECT value FROM settings WHERE key='sample'").fetchone()
        stored_method = db.execute("SELECT value FROM settings WHERE key='generation_method'").fetchone()
        requests = []
        for row in db.execute('SELECT * FROM pages ORDER BY number'):
            item = compile_request(brief, json.loads(row['spec']),
                                   project.root / sample[0] if sample else None,
                                   json.loads(stored_method[0]) if stored_method else None)
            item.update(revision=row['revision'], planning_only=True)
            for asset in item['references']:
                if digest(asset['path']) != asset['sha256']:
                    raise ValueError('Reference changed; revise the page before preparing requests')
            requests.append(item)
        paths = []
        for item in requests:
            path = project.root / 'plans' / f'page-{item["page"]:03d}.json'
            write(path, item)
            paths.append(str(path))
    return {'pages': len(paths), 'requests': paths,
            'notice': 'Planning snapshots only. Claim a page to obtain an executable lease.'}


def api_job(request_path, output, save_path):
    request = read(request_path)
    if request.get('backend') not in ('openai', 'atlascloud'):
        raise ValueError('A builtin request must be executed by the host image tool')
    if not request.get('prompt'):
        raise ValueError('Request needs a prompt')
    images = []
    for asset in request.get('references', []):
        if digest(asset['path']) != asset['sha256']:
            raise ValueError('Reference changed since the request was prepared')
        images.append(str(Path(asset['path']).resolve()))
    job = {'backend': request['backend'], 'prompt': request['prompt'],
           'options': request.get('options', {}), 'images': images,
           'out': str(Path(output).resolve()), 'overwrite': False}
    write(save_path, job)
    return {'path': str(Path(save_path).resolve()), 'images': len(images),
            'planning_only': bool(request.get('planning_only'))}


def template(output):
    path = Path(output)
    if path.exists():
        raise FileExistsError('Template destination already exists')
    brief = {
        'title': '演示项目：替换为实际主题', 'language': 'Chinese',
        'audience': '替换为实际受众', 'backend': 'builtin', 'ratio': '16:9',
        'parallelism': 3, 'style_name': '学术汇报',
        'context': {'purpose': '替换为实际报告目标', 'canonical_terms': [],
                    'evidence_scope': '所有实际结果必须来自提供的资料'},
        'pages': [{'title': '替换为准确的页面标题', 'role': 'evidence',
                   'bullets': ['替换为已验证的观察', '说明限制与下一步'],
                   'layout': {'intent': '用证据回答本页问题',
                              'composition': '主图为主，解释靠近证据'},
                   'visual_elements': {'main': '使用本页真实素材'},
                   'references': [], 'constraints': ['不编造数值或来源'],
                   'notes': '根据实际材料编写可直接讲述的说明。'}]}
    write(path, brief)
    return {'path': str(path.resolve()), 'notice': 'Replace example content before production.'}

# a4p-provenance: a4p-50d41ed6-f9f9-4470-ac9c-e700dd134a07/91c35f13ddb83af6b085
