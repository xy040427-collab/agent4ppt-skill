"""Host artifact transfer tests; no provider or visual-quality claims."""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/agent4ppt-skill/scripts'))
from PIL import Image
from agent4ppt.cli import parser, dispatch
from agent4ppt.ingest import import_image


class ImageImport(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.source = self.root / 'source.png'
        Image.new('RGB', (160, 90), 'navy').save(self.source)
        self.out = self.root / 'project' / '设计.png'

    def test_cli_preserves_bytes_and_reports_dimensions(self):
        data = self.source.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        result = dispatch(parser().parse_args(['import-image', '--source', str(self.source),
                          '--out', str(self.out), '--sha256', sha]))
        self.assertEqual(data, self.out.read_bytes())
        self.assertEqual((160, 90, sha), (result['width'], result['height'], result['sha256']))

    def test_wrong_hash_does_not_write(self):
        with self.assertRaisesRegex(ValueError, 'SHA-256'):
            import_image(self.source, self.out, '0' * 64)
        self.assertFalse(self.out.exists())

    def test_invalid_image_does_not_write(self):
        self.source.write_bytes(b'not an image')
        with self.assertRaises(Exception):
            import_image(self.source, self.out)
        self.assertFalse(self.out.exists())

    def test_no_overwrite(self):
        import_image(self.source, self.out)
        before = self.out.read_bytes()
        with self.assertRaisesRegex(ValueError, 'already exists'):
            import_image(self.source, self.out)
        self.assertEqual(before, self.out.read_bytes())

    def test_missing_source_does_not_search_for_another(self):
        with self.assertRaisesRegex(ValueError, 'missing'):
            import_image(self.root / 'missing.png', self.out)
        self.assertFalse(self.out.exists())
