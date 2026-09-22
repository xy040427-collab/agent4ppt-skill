"""Inspectable planning artifacts and an explicit bridge to image API jobs."""
import json
from pathlib import Path
from .files import digest, read, write
from .plan import compile_request
from .composition import MODES, verify_assets


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
            verify_assets(item.get('overlays', []))
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


def template(output, mode='full_slide'):
    if mode not in MODES:
        raise ValueError('Unknown production mode')
    path = Path(output)
    if path.exists():
        raise FileExistsError('Template destination already exists')
    brief = {
        'title': '演示项目：替换为实际主题', 'language': 'Chinese', 'mode': mode,
        'audience': '替换为实际受众', 'backend': 'builtin', 'ratio': '16:9',
        'parallelism': 10, 'style_name': '学术汇报',
        'context': {'purpose': '替换为实际报告目标', 'canonical_terms': [],
                    'evidence_scope': '所有实际结果必须来自提供的资料'},
        'pages': [{'title': '替换为准确的页面标题', 'role': 'evidence',
                   'bullets': ['替换为已验证的观察', '说明限制与下一步'],
                   'layout': {'intent': '用证据回答本页问题',
                              'composition': '主图为主，解释靠近证据'},
                   'visual_elements': {'main': '使用本页真实素材'},
                   'references': [], 'constraints': ['不编造数值或来源'],
                   'notes': '根据实际材料编写可直接讲述的说明。'}]}
    if mode == 'editable':
        brief['review_policy'] = 'structured-v1'
        brief['editable_workflow'] = 'full_slide_first'
        page = brief['pages'][0]
        copy = [page['title'], *page.pop('bullets')]
        page['raster_text'] = []
        page['overlays'] = [
            {'id': 'title', 'type': 'text', 'text': copy[0], 'x': .04, 'y': .04, 'w': .92, 'h': .12,
             'font_size': 28, 'bold': True},
            {'id': 'conclusion', 'type': 'text', 'text': '\n'.join(copy[1:]), 'x': .67, 'y': .28,
             'w': .29, 'h': .45, 'font_size': 18}]
        page['layout'] = 'Design a finished evidence-led slide WITH the title and conclusion. Choose a coherent composition; measure native text placement from the accepted design afterwards.'
    write(path, brief)
    return {'path': str(path.resolve()), 'notice': 'Replace example content before production.'}


def layout_guide(page_file, output, ratio='16:9'):
    from .composition import validate_overlays, fingerprint
    from .layout import write_layout_guide, layout_issues
    page = read(page_file)
    page['overlays'] = validate_overlays(page.get('overlays'), Path(page_file).resolve().parent)
    if Path(output).exists():
        raise FileExistsError('Use a new layout guide path after revising the page')
    result = write_layout_guide(page, output, ratio)
    result.update(spec_sha256=fingerprint(page), issues=layout_issues(page, ratio))
    return result

# a4p-provenance: a4p-50d41ed6-f9f9-4470-ac9c-e700dd134a07/91c35f13ddb83af6b085
