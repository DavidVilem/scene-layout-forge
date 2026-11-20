"""Stage 8: verify the PNG-bound review and architectural witnesses before copying.

No cleanup or overwrite; unsuccessful attempts remain in the run history.
"""
import json
import shutil
from pathlib import Path
from architecture_stages import enabled,record_stage,save_record
from pixel_review import errors,image_identity
from finish_contract import check

def accept(lock,image,review,run,destination):
    from execution_history import errors as history_errors,save
    issues=history_errors(lock,run)
    if issues:raise ValueError('; '.join(issues))
    check(lock,lock['scene'])
    issues=errors(lock,image,review)
    if review.get('status')=='needs_correction':issues.append('visible defects require correction or a separately disclosed failed study, not acceptance')
    if issues:raise ValueError('; '.join(issues))
    dst=Path(destination)
    if dst.exists():raise FileExistsError('selected destination already exists')
    source=Path(image).resolve();history=Path(run).resolve()
    if history not in source.parents:raise ValueError('retain generated PNG inside run history before delivery')
    import uuid
    save(history/'08-finish'/('pixel-review-'+uuid.uuid4().hex+'.json'),review)
    record=None
    if enabled(lock['scene']):
        record=record_stage(lock['scene'],8,lock['architecture_stages'],lock['view'],review['observations'],note='Independent image-bound review; geometric approval is not pixel proof')
        record['image']=image_identity(image)
        save_record(run,record)
    dst.parent.mkdir(parents=True,exist_ok=True)
    with Path(image).open('rb') as src,dst.open('xb') as out:shutil.copyfileobj(src,out)
    selected={'image':image_identity(dst),'selected':str(dst),'source':str(image),'stage_8':record,'limitations':[o for o in review['observations'] if o['state'] in ('uncertain','occluded')]}
    path=Path(run)/'08-finish'/('selected-'+selected['image']['file_sha256'][:12]+'.json')
    with path.open('x',encoding='utf-8') as f:json.dump(selected,f,indent=2)
    return selected
