"""Revision-bound full-slide design -> erase -> native composition artifacts."""
import json
from pathlib import Path
from PIL import Image
from .files import atomic, digest, write, read
from .composition import validate_overlays, fingerprint
from .plan import method, execution_contract


def enabled(brief):
    # Missing fields in already initialized projects retain the legacy route.
    return brief.get('mode') == 'editable' and brief.get('editable_workflow') == 'full_slide_first'


def artifacts(project, db, row):
    found = {}
    for event in db.execute("SELECT kind,detail FROM events WHERE page=? AND kind IN ('design_recorded','background_recorded') ORDER BY id", (row['number'],)):
        value = json.loads(event['detail'])
        if value['revision'] == row['revision']:
            found[event['kind'].split('_')[0]] = value
    for value in found.values():
        if digest(project.root / value['image']) != value['sha256']:
            raise ValueError('Conversion artifact changed; revise and register again')
        if value['spec_sha256'] != fingerprint(json.loads(row['spec'])):
            raise ValueError('Conversion artifact specification mismatch')
    if 'background' in found and ('design' not in found or found['background']['design_sha256'] != found['design']['sha256']):
        raise ValueError('Background belongs to a different design')
    return found


def erase_request(project, brief, row, design):
    page = json.loads(row['spec'])
    targets = [{k: o[k] for k in ('id', 'type', 'x', 'y', 'w', 'h', 'text') if k in o} for o in page['overlays']]
    return dict(page=row['number'], revision=row['revision'], stage='erase', mode='editable',
                execution=execution_contract(brief),
                visual_comparison=brief.get('visual_comparison'),
                native_review={'guide': str(Path(__file__).resolve().parents[2] / 'references/visual-replication.md'), 'next': 'PowerPoint MCP adjustment -> compose --native-draft -> render checkpoint -> coordinator comparison'},
                backend=brief['backend'], editable_workflow='full_slide_first',
                generation_method={'tool': design['generation_method']['tool'], 'mode': 'edit', 'backend': brief['backend']},
                prompt='Edit the supplied finished slide. Remove ONLY the selected editable contents below, inpainting the original background. '
                       'Do not remove surrounding icons, containers, arrows or decoration. Keep all other artwork, fixed text, '
                       'geometry, camera, colors and canvas unchanged. Do not redesign or add placeholders. '
                       'Boxes are normalized location hints, not rectangles to erase wholesale. '
                       'For selected pictures remove that picture only; keep neighboring content.\n'
                       + json.dumps(targets, ensure_ascii=False)
                       + '\nFixed raster text to preserve: ' + json.dumps(page.get('raster_text', []), ensure_ascii=False),
                references=[dict(path=str(project.root / design['image']), sha256=design['sha256'], role='finished slide edit target; preserve everything except listed content')],
                options=dict(brief.get('image_options', {}), **page.get('image_options', {})),
                overlays=page['overlays'], requires_images=True, design_sha256=design['sha256'])


def register(project, number, token, stage, image, generation_method, qa, overlays=None):
    if stage not in ('design', 'background') or not qa.strip():
        raise ValueError('A design/background stage and visual QA note are required')
    source = Path(image).resolve()
    with Image.open(source) as im:
        size = im.size
        im.verify()
    with project.transaction() as db:
        row = project._lease(db, number, token)
        brief = project.settings(db)
        if not enabled(brief):
            raise ValueError('Stage registration requires full_slide_first editable workflow')
        found = artifacts(project, db, row)
        if stage in found:
            raise ValueError('Stage already registered; use revise before replacing it')
        actual = method(generation_method, brief['backend'])
        if not actual or (stage == 'background' and actual['mode'] != 'edit'):
            raise ValueError('Stage requires generation method; background must use edit')
        spec = json.loads(row['spec'])
        if stage == 'design':
            if overlays is None:
                raise ValueError('Design requires measured --overlays-file from the finished slide')
            measured = validate_overlays(overlays, source.parent)
            def contents(items):
                return {o['id']: (o['type'], o.get('text'), o.get('sha256')) for o in items}
            if contents(measured) != contents(spec['overlays']):
                raise ValueError('Measured overlays must preserve selected IDs, types and contents')
            request = read(project.root / 'requests' / f'page-{number:03d}.json')
            for ref in request['references']:
                if digest(ref['path']) != ref['sha256']:
                    raise ValueError('Design reference changed')
            required = request.get('generation_method')
            if required and any(actual.get(k) != required[k] for k in ('tool','mode','model','size','quality','input_preparation') if k in required):
                raise ValueError('Design generation method mismatch')
            spec['overlays'] = measured
            db.execute('UPDATE pages SET spec=? WHERE number=?', (json.dumps(spec, ensure_ascii=False), number))
        else:
            if overlays is not None or 'design' not in found:
                raise ValueError('Register the design and measured overlays before the background')
            with Image.open(project.root / found['design']['image']) as im:
                # Image services may round one canvas edge by a single pixel.
                # Normalized overlay coordinates remain valid at this tolerance.
                if any(abs(before - after) > 1 for before, after in zip(im.size, size)):
                    raise ValueError('Erased background must preserve design canvas dimensions')
            if actual['tool'] != found['design']['generation_method']['tool']:
                raise ValueError('Background edit must use the design image tool')
        blob = source.read_bytes()
        import hashlib
        checksum = hashlib.sha256(blob).hexdigest()
        if stage == 'background' and checksum == found['design']['sha256']:
            raise ValueError('Background still equals the design; editable content was not removed')
        relative = f'conversion/{number:03d}-r{row["revision"]}-{stage}-{checksum[:16]}{source.suffix.lower()}'
        atomic(project.root / relative, blob)
        value = dict(page=number, revision=row['revision'], image=relative, sha256=checksum,
                     spec_sha256=fingerprint(spec), generation_method=actual, qa=qa)
        if stage == 'background':
            value['design_sha256'] = found['design']['sha256']
        project.event(db, number, stage + '_recorded', value)
        if stage == 'design':
            current = db.execute('SELECT * FROM pages WHERE number=?', (number,)).fetchone()
            result = erase_request(project, brief, current, value)
            result.update(token=token, worker=row['worker'], deadline=row['deadline'])
            write(project.root / 'requests' / f'page-{number:03d}-erase.json', result)
        else:
            result = dict(stage='compose', page=number, revision=row['revision'], token=token,
                          visual_comparison=brief.get('visual_comparison'),
                          native_review={'guide': str(Path(__file__).resolve().parents[2] / 'references/visual-replication.md'), 'next': 'PowerPoint MCP adjustment -> compose --native-draft -> render checkpoint -> coordinator comparison'},
                          image=str(project.root / relative), design_sha256=value['design_sha256'])
    project.snapshot()
    return result


def require_background(project, db, row, image):
    found = artifacts(project, db, row)
    if 'background' not in found or digest(image) != found['background']['sha256']:
        raise ValueError('Compose requires the registered erased background for this revision')
    return found
