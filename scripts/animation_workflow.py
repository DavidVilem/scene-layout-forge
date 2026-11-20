"""Optional, masked animation of an accepted colored PNG. No image generation or training.

Pillow/NumPy render fixed-camera loops; optional imageio-ffmpeg encodes MP4.
Plans, sources, masks, candidate, decoded samples and manual reviews stay in history.
"""
import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from temporal_motion import law, state, validate_temporal

REVIEW_KEYS = ('source_fidelity', 'connections', 'occlusion', 'motion', 'loop', 'style')
KINDS = {'drift', 'breeze', 'light', 'plume', 'sprite'}


def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write(p, value):
    with Path(p).open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2, ensure_ascii=False, allow_nan=False)


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


def validate(plan, size):
    """Validate renderable scope, not semantics of inferred objects or human gait."""
    duration, fps = plan.get('seconds', 6), plan.get('fps', 24)
    if not isinstance(duration, (int, float)) or not math.isfinite(duration) or not 2 <= duration <= 20:
        raise ValueError('seconds must be finite, 2..20')
    if type(fps) is not int or not 12 <= fps <= 30 or duration * fps != int(duration * fps):
        raise ValueError('fps must be 12..30 with integral frame count')
    effects = plan.get('effects', [])
    if not effects:
        raise ValueError('At least one motivated effect required')
    ids = set()
    for e in effects:
        if not isinstance(e.get('id'), str) or not e['id'] or e['id'] in ids:
            raise ValueError('Unique effect IDs required')
        ids.add(e['id'])
        if e.get('kind') not in KINDS:
            raise ValueError('Unsupported effect; prepare layers/provider explicitly')
        for key in ('reason', 'anchor', 'occlusion', 'limits'):
            if not isinstance(e.get(key), str) or not e[key].strip():
                raise ValueError('Missing motion reasoning: ' + key)
        if type(e.get('cycles', 1)) is not int or not 1 <= e.get('cycles', 1) <= 8:
            raise ValueError('Integral cycles 1..8 required for seamless loops')
        for key in ('dx', 'dy', 'strength', 'angle'):
            v = e.get(key, 0)
            if not isinstance(v, (float, int)) or not math.isfinite(v):
                raise ValueError('Finite motion parameters required')
        if abs(e.get('dx', 0)) > 32 or abs(e.get('dy', 0)) > 32 or abs(e.get('angle', 0)) > 10:
            raise ValueError('Local subtle-motion renderer: <=32px translation, <=10deg rotation')
        if not 0 <= e.get('strength', .04) <= .2:
            raise ValueError('strength must be 0..0.2')
        if e['kind'] == 'sprite' and not all(e.get(k) for k in ('sprite', 'clean_plate', 'removal_mask', 'pivot')):
            raise ValueError('Sprite motion requires RGBA layer, clean plate, removal mask and pivot')
        if e['kind'] == 'sprite':
            pivot = e['pivot']
            if len(pivot) != 2 or not all(isinstance(v, (int, float)) and math.isfinite(v) for v in pivot) or not (0 <= pivot[0] < size[0] and 0 <= pivot[1] < size[1]):
                raise ValueError('Sprite pivot must lie on the source canvas')
        if e['kind'] == 'plume':
            origin = e.get('origin', [])
            if len(origin) != 2 or not all(isinstance(v, (float, int)) and math.isfinite(v) for v in origin):
                raise ValueError('Plume requires a visible, identified origin')
            if not 0 <= origin[0] < size[0] or not 0 <= origin[1] < size[1]:
                raise ValueError('Plume origin outside image')

    validate_temporal(plan, size)


