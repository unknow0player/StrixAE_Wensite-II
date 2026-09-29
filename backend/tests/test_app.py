import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import soundfile as sf
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app


def wav(duration=0.2, rate=16000):
    stream = io.BytesIO()
    values = 0.3 * np.sin(2 * np.pi * 440 * np.arange(int(duration * rate)) / rate)
    sf.write(stream, values, rate, format='WAV')
    stream.seek(0)
    return stream


class BackendTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = create_app(self.tmp.name, testing=True)
        self.client = self.app.test_client()
        token = self.client.get('/api/session').json['csrf']
        password = (Path(self.tmp.name) / 'admin-password.txt').read_text()
        response = self.client.post('/api/login', json={'password': password}, headers={'X-CSRF-Token': token})
        self.assertEqual(response.status_code, 200)
        self.headers = {'X-CSRF-Token': response.json['csrf']}

    def tearDown(self):
        for handler in self.app.logger.handlers[:]:
            if hasattr(handler, 'baseFilename') and Path(handler.baseFilename).parent == Path(self.tmp.name).resolve():
                handler.close()
                self.app.logger.removeHandler(handler)
        self.tmp.cleanup()

    def upload(self, content=None, name='example.wav', role='ground_truth'):
        return self.client.post(f'/api/slots/1/{role}/upload', data={'file': (content or wav(), name)}, headers=self.headers)

    def test_original_mapping_and_static_security(self):
        response = self.client.get('/api/samples')
        self.assertEqual(len(response.json['slots']), 12)
        self.assertTrue(all(s['id'] is None for s in response.json['slots']))
        for slot in response.json['slots']:
            with self.client.get(slot['audio']) as asset:
                self.assertEqual(asset.status_code, 200)
            if slot['image']:
                with self.client.get(slot['image']) as asset:
                    self.assertEqual(asset.status_code, 200)
        for path in ('/.git/config', '/backend/app.py', '/data/admin-password.txt', '/figs/../../plot_specs.py'):
            self.assertEqual(self.client.get(path).status_code, 404)
        self.assertEqual(self.client.get('/api/health', headers={'Host': 'evil.example'}).status_code, 400)

    def test_auth_and_csrf(self):
        anonymous = self.app.test_client()
        self.assertEqual(anonymous.get('/api/slots/1/mixture/history').status_code, 401)
        self.assertEqual(self.client.post('/api/slots/1/mixture/restore', json={'version_id': None}).status_code, 403)
        token = anonymous.get('/api/session').json['csrf']
        self.assertEqual(anonymous.post('/api/slots/1/mixture/restore', json={'version_id': None}, headers={'X-CSRF-Token': token}).status_code, 401)

    def test_upload_image_range_history_restore_and_persistence(self):
        response = self.upload()
        self.assertEqual(response.status_code, 201, response.json)
        version = response.json['id']
        slots = self.client.get('/api/samples').json['slots']
        self.assertEqual(slots[1]['id'], version)
        self.assertEqual(sum(s['id'] is not None for s in slots), 1)
        png = self.client.get(slots[1]['image'])
        image = Image.open(io.BytesIO(png.data))
        self.assertEqual(image.size, (800, 800))
        png.close()
        audio = self.client.get(slots[1]['audio'], headers={'Range': 'bytes=0-99'})
        self.assertEqual(audio.status_code, 206)
        self.assertEqual(len(audio.data), 100)
        audio.close()
        second = self.upload(wav(0.3), 'second.wav').json['id']
        self.assertNotEqual(second, version)
        self.assertEqual(len(self.client.get('/api/slots/1/ground_truth/history').json['versions']), 2)
        for target in (version, None, second):
            result = self.client.post('/api/slots/1/ground_truth/restore', json={'version_id': target}, headers=self.headers)
            self.assertEqual(result.status_code, 200)
            self.assertEqual(self.client.get('/api/samples').json['slots'][1]['id'], target)
        restarted = create_app(self.tmp.name, testing=True)
        self.assertEqual(restarted.test_client().get('/api/samples').json['slots'][1]['id'], second)
        self.assertEqual(self.client.post('/api/slots/1/mixture/restore', json={'version_id': version}, headers=self.headers).status_code, 404)

    def test_invalid_uploads_leave_original(self):
        for content, name in ((io.BytesIO(b'invalid'), 'broken.wav'), (wav(), 'script.html'), (wav(121), 'long.wav'), (wav(rate=4000), 'rate.wav')):
            response = self.upload(content, name)
            self.assertEqual(response.status_code, 400, response.json)
        self.assertEqual(self.client.get('/api/samples').json['slots'][1]['id'], None)
        self.assertEqual(list((Path(self.tmp.name) / 'media').iterdir()), [])

    def test_failed_plot_preserves_previous_version(self):
        version = self.upload().json['id']
        with patch('app.generate', side_effect=RuntimeError('test plotting failure')):
            self.assertEqual(self.upload().status_code, 500)
        self.assertEqual(self.client.get('/api/samples').json['slots'][1]['id'], version)
        self.assertEqual(len(list((Path(self.tmp.name) / 'media').iterdir())), 1)

    def test_missing_slot_and_request_limit(self):
        self.assertEqual(self.client.post('/api/slots/99/invalid/upload', headers=self.headers).status_code, 404)
        self.assertEqual(self.client.post('/api/slots/1/mixture/upload', headers=self.headers).status_code, 400)
        self.app.config['MAX_CONTENT_LENGTH'] = 100
        self.assertEqual(self.upload().status_code, 413)


if __name__ == '__main__':
    unittest.main()
