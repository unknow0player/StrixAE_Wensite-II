from datetime import timedelta
from contextlib import contextmanager
from functools import wraps
from html.parser import HTMLParser
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler
import os
import secrets
import sqlite3
import tempfile
import threading
import time
import uuid

from flask import Flask, abort, jsonify, request, send_from_directory, session
from werkzeug.exceptions import HTTPException
from spectrogram import generate

BASE = Path(__file__).resolve().parent
FRONTEND = BASE.parent / 'StrixAE-Website'
ROLES = ('mixture', 'ground_truth', 'tf_gridnet', 'strixae')
LABELS = ('Mixture', 'Ground Truth', 'TF-GridNet', 'StrixAE')


class DemoParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.slots = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'audio':
            index = len(self.slots)
            self.slots.append(dict(sample=index // 4 + 1, role=ROLES[index % 4],
                                   label=LABELS[index % 4], audio=attrs['src'], image=None))
        if tag == 'img' and self.slots and self.slots[-1]['role'] != 'mixture':
            self.slots[-1]['image'] = attrs['src']


def create_app(data_dir=None, testing=False):
    app = Flask(__name__, static_folder=None)
    data = Path(data_dir or os.environ.get('STRIXAE_DATA_DIR', BASE / 'data')).resolve()
    media = data / 'media'
    media.mkdir(parents=True, exist_ok=True)
    def persistent_secret(name):
        path = data / name
        if not path.exists():
            path.write_text(secrets.token_urlsafe(32), encoding='utf-8')
        return path.read_text(encoding='utf-8').strip()
    app.config.update(SECRET_KEY=persistent_secret('session.key'), TESTING=testing,
                      MAX_CONTENT_LENGTH=26 * 1024 * 1024,
                      SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Strict',
                      PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
                      TRUSTED_HOSTS=['localhost', '127.0.0.1', '[::1]'])
    password = persistent_secret('admin-password.txt')
    database = data / 'library.sqlite3'
    lock = threading.Lock()
    attempts = []
    @contextmanager
    def connect():
        con = sqlite3.connect(database, timeout=30)
        con.row_factory = sqlite3.Row
        try:
            with con:
                yield con
        finally:
            con.close()
    with connect() as con:
        con.executescript('''
            CREATE TABLE IF NOT EXISTS versions (
                id TEXT PRIMARY KEY, sample INTEGER NOT NULL, role TEXT NOT NULL,
                filename TEXT NOT NULL, duration REAL, sample_rate INTEGER, channels INTEGER,
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')));
            CREATE TABLE IF NOT EXISTS current (
                sample INTEGER NOT NULL, role TEXT NOT NULL, version_id TEXT,
                PRIMARY KEY(sample, role));
        ''')
    parser = DemoParser()
    parser.feed((FRONTEND / 'demo.html').read_text(encoding='utf-8'))
    originals = {(s['sample'], s['role']): s for s in parser.slots}
    if len(originals) != 12:
        raise RuntimeError('demo.html 应包含 3 组、每组 4 个音频。')
    handler = RotatingFileHandler(data / 'server.log', maxBytes=1024*1024, backupCount=3, encoding='utf-8')
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

    def require_admin(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if not session.get('admin'):
                abort(401, description='请先登录管理后台。')
            return fn(*args, **kwargs)
        return wrapped

    @app.before_request
    def csrf():
        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            token = session.get('csrf', '')
            if not token or not secrets.compare_digest(token, request.headers.get('X-CSRF-Token', '')):
                abort(403, description='会话校验失败，请刷新页面后重试。')

    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'same-origin'
        if request.path.startswith('/api/') or request.path in ('/admin', '/demo.html'):
            response.headers['Cache-Control'] = 'no-store'
        return response

    @app.errorhandler(HTTPException)
    def http_error(exc):
        message = '上传请求过大，单个文件最多 25 MB。' if exc.code == 413 else exc.description
        return jsonify(error=message), exc.code

    @app.errorhandler(Exception)
    def server_error(exc):
        app.logger.exception('Request failed')
        return jsonify(error='处理失败，原内容未被替换。请查看后台日志或重试。'), 500

    @app.get('/api/health')
    def health():
        with connect() as con:
            con.execute('SELECT 1').fetchone()
        return jsonify(status='ok')

    @app.get('/api/session')
    def get_session():
        if 'csrf' not in session:
            session['csrf'] = secrets.token_urlsafe(32)
        return jsonify(authenticated=bool(session.get('admin')), csrf=session['csrf'])

    @app.post('/api/login')
    def login():
        now = time.monotonic()
        with lock:
            attempts[:] = [t for t in attempts if now-t < 60]
            if len(attempts) >= 10:
                abort(429, description='登录尝试过多，请一分钟后重试。')
            body = request.get_json(silent=True)
            supplied = body.get('password', '') if isinstance(body, dict) else ''
            if not isinstance(supplied, str) or not secrets.compare_digest(supplied.encode(), password.encode()):
                attempts.append(now)
                abort(401, description='管理密码不正确。')
            attempts.clear()
        session.clear()
        session.update(admin=True, csrf=secrets.token_urlsafe(32))
        session.permanent = True
        return jsonify(csrf=session['csrf'])

    @app.post('/api/logout')
    def logout():
        session.clear()
        return jsonify(ok=True)

    def version_dict(row):
        result = dict(row)
        result.update(audio=f"/media/{row['id']}/audio.wav", image=f"/media/{row['id']}/spec.png")
        return result

    @app.get('/api/samples')
    def samples():
        with connect() as con:
            rows = con.execute('SELECT v.* FROM current c JOIN versions v ON v.id=c.version_id').fetchall()
        active = {(r['sample'], r['role']): r for r in rows}
        result = []
        for key, original in originals.items():
            slot = dict(original, audio='/' + original['audio'],
                        image='/' + original['image'] if original['image'] else None, id=None)
            if key in active:
                slot.update(version_dict(active[key]))
            result.append(slot)
        return jsonify(slots=result)

    def check_slot(sample, role):
        if (sample, role) not in originals:
            abort(404, description='不存在这个样本或音频位置。')

    @app.get('/api/slots/<int:sample>/<role>/history')
    @require_admin
    def history(sample, role):
        check_slot(sample, role)
        with connect() as con:
            rows = con.execute('SELECT * FROM versions WHERE sample=? AND role=? ORDER BY created_at DESC', (sample, role)).fetchall()
        return jsonify(versions=[version_dict(r) for r in rows])

    @app.post('/api/slots/<int:sample>/<role>/upload')
    @require_admin
    def upload(sample, role):
        check_slot(sample, role)
        file = request.files.get('file')
        if not file or not file.filename:
            abort(400, description='请选择音频文件。')
        suffix = Path(file.filename).suffix.lower()
        if suffix not in {'.wav', '.flac', '.ogg', '.mp3'}:
            abort(400, description='支持 WAV、FLAC、OGG、MP3 文件。')
        # Serialize expensive plotting and mutations; fail fast instead of queuing large jobs.
        if not lock.acquire(blocking=False):
            abort(409, description='后台正在处理另一个操作，请稍后重试。')
        version = uuid.uuid4().hex
        destination = media / version
        committed = False
        try:
            with tempfile.TemporaryDirectory(dir=data) as tmp:
                tmp = Path(tmp)
                source = tmp / ('source' + suffix)
                file.save(source)
                if source.stat().st_size > 25 * 1024 * 1024:
                    abort(413)
                try:
                    metadata = generate(source, tmp / 'audio.wav', tmp / 'spec.png')
                except ValueError as exc:
                    abort(400, description=str(exc))
                destination.mkdir()
                (tmp / 'audio.wav').replace(destination / 'audio.wav')
                (tmp / 'spec.png').replace(destination / 'spec.png')
                with connect() as con:
                    con.execute('INSERT INTO versions (id,sample,role,filename,duration,sample_rate,channels) VALUES (?,?,?,?,?,?,?)',
                                (version, sample, role, file.filename.replace('\\', '/').rsplit('/', 1)[-1][:200],
                                 metadata['duration'], metadata['sample_rate'], metadata['channels']))
                    con.execute('INSERT OR REPLACE INTO current VALUES (?,?,?)', (sample, role, version))
                committed = True
            app.logger.info('Uploaded sample=%s role=%s version=%s', sample, role, version)
            return jsonify(ok=True, id=version, **metadata), 201
        finally:
            if not committed and destination.exists():
                for name in ('audio.wav', 'spec.png'):
                    (destination / name).unlink(missing_ok=True)
                destination.rmdir()
            lock.release()

    @app.post('/api/slots/<int:sample>/<role>/restore')
    @require_admin
    def restore(sample, role):
        check_slot(sample, role)
        body = request.get_json(silent=True)
        if not isinstance(body, dict) or 'version_id' not in body:
            abort(400, description='请指定要恢复的版本。')
        version = body['version_id']
        if version is not None and not isinstance(version, str):
            abort(400, description='版本格式不正确。')
        with lock, connect() as con:
            if version is not None and not con.execute('SELECT 1 FROM versions WHERE id=? AND sample=? AND role=?', (version, sample, role)).fetchone():
                abort(404, description='该位置没有这个历史版本。')
            con.execute('INSERT OR REPLACE INTO current VALUES (?,?,?)', (sample, role, version))
        app.logger.info('Restored sample=%s role=%s version=%s', sample, role, version or 'original')
        return jsonify(ok=True)

    @app.get('/media/<version>/<name>')
    def asset(version, name):
        if len(version) != 32 or any(c not in '0123456789abcdef' for c in version) or name not in ('audio.wav', 'spec.png'):
            abort(404)
        return send_from_directory(media / version, name, max_age=31536000, conditional=True)

    @app.get('/admin')
    def admin():
        return send_from_directory(BASE / 'static', 'admin.html')

    @app.get('/backend-assets/<name>')
    def backend_asset(name):
        if name not in ('admin.js', 'admin.css', 'demo-data.js'):
            abort(404)
        return send_from_directory(BASE / 'static', name, max_age=0)

    @app.get('/')
    def home():
        return send_from_directory(FRONTEND, 'index.html')

    @app.get('/<path:name>')
    def frontend(name):
        path = Path(name)
        if any(part.startswith('.') for part in path.parts):
            abort(404)
        if name not in {'index.html', 'demo.html', 'design.html', 'results.html', 'style.css', 'script.js', 'demo-data.js'} and not (
                path.parts[0] in {'Audios', 'figs'} and path.suffix.lower() in {'.wav', '.mp3', '.ogg', '.flac', '.png', '.jpg', '.jpeg', '.svg', '.webp', '.gif', '.pdf'}):
            abort(404)
        return send_from_directory(FRONTEND, name, max_age=0)

    return app


if __name__ == '__main__':
    from waitress import serve
    app = create_app()
    print('展示页: http://127.0.0.1:8000/demo.html\n管理后台: http://127.0.0.1:8000/admin')
    print('管理密码保存在 backend/data/admin-password.txt；按 Ctrl+C 停止。')
    serve(app, host='127.0.0.1', port=8000, threads=4, max_request_body_size=26*1024*1024)
