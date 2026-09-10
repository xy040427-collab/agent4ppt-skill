"""Local HTTP contract tests; these do not claim access to a paid provider."""
import base64
import io
import json
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/agent4ppt-skill/scripts'))
from PIL import Image
from agent4ppt.providers import OpenAIImages,AtlasImages,Transport,ServiceError
from agent4ppt.imaging import generate,batch


class Services(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        image=Image.new('RGB',(160,90),'red');buf=io.BytesIO();image.save(buf,'PNG')
        self.blob=buf.getvalue();self.encoded=base64.b64encode(self.blob).decode()
        self.requests=[];owner=self
        class Handler(BaseHTTPRequestHandler):
            def log_message(*args):pass
            def do_POST(self):
                body=self.rfile.read(int(self.headers.get('Content-Length','0')))
                owner.requests.append((self.path,dict(self.headers),body))
                if self.path.endswith('/generateImage'):
                    data={'code':200,'data':{'prediction_id':'test-123'}}
                else:data={'data':[{'b64_json':owner.encoded}]}
                self.send_response(200);self.end_headers();self.wfile.write(json.dumps(data).encode())
            def do_GET(self):
                owner.requests.append((self.path,dict(self.headers),b''))
                self.send_response(200);self.end_headers()
                self.wfile.write(json.dumps({'data':{'status':'completed','outputs':[owner.encoded]}}).encode())
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=self.server.serve_forever,daemon=True);thread.start()
        def close():self.server.shutdown();self.server.server_close();thread.join()
        self.addCleanup(close)
        self.settings={'base_url':f'http://127.0.0.1:{self.server.server_port}/v1','api_key':'fixture-key','model':'gpt-image-2'}

    def test_openai_generation_over_http(self):
        generate({'prompt':'Chinese page','out':str(self.root/'out.png')},settings=self.settings)
        path,headers,body=self.requests[0]
        self.assertEqual(path,'/v1/images/generations')
        self.assertEqual(headers['Authorization'],'Bearer fixture-key')
        self.assertEqual(json.loads(body)['prompt'],'Chinese page')
        self.assertEqual((self.root/'out.png').read_bytes(),self.blob)

    def test_openai_multi_reference_edit_and_mask(self):
        ref=self.root/'中文.png';ref.write_bytes(self.blob)
        mask=self.root/'mask.png';Image.new('RGBA',(160,90)).save(mask)
        generate({'prompt':'Keep photo','images':[str(ref),str(ref)],'mask':str(mask),'out':str(self.root/'out.png')},settings=self.settings)
        path,headers,body=self.requests[0]
        self.assertEqual(path,'/v1/images/edits')
        self.assertEqual(body.count(b'name="image[]"'),2)
        self.assertIn(b'name="mask"',body)
        self.assertIn(self.blob,body)

    def test_atlas_submit_poll_decode(self):
        generate({'backend':'atlascloud','prompt':'Make page','out':str(self.root/'out.png')},settings=self.settings)
        body=json.loads(self.requests[0][2])
        self.assertEqual(body['model'],'openai/gpt-image-2/text-to-image')
        self.assertEqual(self.requests[1][0],'/api/v1/model/result/test-123')
        self.assertEqual((self.root/'out.png').read_bytes(),self.blob)

    def test_atlas_edit_and_unsupported_mask(self):
        ref=self.root/'ref.png';ref.write_bytes(self.blob)
        generate({'backend':'atlascloud','prompt':'Edit page','images':[str(ref)],'out':str(self.root/'out.png')},settings=self.settings)
        body=json.loads(self.requests[0][2])
        self.assertEqual(body['model'],'openai/gpt-image-2/edit')
        self.assertTrue(body['images'][0].startswith('data:image/png;base64,'))
        with self.assertRaises(ValueError):AtlasImages(self.settings).run({'model':'gpt-image-2'},[ref],ref)

    def test_atlas_timeout_and_failure(self):
        class Pending:
            def request(self,method,*args):return {'id':'p'} if method=='POST' else {'status':'processing'}
        with self.assertRaises(TimeoutError):
            AtlasImages(self.settings,Pending(),sleep=lambda _:None,poll_limit=2).run({'model':'gpt-image-2','prompt':'test'})
        class Failed:
            def request(self,method,*args):return {'id':'p'} if method=='POST' else {'status':'failed'}
        with self.assertRaises(RuntimeError):
            AtlasImages(self.settings,Failed(),sleep=lambda _:None).run({'model':'gpt-image-2','prompt':'test'})

    def test_batch_http_and_failure_report(self):
        jobs=[{'prompt':'x','out':str(self.root/f'{i}.png')} for i in range(3)]
        def runner(job,dry_run=False):return generate(job,settings=self.settings)
        results=batch(jobs,2,runner=runner)
        self.assertTrue(all(x['ok'] for x in results))
        self.assertEqual(len(list(self.root.glob('*.png'))),3)
        results=batch(jobs,2,runner=runner)
        self.assertTrue(all(not x['ok'] for x in results))


if __name__=='__main__':unittest.main()
