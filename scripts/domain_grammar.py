"""Versioned domain planning grammars and honest materialization capabilities.

Planning support is distinct from geometry support. No generic box is a fallback
for an unsupported functional object. These are conceptual design contracts.
"""
VERSION = 'domain-grammar-1'
ALIASES = {'edificio':'building','proceso':'process','mecanismo':'mechanism',
           'vehiculo':'vehicle','vehículo':'vehicle','entorno':'environment'}
DOMAINS = {
    'building': {'entity':'space','relation':'circulation','requires':['opening','clearance'],
        'default_count':5,'has_circulation':True,'extent':[1.8,1.8,2.8],
        'invariants':['occupied spaces have access','vertical travel has landings and apertures']},
    'process': {'entity':'process_unit','relation':'process_flow','requires':['typed_interface','continuous_route','maintenance_access'],
        'default_count':3,'has_circulation':False,'extent':[2.4,1.5,2.1],
        'invariants':['flow endpoints are typed','maintenance access remains independent from fluid paths']},
    'mechanism': {'entity':'mechanical_component','relation':'transmission','requires':['typed_interface','coaxial_or_routed_transmission','support'],
        'default_count':2,'has_circulation':False,'extent':[.8,.6,.5],
        'invariants':['transmission and load paths are distinct','one or two parts are valid inventories']},
    'vehicle': {'entity':'vehicle_subsystem','relation':'service_connection','requires':['typed_interface','mount','clearance'],
        'default_count':3,'has_circulation':False,'extent':[1.2,.9,1.1],
        'invariants':['subsystems attach to structure','curved envelopes need a tested shape adapter']},
    'environment': {'entity':'site_region','relation':'site_access','requires':['walkable_surface','clearance'],
        'default_count':3,'has_circulation':False,'extent':[5.,4.,.3],
        'invariants':['parcels connect through site access','terrain contacts are geometric evidence']},
}
BUNKER_FAMILIES = ('hub','spine','branched')

def domain_name(name):
    name=ALIASES.get(name,name)
    if name not in DOMAINS:raise ValueError('unsupported design domain: '+str(name))
    return name

def infer_domain(subject):
    """Conservative migration default; explicit domain always takes precedence."""
    text=subject.lower()
    for name,words in [('mechanism',('winch','machine','mechanism','cabrestante','mecanismo')),
                       ('vehicle',('airship','vehicle','gondola','vehículo','aeronave')),
                       ('process',('treatment','process plant','refinery','tratamiento')),
                       ('environment',('urban','district','landscape','city','ciudad'))]:
        if any(word in text for word in words):return name
    return 'building'

def capability(domain,family,features=(),materializer=None,levels=1,count=5):
    domain=domain_name(domain)
    reasons=[]
    if 'curved_enclosure' in features:reasons.append('curved enclosure has no registered materialization adapter')
    if materializer=='bunker':
        if domain!='building':reasons.append('bunker adapter requires building domain')
        if family not in BUNKER_FAMILIES:reasons.append('bunker family adapter unavailable: '+family)
        if type(count)!=int or count!=5:reasons.append('bunker adapter currently realizes five allocated spaces per level')
        if type(levels)!=int or not 2<=levels<=12:reasons.append('bunker stair core supports 2..12 levels')
    elif materializer=='urban_exterior':
        if domain!='environment':reasons.append('urban exterior composer requires environment domain')
        if family not in ('avenue','staggered','courtyard'):reasons.append('unsupported urban organization')
        if type(count)!=int or not 6<=count<=64:reasons.append('bounded composer supports 6..64 exterior towers')
        if set(features)-{'setbacks','roof_equipment','street_network'}:reasons.append('feature outside bounded exterior adapter')
    else:reasons.append('no complete domain materializer requested or registered; this registry is not a denylist for composition from validated parts')
    return {'version':VERSION,'materializer':materializer,'status':'unsupported' if reasons else 'supported',
            'reasons':reasons,'validation':'not_run','scope':'capability declaration; actual geometry still requires validation'}
