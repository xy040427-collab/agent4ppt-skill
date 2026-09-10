"""Generation request validation, batch execution and explicitly requested keying."""
import concurrent.futures
import io
import json
import math
import re
import sys
import time
from pathlib import Path
from PIL import Image, ImageFilter, ImageChops
from .files import atomic
from .providers import OpenAIImages, AtlasImages, ServiceError
from .runtime import config


def prepare(job, settings):
    prompt = job.get('prompt', '')
    if job.get('prompt_file'):
        prompt = sys.stdin.read() if job['prompt_file'] == '-' else Path(job['prompt_file']).read_text(encoding='utf-8')
    if not isinstance(prompt,str) or not prompt.strip():
        raise ValueError('A nonempty prompt is required')
    if job.get('brief') and job.get('augment', True):
        prompt += '\n\n' + json.dumps(job['brief'],ensure_ascii=False)
    fields = dict(job.get('options',{}), prompt=prompt)
    fields.setdefault('model', settings.get('model','gpt-image-2'))
    fields.setdefault('size','2560x1440')
    fields.setdefault('quality','medium')
    fields.setdefault('output_format','png')
    fields.setdefault('n',1)
    if type(fields['n']) is not int or not 1 <= fields['n'] <= 10:
        raise ValueError('n must be 1..10')
    if fields['quality'] not in ('low','medium','high','auto'):
        raise ValueError('Invalid quality')
    if fields['output_format'] not in ('png','jpeg','webp'):
        raise ValueError('Invalid output_format')
    if fields.get('background') not in (None,'transparent','opaque','auto'):
        raise ValueError('Invalid background')
    if fields['size'] != 'auto':
        try:
            w,h = map(int, fields['size'].split('x'))
        except (AttributeError,ValueError):
            raise ValueError('size must be auto or WIDTHxHEIGHT') from None
        if 'gpt-image-2' in fields['model']:
            if min(w,h)<=0 or w%16 or h%16 or max(w,h)>3840 or max(w,h)/min(w,h)>3 or not 655360 <= w*h <= 8294400:
                raise ValueError('Size outside GPT Image 2 limits')
        elif fields['size'] not in ('1024x1024','1536x1024','1024x1536'):
            raise ValueError('Use a supported legacy model size or auto')
    if 'gpt-image-2' in fields['model']:
        if fields.get('background')=='transparent':
            raise ValueError('This model does not support transparent API output; choose a supported model explicitly')
        fields.pop('input_fidelity',None)
    if fields.get('input_fidelity') not in (None,'low','high'):
        raise ValueError('Invalid input_fidelity')
    if fields.get('moderation') not in (None,'auto','low'):
        raise ValueError('Invalid moderation')
    compression = fields.get('output_compression')
    if compression is not None and (type(compression) is not int or not 0<=compression<=100 or fields['output_format']=='png'):
        raise ValueError('output_compression needs JPEG/WebP and integer 0..100')
    images = [Path(p).resolve() for p in job.get('images',[])]
    if len(images)>16:
        raise ValueError('At most 16 input images')
    for p in images:
        if not p.is_file() or p.stat().st_size > 50*1024*1024:
            raise ValueError('Input image missing or exceeds 50 MiB')
        with Image.open(p) as image:
            image.verify()
    mask = Path(job['mask']).resolve() if job.get('mask') else None
    if mask:
        if not images:
            raise ValueError('Mask requires an input image')
        with Image.open(images[0]) as source, Image.open(mask) as m:
            if m.format!='PNG' or 'A' not in m.getbands() or m.size!=source.size:
                raise ValueError('Mask must be RGBA PNG matching the first image dimensions')
    return fields, images, mask


def destinations(job, fields):
    suffix = {'png':'.png','jpeg':'.jpg','webp':'.webp'}[fields['output_format']]
    output = Path(job['out']).resolve() if job.get('out') else (Path(job.get('out_dir', '.')) / ('image' + suffix)).resolve()
    if output.suffix.lower() not in (suffix, '.jpeg' if suffix=='.jpg' else suffix):
        raise ValueError('Output extension must match output_format')
    return [output] if fields['n']==1 else [output.with_name(f'{output.stem}-{i:02d}{output.suffix}') for i in range(1,fields['n']+1)]


