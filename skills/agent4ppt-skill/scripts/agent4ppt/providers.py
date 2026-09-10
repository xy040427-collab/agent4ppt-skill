"""HTTP adapters. Return bytes; output naming and orchestration live elsewhere."""
import base64
import json
import mimetypes
import time
import uuid
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


class ServiceError(RuntimeError):
    def __init__(self, status, retry_after=0):
        super().__init__(f'Image service returned HTTP {status}')
        self.status, self.retry_after = status, retry_after


class Transport:
    def __init__(self, key, timeout=180, opener=urlopen):
        self.key, self.timeout, self.opener = key, timeout, opener

    def request(self, method, url, body=None, content_type='application/json', authenticated=True, raw=False):
        headers = {'User-Agent': 'agent4ppt/0.1', 'Accept':'application/json'}
        if authenticated:
            headers['Authorization'] = 'Bearer ' + (self.key or '')
        if body is not None:
            headers['Content-Type'] = content_type
            if not isinstance(body, bytes):
                body = json.dumps(body).encode()
        try:
            with self.opener(Request(url, data=body, headers=headers, method=method), timeout=self.timeout) as response:
                data = response.read()
        except HTTPError as exc:
            retry = exc.headers.get('Retry-After', '0')
            raise ServiceError(exc.code, float(retry) if retry.replace('.','',1).isdigit() else 0) from None
        return data if raw else json.loads(data)

    def image_bytes(self, value):
        if value.startswith(('https://','http://')):
            return self.request('GET', value, authenticated=False, raw=True)
        if value.startswith('data:'):
            value = value.split(',', 1)[1]
        return base64.b64decode(value, validate=True)


def multipart(fields, paths, mask=None):
    boundary = 'a4p-' + uuid.uuid4().hex
    data = bytearray()
    def part(name, body, filename=None):
        data.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"'.encode())
        if filename:
            # A controlled filename avoids encoding ambiguities with Unicode user paths.
            data.extend(f'; filename="{filename}"\r\nContent-Type: {mimetypes.guess_type(filename)[0] or "application/octet-stream"}'.encode())
        data.extend(b'\r\n\r\n' + body + b'\r\n')
    for name,value in fields.items():
        if value is not None:
            part(name, (str(value).lower() if isinstance(value,bool) else str(value)).encode())
    for i,path in enumerate(paths):
        path = Path(path)
        part('image[]' if len(paths)>1 else 'image', path.read_bytes(), f'image{i}{path.suffix}')
    if mask:
        part('mask', Path(mask).read_bytes(), 'mask.png')
    data.extend(f'--{boundary}--\r\n'.encode())
    return bytes(data), 'multipart/form-data; boundary=' + boundary


class OpenAIImages:
    def __init__(self, settings, transport=None):
        self.base = settings['base_url'].rstrip('/')
        self.http = transport or Transport(settings.get('api_key'))

    def run(self, fields, images=(), mask=None):
        if images:
            body, mime = multipart(fields, images, mask)
            response = self.http.request('POST', self.base+'/images/edits', body, mime)
        else:
            response = self.http.request('POST', self.base+'/images/generations', fields)
        values = response.get('data', [])
        if not values:
            raise ValueError('Image service returned no images')
        return [self.http.image_bytes(item.get('b64_json') or item['url']) for item in values]


class AtlasImages:
    def __init__(self, settings, transport=None, sleep=time.sleep, poll_limit=120):
        parsed = urlparse(settings['base_url'])
        self.base = f'{parsed.scheme}://{parsed.netloc}/api/v1/model'
        self.http = transport or Transport(settings.get('api_key'))
        self.sleep, self.poll_limit = sleep, poll_limit

    def run(self, fields, images=(), mask=None):
        if mask:
            raise ValueError('AtlasCloud does not support masks in this adapter')
        if fields.get('output_format', 'png') not in ('png','jpeg'):
            raise ValueError('AtlasCloud supports PNG and JPEG output')
        model = fields['model'].removesuffix('/edit').removesuffix('/text-to-image')
        if '/' not in model:
            model = 'openai/' + model
        body = {'model':model + ('/edit' if images else '/text-to-image'), 'prompt':fields['prompt'],
                'enable_sync_mode':False, 'enable_base64_output':True}
        for key in ('size','quality','output_format'):
            if fields.get(key) not in (None,'auto'):
                body[key] = fields[key]
        if images:
            body['images'] = ['data:'+(mimetypes.guess_type(str(p))[0] or 'image/png')+';base64,'+base64.b64encode(Path(p).read_bytes()).decode() for p in images]
        results = []
        for _ in range(fields.get('n',1)):
            submitted = self.unwrap(self.http.request('POST',self.base+'/generateImage',body))
            prediction = submitted.get('id') or submitted.get('prediction_id')
            if not prediction:
                raise ValueError('Prediction id missing')
            url = submitted.get('urls',{}).get('get') or self.base+'/result/'+str(prediction)
            if urlparse(url).netloc != urlparse(self.base).netloc:
                raise ValueError('Refusing to send credentials to a different poll host')
            for attempt in range(self.poll_limit):
                result = self.unwrap(self.http.request('GET',url))
                status = str(result.get('status','')).lower()
                if status in ('succeeded','completed'):
                    outputs = result.get('outputs')
                    if not outputs:
                        raise ValueError('Completed prediction has no images')
                    results.extend(self.http.image_bytes(item) for item in outputs)
                    break
                if status in ('failed','cancelled','canceled'):
                    raise RuntimeError(f'Prediction {prediction} {status}')
                self.sleep(2)
            else:
                raise TimeoutError(f'Prediction {prediction} did not complete within poll limit')
        return results

    @staticmethod
    def unwrap(response):
        if response.get('code') not in (None,0,200,'0','200'):
            raise ValueError('AtlasCloud returned an application error')
        data = response.get('data',response)
        if not isinstance(data,dict):
            raise ValueError('Unexpected prediction response')
        return data

# a4p-provenance: a4p-50d41ed6-f9f9-4470-ac9c-e700dd134a07/0bbd1a8389e33439e37d
