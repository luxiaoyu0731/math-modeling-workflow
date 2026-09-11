"""Optional review contracts, shared by generated and existing paper projects."""
from pathlib import Path
import json

LEVELS = {'historical_hash', 'recomputed', 'isolated_rebuild', 'cold_start', 'cross_environment'}

def audit_contracts(root, plan, local, digest):
    errors=[]; paths=[]
    def record(key):
        if not plan.get(key):return None
        p=local(root,plan[key]); paths.append(p)
        return json.loads(p.read_text(encoding='utf-8'))
    model=record('model_review')
    if model is not None:
        rows=model.get('relations',[])
        if not rows:errors.append('model review has no relations')
        for row in rows:
            if any(not row.get(k) for k in ('id','given','interpretation','choice','reason','status')):
                errors.append('incomplete model relation')
            if row.get('status') not in ('accepted','conditional'):errors.append('unresolved model relation: '+str(row.get('id')))
            if row.get('choice') not in ('as_given','additional','modified'):errors.append('invalid model choice')
            if row.get('choice')!='as_given' and not row.get('comparison') and not row.get('limitation'):
                errors.append('changed model relation needs comparison or explicit limitation')
            for name,sha in row.get('comparison',{}).items():
                p=local(root,name);paths.append(p)
                if not p.is_file() or digest(p)!=sha:errors.append('stale model comparison: '+name)
        if not model.get('reviewer') or not model.get('notes'):errors.append('model review attribution missing')
    validation=record('validation_ledger')
    if validation is not None:
        for entry in validation.get('checks',[]):
            if entry.get('level') not in LEVELS:errors.append('unknown validation level')
            if entry.get('status') not in ('passed','failed','not_run'):errors.append('invalid validation status')
            if entry.get('status')=='failed':errors.append('failed validation: '+str(entry.get('id')))
            if entry.get('status')!='passed':continue
            if not entry.get('artifacts') or not entry.get('scope') or not entry.get('limitations'):
                errors.append('validation needs artifacts, scope and limitations')
            if entry.get('level')!='historical_hash' and (not entry.get('command') or not entry.get('environment') or not entry.get('log')):
                errors.append('execution validation needs command, environment and log')
            if entry.get('log') and entry['log'] not in entry.get('artifacts',{}):errors.append('execution log must be hash-bound')
            if entry.get('level')=='cross_environment' and not entry.get('source_environment'):errors.append('cross-environment source missing')
            for name,sha in entry.get('artifacts',{}).items():
                p=local(root,name);paths.append(p)
                if not p.is_file() or digest(p)!=sha:errors.append('stale validation evidence: '+name)
    impact=record('change_impact')
    if impact is not None:
        for change in impact.get('changes',[]):
            if not all(change.get(k) for k in ('path','before_sha256','after_sha256','effect','affected_outputs','decision')):
                errors.append('incomplete change impact')
            p=local(root,change['path']);paths.append(p)
            if not p.is_file() or digest(p)!=change.get('after_sha256'):errors.append('stale change impact: '+change['path'])
            if change.get('decision') not in ('rerun','compatible','pending'):errors.append('invalid impact decision')
            if change.get('decision')=='pending':errors.append('pending change impact')
            if not change.get('evidence'):errors.append('impact decision needs evidence')
            for name,sha in change.get('evidence',{}).items():
                p=local(root,name);paths.append(p)
                if not p.is_file() or digest(p)!=sha:errors.append('stale impact evidence: '+name)
    return errors,paths


def page_review(profile, review, pages):
    errors=[]
    # Each declared partition is exhaustive and non-overlapping for that PDF.
    for fmt,parts in profile.get('page_parts',{}).items():
        if fmt not in pages:errors.append('page partition has unknown format: '+fmt);continue
        covered=set()
        for part in parts:
            start,end=part.get('start'),part.get('end')
            if (type(start)!=int or type(end)!=int or start<1 or end<start or end>pages[fmt]):
                errors.append('invalid page range: '+fmt);continue
            span=set(range(start,end+1))
            if covered & span:errors.append('overlapping page partitions: '+fmt)
            covered |= span
            count=len(span)
            if part.get('min_pages',0)>count or (part.get('max_pages',0) and part['max_pages']<count):errors.append('section page limit: '+str(part.get('role')))
        if covered!=set(range(1,pages[fmt]+1)):errors.append('page partitions incomplete: '+fmt)
    if review.get('schema')=='mm-visual/v2' or profile.get('require_page_review'):
        for fmt,n in pages.items():
            rows=review.get('page_reviews',{}).get(fmt,[])
            if sorted(r.get('page',0) for r in rows)!=list(range(1,n+1)):errors.append('per-page review incomplete: '+fmt)
            for row in rows:
                if row.get('status')!='passed' or not row.get('notes') or row.get('method') not in ('full_size','contact_sheet','zoomed'):
                    errors.append('page review unresolved or incomplete: '+fmt)
    return errors