def preview_path(output, job):
    suffix = job.get('downscale_suffix', '-web')
    if not isinstance(suffix, str) or not suffix or re.search(r'[\\/:*?"<>|]', suffix):
        raise ValueError('downscale_suffix must be a nonempty filename suffix')
    return output.with_name(output.stem + suffix + '.png')


def normalize_batch(jobs, defaults=None):
    """Keep shared options while allowing per-job overrides and short prompts."""
    defaults = defaults or {}
    result = []
    for index, entry in enumerate(jobs, 1):
        if isinstance(entry, str):
            entry = {'prompt': entry}
        if not isinstance(entry, dict):
            raise ValueError('Each batch job must be an object or a prompt string')
        job = dict(defaults, **entry)
        job['options'] = dict(defaults.get('options', {}), **entry.get('options', {}))
        if 'brief' in defaults or 'brief' in entry:
            job['brief'] = dict(defaults.get('brief', {}), **entry.get('brief', {}))
        if job.get('prompt_file') == '-':
            raise ValueError('Batch jobs cannot share stdin; use prompt text or separate files')
        if not job.get('out'):
            extension = {'png': '.png', 'jpeg': '.jpg', 'webp': '.webp'}.get(job['options'].get('output_format', 'png'))
            if extension is None:
                raise ValueError('Invalid output_format')
            job['out'] = str(Path(job.get('out_dir', '.')) / f'image-{index:03d}{extension}')
        result.append(job)
    return result


def generate(job, dry_run=False, provider=None, settings=None):
    settings = settings or config()
    fields, images, mask = prepare(job, settings)
    targets = destinations(job,fields)
    if job.get('downscale_max_dim') is not None and (type(job['downscale_max_dim']) is not int or job['downscale_max_dim']<=0):
        raise ValueError('downscale_max_dim must be a positive integer')
    if job.get('downscale_max_dim'):
        for target in targets:
            preview_path(target, job)
    if job.get('downscale_max_dim') and not job.get('overwrite'):
        if any(preview_path(p, job).exists() for p in targets):
            raise FileExistsError('A downscaled output already exists')
    if not job.get('overwrite') and any(p.exists() for p in targets):
        raise FileExistsError('An output already exists; set overwrite explicitly')
    backend = job.get('backend','openai')
    if backend not in ('openai','atlascloud'):
        raise ValueError('CLI image execution supports openai or atlascloud; builtin is executed by the agent')
    if dry_run:
        return {'backend':backend,'request':fields,'images':[str(p) for p in images],'mask':str(mask) if mask else None,'outputs':[str(p) for p in targets]}
    if provider is None:
        if not settings.get('api_key'):
            raise ValueError('No API key configured; builtin tool needs no key')
        provider = (AtlasImages if backend=='atlascloud' else OpenAIImages)(settings)
    attempts = job.get('attempts',1)
    if type(attempts) is not int or not 1<=attempts<=5:
        raise ValueError('attempts must be 1..5')
    for attempt in range(attempts):
        try:
            results = provider.run(fields,images,mask)
            break
        except ServiceError as exc:
            if exc.status not in (429,500,502,503,504) or attempt==attempts-1:
                raise
            time.sleep(min(60,max(exc.retry_after,2**attempt)))
    if len(results)!=len(targets):
        raise ValueError('Image count does not match request')
    for data in results:
        with Image.open(io.BytesIO(data)) as image:
            expected = {'png':'PNG','jpeg':'JPEG','webp':'WEBP'}[fields['output_format']]
            if image.format != expected:
                raise ValueError('Service returned a different format than requested')
            image.verify()
    for data,target in zip(results,targets):
        atomic(target,data)
        if job.get('downscale_max_dim'):
            maximum = int(job['downscale_max_dim'])
            if maximum<=0:
                raise ValueError('downscale_max_dim must be positive')
            with Image.open(io.BytesIO(data)) as image:
                image.thumbnail((maximum,maximum),Image.Resampling.LANCZOS)
                buffer = io.BytesIO()
                image.save(buffer,'PNG')
                atomic(preview_path(target, job),buffer.getvalue())
    return {'outputs':[str(p) for p in targets], 'backend':backend}


