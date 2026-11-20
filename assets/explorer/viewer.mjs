import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';

const D=JSON.parse(document.getElementById('scene-data').textContent), $=id=>document.getElementById(id);
const canvas=$('viewport'), stage=canvas.parentElement, low=D.bounds[0], high=D.bounds[1];
const center=new THREE.Vector3(...low).add(new THREE.Vector3(...high)).multiplyScalar(.5);
const radius=Math.max(...high.map((v,i)=>v-low[i]))*.73;
const scene=new THREE.Scene();scene.background=new THREE.Color('#edf2ef');
const camera=new THREE.OrthographicCamera(-radius,radius,radius,-radius,.01,radius*40);camera.up.set(0,0,1);
let renderer;
try{renderer=new THREE.WebGLRenderer({canvas,antialias:true,preserveDrawingBuffer:true});}
catch(error){$('fallback').style.display='block';window.__explorer={ready:false,error:String(error)};throw error;}
renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.localClippingEnabled=true;
renderer.outputColorSpace=THREE.SRGBColorSpace;
renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;
renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.15;
const ambient=new THREE.HemisphereLight(0xffffff,0xc3c5c0,2.0);ambient.position.set(0,0,1);scene.add(ambient);
const light=new THREE.DirectionalLight(0xfff8ed,3.0);
light.position.copy(center).add(new THREE.Vector3(-radius,-radius,radius*2));light.target.position.copy(center);scene.add(light,light.target);
light.castShadow=true;light.shadow.mapSize.set(2048,2048);light.shadow.camera.left=-radius*2;light.shadow.camera.right=radius*2;light.shadow.camera.top=radius*2;light.shadow.camera.bottom=-radius*2;light.shadow.camera.near=.1;light.shadow.camera.far=radius*8;light.shadow.normalBias=.02;light.shadow.bias=-.0001;
const fill=new THREE.DirectionalLight(0xe2edff,1.2);fill.position.copy(center).add(new THREE.Vector3(radius,-radius,radius));scene.add(fill);

const controls=new OrbitControls(camera,canvas);controls.target.copy(center);controls.enableDamping=true;
controls.minZoom=.35;controls.maxZoom=12;controls.maxPolarAngle=Math.PI*.95;
const clip=new THREE.Plane(new THREE.Vector3(0,0,-1),high[2]);
const groups=new Map(), meshes=[], lines=[], partMap=new Map();
let selected=null, view='iso', showEdges=true, reviewCamera=null;
const reduced=matchMedia('(prefers-reduced-motion: reduce)');
const colors={vessel:0xc8d8d8,pump:0x4c838b,manifold:0x86a7a8,connection:0x819f9f,slab:0xd5d4c6,
 wall:0xe5e2d7,column:0x71878b,beam:0x71878b,stair:0x8d9a99,landing:0xa1adac,railing:0x536b70,worker:0xc4a46d};