def mask_for(effect, size):
    if effect.get('mask'):
        with Image.open(effect['mask']) as im:
            if im.size != size:
                raise ValueError('Mask size differs from source')
            mask = im.convert('L')
    else:
        points = effect.get('polygon', [])
        if len(points) < 3 or any(len(p) != 2 or not all(isinstance(v, (int, float)) and math.isfinite(v) for v in p)
                                 or not (0 <= p[0] < size[0] and 0 <= p[1] < size[1]) for p in points):
            raise ValueError('Mask or >=3 valid pixel polygon points required')
        mask = Image.new('L', size)
        ImageDraw.Draw(mask).polygon([tuple(p) for p in points], fill=255)
    feather = effect.get('feather', 2)
    if not isinstance(feather, (int, float)) or not math.isfinite(feather) or not 0 <= feather <= 12:
        raise ValueError('Feather must be 0..12 pixels')
    if feather:
        # Blur inward only; never leak into protected pixels outside the supplied mask.
        blurred = np.asarray(mask.filter(ImageFilter.GaussianBlur(feather)))
        mask = Image.fromarray(np.minimum(np.asarray(mask), blurred))
    if mask.getbbox() is None:
        raise ValueError('Empty animation mask')
    return mask


def prepare(project, colored, plan, brief, parent_history=None):
    """Existing paired PNGs can start a linked continuation; never fabricate old provenance."""
    colored = Path(colored).resolve()
    illustrated = colored.with_name('ilustrada.png')
    if colored.name != 'coloreada.png' or not illustrated.is_file():
        raise ValueError('Use coloreada.png beside its ilustrada.png')
    with Image.open(colored) as im:
        if im.format != 'PNG': raise ValueError('PNG source required')
        im.load(); size = im.size
    with Image.open(illustrated) as im:
        im.load()
        if im.format != 'PNG' or im.size != size: raise ValueError('Source pair must match dimensions')
    if not isinstance(brief, str) or not brief.strip(): raise ValueError('Original brief required')
    history = Path(project).resolve() / 'output' / 'history'
    history.mkdir(parents=True, exist_ok=True)
    job = Path(tempfile.mkdtemp(prefix='animation-', dir=history))
    write(job / 'brief.json', {'brief': brief, 'parent_history': str(parent_history) if parent_history else None,
                              'provenance': 'continuation of existing pair; see parent when supplied'})
    try:
        validate(plan, size)
        shutil.copyfile(colored, job / 'coloreada-source.png')
        shutil.copyfile(illustrated, job / 'ilustrada-source.png')
        shutil.copyfile(__file__, job / 'renderer-source.py')
        shutil.copyfile(Path(__file__).with_name('temporal_motion.py'), job / 'temporal_motion.py')
        local = json.loads(json.dumps(plan, allow_nan=False))
        protected = Image.new('L', size)
        if plan.get('protected_mask'):
            with Image.open(plan['protected_mask']) as im:
                if im.size != size: raise ValueError('Protected mask dimension mismatch')
                protected = im.convert('L')
        protected.save(job / 'protected.png')
        for i, e in enumerate(local['effects']):
            mask = mask_for(e, size)
            if e['kind'] in ('drift', 'breeze'):
                # Inverse sampling must not reveal black outside the source canvas.
                x0,y0,x1,y1 = mask.getbbox()
                cycles=e.get('cycles',1)
                poses=[state(e,t) for t in (0,1/(4*cycles),3/(4*cycles),1)]
                if any(x0-p['dx'] < 0 or y0-p['dy'] < 0 or x1-1-p['dx'] >= size[0] or y1-1-p['dy'] >= size[1] for p in poses):
                    raise ValueError('Displacement samples beyond source; inset mask or prepare extended layer')
            if np.any((np.asarray(mask) > 0) & (np.asarray(protected) > 0)):
                raise ValueError('Motion intersects explicitly protected connections/labels')
            mask.save(job / f'mask-{i}.png'); e['mask'] = f'mask-{i}.png'
            for key in ('sprite', 'clean_plate', 'removal_mask', 'occluder_mask'):
                if e.get(key):
                    src = Path(e[key])
                    with Image.open(src) as im:
                        im.load()
                        if im.size != size: raise ValueError('All layers must use full canvas coordinates')
                        if key == 'sprite' and (im.mode != 'RGBA' or im.getextrema()[3][0] == 255):
                            raise ValueError('Sprite requires real transparency')
                        if key == 'removal_mask' and np.any((np.asarray(im.convert('L')) > 0) & (np.asarray(mask) == 0)):
                            raise ValueError('Removal exceeds motion mask')
                    target = f'{key}-{i}.png'; shutil.copyfile(src, job / target); e[key] = target
            if e.get('frames'):
                kept=[]
                for frame_index, frame in enumerate(e['frames']):
                    with Image.open(frame) as im:
                        im.load()
                        if im.size != size or im.mode != 'RGBA' or im.getextrema()[3][0] == 255:
                            raise ValueError('Pose/content frames need full-canvas RGBA with transparency')
                    name=f'pose-{i}-{frame_index}.png'; shutil.copyfile(frame,job/name); kept.append(name)
                e['frames']=kept
        local.pop('protected_mask', None)
        write(job / 'plan.json', local)
        root = Path(__file__).resolve().parents[1]
        write(job / 'source.json', {'colored': str(colored), 'illustrated': str(illustrated),
              'colored_hash': digest(colored), 'illustrated_hash': digest(illustrated), 'size': size,
              'revision': re.search(r'revision:\s*"([^"]+)"', (root / 'SKILL.md').read_text(encoding='utf-8')).group(1),
              'skill_hash': digest(root / 'SKILL.md'), 'renderer_hash': digest(__file__), 'temporal_hash': digest(Path(__file__).with_name('temporal_motion.py'))})
        write(job / 'receipt.json', {p.name: digest(p) for p in job.iterdir() if p.is_file()})
    except Exception as exc:
        write(job / 'failure.json', {'error': str(exc)}); raise
    return job


