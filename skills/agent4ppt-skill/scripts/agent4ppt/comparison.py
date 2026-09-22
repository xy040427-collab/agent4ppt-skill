"""Deterministic raster diagnostics, not OCR or a substitute for visual review."""
import json
from contextlib import nullcontext
from pathlib import Path
from xml.etree import ElementTree as ET
from PIL import Image, ImageChops, ImageDraw
from .files import digest, write, read
from .native import read_text_shapes
from .package import A, P
from . import conversion


def footprint(image, background):
    delta = ImageChops.difference(image, background)
    channels = delta.split()
    mask = ImageChops.lighter(ImageChops.lighter(channels[0], channels[1]), channels[2]).point(lambda x: 255 if x > 32 else 0)
    bbox = mask.getbbox()
    count = mask.histogram()[255]
    colors = []
    for channel in image.split():
        hist = channel.histogram(mask)
        total = 0
        value = 0
        for value, n in enumerate(hist):
            total += n
            if total >= count / 2:
                break
        colors.append(value)
    # Coarse palette catches lost emphasis even when the median remains unchanged.
    palette = [0] * 64
    pixels = lambda im: im.get_flattened_data() if hasattr(im, 'get_flattened_data') else im.getdata()
    for rgb, selected in zip(pixels(image), pixels(mask)):
        if selected:
            palette[(rgb[0] // 64) * 16 + (rgb[1] // 64) * 4 + rgb[2] // 64] += 1
    return dict(bbox=list(bbox) if bbox else None, pixels=count, color=colors,
                palette=[v / max(count, 1) for v in palette], density=count / (image.width * image.height))


def measure(target, background, rendered, overlays, shapes):
    width, height = target.size
    results = []
    for item in overlays:
        # Shapes are looked up by name, never assumed to retain their slide index.
        native = shapes[item['id']]
        b = native['bounds']
        x = min(item['x'], b[0]); y = min(item['y'], b[1])
        r = max(item['x'] + item['w'], b[0] + b[2]); bottom = max(item['y'] + item['h'], b[1] + b[3])
        region = (max(0, int(x*width)-8), max(0, int(y*height)-8), min(width, int(r*width)+9), min(height, int(bottom*height)+9))
        images = [im.crop(region) for im in (target, background, rendered)]
        expected = footprint(images[0], images[1]); actual = footprint(images[2], images[1])
        flags = ['rotated_text_requires_inspection'] if native.get('rotation',0) else []
        metrics = {}
        if not expected['bbox'] or expected['pixels'] < 8:
            flags.append('target_unmeasurable')
        if not actual['bbox'] or actual['pixels'] < 8:
            flags.append('render_text_missing')
        if max(expected['density'], actual['density']) > .65:
            flags.append('background_or_region_contamination')
        if expected['bbox'] and actual['bbox']:
            e, a = expected['bbox'], actual['bbox']
            ew, eh = e[2]-e[0], e[3]-e[1]
            aw, ah = a[2]-a[0], a[3]-a[1]
            dx, dy = (a[0]+a[2]-e[0]-e[2])/2, (a[1]+a[3]-e[1]-e[3])/2
            metrics = dict(center_delta_px=[dx,dy], width_ratio=aw/ew, height_ratio=ah/eh,
                           ink_ratio=actual['pixels']/max(1,expected['pixels']),
                           color_delta=max(abs(c-d) for c,d in zip(expected['color'],actual['color'])),
                           palette_distance=sum(abs(c-d) for c,d in zip(expected['palette'],actual['palette']))/2)
            if max(abs(dx),abs(dy)) > max(3,eh*.15): flags.append('position')
            if abs(aw/ew-1) > .2 or abs(ah/eh-1) > .2: flags.append('visible_size_or_wrapping')
            if abs(metrics['ink_ratio']-1) > .35: flags.append('ink_amount_or_missing_content')
            if metrics['color_delta'] > 35 or metrics['palette_distance'] > .35: flags.append('color_or_emphasis')
        results.append(dict(id=item['id'], text=item['text'], region=list(region), native=native,
                            target=expected, rendered=actual, metrics=metrics, flags=flags))
    return results


def analyze(project, receipt_file, preview, connection=None):
    receipt = read(receipt_file)
    with (nullcontext(connection) if connection is not None else project.transaction()) as db:
        row = db.execute('SELECT * FROM pages WHERE number=?', (receipt['page'],)).fetchone()
        if row is None or row['revision'] != receipt['revision']:
            raise ValueError('Comparison receipt revision is stale')
        events = [json.loads(e['detail']) for e in db.execute("SELECT detail FROM events WHERE page=? AND kind='composed'", (receipt['page'],))]
        if receipt not in events or digest(receipt['draft']) != receipt['draft_sha256']:
            raise ValueError('Comparison requires an unchanged project compose checkpoint')
        stages = conversion.artifacts(project, db, row)
        if 'background' not in stages:
            raise ValueError('Comparison requires registered design and background')
        spec = json.loads(row['spec']); brief = project.settings(db)
        target_path = project.root / stages['design']['image']
        background_path = project.root / stages['background']['image']
        xml = read_text_shapes(Path(receipt['draft']).read_bytes(),spec['overlays'],digest(background_path),brief['ratio'])
    root = ET.fromstring('<root>'+xml+'</root>')
    shapes = {}
    for shape in root:
        identity = shape.find(f'{{{P}}}nvSpPr/{{{P}}}cNvPr').get('name')
        tr = shape.find(f'{{{P}}}spPr/{{{A}}}xfrm')
        off, ext = tr.find(f'{{{A}}}off'), tr.find(f'{{{A}}}ext')
        h = 5143500 if brief['ratio']=='16:9' else 6858000
        runs = []
        for run in shape.findall(f'.//{{{A}}}r'):
            pr = run.find(f'{{{A}}}rPr'); clr = pr.find(f'{{{A}}}solidFill/{{{A}}}srgbClr')
            runs.append(dict(text=run.findtext(f'{{{A}}}t'),font_size=float(pr.get('sz'))/100,
                             font=pr.find(f'{{{A}}}latin').get('typeface'),font_east_asian=pr.find(f'{{{A}}}ea').get('typeface'),
                             color=clr.get('val') if clr is not None else None))
        shapes[identity] = dict(bounds=[int(off.get('x'))/9144000,int(off.get('y'))/h,int(ext.get('cx'))/9144000,int(ext.get('cy'))/h],
                                bounds_pt=[int(off.get('x'))/12700,int(off.get('y'))/12700,int(ext.get('cx'))/12700,int(ext.get('cy'))/12700],
                                rotation=int(tr.get('rot','0'))/60000,runs=runs)
    with Image.open(target_path) as im: target=im.convert('RGB')
    with Image.open(background_path) as im: background=im.convert('RGB')
    with Image.open(preview) as im: rendered=im.convert('RGB')
    if rendered.size != target.size:
        raise ValueError('Comparison preview must match target pixel dimensions')
    # Registration permits one-pixel service rounding; align only that discrepancy.
    if background.size != target.size: background=background.resize(target.size)
    objects = measure(target,background,rendered,spec['overlays'],shapes)
    for item in objects:
        delta=item['metrics'].get('center_delta_px')
        if delta:
            item['suggested_shift_pt']=[-delta[0]*720/target.width,-delta[1]*(405 if brief['ratio']=='16:9' else 540)/target.height]
    report = dict(version='raster-v1',page=receipt['page'],revision=receipt['revision'],
                  design_sha256=digest(target_path),image_sha256=digest(background_path),
                  draft_sha256=receipt['draft_sha256'],preview_sha256=digest(preview),
                  objects=objects,requires_inspection=True)
    return report, (target,background,rendered)


def compare(project, receipt_file, preview, output):
    report, images = analyze(project,receipt_file,preview)
    output=Path(output).resolve(); output.mkdir(parents=True,exist_ok=False)
    for i,item in enumerate(report['objects'],1):
        crops=[im.crop(item['region']) for im in images]
        w,h=crops[0].size
        crops.append(ImageChops.difference(crops[0],crops[2]))
        panel=Image.new('RGB',(w*4,h+25),'white'); draw=ImageDraw.Draw(panel)
        for n,(crop,label) in enumerate(zip(crops,('TARGET','ERASED BACKGROUND','PPT RENDER','ABS DIFFERENCE'))):
            panel.paste(crop,(w*n,25));draw.text((w*n+3,3),label,fill='black')
        panel.save(output/f'{i:03d}.png')
        item['panel']=str(output/f'{i:03d}.png')
    w,h=images[0].size
    overview=Image.new('RGB',(w*2,h),'white');overview.paste(images[0]);overview.paste(images[2],(w,0));overview.save(output/'overview.png')
    write(output/'comparison.json',report)
    return dict(report=str(output/'comparison.json'),overview=str(output/'overview.png'),
                objects=[dict(id=o['id'],flags=o['flags'],metrics=o['metrics'],panel=o['panel']) for o in report['objects']],
                next='Inspect overview and EVERY object panel; use native object ID and runs in comparison.json to adjust via MCP, recompose, rerender, compare again. Metrics are not a visual approval.')


def verify(project, receipt_file, preview, qa, connection=None):
    reference=qa.get('comparison_file')
    if not reference or not Path(reference).is_absolute():
        raise ValueError('raster-v1 requires absolute comparison_file from compare-render')
    saved=read(reference); current,_=analyze(project,receipt_file,preview,connection)
    clean=dict(saved); clean['objects']=[{k:v for k,v in o.items() if k!='panel'} for o in saved.get('objects',[])]
    if clean != current:
        raise ValueError('Comparison is stale or changed; rerun compare-render on this checkpoint and preview')
    # Suspicious measurements are review findings, never silently promoted to pass.
    exceptions=qa.get('comparison_exceptions',{})
    for item in current['objects']:
        for flag in item['flags']:
            detail=exceptions.get(item['id'],{}).get(flag,{})
            if not isinstance(detail,dict) or any(not isinstance(detail.get(k),str) or not detail[k].strip() for k in ('reason','visual_evidence')):
                raise ValueError(f"Comparison finding {item['id']}: {flag}; fix via MCP or document a specific measurement false positive with reason and visual_evidence")
    return dict(comparison_sha256=digest(reference),comparison_file=reference)