for(const g of D.assemblies){
 const node=new THREE.Group();node.userData={id:g.id};scene.add(node);groups.set(g.id,{...g,node});
 const row=document.createElement('div');row.className='assembly';
 const checkbox=document.createElement('input');checkbox.type='checkbox';checkbox.checked=true;checkbox.setAttribute('aria-label',`Mostrar ${g.label}`);checkbox.dataset.assembly=g.id;
 checkbox.addEventListener('change',()=>{node.visible=checkbox.checked;updateGuides();});
 const button=document.createElement('button');button.dataset.select=g.id;button.textContent=g.label;
 const small=document.createElement('small');small.textContent={modeled:'Modelado',observed:'Desde evidencia visible',inferred:'Inferido'}[g.provenance];button.append(small);
 button.addEventListener('click',()=>select(g.id));row.append(checkbox,button);$('assemblyList').append(row);
}
for(const p of D.parts){
 const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.Float32BufferAttribute(p.positions,3));geo.computeVertexNormals();
 const opacity=p.opacity??1;
 const mat=new THREE.MeshStandardMaterial({color:p.color??colors[p.kind]??0xa8b5b4,opacity,transparent:opacity<1,depthWrite:opacity>=1,roughness:.86,metalness:.05,side:THREE.DoubleSide,polygonOffset:true,polygonOffsetFactor:1,polygonOffsetUnits:1});
 const mesh=new THREE.Mesh(geo,mat);mesh.castShadow=opacity>=.95;mesh.receiveShadow=true;mesh.userData={part:p.id,assembly:p.assembly};groups.get(p.assembly).node.add(mesh);meshes.push(mesh);partMap.set(p.id,mesh);
 const line=new THREE.LineSegments(new THREE.EdgesGeometry(geo,24),new THREE.LineBasicMaterial({color:0x304c52,transparent:true,opacity:.25}));line.userData={assembly:p.assembly};groups.get(p.assembly).node.add(line);lines.push(line);
}
const grid=new THREE.GridHelper(radius*3,30,0xa4b9b6,0xd4ded9);grid.rotation.x=Math.PI/2;grid.position.set(center.x,center.y,low[2]-.03);grid.visible=false;scene.add(grid);
const ground=new THREE.Mesh(new THREE.PlaneGeometry(radius*8,radius*8),new THREE.ShadowMaterial({opacity:.16}));ground.position.set(center.x,center.y,low[2]-.035);ground.receiveShadow=true;scene.add(ground);
function updateGuides(){ $('status').textContent='Maqueta fija · aislamiento por visibilidad, sin mover piezas.'; }
function select(id){
 selected=id;const g=groups.get(id);if(!g)return;
 for(const m of meshes)m.material.emissive.setHex(m.userData.assembly===id?0x15393c:0x000000);
 document.querySelectorAll('[data-select]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.select===id)));
 $('selection').textContent=g.label;$('evidence').textContent=`${g.evidence}`;
}
function hideReference(){ $('reference').style.display='none';canvas.style.visibility='visible';}
function setView(name){
 reviewCamera=null;controls.enabled=true;hideReference();view=name;const r=radius*2.2;
 camera.up.set(0,0,1);
 if(name==='top'){camera.position.copy(center).add(new THREE.Vector3(0,0,r));camera.up.set(0,1,0);}
 else if(name==='front')camera.position.copy(center).add(new THREE.Vector3(0,r,0));
 else if(name==='side')camera.position.copy(center).add(new THREE.Vector3(r,0,0));
 else camera.position.copy(center).add(new THREE.Vector3(...(D.presentation?.direction??[.82,1,.66])).multiplyScalar(r));
 camera.zoom=name==='iso'?(D.presentation?.zoom??1):1;controls.target.copy(center);camera.lookAt(center);camera.updateProjectionMatrix();controls.update();
 document.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===name)));
 $('badge').textContent=({iso:'3D · gira para explorar',top:'Planta conceptual',front:'Alzado conceptual',side:'Vista lateral conceptual'})[name];
}
function showAll(){for(const g of groups.values())g.node.visible=true;document.querySelectorAll('[data-assembly]').forEach(c=>c.checked=true);updateGuides();}
function reset(){showAll();$('cutEnabled').checked=false;updateCut();setView('iso');}
function updateCut(){const axis=Number($('cutAxis').value),ratio=Number($('cut').value)/100;
 const h=low[axis]+(high[axis]-low[axis])*ratio;clip.normal.set(0,0,0).setComponent(axis,-1);clip.constant=h;
 renderer.clippingPlanes=$('cutEnabled').checked?[clip]:[];light.castShadow=!$('cutEnabled').checked;$('cutValue').textContent=`${Math.round(ratio*100)} %`;
}
function resize(){const w=stage.clientWidth,h=stage.clientHeight,r=radius*Math.max(1,h/w);renderer.setSize(w,h,false);camera.left=-r*w/h;camera.right=r*w/h;camera.top=r;camera.bottom=-r;camera.updateProjectionMatrix();}
new ResizeObserver(resize).observe(stage);
document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>setView(b.dataset.view)));
$('reset').onclick=reset;$('showAll').onclick=showAll;
$('isolate').onclick=()=>{if(!selected)return;for(const g of groups.values())g.node.visible=g.id===selected;document.querySelectorAll('[data-assembly]').forEach(c=>c.checked=c.dataset.assembly===selected);updateGuides();};
$('wire').onclick=()=>{showEdges=!showEdges;for(const l of lines)l.visible=showEdges;$('wire').setAttribute('aria-pressed',String(showEdges));};
for(const id of ['cut','cutAxis','cutEnabled'])$(id).addEventListener('input',updateCut);
const ray=new THREE.Raycaster();let down=null;
canvas.addEventListener('pointerdown',e=>down=[e.clientX,e.clientY]);
canvas.addEventListener('pointerup',e=>{
 if(!down||Math.hypot(e.clientX-down[0],e.clientY-down[1])>5)return;
 const rect=canvas.getBoundingClientRect();ray.setFromCamera(new THREE.Vector2((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1),camera);
 const hits=ray.intersectObjects(meshes.filter(m=>groups.get(m.userData.assembly).node.visible));
 const hit=hits.find(h=>!$('cutEnabled').checked||clip.distanceToPoint(h.point)>=0);
 if(hit)select(hit.object.userData.assembly);
});
canvas.addEventListener('keydown',e=>{
 if(e.key==='Escape'){reset();e.preventDefault();return;}
 if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key)){
  const v=camera.position.clone().sub(controls.target),s=new THREE.Spherical().setFromVector3(new THREE.Vector3(v.x,v.z,v.y));
  if(e.key==='ArrowLeft')s.theta-=.12;if(e.key==='ArrowRight')s.theta+=.12;
  if(e.key==='ArrowUp')s.phi=Math.max(.05,s.phi-.12);if(e.key==='ArrowDown')s.phi=Math.min(Math.PI-.05,s.phi+.12);
  const out=new THREE.Vector3().setFromSpherical(s);camera.position.copy(controls.target).add(new THREE.Vector3(out.x,out.z,out.y));camera.up.set(0,0,1);controls.update();e.preventDefault();
 }
});
if(D.single_source){const b=document.createElement('button');b.dataset.image=D.single_source;b.textContent='Imagen original';$('images').append(b);}
document.querySelectorAll('[data-image]').forEach(b=>b.onclick=()=>{
 $('reference').src=b.dataset.image;$('reference').style.display='block';canvas.style.visibility='hidden';$('badge').textContent='Imagen original · la vista 3D no reproduce todos sus trazos';
});
$('images').hidden=!D.has_images&&!D.single_source;
if(D.single_source)document.querySelectorAll('[data-image]').forEach(b=>{if(b.dataset.image!==D.single_source)b.hidden=true;});
for(const note of D.limitations){const p=document.createElement('p');p.textContent=note;$('limits').append(p);}
if(D.example_only){const p=document.createElement('p');p.textContent='Prototipo técnico independiente. No es una conversión de una imagen artística.';$('limits').prepend(p);}
function exportSVG(){
 const axis=view==='front'?[0,2,1]:view==='side'?[1,2,0]:[0,1,2];
 const w=1000,h=800,pad=45,s=Math.min((w-2*pad)/(high[axis[0]]-low[axis[0]]),(h-2*pad)/(high[axis[1]]-low[axis[1]]));
 const polys=[];for(const p of D.parts){if(!groups.get(p.assembly).node.visible)continue;const v=p.positions;
  for(let i=0;i<v.length;i+=9){let points=[],depth=0;for(let j=0;j<3;j++){const a=v.slice(i+j*3,i+j*3+3);points.push(`${(pad+(a[axis[0]]-low[axis[0]])*s).toFixed(2)},${(h-pad-(a[axis[1]]-low[axis[1]])*s).toFixed(2)}`);depth+=a[axis[2]];}polys.push({depth:depth/3,points:points.join(' ')});}}
 polys.sort((a,b)=>a.depth-b.depth);
 const svg=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}"><rect width="100%" height="100%" fill="white"/><text x="30" y="25" font-family="sans-serif" font-size="15">Proyección conceptual ensamblada · sin cotas verificadas · corte no aplicado</text>${polys.map(p=>`<polygon points="${p.points}" fill="#e4ebea" stroke="#536b70" stroke-width=".35"/>`).join('')}</svg>`;
 const url=URL.createObjectURL(new Blob([svg],{type:'image/svg+xml'}));const link=document.createElement('a');link.href=url;link.download=`plano-${view==='iso'?'top':view}.svg`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);return svg;
}
$('export').onclick=exportSVG;
setView('iso');updateCut();resize();updateGuides();
function tick(){controls.update();renderer.render(scene,reviewCamera??camera);requestAnimationFrame(tick);}
requestAnimationFrame(tick);
function setReviewCamera(spec){
 if(spec.projection!=='perspective'||!spec.eye?.every(Number.isFinite)||spec.eye.length!==3||!spec.target?.every(Number.isFinite)||spec.target.length!==3)throw Error('Explicit finite comparison camera required');
 reset();controls.enabled=false;hideReference();
 reviewCamera=new THREE.PerspectiveCamera(spec.fov??50,stage.clientWidth/stage.clientHeight,spec.near??.1,radius*40);
 reviewCamera.up.set(0,0,1);reviewCamera.position.set(...spec.eye);reviewCamera.lookAt(new THREE.Vector3(...spec.target));reviewCamera.updateProjectionMatrix();
 return {projection:'perspective',eye:reviewCamera.position.toArray(),target:spec.target,fov:reviewCamera.fov};
}
window.__explorer={ready:true,select,setView,reset,exportSVG,setReviewCamera,
 snapshot:()=>({fixed:true,view,selected,clip:$('cutEnabled').checked,axes:clip.normal.toArray(),
  positions:Object.fromEntries([...groups].map(([id,g])=>[id,g.node.position.toArray()])),
  visible:[...groups].filter(([,g])=>g.node.visible).map(([id])=>id),
  camera:camera.position.toArray(),connections:D.connections.length,assemblies:groups.size,owners:meshes.length})};