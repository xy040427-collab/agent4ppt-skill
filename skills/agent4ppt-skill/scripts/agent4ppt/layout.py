"""Disposable layout guides, not final slide artwork or visual QA substitutes."""
import math
from pathlib import Path


def reserved_regions(page, ratio='16:9'):
    aspect = 16 / 9 if ratio == '16:9' else 4 / 3
    regions = []
    for item in page['overlays']:
        pad = item.get('safe_padding', .012)
        if type(pad) not in (int, float) or not math.isfinite(pad) or not 0 <= pad <= .1:
            raise ValueError('safe_padding must be a finite fraction of page height in 0..0.1')
        px = pad / aspect
        x, y = max(0, item['x'] - px), max(0, item['y'] - pad)
        right, bottom = min(1, item['x'] + item['w'] + px), min(1, item['y'] + item['h'] + pad)
        regions.append(dict(id=item['id'], x=x, y=y, w=right-x, h=bottom-y,
                            policy=item.get('background_policy', 'quiet')))
    return regions


def layout_issues(page, ratio='16:9'):
    """Report native rectangle intersections. Background pixels require visual review."""
    issues = []
    overlays = page['overlays']
    for i, a in enumerate(overlays):
        for b in overlays[i+1:]:
            dx = min(a['x']+a['w'], b['x']+b['w']) - max(a['x'], b['x'])
            dy = min(a['y']+a['h'], b['y']+b['h']) - max(a['y'], b['y'])
            if dx > 1e-6 and dy > 1e-6:
                issues.append(dict(kind='native_bounds_overlap', objects=[a['id'], b['id']], area=dx*dy))
    reserved_regions(page, ratio)
    return issues


def write_layout_guide(page, output, ratio='16:9'):
    """Draw only diagnostic reservation boxes for image-model layout conditioning."""
    from PIL import Image, ImageDraw
    width, height = (1600, 900) if ratio == '16:9' else (1200, 900)
    canvas = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(canvas)
    for region in reserved_regions(page, ratio):
        x, y, w, h = (region[k] for k in ('x', 'y', 'w', 'h'))
        draw.rectangle((round(x*width), round(y*height), round((x+w)*width), round((y+h)*height)),
                       fill='#FFF1F7', outline='#D84A84', width=2)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)
    return {'path': str(output.resolve()), 'role': 'layout guide only: pink rectangles reserve native overlays and safety margins; remove all pink fills/outlines in final artwork. Keep these regions quiet. This is NOT a style reference.'}
