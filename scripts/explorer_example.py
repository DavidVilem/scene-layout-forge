"""Independent technical example; not a reconstruction of any user's raster image."""
from connected_plant import fixture


def example():
    scene=fixture()
    sets=[
        ('base','Base y estructura',['floor','wall','hall-column-0','hall-column-1','hall-beam','operator'],[0,0,0]),
        ('vessel-a','Depósito A',['tank-0'],[-3,0,.8]),
        ('vessel-b','Depósito B',['tank-1'],[3,0,.8]),
        ('pump','Bomba y motor',['pump'],[0,3,.5]),
        ('access','Acceso y plataforma',['deck','deck-leg-0','deck-leg-1','deck-leg-2','stairs','back-rail','front-rail','inspector'],[0,3.8,2]),
        ('services','Colector y tuberías',['header','return','connection[0]','connection[1]','connection[2]','connection[3]'],[0,2.2,2.5])]
    config={'title':'Dos depósitos · conjunto de bombeo','dimensions_verified':False,
        'limitations':['Modelo conceptual del ejemplo geométrico; no reconstrucción de una imagen existente.',
        'Las dimensiones son de diseño, no medidas de una instalación real.',
        'Las verificaciones heredadas cubren solo sus adaptadores; la separación no simula cargas ni desmontaje real.',
        'Las proyecciones SVG son esquemáticas. La sección no añade interiores ocultos.'],
        'assemblies':[dict(id=id,label=label,members=members,offset=offset,fixed=id=='base',provenance='modeled',
          evidence='Geometría del ejemplo conectado del núcleo.',
          separation_note='Conjunto fijo.' if id=='base' else 'Traslación didáctica; sus uniones quedan separadas, no estiradas.') for id,label,members,offset in sets]}
    for g in config['assemblies']:
        g['phase']=[0,.35] if g['id'].startswith('vessel') else ([.65,1] if g['id']=='access' else [.35,.65])
    return scene,config
