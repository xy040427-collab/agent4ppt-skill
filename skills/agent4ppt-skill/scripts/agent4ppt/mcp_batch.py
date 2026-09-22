"""Plan one page's native corrections without calling or impersonating MCP.

Host executes ALL preflight get-name calls and checks expected_name before ANY
mutation; then awaits mutation calls sequentially in one host tool invocation.
Stop on every tool error, including an MCP success=false payload. This is not a
transaction: a later failure can leave earlier edits applied. Save a new copy,
adopt, render once and visually review through the existing workflow afterward.
All geometry and font sizes are in PowerPoint points, not image pixels.
"""
import math
import re


def _keys(value, allowed, label):
    if not isinstance(value, dict):
        raise ValueError(f'{label} must be an object')
    unknown = set(value) - set(allowed)
    if unknown:
        raise ValueError(f'{label}: unknown fields {sorted(unknown)}')


def _positive(value, label, integer=False):
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or value <= 0
            or (integer and not isinstance(value, int))):
        raise ValueError(f'{label} must be a positive {"integer" if integer else "finite number"}')
    return value


def _string(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{label} must be a nonempty string')
    return value


def plan_batch(spec):
    """Validate {session_id, slide_index, objects, edits}; return a call plan.

    objects maps stable native shape names to {shape_index, mixed_runs?} from
    current MCP inspection. edits contains {id, position?, size?, font_size?,
    font_name?, bold?, color?, alignment?}. Unknown fields are errors. Mixed-run
    shapes permit geometry edits only, preventing accidental style flattening.
    """
    _keys(spec, ('session_id', 'slide_index', 'objects', 'edits'), 'spec')
    session = _string(spec.get('session_id'), 'session_id')
    slide = _positive(spec.get('slide_index'), 'slide_index', integer=True)
    objects = spec.get('objects')
    if not isinstance(objects, dict) or not objects:
        raise ValueError('objects must be a nonempty stable-name mapping')
    indices = set()
    for name, obj in objects.items():
        _string(name, 'object name')
        _keys(obj, ('shape_index', 'mixed_runs'), f'objects.{name}')
        index = _positive(obj.get('shape_index'), 'shape_index', integer=True)
        if index in indices:
            raise ValueError('duplicate shape_index in objects')
        indices.add(index)
        if 'mixed_runs' in obj and not isinstance(obj['mixed_runs'], bool):
            raise ValueError('mixed_runs must be boolean')
    edits = spec.get('edits')
    if not isinstance(edits, list) or not edits:
        raise ValueError('edits must be a nonempty list')
    preflight, calls, seen = [], [], set()
    for edit in edits:
        _keys(edit, ('id', 'position', 'size', 'font_size', 'font_name', 'bold',
                     'color', 'alignment'), 'edit')
        name = _string(edit.get('id'), 'edit.id')
        if name not in objects:
            raise ValueError(f'unknown object id: {name}')
        if name in seen:
            raise ValueError(f'duplicate edit id: {name}')
        seen.add(name)
        if len(edit) == 1:
            raise ValueError(f'empty edit for {name}')
        obj = objects[name]
        if obj.get('mixed_runs', False) and set(edit) - {'id', 'position', 'size'}:
            raise ValueError(f'{name}: mixed_runs allows geometry changes only')
        base = dict(session_id=session, slide_index=slide, shape_index=obj['shape_index'])
        preflight.append({'tool': 'shape', 'arguments': dict(base, action='get-name'),
                          'expected_name': name})

        def add(tool, action, **kwargs):
            calls.append({'tool': tool, 'arguments': dict(base, action=action, **kwargs)})

        if 'position' in edit:
            pos = edit['position']
            _keys(pos, ('left', 'top'), 'position')
            for axis in ('left', 'top'):
                value = pos.get(axis)
                if (isinstance(value, bool) or not isinstance(value, (int, float))
                        or not math.isfinite(value) or value < 0):
                    raise ValueError(f'position.{axis} must be a nonnegative finite number')
            add('shape', 'set-position', **pos)
        if 'size' in edit:
            size = edit['size']
            _keys(size, ('width', 'height'), 'size')
            for axis in ('width', 'height'):
                _positive(size.get(axis), f'size.{axis}')
            add('shape', 'set-size', **size)
        if 'font_size' in edit:
            add('textframe', 'set-font-size', font_size=_positive(edit['font_size'], 'font_size'))
        if 'font_name' in edit:
            add('textframe', 'set-font-name', font_name=_string(edit['font_name'], 'font_name'))
        if 'bold' in edit:
            if not isinstance(edit['bold'], bool):
                raise ValueError('bold must be boolean')
            add('textframe', 'set-bold', bold=edit['bold'])
        if 'color' in edit:
            color = edit['color']
            if not isinstance(color, str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', color):
                raise ValueError('color must be #RRGGBB')
            add('textframe', 'set-font-color', **dict(zip(('red', 'green', 'blue'),
                (int(color[i:i+2], 16) for i in (1, 3, 5)))))
        if 'alignment' in edit:
            if edit['alignment'] not in ('left', 'center', 'right'):
                raise ValueError('alignment must be left, center or right')
            add('textframe', 'set-alignment', alignment=edit['alignment'])
    return {'schema': 'agent4ppt.mcp-batch.v1', 'executed': False,
            'units': 'points', 'preflight': preflight, 'calls': calls,
            'execution_policy': {'verify_all_names_before_mutation': True,
                                 'sequential': True, 'stop_on_error': True,
                                 'atomic': False},
            'after_execution': ['save-copy-as', 'compose --native-draft',
                                'render', 'compare-render', 'visual-review']}
