"""Portable, content-free visual recipes with user overrides outside installation."""
import re
from pathlib import Path
from .files import read, write
from .runtime import home

def catalog():
    result = {}
    for path in sorted((Path(__file__).parent / 'recipes').glob('*.json')):
        value = read(path)
        result[value['name']] = dict(value, source='bundled')
    if not result:
        raise FileNotFoundError('Bundled style recipes are missing; reinstall the complete package')
    directory=home()/'styles'
    if directory.exists():
        for path in sorted(directory.glob('*.json')):
            value=read(path)
            result[path.stem]=dict(value,source='personal')
    return result


def save(name, recipe, overwrite=False):
    if not name or re.search(r'[\\/:*?"<>|]',name) or name in ('.','..'):
        raise ValueError('Invalid style name')
    if not isinstance(recipe,dict) or not recipe.get('guidance'):
        raise ValueError('Style needs a guidance field')
    target=home()/'styles'/f'{name}.json'
    if (target.exists() or name in catalog()) and not overwrite:
        raise FileExistsError('Style already exists; pass overwrite to replace or override it')
    write(target,dict(recipe,name=name))
    return {'path':str(target)}

# a4p-provenance: a4p-50d41ed6-f9f9-4470-ac9c-e700dd134a07/9303d87226645d067d6d
