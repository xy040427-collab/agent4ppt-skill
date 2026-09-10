"""Installation-independent configuration, explicit setup and diagnostics."""
import importlib.util
import os
import subprocess
import sys
import venv
from pathlib import Path
from .files import read, write


def home():
    return Path(os.environ.get('AGENT4PPT_HOME', '~/.agent4ppt')).expanduser().resolve()


def config():
    path = home() / 'config.json'
    data = read(path) if path.exists() else {}
    mapping = {'api_key':'OPENAI_API_KEY', 'base_url':'OPENAI_BASE_URL', 'model':'AGENT4PPT_MODEL'}
    for key, variable in mapping.items():
        if os.environ.get(variable):
            data[key] = os.environ[variable]
    data.setdefault('model', 'gpt-image-2')
    data.setdefault('base_url', 'https://api.openai.com/v1')
    return data


def configure(base_url=None, model=None, key_env=None, clear_base=False):
    path = home() / 'config.json'
    data = read(path) if path.exists() else {}
    if clear_base:
        data.pop('base_url', None)
    if base_url is not None:
        from urllib.parse import urlparse
        if urlparse(base_url).scheme not in ('https','http'):
            raise ValueError('Expected http(s) API base URL')
        data['base_url'] = base_url.rstrip('/')
    if model:
        data['model'] = model
    if key_env:
        value = os.environ.get(key_env)
        if not value:
            raise ValueError('Selected key environment variable is empty')
        data['api_key'] = value
    write(path, data)
    path.chmod(0o600)
    return {'path': str(path), 'model': data.get('model'), 'key_configured': bool(data.get('api_key'))}


def bootstrap(upgrade=False):
    directory = home() / 'venv'
    python = directory / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if not python.exists():
        venv.EnvBuilder(with_pip=True).create(directory)
    command = [str(python), '-m', 'pip', 'install', 'Pillow>=10.0,<13']
    if upgrade:
        command.append('--upgrade')
    subprocess.run(command, check=True)
    return {'python': str(python)}


def doctor(check_api=False):
    data = config()
    report = {'python': sys.executable, 'home': str(home()), 'pillow': bool(importlib.util.find_spec('PIL')),
              'model': data['model'], 'api_key_configured': bool(data.get('api_key')),
              'builtin_image_tool': 'Agent must check its callable tools; Python cannot detect it.'}
    if check_api:
        from .providers import Transport
        if not data.get('api_key'):
            raise ValueError('No API key configured')
        from urllib.parse import urlparse
        if 'atlascloud.ai' in (urlparse(data['base_url']).hostname or ''):
            report['api_check'] = 'No non-billable generation probe performed for AtlasCloud'
        else:
            Transport(data['api_key']).request('GET', data['base_url'].rstrip('/')+'/models')
            report['api_check'] = 'models endpoint reachable; image-generation access not proven'
    return report

# a4p-provenance: a4p-50d41ed6-f9f9-4470-ac9c-e700dd134a07/4c7c9450e0b42988d33b
