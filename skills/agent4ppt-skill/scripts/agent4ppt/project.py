"""A transactional work queue: leases prevent stale workers overwriting revisions."""
import contextlib
import json
import secrets
import sqlite3
import time
from pathlib import Path
from .files import atomic, digest, read, write
from .plan import validate, compile_request, method
from .composition import fingerprint, verify_assets
from . import conversion


class Project:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.db = self.root / 'project.sqlite3'
        if not self.db.is_file():
            raise ValueError('Not an initialized Agent4PPT project')

    @contextlib.contextmanager
    def transaction(self):
        connection = sqlite3.connect(self.db, timeout=30)
        connection.row_factory = sqlite3.Row
        try:
            connection.execute('BEGIN IMMEDIATE')
            yield connection
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    @classmethod
    def create(cls, root, brief, base='.'):
        spec = validate(brief, base)
        # Version only new text-restoration projects; do not migrate old databases.
        if conversion.enabled(spec) and all(o['type'] == 'text' for p in spec['pages'] for o in p['overlays']):
            spec['native_acceptance'] = 'target-v1'
            spec['visual_comparison'] = 'raster-v1'
        root = Path(root).resolve()
        root.mkdir(parents=True, exist_ok=True)
        database = root / 'project.sqlite3'
        # Exclusive creation prevents accidentally replacing an existing project.
        database.touch(exist_ok=False)
        try:
            with contextlib.closing(sqlite3.connect(database)) as db, db:
                db.executescript('''
                CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE pages (number INTEGER PRIMARY KEY, spec TEXT NOT NULL,
                  state TEXT NOT NULL DEFAULT 'pending', worker TEXT, token TEXT,
                  deadline REAL, revision INTEGER NOT NULL DEFAULT 1,
                  image TEXT, sha256 TEXT, backend TEXT, qa TEXT, error TEXT);
                CREATE TABLE events (id INTEGER PRIMARY KEY, at REAL NOT NULL,
                  page INTEGER, kind TEXT NOT NULL, detail TEXT NOT NULL);
                ''')
                db.execute('INSERT INTO settings VALUES (?, ?)', ('brief', json.dumps(spec, ensure_ascii=False)))
                db.executemany('INSERT INTO pages(number,spec) VALUES (?,?)',
                               [(s['number'], json.dumps(s, ensure_ascii=False)) for s in spec['pages']])
            project = cls(root)
            write(root / 'brief.json', spec)
            (root / 'images').mkdir(exist_ok=True)
            (root / 'requests').mkdir(exist_ok=True)
            atomic(root / 'notes.md', '\n\n'.join(f'## Slide {s["number"]}: {s["title"]}\n\n{s.get("notes", "")}' for s in spec['pages']).encode())
            project.snapshot()
            return project
        except BaseException:
            database.unlink(missing_ok=True)
            raise

    @staticmethod
    def event(db, page, kind, detail):
        db.execute('INSERT INTO events(at,page,kind,detail) VALUES (?,?,?,?)',
                   (time.time(), page, kind, json.dumps(detail, ensure_ascii=False)))

    @staticmethod
    def settings(db):
        return json.loads(db.execute("SELECT value FROM settings WHERE key='brief'").fetchone()[0])

    def status(self):
        with self.transaction() as db:
            pages = [dict(row) for row in db.execute('SELECT * FROM pages ORDER BY number')]
            brief = self.settings(db)
            for row in pages:
                if conversion.enabled(brief):
                    stages = conversion.artifacts(self, db, row)
                    row['stage'] = 'complete' if row['state'] == 'complete' else 'compose' if 'background' in stages else 'erase' if 'design' in stages else 'design'
                row['spec'] = json.loads(row['spec'])
                row.pop('token', None)
            return {'title': brief['title'], 'mode': brief.get('mode', 'full_slide'), 'backend': brief['backend'], 'parallelism': brief['parallelism'], 'pages': pages,
                    'ready': all(x['state'] == 'complete' for x in pages)}

    def snapshot(self):
        state = self.status()
        write(self.root / 'status.json', state)
        return state

    def dispatch_plan(self, host_slots, sample_page=None):
        """Read-only capacity advice; the host launches agents and claim leases work.

        host_slots means FREE child slots, excluding the coordinator, existing
        workers and unrelated agents. Never infer capacity from a project limit.
        Expired leases are candidates here; only claim performs reclamation.
        """
        if type(host_slots) is not int or host_slots < 0:
            raise ValueError('host_slots must be a nonnegative integer of free child slots')
        if sample_page is not None and (type(sample_page) is not int or sample_page < 1):
            raise ValueError('sample_page must be a positive page number')
        with self.transaction() as db:
            brief = self.settings(db)
            now = time.time()
            rows = [dict(r) for r in db.execute('SELECT number,state,deadline,worker FROM pages ORDER BY number')]
            active = [r for r in rows if r['state'] == 'running' and r['deadline'] > now]
            candidates = [r['number'] for r in rows if r['state'] == 'pending' or
                          (r['state'] == 'running' and r['deadline'] <= now)]
            sample = db.execute("SELECT value FROM settings WHERE key='sample'").fetchone()
            limit = min(10, brief['parallelism'])
            available = min(host_slots, max(0, limit-len(active)), len(candidates))
            phase = 'production' if sample else 'sample'
            if not sample:
                # The host chooses a representative content page, not just a cover.
                available = min(available, 0 if active else 1)
                if sample_page is not None:
                    if sample_page not in candidates:
                        raise ValueError('Requested sample page is not claimable')
                    candidates = [sample_page] + [n for n in candidates if n != sample_page]
                elif len(candidates) > 1 and candidates[0] == 1:
                    candidates = candidates[1:] + candidates[:1]
            return {'phase': phase, 'max_page_workers': 10, 'project_parallelism': brief['parallelism'],
                    'effective_limit': limit, 'active_workers': active, 'host_free_slots': host_slots,
                    'launch_count': available, 'pages': candidates[:available],
                    'requires_sample_acceptance': not bool(sample),
                    'notice': 'Advisory only; no agents launched or leases changed. Recompute after each completion; claim is authoritative.',
                    'powerpoint_policy': 'One writer per page; serialize MCP calls across a shared PowerPoint endpoint. Keep image workers running while native operations wait.'}

    def claim(self, worker, page=None, lease=900):
        if not worker.strip() or lease <= 0:
            raise ValueError('worker and positive lease required')
        with self.transaction() as db:
            now = time.time()
            for row in db.execute("SELECT number FROM pages WHERE state='running' AND deadline<=?", (now,)).fetchall():
                db.execute("UPDATE pages SET state='pending',token=NULL,worker=NULL WHERE number=?", (row['number'],))
                self.event(db, row['number'], 'lease_expired', {})
            brief = self.settings(db)
            active = db.execute("SELECT count(*) FROM pages WHERE state='running'").fetchone()[0]
            if active >= brief['parallelism']:
                raise ValueError('No concurrency slot available')
            if page is None:
                row = db.execute("SELECT * FROM pages WHERE state='pending' ORDER BY number LIMIT 1").fetchone()
            else:
                row = db.execute("SELECT * FROM pages WHERE number=? AND state='pending'", (page,)).fetchone()
            if row is None:
                raise ValueError('No pending page matches the request')
            sample = db.execute("SELECT value FROM settings WHERE key='sample'").fetchone()
            reference = self.root / sample[0] if sample else None
            recorded_method = db.execute("SELECT value FROM settings WHERE key='generation_method'").fetchone()
            request = compile_request(brief, json.loads(row['spec']), reference,
                                      json.loads(recorded_method[0]) if recorded_method else None)
            verify_assets(request.get('overlays', []))
            for ref in request['references']:
                if digest(ref['path']) != ref['sha256']:
                    raise ValueError('Reference changed; update the brief deliberately')
            token = secrets.token_hex(16)
            deadline = now + lease
            db.execute("UPDATE pages SET state='running',worker=?,token=?,deadline=?,error=NULL WHERE number=?",
                       (worker, token, deadline, row['number']))
            request.update(token=token, worker=worker, deadline=deadline, revision=row['revision'])
            if conversion.enabled(brief):
                stages = conversion.artifacts(self, db, row)
                if 'background' in stages:
                    request.update(stage='compose', image=str(self.root / stages['background']['image']),
                                   design_sha256=stages['design']['sha256'])
                elif 'design' in stages:
                    request = conversion.erase_request(self, brief, row, stages['design'])
                    request.update(token=token, worker=worker, deadline=deadline, revision=row['revision'])
            self.event(db, row['number'], 'claimed', {'worker': worker, 'revision': row['revision']})
            write(self.root / 'requests' / f'page-{row["number"]:03d}.json', request)
        return request

    def _lease(self, db, number, token):
        row = db.execute('SELECT * FROM pages WHERE number=?', (number,)).fetchone()
        if row is None or row['state'] != 'running' or row['token'] != token or row['deadline'] <= time.time():
            raise ValueError('Invalid or expired lease; stale results cannot replace current work')
        return row

    def renew(self, number, token, seconds=900):
        if seconds <= 0:
            raise ValueError('Positive lease required')
        with self.transaction() as db:
            self._lease(db, number, token)
            db.execute('UPDATE pages SET deadline=? WHERE number=?', (time.time()+seconds, number))

    def compose(self, number, token, image, output, native_draft=None):
        """Build a reviewable native page without marking its task complete."""
        from .package import export_pptx
        output = Path(output).resolve()
        receipt = output.with_suffix('.review.json')
        if output.exists() or receipt.exists():
            raise FileExistsError('Use a new draft path for each composition attempt')
        with self.transaction() as db:
            row = self._lease(db, number, token)
            brief = self.settings(db)
            if brief.get('mode') != 'editable':
                raise ValueError('compose requires mode=editable')
            spec = json.loads(row['spec'])
            verify_assets(spec['overlays'])
            checksum = digest(image)
            stages = conversion.require_background(self, db, row, image) if conversion.enabled(brief) else None
            if native_draft:
                from .native import read_text_shapes
                blob = Path(native_draft).read_bytes()
                read_text_shapes(blob, spec['overlays'], checksum, brief['ratio'])
                atomic(output, blob)
            else:
                export_pptx([image], output, brief['ratio'], {1: spec.get('notes', '')},
                            brief['title'], overlays={1: spec['overlays']})
            if digest(image) != checksum:
                raise ValueError('Background changed during composition')
            data = {'page': number, 'revision': row['revision'], 'spec_sha256': fingerprint(spec),
                    'image_sha256': checksum, 'draft': str(output), 'draft_sha256': digest(output)}
            if native_draft:
                data['native_draft'] = True
            if stages:
                data['design_sha256'] = stages['design']['sha256']
            write(receipt, data)
            self.event(db, number, 'composed', data)
        return {'draft': str(output), 'review_file': str(receipt),
                'visual_comparison': brief.get('visual_comparison'),
                'comparison_next': 'After PowerPoint rendering: compare-render PROJECT --review-file THIS_RECEIPT --preview RENDER --out NEW_DIRECTORY; inspect every panel and adjust named objects via MCP' if brief.get('visual_comparison') else None,
                'notice': 'Render and inspect this PPTX; complete requires its review file and rendered preview.'}

    def verify_review(self, db, number):
        event = db.execute("SELECT detail FROM events WHERE page=? AND kind='completed' ORDER BY id DESC LIMIT 1", (number,)).fetchone()
        review = json.loads(event['detail']).get('review') if event else None
        if not review:
            raise ValueError('Editable page has no composition review')
        if self.settings(db).get('native_acceptance') == 'target-v1' and not review.get('native_draft'):
            raise ValueError('target-v1 requires a compose --native-draft checkpoint')
        if conversion.enabled(self.settings(db)):
            row = db.execute('SELECT * FROM pages WHERE number=?', (number,)).fetchone()
            stages = conversion.require_background(self, db, row, self.root / row['image'])
            if review.get('design_sha256') != stages['design']['sha256']:
                raise ValueError('Review belongs to a different design')
        if self.settings(db).get('visual_comparison') == 'raster-v1':
            if not review.get('comparison') or digest(self.root / review['comparison']) != review.get('comparison_sha256'):
                raise ValueError('Accepted visual comparison missing or changed')
        for key in ('draft', 'preview'):
            if digest(self.root / review[key]) != review[key + '_sha256']:
                raise ValueError(f'Accepted composition {key} changed after QA')
        if self.settings(db).get('review_policy') == 'structured-v1' or review.get('qa_report'):
            if not review.get('qa_report') or not review.get('qa_report_sha256'):
                raise ValueError('Accepted composition has no structured QA report')
            if digest(self.root / review['qa_report']) != review['qa_report_sha256']:
                raise ValueError('Accepted composition QA report changed after QA')
        return review

    def complete(self, number, token, image, backend, qa, sample=False, generation_method=None,
                 review_file=None, preview=None, qa_report=None):
        from PIL import Image
        if not qa.strip():
            raise ValueError('A visual QA note is required')
        source = Path(image).resolve()
        with Image.open(source) as im:
            im.verify()
        data = source.read_bytes()
        import hashlib
        checksum = hashlib.sha256(data).hexdigest()
        with self.transaction() as db:
            row = self._lease(db, number, token)
            spec = json.loads(row['spec'])
            verify_assets(spec.get('overlays', []))
            if backend != self.settings(db)['backend']:
                raise ValueError('Backend does not match project')
            request = read(self.root / 'requests' / f'page-{number:03d}.json')
            actual_method = method(generation_method, backend)
            required_method = request.get('generation_method')
            stages = None
            if conversion.enabled(self.settings(db)):
                stages = conversion.require_background(self, db, row, image)
                required_method = stages['background']['generation_method']
            if required_method:
                if actual_method is None:
                    raise ValueError('This request requires generation method evidence')
                for field in ('tool', 'mode', 'model', 'size', 'quality', 'input_preparation'):
                    if field in required_method and actual_method.get(field) != required_method[field]:
                        raise ValueError(f'Generation method mismatch: {field}')
            for ref in request['references']:
                if digest(ref['path']) != ref['sha256']:
                    raise ValueError('Reference was changed during generation')
            review = None
            if self.settings(db).get('mode') == 'editable':
                if not review_file or not preview:
                    raise ValueError('Editable completion requires compose --review-file and a rendered --preview')
                receipt = read(review_file)
                expected = {'page': number, 'revision': row['revision'], 'spec_sha256': fingerprint(spec), 'image_sha256': checksum}
                if stages:
                    expected['design_sha256'] = stages['design']['sha256']
                if any(receipt.get(k) != v for k, v in expected.items()):
                    raise ValueError('Composition receipt belongs to a different page, revision, specification or background')
                composed = [json.loads(e['detail']) for e in db.execute("SELECT detail FROM events WHERE page=? AND kind='composed'", (number,))]
                if receipt not in composed:
                    raise ValueError('Composition receipt was not produced by this project')
                strict_native = self.settings(db).get('native_acceptance') == 'target-v1'
                if strict_native and receipt.get('native_draft') is not True:
                    raise ValueError('target-v1 requires compose --native-draft; the initial draft cannot be completed')
                if digest(receipt['draft']) != receipt['draft_sha256']:
                    raise ValueError('Draft changed; compose and review again')
                with Image.open(preview) as im:
                    im.verify()
                if strict_native:
                    with Image.open(preview) as rendered, Image.open(self.root / stages['design']['image']) as target:
                        if rendered.size != target.size:
                            raise ValueError('target-v1 preview must match the design pixel dimensions; export at target width and height')
                # A re-encoded copy of the bare background is not a composed render.
                from PIL import ImageChops
                with Image.open(preview) as rendered, Image.open(image) as background:
                    if rendered.size == background.size and ImageChops.difference(
                            rendered.convert('RGB'), background.convert('RGB')).getbbox() is None:
                        raise ValueError('Rendered preview equals the bare background; render the composed PPTX before completion')
                review = dict(receipt)
                for key, path in [('draft', receipt['draft']), ('preview', preview)]:
                    blob = Path(path).read_bytes()
                    value = hashlib.sha256(blob).hexdigest()
                    relative_review = f'reviews/{number:03d}-r{row["revision"]}-{key}-{value[:16]}{Path(path).suffix.lower()}'
                    atomic(self.root / relative_review, blob)
                    review[key] = relative_review
                    review[key + '_sha256'] = value
                if review['draft_sha256'] != receipt['draft_sha256']:
                    raise ValueError('Draft changed during completion; compose and review again')
                if self.settings(db).get('review_policy') == 'structured-v1' or qa_report:
                    if not qa_report:
                        raise ValueError('structured-v1 completion requires --qa-report')
                    report_blob = Path(qa_report).read_bytes()
                    report = json.loads(report_blob.decode('utf-8-sig'))
                    bindings = {key: review[key] for key in ('page', 'revision', 'spec_sha256',
                                'image_sha256', 'draft_sha256', 'preview_sha256')}
                    if stages:
                        bindings['design_sha256'] = stages['design']['sha256']
                    if not isinstance(report, dict) or any(report.get(k) != v for k, v in bindings.items()):
                        raise ValueError('QA report does not match the current composition and rendered preview')
                    checks = report.get('checks')
                    required = ('text_overflow', 'text_overlap', 'background_interference',
                                'label_alignment', 'readability')
                    if stages:
                        required += ('erasure_clean', 'artwork_preserved', 'design_alignment')
                    if not isinstance(checks, dict) or any(checks.get(k) != 'pass' for k in required):
                        raise ValueError('QA report must pass every required check')
                    if report.get('issues') != []:
                        raise ValueError('QA report must have no unresolved issues')
                    if not isinstance(report.get('reviewer'), str) or not report['reviewer'].strip():
                        raise ValueError('QA report requires a reviewer')
                    if strict_native:
                        objects = report.get('objects')
                        ids = {o['id'] for o in spec['overlays']}
                        fields = ('placement', 'typography', 'content')
                        if (not isinstance(objects, dict) or set(objects) != ids or
                                any(not isinstance(v, dict) or any(not isinstance(v.get(f), str) or not v[f].strip()
                                    for f in fields) for v in objects.values())):
                            raise ValueError('target-v1 QA requires objects keyed by every overlay ID with placement, typography and content observations')
                    if self.settings(db).get('visual_comparison') == 'raster-v1':
                        from .comparison import verify
                        evidence = verify(self, review_file, preview, report, db)
                        comparison_relative = f'reviews/{number:03d}-r{row["revision"]}-comparison-{evidence["comparison_sha256"][:16]}.json'
                        comparison_blob = Path(evidence['comparison_file']).read_bytes()
                        if hashlib.sha256(comparison_blob).hexdigest() != evidence['comparison_sha256']:
                            raise ValueError('Comparison changed during completion')
                        atomic(self.root / comparison_relative, comparison_blob)
                        review.update(comparison=comparison_relative, comparison_sha256=evidence['comparison_sha256'])
                    report_hash = hashlib.sha256(report_blob).hexdigest()
                    report_relative = f'reviews/{number:03d}-r{row["revision"]}-qa-{report_hash[:16]}.json'
                    atomic(self.root / report_relative, report_blob)
                    review.update(qa_report=report_relative, qa_report_sha256=report_hash)
            elif review_file or preview or qa_report:
                raise ValueError('Composition review arguments require mode=editable')
            relative = f'images/{number:03d}-r{row["revision"]}-{checksum[:16]}{source.suffix.lower()}'
            atomic(self.root / relative, data)
            db.execute("UPDATE pages SET state='complete',image=?,sha256=?,backend=?,qa=?,token=NULL,deadline=NULL WHERE number=?",
                       (relative, checksum, backend, qa, number))
            if sample:
                sample_image = stages['design']['image'] if stages else relative
                sample_method = stages['design']['generation_method'] if stages else actual_method
                db.execute("INSERT OR REPLACE INTO settings VALUES ('sample', ?)", (sample_image,))
                if sample_method:
                    db.execute("INSERT OR REPLACE INTO settings VALUES ('generation_method', ?)",
                               (json.dumps(sample_method, ensure_ascii=False),))
            self.event(db, number, 'completed', {'image': relative, 'sha256': checksum, 'qa': qa,
                                               'sample': sample, 'generation_method': actual_method, 'review': review})
        return self.snapshot()

    def fail(self, number, token, reason):
        if not reason.strip():
            raise ValueError('A reason is required')
        with self.transaction() as db:
            self._lease(db, number, token)
            db.execute("UPDATE pages SET state='failed',error=?,token=NULL,deadline=NULL WHERE number=?", (reason, number))
            self.event(db, number, 'failed', {'reason': reason})

    def retry(self, number, reason, replacement=None):
        if not reason.strip():
            raise ValueError('Revision reason is required')
        with self.transaction() as db:
            row = db.execute('SELECT * FROM pages WHERE number=?', (number,)).fetchone()
            if row is None:
                raise ValueError('Page does not exist')
            page = json.loads(row['spec'])
            if replacement is not None:
                spec = self.settings(db)
                if spec.get('mode') == 'editable':
                    spec.setdefault('editable_workflow', 'reserved')
                # Validate the page without migrating a legacy queue's stored capacity.
                page = validate(dict(spec, parallelism=min(10, spec['parallelism']), pages=[replacement]), self.root)['pages'][0]
                page['number'] = number
            db.execute("UPDATE pages SET state='pending',revision=revision+1,spec=?,token=NULL,deadline=NULL,image=NULL,sha256=NULL,qa=NULL,error=NULL WHERE number=?",
                       (json.dumps(page, ensure_ascii=False), number))
            self.event(db, number, 'revision', {'reason': reason})
        return self.snapshot()

    def ready(self):
        state = self.status()
        if not state['ready']:
            raise ValueError('Every page must be completed before export')
        for row in state['pages']:
            if digest(self.root / row['image']) != row['sha256']:
                raise ValueError(f'Page {row["number"]} image changed after QA')
        return state

    def history(self):
        with self.transaction() as db:
            return [dict(row) for row in db.execute('SELECT * FROM events ORDER BY id')]

# a4p-provenance: a4p-50d41ed6-f9f9-4470-ac9c-e700dd134a07/60aaf5451770b2b3f2d9
