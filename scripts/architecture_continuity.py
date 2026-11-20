"""Architectural enclosure intent; separates physical openings from display cuts."""
def validate(plan,brief):
    c=plan.get('architecture')
    if c is None:return
    if c.get('representation') not in ('complete','section'):raise ValueError('Architecture representation required')
    if c['representation']=='section':
        quote=c.get('user_cut_request','')
        if not quote or quote not in brief:raise ValueError('A display cut requires the actual user request; do not invent it')
        if not c.get('cut_boundary'):raise ValueError('Define the display cut independently of the complete building')
    for field in ('enclosure','roof_wall_junctions','openings','routes'):
        if not c.get(field):raise ValueError('Architecture needs '+field)
    for opening in c['openings']:
        if opening.get('kind') not in ('door','window','permanent_open_bay','display_cut') or not opening.get('boundary') or not opening.get('reason'):
            raise ValueError('Describe real opening boundaries and purpose')
        if opening['kind']=='display_cut' and c['representation']!='section':raise ValueError('No unexplained missing walls')
    design=c.get('design')
    if design is None:return  # Read older evidence without retroactive certification.
    elements=design.get('elements',[])
    ids=[e.get('id') for e in elements]
    if not ids or any(not isinstance(i,str) or not i.strip() for i in ids) or len(set(ids))!=len(ids):
        raise ValueError('Unique architectural element IDs required')
    if design.get('primary') not in ids or not design.get('selected_reason') or not design.get('rejected_alternative'):
        raise ValueError('Explain the primary system and the rejected design alternative')
    for e in elements:
        if e.get('role') not in ('structure','enclosure','opening','canopy','ornament','ground'):
            raise ValueError('Declare each architectural role')
        if not e.get('extent') or not e.get('junction'):
            raise ValueError('Declare extent and physical junction, not just visual proximity')
        hosts=e.get('hosts',[])
        if not isinstance(hosts,list) or set(hosts)-set(ids) or e['id'] in hosts:
            raise ValueError('Architectural hosts must name other known elements')
        if e['role']!='ground' and not hosts:raise ValueError('Architectural element lacks a host or support')
        if e.get('spanning') and (len(set(e.get('supports',[])))<2 or set(e['supports'])-set(ids) or e['id'] in e['supports']):
            raise ValueError('A spanning element needs two named supports')
    # Reachability prevents mutually supporting orphan islands; not a load solver.
    byid={e['id']:e for e in elements}
    def grounded(key,seen):
        if key in seen:return False
        e=byid[key]
        return e['role']=='ground' or any(grounded(h,seen|{key}) for h in e.get('hosts',[]))
    if any(not grounded(i,set()) for i in ids):raise ValueError('Disconnected architectural support/host graph')

def keys(plan):
    c=plan.get('architecture')
    return ({'architecture:enclosure','architecture:junctions','architecture:openings','architecture:routes'} |
            ({'architecture:design'} if c.get('design') else set())) if c else set()

def rules(plan):
    if not plan.get('architecture'):return ''
    return ('\nPreserve the physical building enclosure and connected roof/wall returns. Show interiors through actual glazing and doors; do not remove walls to expose furniture. A permanent open platform bay needs a complete framed boundary. Never turn a facade arch into a detached thin screen or unexplained cut edge. '
            'Resolve the primary structural span, enclosure and entrance together. An arch, canopy or portal must have its declared role, extent, supports and host junction; glass filling a gap does not by itself repair architectural composition. Do not preserve a rejected design feature merely because it appeared in an earlier image.')