def verify(job):
    job = Path(job)
    for name, value in read(job / 'receipt.json').items():
        if digest(job / name) != value: raise ValueError('History changed: ' + name)
    source = read(job / 'source.json')
    for key in ('colored', 'illustrated'):
        if digest(source[key]) != source[key + '_hash']: raise ValueError('Source pair changed')
    if digest(__file__) != source['renderer_hash']: raise ValueError('Renderer changed since preparation')
    if digest(Path(__file__).with_name('temporal_motion.py')) != source['temporal_hash']: raise ValueError('Temporal helper changed')
    return source


class Renderer:
    def __init__(self, job):
        self.job = Path(job); verify(job)
        self.plan = read(self.job / 'plan.json')
        self.source = Image.open(self.job / 'coloreada-source.png').convert('RGB')
        self.base = self.source.copy(); self.layers = []
        self.union = np.zeros((self.source.height, self.source.width), dtype=bool)
        for e in self.plan['effects']:
            mask = Image.open(self.job / e['mask']).convert('L')
            self.union |= np.asarray(mask) > 0
            assets = {k: Image.open(self.job / e[k]).copy() for k in ('sprite', 'clean_plate', 'removal_mask', 'occluder_mask') if e.get(k)}
            if e.get('frames'): assets['frames'] = [Image.open(self.job / f).convert('RGBA') for f in e['frames']]
            if e['kind'] == 'sprite':
                self.base = Image.composite(assets['clean_plate'].convert('RGB'), self.base, assets['removal_mask'].convert('L'))
            self.layers.append((e, mask, assets))

    def frame(self, phase):
        phase = min(1., max(0., float(phase)))
        out = self.base.copy()
        for e, mask, assets in self.layers:
            motion = state(e, phase)
            dx, dy = motion['dx'], motion['dy']
            kind = e['kind']
            if kind in ('drift', 'breeze'):
                # Small displacement within a fixed mask; feathered boundary stays pinned.
                layer = self.source.transform(self.source.size, Image.Transform.AFFINE,
                                              (1, 0, -dx, 0, 1, -dy), Image.Resampling.BICUBIC)
                out = Image.composite(layer, out, mask)
            elif kind == 'light':
                layer = Image.fromarray(np.clip(np.asarray(out, dtype=np.float32) * (1 + e.get('strength', .04) * motion['light']), 0, 255).astype('uint8'))
                out = Image.composite(layer, out, mask)
            elif kind == 'plume':
                # Periodic staggered puffs fade to zero at birth/death; opaque boundaries remain clipped.
                layer = Image.new('RGBA', out.size); draw = ImageDraw.Draw(layer)
                x, y = e['origin']
                for j in range(12):
                    age = ((phase % 1) * e.get('cycles', 1) + j / 12) % 1
                    radius = 2 + 10 * age
                    px, py = x + e.get('dx', 8) * age, y + e.get('dy', -32) * age
                    alpha = int(255 * e.get('strength', .15) * math.sin(math.pi * age) ** 2)
                    draw.ellipse((px-radius, py-radius, px+radius, py+radius), fill=(180, 185, 190, alpha))
                layer = layer.filter(ImageFilter.GaussianBlur(2))
                layer.putalpha(Image.fromarray((np.asarray(layer.getchannel('A'), dtype=np.float32) * np.asarray(mask) / 255).astype('uint8')))
                out = Image.alpha_composite(out.convert('RGBA'), layer).convert('RGB')
            else:
                frames = assets.get('frames')
                sprite = frames[int((phase % 1)*e.get('cycles',1)*len(frames)) % len(frames)] if frames else assets['sprite']
                layer = sprite.convert('RGBA').rotate(motion['angle'], Image.Resampling.BICUBIC, center=tuple(e['pivot']))
                scale = motion['scale']; px,py = e['pivot']
                layer = layer.transform(layer.size, Image.Transform.AFFINE,
                    (1/scale, 0, px-(px+dx)/scale, 0, 1/scale, py-(py+dy)/scale), Image.Resampling.BICUBIC)
                if assets.get('occluder_mask') is not None:
                    alpha = np.asarray(layer.getchannel('A'),dtype=np.float32)*(1-np.asarray(assets['occluder_mask'].convert('L'))/255)
                    layer.putalpha(Image.fromarray(alpha.astype('uint8')))
                if np.any((np.asarray(layer.getchannel('A')) > 0) & (np.asarray(mask) == 0)):
                    raise ValueError('Sprite leaves declared motion envelope')
                layer.putalpha(Image.fromarray((np.asarray(layer.getchannel('A'), dtype=np.float32) * np.asarray(mask) / 255).astype('uint8')))
                out = Image.alpha_composite(out.convert('RGBA'), layer).convert('RGB')
        if np.any(np.asarray(out)[~self.union] != np.asarray(self.source)[~self.union]):
            raise ValueError('Pixels outside allowed motion changed')
        return out


