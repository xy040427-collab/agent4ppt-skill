"""Write an OPC presentation package directly, without a slide-layout library."""
import html
import io
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from .files import atomic

A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
NS = f'xmlns:a="{A}" xmlns:p="{P}" xmlns:r="{R}"'


def xml(body):
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' + body).encode()


def relationships(items):
    return xml('<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' +
               ''.join(f'<Relationship Id="rId{i}" Type="{R}/{kind}" Target="{html.escape(target, quote=True)}"/>'
                       for i, (kind, target) in enumerate(items, 1)) + '</Relationships>')


def group():
    return ('<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
            '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>'
            '<a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>')


def parse_notes(text):
    result, current, lines = {}, None, []
    for line in text.splitlines() + ['## Slide 0']:
        match = re.match(r'^\s*#{1,6}\s*(?:Slide\s*(\d+)|第\s*(\d+)\s*页)(?:\s|[:：]|$)', line, re.I)
        if match:
            if current is not None:
                result[current] = '\n'.join(lines).strip()
            current, lines = int(match.group(1) or match.group(2)), []
        elif current is not None:
            lines.append(line)
    return result


def media(path, max_bytes=None):
    from PIL import Image
    with Image.open(path) as source:
        source.load()
        if source.format in ('PNG', 'JPEG') and (max_bytes is None or Path(path).stat().st_size <= max_bytes):
            return Path(path).read_bytes(), 'png' if source.format == 'PNG' else 'jpg'
        buffer = io.BytesIO()
        if max_bytes is None:
            source.convert('RGBA').save(buffer, 'PNG')
            return buffer.getvalue(), 'png'
        if max_bytes <= 0:
            raise ValueError('max_bytes must be positive')
        rgba = source.convert('RGBA')
        rgb = Image.new('RGB', rgba.size, 'white')
        rgb.paste(rgba, mask=rgba.getchannel('A'))
        for _ in range(12):
            for quality in (95, 85, 75, 60, 40, 25):
                buffer = io.BytesIO()
                rgb.save(buffer, 'JPEG', quality=quality, optimize=True)
                if len(buffer.getvalue()) <= max_bytes:
                    return buffer.getvalue(), 'jpg'
            if min(rgb.size) <= 32:
                break
            rgb = rgb.resize((max(1, int(rgb.width*.8)), max(1, int(rgb.height*.8))), Image.Resampling.LANCZOS)
        raise ValueError('Image cannot fit requested byte budget without excessive degradation')


