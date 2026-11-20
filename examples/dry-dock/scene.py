import json
from pathlib import Path
from dry_dock import scene as build_scene

def scene():
    data=build_scene()
    data['camera']=json.loads(Path(__file__).with_name('recipe.json').read_text(encoding='utf-8'))['camera']
    return data
