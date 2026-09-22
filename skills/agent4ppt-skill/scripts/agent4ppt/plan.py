"""Validate a presentation brief and compile self-contained image requests."""
from pathlib import Path
import json
import re
from .files import digest
from .composition import MODES, validate_overlays

BACKENDS = {'builtin', 'openai', 'atlascloud'}


def execution_contract(brief):
    return {'max_page_workers': 10, 'project_parallelism': min(10, brief['parallelism']),
            'dispatch': 'After sample acceptance maximize available page workers; refill with dispatch-plan --host-slots FREE_CHILD_SLOTS.',
            'guide': str(Path(__file__).resolve().parents[2] / 'references/production.md'),
            'native_batch': 'mcp-batch validates one page correction plan; host executes MCP calls sequentially in one orchestration pass, then saves/adopts/renders.',
            'shared_powerpoint': 'Serialize calls on a shared endpoint; never close a session while other workers use that process.'}


def describe(value):
    """Keep structured art direction legible without Python repr artifacts."""
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2)


def reference(entry, base):
    """Accept a structured asset or an outline's Markdown image annotation."""
    if isinstance(entry, str):
        match = re.search(r'!\[([^\]]*)\]\((<[^>]+>|[^)]+)\)', entry)
        if not match:
            raise ValueError('Text references must contain a Markdown image')
        role = (entry[:match.start()] + ' ' + match.group(1) + ' ' + entry[match.end():]).strip()
        entry = {'path': match.group(2).strip('<>'), 'role': role or 'required source image'}
    if not isinstance(entry, dict) or not entry.get('path') or not entry.get('role'):
        raise ValueError('Each reference needs path and role')
    source = (Path(base) / entry['path']).resolve()
    if not source.is_file():
        raise ValueError(f'Missing reference: {source.name}')
    return dict(entry, path=str(source), sha256=digest(source))


def method(value, backend):
    if value is None:
        return None
    if not isinstance(value, dict) or not value.get('tool') or value.get('mode') not in ('generate', 'edit'):
        raise ValueError('generation_method requires tool and mode (generate or edit)')
    if value.get('backend', backend) != backend:
        raise ValueError('Generation method and project backend differ')
    return dict(value, backend=backend)


def validate(brief, base):
    if not isinstance(brief, dict) or not str(brief.get('title', '')).strip():
        raise ValueError('A title is required')
    ratio = brief.get('ratio', '16:9')
    if ratio not in ('16:9', '4:3'):
        raise ValueError('ratio must be 16:9 or 4:3')
    backend = brief.get('backend', 'builtin')
    if backend not in BACKENDS:
        raise ValueError('Unknown backend')
    pages = brief.get('pages')
    if not isinstance(pages, list) or not 1 <= len(pages) <= 500:
        raise ValueError('pages must contain 1 to 500 entries')
    limit = brief.get('parallelism', 10)
    if type(limit) is not int or not 1 <= limit <= 10:
        raise ValueError('parallelism must be 1..10')
    prepared = dict(brief, ratio=ratio, backend=backend, parallelism=limit)
    mode = brief.get('mode', 'full_slide')
    if mode not in MODES:
        raise ValueError('mode must be full_slide or editable')
    prepared['mode'] = mode
    if mode == 'editable':
        prepared.setdefault('editable_workflow', 'full_slide_first')
        if prepared['editable_workflow'] not in ('full_slide_first', 'reserved'):
            raise ValueError('Unknown editable_workflow')
        if prepared['editable_workflow'] == 'full_slide_first':
            prepared['review_policy'] = 'structured-v1'
    if brief.get('review_policy') not in (None, 'structured-v1'):
        raise ValueError('Unknown review_policy')
    if brief.get('review_policy') and mode != 'editable':
        raise ValueError('structured-v1 review requires editable mode')
    if brief.get('style_name'):
        from .styles import catalog
        values = catalog()
        if brief['style_name'] not in values:
            raise ValueError('Unknown style_name; inspect styles first')
        prepared['style_recipe'] = values[brief['style_name']]
    if brief.get('generation_method'):
        prepared['generation_method'] = method(brief['generation_method'], backend)
    prepared['pages'] = []
    for index, item in enumerate(pages, 1):
        if not isinstance(item, dict) or not str(item.get('title', '')).strip():
            raise ValueError(f'Page {index} needs a title')
        page = dict(item, number=index)
        if mode == 'editable':
            page['overlays'] = validate_overlays(item.get('overlays'), base)
            from .layout import reserved_regions
            reserved_regions(page, ratio)
            raster_text = item.get('raster_text', [])
            if not isinstance(raster_text, list) or any(not isinstance(x, str) for x in raster_text):
                raise ValueError('raster_text must be a list of exact strings allowed in the image')
            page['raster_text'] = raster_text
            # Keep one unambiguous visible-copy source in this mode.
            if item.get('bullets') or item.get('text'):
                raise ValueError('Editable copy belongs in overlays or raster_text, not bullets/text')
        elif item.get('overlays'):
            raise ValueError('Set mode=editable to export overlays')
        for field in ('bullets', 'constraints'):
            if not isinstance(page.get(field, []), list) or any(not isinstance(x, str) for x in page.get(field, [])):
                raise ValueError(f'{field} must be a list of strings')
        page['references'] = []
        for ref in item.get('references', []):
            page['references'].append(reference(ref, base))
        prepared['pages'].append(page)
    return prepared