def ffmpeg_exe():
    found = shutil.which('ffmpeg')
    if found: return found
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError as exc:
        raise RuntimeError('Install optional requirements-animation.txt or provide ffmpeg on PATH') from exc


def render(job):
    job = Path(job); r = Renderer(job); exe = ffmpeg_exe()
    target = job / 'candidate.mp4'
    if target.exists(): raise FileExistsError('Use a new history attempt; retain failed renders')
    fps = r.plan.get('fps', 24); n = int(r.plan.get('seconds', 6) * fps)
    w, h = r.source.size
    # yuv444p retains original dimensions, including odd sizes; no silent resize/crop.
    cmd = [exe, '-v', 'error', '-n', '-f', 'rawvideo', '-pixel_format', 'rgb24', '-video_size', f'{w}x{h}',
           '-framerate', str(fps), '-i', '-', '-an', '-c:v', 'libx264', '-crf', '15', '-preset', 'medium',
           '-pix_fmt', 'yuv444p', '-movflags', '+faststart', str(target)]
    write(job / 'encode-request.json', {'command': cmd, 'ffmpeg': subprocess.check_output([exe, '-version']).decode(errors='replace').splitlines()[0]})
    selected = {0, n//8, n//4, 3*n//8, n//2, 5*n//8, 3*n//4, 7*n//8, n-1}; frames = []
    with (job / 'encode.log').open('wb') as err:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=err)
        try:
            for i in range(n):
                frame = r.frame(i/n if r.plan.get('timeline','once')=='loop' else i/(n-1))
                if i in selected:
                    frame.save(job / f'frame-{i:04d}.png'); frames.append(frame.copy())
                proc.stdin.write(frame.tobytes())
            proc.stdin.close()
            if proc.wait() != 0: raise RuntimeError('Video encoder failed; see encode.log')
        except Exception as exc:
            proc.kill(); proc.wait(); write(job / 'render-failure.json', {'error': str(exc)}); raise
    seam = float(np.abs(np.asarray(frames[-1], dtype=float) - np.asarray(frames[0], dtype=float)).mean())
    changed = sum(bool(np.any(np.asarray(f) != np.asarray(frames[0]))) for f in frames[1:])
    if not changed: raise ValueError('No visible pixel motion; candidate retained')
    # Decode every encoded frame, verify count and retain actual decoded QA samples.
    decode = subprocess.Popen([exe, '-v', 'error', '-i', str(target), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    count = 0; chunk_size = w*h*3
    while True:
        raw = decode.stdout.read(chunk_size)
        if not raw: break
        if len(raw) != chunk_size: raise ValueError('Truncated decoded frame')
        if count in selected: Image.frombytes('RGB', (w,h), raw).save(job / f'decoded-{count:04d}.png')
        count += 1
    error = decode.stderr.read(); result = decode.wait()
    if result or count != n: raise ValueError(f'Decode failed: {count}/{n}: {error!r}')
    thumbs = []
    for f in sorted(job.glob('decoded-*.png')):
        im = Image.open(f).convert('RGB'); im.thumbnail((480,300)); thumbs.append(im)
    sheet = Image.new('RGB', (480*len(thumbs), 320), 'white')
    for i, im in enumerate(thumbs): sheet.paste(im, (480*i, 20))
    sheet.save(job / 'contact-sheet.png')
    report = {'candidate_hash': digest(target), 'dimensions': [w,h], 'fps': fps, 'frames': count, 'seconds': count/fps,
              'outside_motion_masks': 'exactly unchanged in uncompressed frames', 'seam_mean_delta': seam,
              'timeline': r.plan.get('timeline','once'),
              'periodic_endpoint_equal': np.array_equal(np.asarray(r.frame(0)), np.asarray(r.frame(1))),
              'manual_review_required': True, 'codec_note': 'H264 yuv444p; some hardware players require a separate yuv420p export'}
    write(job / 'render.json', report)
    return report


def accept(job, observations):
    job = Path(job); source = verify(job); report = read(job / 'render.json')
    if digest(job / 'candidate.mp4') != report['candidate_hash']: raise ValueError('Candidate changed')
    if set(observations) != set(REVIEW_KEYS): raise ValueError('Six actual visual review observations required')
    for key, obs in observations.items():
        if obs.get('status') not in ('passed', 'uncertain', 'failed') or not isinstance(obs.get('notes'), str) or not obs['notes'].strip():
            raise ValueError('Status and evidence required: ' + key)
    review_path = job / ('review-' + str(len(list(job.glob('review-*.json'))) + 1) + '.json')
    write(review_path, {'candidate_hash': report['candidate_hash'], 'observations': observations})
    if any(o['status'] == 'failed' for o in observations.values()): raise ValueError('Known defect: retain attempt, correct in a new linked job')
    if report.get('timeline','loop') == 'loop' and not report['periodic_endpoint_equal']: raise ValueError('Nonperiodic renderer')
    destination = Path(source['colored']).with_name('animada.mp4')
    with destination.open('xb') as dst, (job / 'candidate.mp4').open('rb') as src: shutil.copyfileobj(src, dst)
    write(job / 'delivered.json', {'path': str(destination), 'sha256': digest(destination), 'review': review_path.name,
          'limitations': [o['notes'] for o in observations.values() if o['status'] == 'uncertain'], **report})
    return destination


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); sub = p.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('prepare'); a.add_argument('--project', required=True); a.add_argument('--colored', required=True)
    a.add_argument('--plan', required=True); a.add_argument('--brief', required=True); a.add_argument('--parent-history')
    a = sub.add_parser('render'); a.add_argument('job')
    a = sub.add_parser('accept'); a.add_argument('job'); a.add_argument('--review', required=True)
    args = p.parse_args()
    if args.cmd == 'prepare': print(prepare(args.project, args.colored, read(args.plan), args.brief, args.parent_history))
    elif args.cmd == 'render': print(json.dumps(render(args.job)))
    else: print(accept(args.job, read(args.review)))
