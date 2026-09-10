"""A transactional work queue: leases prevent stale workers overwriting revisions."""
import contextlib
import json
import secrets
import sqlite3
import time
from pathlib import Path
from .files import atomic, digest, read, write
from .plan import validate, compile_request, method


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
                row['spec'] = json.loads(row['spec'])
                row.pop('token', None)
            return {'title': brief['title'], 'backend': brief['backend'], 'parallelism': brief['parallelism'], 'pages': pages,
                    'ready': all(x['state'] == 'complete' for x in pages)}

    def snapshot(self):
        state = self.status()
        write(self.root / 'status.json', state)
        return state

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
            for ref in request['references']:
                if digest(ref['path']) != ref['sha256']:
                    raise ValueError('Reference changed; update the brief deliberately')
            token = secrets.token_hex(16)
            deadline = now + lease
            db.execute("UPDATE pages SET state='running',worker=?,token=?,deadline=?,error=NULL WHERE number=?",
                       (worker, token, deadline, row['number']))
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

    def complete(self, number, token, image, backend, qa, sample=False, generation_method=None):
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
            if backend != self.settings(db)['backend']:
                raise ValueError('Backend does not match project')
            request = read(self.root / 'requests' / f'page-{number:03d}.json')
            actual_method = method(generation_method, backend)
            required_method = request.get('generation_method')
            if required_method:
                if actual_method is None:
                    raise ValueError('This request requires generation method evidence')
                for field in ('tool', 'mode', 'model', 'size', 'quality', 'input_preparation'):
                    if field in required_method and actual_method.get(field) != required_method[field]:
                        raise ValueError(f'Generation method mismatch: {field}')
            for ref in request['references']:
                if digest(ref['path']) != ref['sha256']:
                    raise ValueError('Reference was changed during generation')
            relative = f'images/{number:03d}-r{row["revision"]}-{checksum[:16]}{source.suffix.lower()}'
            atomic(self.root / relative, data)
            db.execute("UPDATE pages SET state='complete',image=?,sha256=?,backend=?,qa=?,token=NULL,deadline=NULL WHERE number=?",
                       (relative, checksum, backend, qa, number))
            if sample:
                db.execute("INSERT OR REPLACE INTO settings VALUES ('sample', ?)", (relative,))
                if actual_method:
                    db.execute("INSERT OR REPLACE INTO settings VALUES ('generation_method', ?)",
                               (json.dumps(actual_method, ensure_ascii=False),))
            self.event(db, number, 'completed', {'image': relative, 'sha256': checksum, 'qa': qa,
                                               'sample': sample, 'generation_method': actual_method})
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
                page = validate(dict(spec, pages=[replacement]), self.root)['pages'][0]
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