def compile_request(brief, page, style_reference=None, generation_method=None):
    references = list(page['references'])
    if style_reference:
        references.insert(0, {'path': str(style_reference), 'role': 'style only; do not copy page content', 'sha256': digest(style_reference)})
    sections = [f'Create one complete {brief["ratio"]} presentation slide in {brief.get("language", "Chinese")}.',
                'Render the title and all specified copy clearly. No invented facts, extra page numbers or watermarks.',
                'VISIBLE TEXT BOUNDARY: Render only the page title, Exact copy and Exact structured text values. '
                'All other sections are instructions, not slide copy. In particular do not typeset the style recipe, '
                'its keys or descriptions, deck context, audience, file paths, or this instruction. '
                'Do not add explanatory paragraphs unless explicitly listed in the visible text.',
                f'Deck: {brief["title"]}', f'Audience: {brief.get("audience", "general")}',
                f'Context: {describe(brief.get("context", ""))}',
                f'Visual identity: {describe(brief.get("style", "Follow the complete style recipe below" if brief.get("style_recipe") else "clean editorial"))}',
                f'Page title: {page["title"]}', 'Exact copy:\n' + '\n'.join(page.get('bullets', [])),
                f'Composition: {describe(page.get("layout", "Choose a content-appropriate layout with clear hierarchy"))}',
                f'Page background: {describe(page.get("context", ""))}',
                'Constraints:\n' + '\n'.join(page.get('constraints', []))]
    for label, value in [('Style recipe', brief.get('style_recipe')),
                         ('Page role', page.get('role')),
                         ('Canvas', page.get('canvas', brief.get('canvas'))),
                         ('Visual elements', page.get('visual_elements')),
                         ('Exact structured text', page.get('text'))]:
        if value:
            sections.append(label + ':\n' + describe(value))
    selected_method = generation_method or brief.get('generation_method')
    if selected_method:
        sections.append('Required generation method:\n' + describe(selected_method))
    for i, ref in enumerate(references, 1):
        sections.append(f'Image {i}: {ref["role"]}. Input: {ref["path"]}')
        if ref.get('fidelity'):
            sections.append('Asset fidelity: ' + describe(ref['fidelity']))
    sections.append('Preserve evidence figures and product identity. Do not invent or relabel their data. '
                    'Reference-guided generation does not guarantee pixel-exact preservation; report any discrepancy.')
    mode = brief.get('mode', 'full_slide')
    if mode == 'editable' and brief.get('editable_workflow') == 'full_slide_first':
        sections = [s for s in sections if not s.startswith(('Page title:', 'Exact copy:', 'Exact structured text:'))]
        sections.append('FULL-SLIDE DESIGN STAGE: Render a finished slide WITH all selected text below and fixed raster text. '
                        'Design text and artwork together. Do not leave text blanks or reserve empty overlay boxes. '
                        'Overlay coordinates are provisional and must be measured again from the finished design by the host. '
                        'The page title is metadata; only render the exact visible copy below, once each.')
        sections.append('Exact visible copy:\n' + describe([o['text'] for o in page['overlays'] if o['type'] == 'text'] + page.get('raster_text', [])))
        for overlay in page['overlays']:
            if overlay['type'] == 'image':
                references.append(dict(path=overlay['path'], sha256=overlay['sha256'], role=f'Include this replaceable picture in the complete design: {overlay["id"]}'))
                sections.append(f'Render supplied picture {overlay["id"]}: {overlay["path"]}')
    elif mode == 'editable':
        # Replace the full-image text contract, including the title and copy blocks.
        sections = [s for s in sections[3:] if not s.startswith(('Page title:', 'Exact copy:', 'Exact structured text:'))]
        sections.insert(0,
            f'Create ONE complete {brief["ratio"]} presentation-page artwork, retaining the entire composition. '
            'Render the illustrations, decorative icons, separators, arrows, circles, lighting and other raster-owned details together. '
            'Do not reduce the result to a generic background or separate asset tiles. '
            'EDITABLE BOUNDARY OVERRIDES STYLE EXAMPLES: the reserved overlays below will be added as native PPT objects later. '
            'Do not draw their text, numbers, placeholder words, or image contents into the artwork. '
            'Keep their normalized x/y/w/h regions naturally readable without opaque cover-up panels. '
            'For numbered circles, keep the circle in the artwork and leave its center free for the native number. '
            'Other visual symbols and explicitly allowed raster text may remain in the artwork. '
            'Page title is context only unless explicitly listed as raster text. '
            'Do not typeset instructions, metadata, coordinates, IDs, or style recipe descriptions.')
        regions = [{k: v for k, v in item.items() if k not in ('path', 'sha256')}
                   for item in page['overlays']]
        sections.extend([f'Page subject (context only): {page["title"]}',
                         'Reserved native overlays (layout context, NEVER render these contents):\n' + describe(regions),
                         'Exact raster text allowed in the artwork:\n' + describe(page.get('raster_text', []))])
        from .layout import reserved_regions
        sections.append('Native overlay safety regions (including margins):\n' + describe(reserved_regions(page, brief['ratio'])) +
                        '\nQuiet regions may retain a smooth background but must exclude foreground objects, arrows, separator lines, and decorative edges. '
                        'Container regions may retain a simple circle or panel fill; keep its text interior clear. '
                        'Layout guide colored rectangles are diagnostic only: NEVER copy their fills, borders or markings into final artwork.')
    return {'page': page['number'], 'backend': brief['backend'], 'prompt': '\n\n'.join(sections),
            'execution': execution_contract(brief),
            'mode': mode, 'editable_workflow': brief.get('editable_workflow', 'reserved'),
            'stage': 'design' if mode == 'editable' and brief.get('editable_workflow') == 'full_slide_first' else 'background',
            'overlays': page.get('overlays', []),
            'review_policy': brief.get('review_policy'),
            'native_acceptance': brief.get('native_acceptance'),
            'visual_comparison': brief.get('visual_comparison'),
            'native_review': ({'guide': str(Path(__file__).resolve().parents[2] / 'references/visual-replication.md'),
                               'target': 'accepted complete design',
                               'loop': 'edit named objects in PowerPoint; verify Latin and East Asian fonts; save; compose --native-draft; render checkpoint; visually compare; repeat until accepted',
                               'acceptance': 'preserve every selected text and line break; coordinator inspects content, typography, alignment and artwork; hashes alone do not prove visual quality'}
                              if mode == 'editable' else None),
            'references': references, 'options': dict(brief.get('image_options', {}), **page.get('image_options', {})),
            'title': page['title'], 'generation_method': selected_method,
            'requires_images': bool(references)}

# a4p-provenance: a4p-50d41ed6-f9f9-4470-ac9c-e700dd134a07/8917f63a5aa49b42b494
