"""A whole-page image with explicitly selected native overlays."""
import hashlib
import html
import json
import math
import re
from pathlib import Path
from .files import digest


MODES = ('full_slide', 'editable')


def fingerprint(page):
    return hashlib.sha256(json.dumps(page, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def validate_overlays(items, base):
    if not isinstance(items, list) or not items:
        raise ValueError('Editable pages require explicit overlays')
    result, ids = [], set()
    for source in items:
        if not isinstance(source, dict):
            raise ValueError('Each overlay must be an object')
        item = dict(source)
        identity = item.get('id')
        if not isinstance(identity, str) or not identity.strip() or identity in ids:
            raise ValueError('Overlay IDs must be nonempty and unique within a page')
        ids.add(identity)
        if item.get('type') not in ('text', 'image'):
            raise ValueError('Bundled overlays support text or replaceable image; use host tools for other native objects')
        if item.get('background_policy', 'quiet') not in ('quiet', 'container'):
            raise ValueError('background_policy must be quiet or container')
        for field in ('x', 'y', 'w', 'h'):
            value = item.get(field)
            if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError('Overlay bounds must be finite normalized coordinates in 0..1')
        if item['w'] <= 0 or item['h'] <= 0 or item['x'] + item['w'] > 1.000001 or item['y'] + item['h'] > 1.000001:
            raise ValueError('Overlay must fit inside the page with positive width and height')
        if item['type'] == 'text':
            if 'size' in item:
                raise ValueError('Text overlay uses unsupported size; use font_size in points (remove size even when font_size is present)')
            if not isinstance(item.get('text'), str) or not item['text'].strip():
                raise ValueError('Text overlays require exact nonempty text')
            item.setdefault('font', 'Microsoft YaHei')
            item.setdefault('font_size', 20)
            item.setdefault('color', '172B4D')
            item.setdefault('align', 'left')
            item.setdefault('valign', 'top')
            item.setdefault('bold', False)
            if not isinstance(item['font'], str) or not item['font'].strip():
                raise ValueError('Overlay font must be nonempty')
            if type(item['font_size']) not in (int, float) or not math.isfinite(item['font_size']) or not 1 <= item['font_size'] <= 200:
                raise ValueError('Overlay font_size must be 1..200 points')
            if isinstance(item.get('color'), str):
                item['color'] = item['color'].lstrip('#')
            if not isinstance(item['color'], str) or not re.fullmatch(r'[0-9a-fA-F]{6}', item['color']):
                raise ValueError('Overlay color must contain six hexadecimal digits')
            if item['align'] not in ('left', 'center', 'right') or item['valign'] not in ('top', 'middle', 'bottom') or type(item['bold']) is not bool:
                raise ValueError('Invalid overlay alignment or bold')
        else:
            if not isinstance(item.get('path'), str) or not item['path']:
                raise ValueError('Image overlays require a path')
            path = (Path(base) / item['path']).resolve()
            checksum = digest(path)
            if item.get('sha256') and item['sha256'] != checksum:
                raise ValueError('Overlay image changed; remove the old hash only when deliberately replacing it')
            item.update(path=str(path), sha256=checksum)
        result.append(item)
    return result


def verify_assets(overlays):
    for item in overlays:
        if item['type'] == 'image' and digest(item['path']) != item['sha256']:
            raise ValueError('Overlay image changed; revise the page deliberately')


def transform(item, width, height):
    x, y, w, h = (round(item[k] * extent) for k, extent in [('x', width), ('y', height), ('w', width), ('h', height)])
    return f'<a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm>'


def text_shape(item, identity, width, height):
    esc = lambda value: html.escape(str(value), quote=True)
    align = {'left': 'l', 'center': 'ctr', 'right': 'r'}[item['align']]
    anchor = {'top': 't', 'middle': 'ctr', 'bottom': 'b'}[item['valign']]
    font = esc(item['font'])
    props = (f'<a:rPr lang="zh-CN" sz="{round(item["font_size"] * 100)}" b="{int(item["bold"])}">'
             f'<a:solidFill><a:srgbClr val="{item["color"]}"/></a:solidFill>'
             f'<a:latin typeface="{font}"/><a:ea typeface="{font}"/><a:cs typeface="{font}"/></a:rPr>')
    paragraphs = ''.join(f'<a:p><a:pPr algn="{align}"/><a:r>{props}<a:t xml:space="preserve">{esc(line)}</a:t></a:r></a:p>'
                         for line in item['text'].split('\n'))
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{identity}" name="{esc(item["id"])}"/>'
            '<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr>{transform(item, width, height)}<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/>'
            '<a:ln><a:noFill/></a:ln></p:spPr>'
            f'<p:txBody><a:bodyPr wrap="square" lIns="0" tIns="0" rIns="0" bIns="0" anchor="{anchor}">'
            f'<a:noAutofit/></a:bodyPr><a:lstStyle/>{paragraphs}</p:txBody></p:sp>')


def image_shape(item, identity, relationship, width, height):
    name = html.escape(item['id'], quote=True)
    return (f'<p:pic><p:nvPicPr><p:cNvPr id="{identity}" name="{name}"/>'
            '<p:cNvPicPr/><p:nvPr/></p:nvPicPr>'
            f'<p:blipFill><a:blip r:embed="rId{relationship}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>'
            f'<p:spPr>{transform(item, width, height)}<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>')
