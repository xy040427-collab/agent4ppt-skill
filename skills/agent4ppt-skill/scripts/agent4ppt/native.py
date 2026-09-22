"""Validate and retain self-contained PowerPoint text shapes after host editing."""
import hashlib
import io
import posixpath
import zipfile
from xml.etree import ElementTree as ET
from .package import A, P, R


def read_text_shapes(blob, overlays, background_sha256, ratio):
    """Accept one background plus named text boxes, never flatten host edits."""
    if any(item['type'] != 'text' for item in overlays):
        raise ValueError('Native draft adoption currently supports text overlays only')
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        presentation = ET.fromstring(archive.read('ppt/presentation.xml'))
        if len(presentation.findall(f'{{{P}}}sldIdLst/{{{P}}}sldId')) != 1:
            raise ValueError('Native draft must contain exactly one slide')
        size = presentation.find(f'{{{P}}}sldSz')
        if size is None or (int(size.get('cx')), int(size.get('cy'))) != (9144000, 5143500 if ratio == '16:9' else 6858000):
            raise ValueError('Native draft must retain the compose canvas size')
        rels = ET.fromstring(archive.read('ppt/_rels/presentation.xml.rels'))
        slide_id = presentation.find(f'{{{P}}}sldIdLst/{{{P}}}sldId').get(f'{{{R}}}id')
        target = next(r.get('Target') for r in rels if r.get('Id') == slide_id)
        part = posixpath.normpath(posixpath.join('ppt', target)) if not target.startswith('/') else target.lstrip('/')
        slide = ET.fromstring(archive.read(part))
        tree = slide.find(f'{{{P}}}cSld/{{{P}}}spTree')
        if tree is None or any(c.tag not in {f'{{{P}}}{t}' for t in ('nvGrpSpPr','grpSpPr','pic','sp')} for c in tree):
            raise ValueError('Native draft contains unsupported objects')
        pictures = tree.findall(f'{{{P}}}pic')
        if len(pictures) != 1:
            raise ValueError('Native draft requires exactly one unchanged background')
        picture = pictures[0]
        transform = picture.find(f'{{{P}}}spPr/{{{A}}}xfrm')
        off, ext = transform.find(f'{{{A}}}off'), transform.find(f'{{{A}}}ext')
        if dict(off.attrib) != {'x':'0','y':'0'} or dict(ext.attrib) != {'cx':size.get('cx'),'cy':size.get('cy')} or any(k in transform.attrib for k in ('rot','flipH','flipV')):
            raise ValueError('Native background geometry changed')
        fill = picture.find(f'{{{P}}}blipFill')
        if fill.find(f'{{{A}}}srcRect') is not None or fill.find(f'{{{A}}}stretch') is None:
            raise ValueError('Native background must not be cropped')
        blip = fill.find(f'{{{A}}}blip')
        if list(blip):
            raise ValueError('Native background image effects are unsupported')
        relpath = posixpath.join(posixpath.dirname(part), '_rels', posixpath.basename(part)+'.rels')
        rels = ET.fromstring(archive.read(relpath))
        rel = next(r for r in rels if r.get('Id') == blip.get(f'{{{R}}}embed'))
        target = rel.get('Target')
        media = posixpath.normpath(posixpath.join(posixpath.dirname(part),target)) if not target.startswith('/') else target.lstrip('/')
        if rel.get('TargetMode') == 'External' or hashlib.sha256(archive.read(media)).hexdigest() != background_sha256:
            raise ValueError('Native draft background differs from registered image')
        expected = {item['id']: item['text'] for item in overlays}
        found, result = set(), []
        for shape in tree.findall(f'{{{P}}}sp'):
            identity = shape.find(f'{{{P}}}nvSpPr/{{{P}}}cNvPr')
            name = identity.get('name')
            if name not in expected or name in found:
                raise ValueError('Native text object IDs must match selected overlays')
            found.add(name)
            body = shape.find(f'{{{P}}}txBody')
            if body is None:
                raise ValueError('Native overlay must remain editable text')
            paragraphs = []
            for paragraph in body.findall(f'{{{A}}}p'):
                paragraphs.append(''.join('\n' if node.tag == f'{{{A}}}br' else (node.text or '')
                                          for node in paragraph.iter() if node.tag in (f'{{{A}}}t',f'{{{A}}}br')))
            if '\n'.join(paragraphs) != expected[name].replace('\r\n','\n'):
                raise ValueError('Native draft must preserve exact selected text and line breaks')
            for node in shape.iter():
                if any(key.startswith('{'+R+'}') for key in node.attrib) or node.tag in (f'{{{A}}}schemeClr',f'{{{A}}}style',f'{{{P}}}style'):
                    raise ValueError('Native text must use explicit formatting without external or theme dependencies')
            for run in body.findall(f'.//{{{A}}}r'):
                props = run.find(f'{{{A}}}rPr')
                if props is None or props.get('sz') is None or any(props.find(f'{{{A}}}{t}') is None for t in ('latin','ea','solidFill')):
                    raise ValueError('Native runs require explicit size, Latin/East Asian fonts and color')
            identity.set('id', str(len(result)+3))
            result.append(ET.tostring(shape, encoding='unicode'))
        if found != set(expected):
            raise ValueError('Native draft is missing selected text objects')
        if list(tree).index(picture) > min((list(tree).index(s) for s in tree.findall(f'{{{P}}}sp')), default=999):
            raise ValueError('Native background must be behind the text')
        return ''.join(result)
