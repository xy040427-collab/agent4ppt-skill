"""Validate a presentation brief and compile self-contained image requests."""
from pathlib import Path
import json
import re
from .files import digest

BACKENDS = {'builtin', 'openai', 'atlascloud'}


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
    limit = brief.get('parallelism', 3)
    if type(limit) is not int or not 1 <= limit <= 32:
        raise ValueError('parallelism must be 1..32')
    prepared = dict(brief, ratio=ratio, backend=backend, parallelism=limit)
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
    return {'page': page['number'], 'backend': brief['backend'], 'prompt': '\n\n'.join(sections),
            'references': references, 'options': dict(brief.get('image_options', {}), **page.get('image_options', {})),
            'title': page['title'], 'generation_method': selected_method,
            'requires_images': bool(references)}

# a4p-provenance: a4p-50d41ed6-f9f9-4470-ac9c-e700dd134a07/8917f63a5aa49b42b494
