"""Copy an explicitly selected host image without changing project state."""
import hashlib
from io import BytesIO
from pathlib import Path

from PIL import Image


def import_image(source, out, expected_sha256=None):
    source = Path(source).resolve()
    out = Path(out).resolve()
    if not source.is_file():
        raise ValueError('Source image is missing; locate the output of this tool call, not an unrelated image')
    data = source.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    if expected_sha256 and sha != expected_sha256.lower():
        raise ValueError('Source SHA-256 does not match the selected tool output')
    with Image.open(BytesIO(data)) as im:
        im.verify()
    with Image.open(BytesIO(data)) as im:
        im.load()
        width, height = im.size
        fmt = im.format
    if out == source or out.exists():
        raise ValueError('Destination already exists; choose a new artifact filename')
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('xb') as target:
        target.write(data)
    if hashlib.sha256(out.read_bytes()).hexdigest() != sha:
        raise ValueError('Copied image verification failed; do not register this artifact')
    return dict(source=str(source), path=str(out), sha256=sha,
                width=width, height=height, format=fmt, bytes=len(data))