def export_pptx(images, output, ratio='16:9', notes=None, title='Presentation', max_bytes=None, overlays=None, native_text=None):
    if ratio not in ('16:9', '4:3') or not images:
        raise ValueError('Nonempty images and 16:9 or 4:3 ratio required')
    width, height = 9144000, (5143500 if ratio == '16:9' else 6858000)
    notes = notes or {}
    overlays = overlays or {}
    parts, overrides = {}, {}

    def add(name, data, kind=None):
        parts[name] = data
        if kind:
            overrides['/' + name] = 'application/vnd.openxmlformats-officedocument.' + kind + '+xml'

    add('_rels/.rels', relationships([('officeDocument', 'ppt/presentation.xml')]))
    ids = ''.join(f'<p:sldId id="{255+i}" r:id="rId{i+2}"/>' for i in range(1, len(images)+1))
    add('ppt/presentation.xml', xml(f'<p:presentation {NS}><p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>'
        f'<p:sldIdLst>{ids}</p:sldIdLst>'
        f'<p:sldSz cx="{width}" cy="{height}"/><p:notesSz cx="6858000" cy="9144000"/></p:presentation>'), 'presentationml.presentation.main')
    add('ppt/_rels/presentation.xml.rels', relationships([('slideMaster', 'slideMasters/slideMaster1.xml'),
        ('notesMaster', 'notesMasters/notesMaster1.xml')] + [('slide', f'slides/slide{i}.xml') for i in range(1, len(images)+1)]))
    mapping = 'accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" bg1="lt1" bg2="lt2" folHlink="folHlink" hlink="hlink" tx1="dk1" tx2="dk2"'
    add('ppt/slideMasters/slideMaster1.xml', xml(f'<p:sldMaster {NS}><p:cSld><p:spTree>{group()}</p:spTree></p:cSld><p:clrMap {mapping}/>'
        '<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst><p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles></p:sldMaster>'), 'presentationml.slideMaster')
    add('ppt/slideMasters/_rels/slideMaster1.xml.rels', relationships([('slideLayout', '../slideLayouts/slideLayout1.xml'), ('theme', '../theme/theme1.xml')]))
    add('ppt/slideLayouts/slideLayout1.xml', xml(f'<p:sldLayout {NS} type="blank" preserve="1"><p:cSld name="Blank"><p:spTree>{group()}</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>'), 'presentationml.slideLayout')
    add('ppt/slideLayouts/_rels/slideLayout1.xml.rels', relationships([('slideMaster', '../slideMasters/slideMaster1.xml')]))
    colors = dict(dk1='000000', lt1='FFFFFF', dk2='222222', lt2='EEEEEE', accent1='AF8D5A', accent2='287D8E', accent3='765697', accent4='B34D45', accent5='60885C', accent6='A67542', hlink='0563C1', folHlink='954F72')
    palette = ''.join(f'<a:{name}><a:srgbClr val="{value}"/></a:{name}>' for name,value in colors.items())
    fills = '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>' * 3
    lines = '<a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/></a:ln>' * 3
    font = '<a:latin typeface="Arial"/><a:ea typeface="Microsoft YaHei"/><a:cs typeface="Arial"/>'
    add('ppt/theme/theme1.xml', xml(f'<a:theme xmlns:a="{A}" name="Agent4PPT"><a:themeElements><a:clrScheme name="Neutral">{palette}</a:clrScheme>'
        f'<a:fontScheme name="Readable"><a:majorFont>{font}</a:majorFont><a:minorFont>{font}</a:minorFont></a:fontScheme>'
        f'<a:fmtScheme name="Basic"><a:fillStyleLst>{fills}</a:fillStyleLst><a:lnStyleLst>{lines}</a:lnStyleLst>'
        f'<a:effectStyleLst>{"<a:effectStyle><a:effectLst/></a:effectStyle>"*3}</a:effectStyleLst><a:bgFillStyleLst>{fills}</a:bgFillStyleLst></a:fmtScheme></a:themeElements></a:theme>'), 'theme')
    add('ppt/notesMasters/notesMaster1.xml', xml(f'<p:notesMaster {NS}><p:cSld><p:spTree>{group()}</p:spTree></p:cSld><p:clrMap {mapping}/><p:notesStyle/></p:notesMaster>'), 'presentationml.notesMaster')
    add('ppt/notesMasters/_rels/notesMaster1.xml.rels', relationships([('theme', '../theme/theme1.xml')]))
    for i, image in enumerate(images, 1):
        blob, extension = media(image, max_bytes)
        parts[f'ppt/media/page{i}.{extension}'] = blob
        picture = (f'<p:pic><p:nvPicPr><p:cNvPr id="2" name="Page {i}" descr="{html.escape(title, quote=True)}"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>'
                   '<p:blipFill><a:blip r:embed="rId2"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>'
                   f'<p:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{width}" cy="{height}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>')
        rels = [('slideLayout', '../slideLayouts/slideLayout1.xml'), ('image', f'../media/page{i}.{extension}')]
        native = ''
        from .composition import text_shape, image_shape, verify_assets
        verify_assets(overlays.get(i, []))
        for identity, item in enumerate(overlays.get(i, []), 3):
            if item['type'] == 'text':
                native += text_shape(item, identity, width, height)
            else:
                asset, ext = media(item['path'], max_bytes)
                target = f'overlay{i}-{identity}.{ext}'
                parts[f'ppt/media/{target}'] = asset
                rels.append(('image', f'../media/{target}'))
                native += image_shape(item, identity, len(rels), width, height)
        if native_text and i in native_text:
            native = native_text[i]
        add(f'ppt/slides/slide{i}.xml', xml(f'<p:sld {NS}><p:cSld><p:spTree>{group()}{picture}{native}</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>'), 'presentationml.slide')
        if notes.get(i):
            rels.append(('notesSlide', f'../notesSlides/notesSlide{i}.xml'))
            paragraphs = ''.join(f'<a:p><a:r><a:rPr lang="zh-CN"/><a:t>{html.escape(line)}</a:t></a:r></a:p>' for line in notes[i].split('\n'))
            note_shape = '<p:sp><p:nvSpPr><p:cNvPr id="2" name="Speaker notes"/><p:cNvSpPr/><p:nvPr><p:ph type="body" idx="1"/></p:nvPr></p:nvSpPr><p:spPr/><p:txBody><a:bodyPr/><a:lstStyle/>' + paragraphs + '</p:txBody></p:sp>'
            add(f'ppt/notesSlides/notesSlide{i}.xml', xml(f'<p:notes {NS}><p:cSld><p:spTree>{group()}{note_shape}</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:notes>'), 'presentationml.notesSlide')
            add(f'ppt/notesSlides/_rels/notesSlide{i}.xml.rels', relationships([('notesMaster', '../notesMasters/notesMaster1.xml'), ('slide', f'../slides/slide{i}.xml')]))
        add(f'ppt/slides/_rels/slide{i}.xml.rels', relationships(rels))
    types = '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    for extension, content in [('rels','application/vnd.openxmlformats-package.relationships+xml'), ('xml','application/xml'), ('png','image/png'), ('jpg','image/jpeg')]:
        types += f'<Default Extension="{extension}" ContentType="{content}"/>'
    types += ''.join(f'<Override PartName="{name}" ContentType="{content}"/>' for name,content in overrides.items()) + '</Types>'
    parts['[Content_Types].xml'] = xml(types)
    result = io.BytesIO()
    with zipfile.ZipFile(result, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, content in parts.items():
            if name.endswith(('.xml','.rels')):
                ET.fromstring(content)
            archive.writestr(name, content)
    atomic(output, result.getvalue())
    return {'path': str(Path(output).resolve()), 'pages': len(images), 'notes': sum(bool(notes.get(i)) for i in range(1,len(images)+1))}


def export_project(project, output=None, max_bytes=None):
    # Hold the transaction through serialization so a concurrent revision cannot
    # turn an already checked page into an incomplete page during the export.
    with project.transaction() as db:
        brief = project.settings(db)
        rows = db.execute('SELECT * FROM pages ORDER BY number').fetchall()
        if not rows or any(row['state']!='complete' for row in rows):
            raise ValueError('Every page must be completed before export')
        from .files import digest
        images = [project.root / row['image'] for row in rows]
        for row,image in zip(rows,images):
            if digest(image)!=row['sha256']:
                raise ValueError(f'Page {row["number"]} image changed after QA')
        import json
        layers, native_text = {}, {}
        if brief.get('mode') == 'editable':
            for row in rows:
                review = project.verify_review(db, row['number'])
                layers[row['number']] = json.loads(row['spec'])['overlays']
                if review.get('native_draft'):
                    from .native import read_text_shapes
                    native_text[row['number']] = read_text_shapes((project.root/review['draft']).read_bytes(),
                        layers[row['number']], row['sha256'], brief['ratio'])
        path = project.root / 'notes.md'
        notes = parse_notes(path.read_text(encoding='utf-8')) if path.exists() else {}
        if native_text and max_bytes is not None:
            raise ValueError('Reviewed native pages must retain their background bytes; omit image compression')
        result = export_pptx(images, output or project.root/'presentation.pptx', brief['ratio'], notes, brief['title'], max_bytes, layers, native_text)
        project.event(db, None, 'exported', result)
    return result

# a4p-provenance: a4p-50d41ed6-f9f9-4470-ac9c-e700dd134a07/97d1408eb4fc0b8a046f