def batch(jobs, concurrency=3, dry_run=False, fail_fast=False, runner=generate, defaults=None):
    if not 1<=concurrency<=32 or not 1<=len(jobs)<=500:
        raise ValueError('Invalid concurrency or job count')
    jobs = normalize_batch(jobs, defaults)
    paths=[]
    for job in jobs:
        fields,_,_=prepare(job,config())
        target=destinations(job,fields)
        paths.extend(target)
        if job.get('downscale_max_dim'):
            paths.extend(preview_path(p, job) for p in target)
    if len(paths)!=len(set(paths)):
        raise ValueError('Batch output paths collide')
    results=[None]*len(jobs)
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures={pool.submit(runner,job,dry_run=dry_run):i for i,job in enumerate(jobs)}
        for future in concurrent.futures.as_completed(futures):
            i=futures[future]
            if future.cancelled():
                results[i]={'ok':False,'error':'cancelled before starting'}
                continue
            try:
                results[i]={'ok':True,**future.result()}
            except Exception as exc:
                results[i]={'ok':False,'error':str(exc)}
                if fail_fast:
                    for pending in futures:
                        pending.cancel()
    return results


def chroma(source, output, key='#00ff00', tolerance=12, soft=False, opaque=96,
           sample='none', contract=0, feather=0, despill=False, overwrite=False):
    if Path(output).exists() and not overwrite:
        raise FileExistsError(output)
    if not 0<=tolerance<=255 or (soft and not tolerance<opaque<=255) or not 0<=contract<=32 or not 0<=feather<=64:
        raise ValueError('Invalid matte thresholds or edge settings')
    if Path(output).suffix.lower() not in ('.png','.webp'):
        raise ValueError('Transparent output needs PNG or WebP')
    image=Image.open(source).convert('RGBA')
    if sample not in ('none','corners','border'):
        raise ValueError('Invalid key sampling mode')
    color=tuple(bytes.fromhex(key.lstrip('#')))
    if len(color)!=3:
        raise ValueError('key must have six hexadecimal digits')
    if sample!='none':
        w,h=image.size
        points=([image.getpixel((x,y)) for x,y in [(0,0),(w-1,0),(0,h-1),(w-1,h-1)]] if sample=='corners' else
                [image.getpixel((x,y)) for x in range(w) for y in (0,h-1)] + [image.getpixel((x,y)) for y in range(h) for x in (0,w-1)])
        from collections import Counter
        color=Counter(tuple(v[:3]) for v in points).most_common(1)[0][0]
    dominant=max(range(3),key=lambda i:color[i])
    rgba=[]
    for pixel in image.getdata():
        distance=max(abs(pixel[i]-color[i]) for i in range(3))
        ramp=max(0,min(1,(distance-tolerance)/(opaque-tolerance))) if soft else float(distance>tolerance)
        ramp=ramp*ramp*(3-2*ramp)
        rgb=list(pixel[:3])
        if despill and ramp<1 and color[dominant]>min(color):
            other=max(rgb[i] for i in range(3) if i!=dominant)
            rgb[dominant]=round(other+(rgb[dominant]-other)*ramp)
        rgba.append(tuple(rgb)+(round(pixel[3]*ramp),))
    image.putdata(rgba)
    alpha=image.getchannel('A')
    if contract:
        alpha=alpha.filter(ImageFilter.MinFilter(contract*2+1))
    if feather:
        alpha=alpha.filter(ImageFilter.GaussianBlur(feather))
    # Never make previously transparent pixels opaque.
    with Image.open(source) as original:
        alpha=ImageChops.darker(alpha,original.convert('RGBA').getchannel('A'))
    image.putalpha(alpha)
    buffer=io.BytesIO()
    image.save(buffer,'WEBP' if Path(output).suffix.lower()=='.webp' else 'PNG',lossless=True)
    atomic(output,buffer.getvalue())
    return {'path':str(Path(output).resolve()),'key':color,'transparent_pixels':sum(a==0 for a in alpha.getdata())}

# a4p-provenance: a4p-50d41ed6-f9f9-4470-ac9c-e700dd134a07/72c212a70eb0376c9813
