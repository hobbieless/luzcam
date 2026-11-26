const DATA = {
  contract: '../Portable/contract-v1.json',
  ranges: '../CrossPlatform/luzcam/exposure-ranges.json',
  translations: '../CrossPlatform/luzcam/translations.json',
  scene: '../Scene/scene.json',
};
const CAMERA_IDS = ['reflex', 'mirrorless', 'compact'];
const LIGHTS = ['day', 'dusk', 'night'];
const $ = (id) => document.getElementById(id);
const state = { camera: 0, light: 0, a: 3, s: 8, i: 0, thirds: false, stepByStep: true, phase: 0, visualPhase: 0, transition: null, shot: null, pendingShot: null, history: [], rollVersion: 0, image: null, geometry: null, reviewImage: null, playing: false, capturing: false, loadingLight: false, offlineReady: false, timer: 0, lang: 'es', videoPaused: false, lightRequest: 0 };
let contract, ranges, dictionary, cameraImage, focusMotionImage, sceneMeta, resizeObserver, reducedMotion, offlineRegistration;
let renderedRollVersion=-1,renderedRollLanguage='';
const motionAtlasCache = new Map();
const linearLut = Float32Array.from({length:256},(_,i)=>{const v=i/255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4;});
let sensitivityTextureCanvas;

const copy = {
  es: {
    offline:'Funciona en este dispositivo', offlineReady:'Caché sin conexión activa', home:'LuzCam, inicio', simulator:'Simulador LuzCam', eyebrow:'FOTOGRAFÍA · MODO MANUAL', title:'El instante,\npor dentro.', intro:'Observa la luz. Ajusta la cámara. Predice qué ocurrirá al disparar.', slow:'El disparo se ralentiza para explicar cada fase.', inside:'LA CÁMARA, POR DENTRO', settings:'AJUSTES MANUALES', thirds:'Pasos de ⅓ EV', stepByStep:'Paso a paso', aperture:'DIAFRAGMA', shutter:'VELOCIDAD', sensor:'SENSOR', iso:'SENSIBILIDAD', noise:'Ruido', curtain:'OBTURADOR', mechanisms:'MECANISMOS DE LA CÁMARA', irisGraphic:'Gráfico del diafragma de siete palas', shutterGraphic:'Gráfico de las cortinillas del obturador', sensorGraphic:'Gráfico de ruido del sensor', meter:'FOTÓMETRO', sceneLabel:'ESCENA / VISOR', sceneTitle:'El taller del tiempo', pauseMotion:'Pausar movimiento', resumeMotion:'Reanudar movimiento', day:'Día', dusk:'Atardecer', night:'Noche', sceneHint:'Observa el péndulo, predice el resultado y dispara.', roll:'CARRETE', clear:'Vaciar carrete', empty:'Las fotografías aparecerán aquí después del disparo.', footer:'LuzCam · Modelos didácticos · Uso educativo', reference:'Exposición de referencia', under:'Por debajo de la referencia', over:'Por encima de la referencia', first:'Preparar la cámara', desc0:'La luz llega al espejo y sube al visor óptico.', desc0other:'La luz llega al sensor y produce la imagen de la pantalla. Todavía no es una captura.', desc1:'Las palas forman la abertura seleccionada.', desc2:'El espejo se levanta y deja libre el camino al sensor.', desc2other:'Se prepara el obturador. No hay espejo.', desc2compact:'Se prepara el registro electrónico. Esta cámara no utiliza cortinillas.', desc3:'La luz empieza a registrarse en el sensor.', desc4:'Cada zona registra luz durante el tiempo seleccionado.', desc5:'Termina la exposición. ISO modifica la respuesta; no añade luz.', desc6:'La cámara vuelve al reposo y recupera la vista de la escena.', desc7:'Estos ajustes quedaron guardados al disparar.', phase:['Preparar la cámara','Ajustar el diafragma','Preparar la exposición','Comienza la exposición','La luz se registra','Termina la exposición','Volver al reposo','Examinar la fotografía'], shoot:'Disparar', continue:'Continuar', pause:'Pausar', previous:'Paso anterior', next:'Siguiente paso', shot:'Fotografía capturada', remove:'Eliminar fotografía', clearConfirm:'¿Vaciar las {count} fotografías del carrete?', full:'Carrete completo: elimina una fotografía para poder disparar.', language:'Idioma', cameraPicker:'Seleccionar cámara', cameraCanvas:'Corte animado de la cámara y recorrido de la luz', lightPicker:'Iluminación de la escena', sceneVideo:'Escena del taller en movimiento', returnScene:'Volver a escena', close:'Cerrar', loading:'Preparando la fotografía…', captureError:'No se pudo preparar la fotografía. Comprueba la conexión y vuelve a intentarlo.'
  },
  en: {
    offline:'Runs on this device', offlineReady:'Offline cache active', home:'LuzCam home', simulator:'LuzCam simulator', eyebrow:'PHOTOGRAPHY · MANUAL MODE', title:'Inside the\ninstant.', intro:'Watch the light. Set the camera. Predict what happens when you shoot.', slow:'The shutter sequence is slowed down to explain each phase.', inside:'INSIDE THE CAMERA', settings:'MANUAL SETTINGS', thirds:'⅓ EV steps', stepByStep:'Step by step', aperture:'APERTURE', shutter:'SHUTTER SPEED', sensor:'SENSOR', iso:'SENSITIVITY', noise:'Noise', curtain:'SHUTTER', mechanisms:'CAMERA MECHANISMS', irisGraphic:'Seven-blade aperture diagram', shutterGraphic:'Shutter curtain diagram', sensorGraphic:'Sensor noise diagram', meter:'LIGHT METER', sceneLabel:'SCENE / VIEWFINDER', sceneTitle:'The time workshop', pauseMotion:'Pause motion', resumeMotion:'Resume motion', day:'Day', dusk:'Dusk', night:'Night', sceneHint:'Watch the pendulum, predict the result and shoot.', roll:'FILM ROLL', clear:'Clear roll', empty:'Photographs will appear here after shooting.', footer:'LuzCam · Educational models · For learning', reference:'Reference exposure', under:'Below reference', over:'Above reference', first:'Prepare the camera', desc0:'Light reaches the mirror and travels up to the optical viewfinder.', desc0other:'Light reaches the sensor and forms the screen image. This is not a capture yet.', desc1:'The blades form the selected aperture.', desc2:'The mirror lifts and clears the path to the sensor.', desc2other:'The shutter is prepared. There is no mirror.', desc2compact:'Electronic recording is prepared. This camera has no curtains.', desc3:'Light begins recording on the sensor.', desc4:'Each area records light for the selected time.', desc5:'The exposure ends. ISO changes the output response; it does not add light.', desc6:'The camera returns to rest and restores the scene view.', desc7:'These settings were saved when you shot.', phase:['Prepare the camera','Set the aperture','Prepare the exposure','Exposure begins','Light is recorded','Exposure ends','Return to rest','Review photograph'], shoot:'Shoot', continue:'Continue', pause:'Pause', previous:'Previous step', next:'Next step', shot:'Captured photograph', remove:'Remove photograph', clearConfirm:'Clear all {count} photographs from the roll?', full:'Film roll is full. Remove a photo before shooting.', language:'Language', cameraPicker:'Choose camera', cameraCanvas:'Animated camera cutaway and light path', lightPicker:'Scene lighting', sceneVideo:'Moving workshop scene', returnScene:'Return to scene', close:'Close', loading:'Preparing photograph…', captureError:'The photograph could not be prepared. Check the connection and try again.'
  }
};
copy.es.reviewLabel='REVISIÓN / PLAY';
copy.en.reviewLabel='REVIEW / PLAY';

function T(key) { return copy[state.lang][key] ?? (state.lang === 'en' ? (dictionary?.[key] ?? key) : key); }
function updateMotionControl() {
  const button=$('motionToggle'),label=state.videoPaused?T('resumeMotion'):T('pauseMotion');
  button.setAttribute('aria-label',label);button.title=label;
  button.classList.toggle('is-paused',state.videoPaused);
  button.querySelector('.motion-label').textContent=label;
}
function applyLanguage() {
  document.documentElement.lang = state.lang;
  document.querySelectorAll('[data-t]').forEach((el) => { const key = el.dataset.t; el.textContent = T(key); });
  document.title = `LuzCam · ${T('title').replace('\n',' ')}`;
  $('language').value = state.lang;
  $('language').setAttribute('aria-label',T('language'));
  document.querySelector('.brand').setAttribute('aria-label',T('home'));
  document.querySelector('.workbench').setAttribute('aria-label',T('simulator'));
  $('meterLine').setAttribute('aria-label',T('meter'));
  document.querySelector('.camera-picker').setAttribute('aria-label',T('cameraPicker'));
  document.querySelector('.light-tabs').setAttribute('aria-label',T('lightPicker'));
  $('cameraCanvas').setAttribute('aria-label',T('cameraCanvas'));
  document.querySelector('.mechanism-strip').setAttribute('aria-label',T('mechanisms'));
  $('irisMechanism').setAttribute('aria-label',T('irisGraphic'));
  $('shutterMechanism').setAttribute('aria-label',T('shutterGraphic'));
  $('sensitivityMechanism').setAttribute('aria-label',T('sensorGraphic'));
  $('sceneVideo').setAttribute('aria-label',T('sceneVideo'));
  document.querySelectorAll('.camera-choice').forEach((b,i) => { const name=state.lang==='en'?(dictionary?.[contract.cameras[i].name]??contract.cameras[i].name):contract.cameras[i].name;b.setAttribute('aria-label',name);b.title=name;b.querySelector('.sr-only').textContent=name; });
  document.querySelectorAll('.light-tab').forEach((b,i)=>{const label=T(LIGHTS[i]);b.setAttribute('aria-label',label);b.title=label;b.querySelector('.sr-only').textContent=label;});
  updateMotionControl();
  $('previous').setAttribute('aria-label',T('previous'));$('previous').title=T('previous');
  $('next').setAttribute('aria-label',T('next'));$('next').title=T('next');
  $('returnScene').title=T('returnScene');
  $('clearRoll').setAttribute('aria-label',T('clear'));$('clearRoll').title=T('clear');$('clearRoll').querySelector('.sr-only').textContent=T('clear');
  $('offlineStatus').textContent=state.offlineReady?T('offlineReady'):T('offline');
  refresh();
}
function activeApertures() {
  const camera = contract.cameras[state.camera];
  if (state.camera < 2) return state.thirds ? ranges.thirdApertures : ranges.fullApertures;
  return state.thirds ? camera.thirdApertures : camera.fullApertures;
}
function shutters() { return state.thirds ? ranges.thirdShutterLabels : ranges.fullShutterLabels; }
function shutterEV() { return state.thirds ? ranges.thirdShutterEV[state.s] : ranges.fullShutterEV[state.s]; }
function isoValues() { return state.thirds ? ranges.thirdISOs : ranges.fullISOs; }
function setting() {
  const camera = contract.cameras[state.camera];
  const apertureIndex = activeApertures()[state.a];
  const divisor = state.thirds ? 3 : 1;
  const fNumber = apertureIndex;
  const opticalF = 2 ** ((camera.apertureBaseEV + state.a / divisor) / 2);
  const gain = state.i / divisor;
  const light = contract.lights[state.light];
  const meterThird = Math.round((light.referenceEV - camera.apertureBaseEV + gain - state.a / divisor - shutterEV()) * 3);
  return { camera: state.camera, light: state.light, a: state.a, s: state.s, i: state.i, thirds: state.thirds,
    f: fNumber, opticalF, seconds: 2 ** -shutterEV(), gain, meterThird, offset: meterThird / 3,
    iso: isoValues()[state.i], shutter: shutters()[state.s] };
}
function limits() {
  const apertureValues=activeApertures();
  $('aperture').max = apertureValues.length - 1;
  $('shutter').max = shutters().length - 1;
  $('iso').max = isoValues().length - 1;
  state.a = Math.min(state.a, +$('aperture').max); state.s = Math.min(state.s, +$('shutter').max); state.i = Math.min(state.i, +$('iso').max);
  $('aperture').value = state.a; $('shutter').value = state.s; $('iso').value = state.i;
  $('apertureMin').textContent=`f/${apertureValues[0]}`;$('apertureMax').textContent=`f/${apertureValues.at(-1)}`;
}
function description() {
  const c = state.camera, p = state.phase;
  if (p === 0) return c === 0 ? T('desc0') : T('desc0other');
  if (p === 1) return T('desc1');
  if (p === 2) return c === 0 ? T('desc2') : c === 2 ? T('desc2compact') : T('desc2other');
  return T(`desc${p}`);
}
function refresh() {
  if (!contract) return;
  limits();
  const s = state.phase===7&&state.history.length?state.history[0].setting:setting();
  $('apertureValue').textContent = `f/${s.f}`;
  $('shutterValue').textContent = s.shutter;
  $('isoValue').textContent = `ISO ${s.iso}`;
  $('mechanismApertureValue').textContent = `f/${s.f}`;
  $('mechanismShutterValue').textContent = s.shutter;
  $('mechanismSensitivityValue').textContent = `ISO ${s.iso}`;
  $('shutterMechanismTitle').textContent = state.camera===2 ? T('sensor') : T('curtain');
  $('cameraTitle').textContent = state.lang==='en'?(dictionary?.[contract.cameras[state.camera].name]??contract.cameras[state.camera].name):contract.cameras[state.camera].name;
  $('phaseChip').textContent = T('phase')[state.phase];
  $('cameraCanvas').parentElement.dataset.phase=String(state.phase);
  $('phaseDescription').textContent = description();
  const playLabel=state.capturing?T('loading'):state.playing?T('pause'):(state.phase===0||state.phase===7?T('shoot'):T('continue'));
  $('play').setAttribute('aria-label',playLabel);$('play').title=playLabel;$('playGlyph').classList.toggle('is-playing',state.playing);$('play').disabled=state.capturing||state.loadingLight;
  $('play').setAttribute('aria-busy',String(state.capturing||state.loadingLight));
  // The scale spans -2 to +2 EV. meterThird is measured in thirds,
  // so ±6 thirds must reach the outer EV marks and ±3 the inner marks.
  $('meterNeedle').style.left = `${50 + Math.max(-6, Math.min(6, s.meterThird)) / 6 * 46.6667}%`;
  $('meterLeftEdge').textContent = s.meterThird < -6 ? '◀' : '−';
  $('meterRightEdge').textContent = s.meterThird > 6 ? '▶' : '+';
  $('meterText').textContent = s.meterThird === 0 ? T('reference') : s.meterThird < 0 ? T('under') : T('over');
  $('meterLine').setAttribute('aria-valuenow',String(Math.max(-2,Math.min(2,s.meterThird/3))));
  $('meterLine').setAttribute('aria-valuetext',$('meterText').textContent);
  $('stepByStep').checked=state.stepByStep;
  $('rollCount').textContent = `${state.history.length} / 100`;
  $('clearRoll').disabled = state.history.length === 0;
  document.querySelectorAll('.camera-choice').forEach((b,i) => {b.classList.toggle('active',i===state.camera);b.setAttribute('aria-pressed',String(i===state.camera));b.disabled=state.capturing;});
  document.querySelectorAll('.light-tab').forEach((b,i) => {b.classList.toggle('active',i===state.light);b.setAttribute('aria-pressed',String(i===state.light));b.disabled=state.capturing||state.loadingLight;});
  const locked = state.phase > 0 && state.phase < 7;
  for (const id of ['aperture','shutter','iso','thirds','stepByStep']) $(id).disabled = locked||state.capturing;
  $('previous').disabled=state.phase===0||state.phase===7||state.capturing;
  $('next').disabled=state.phase===7||state.capturing;
  $('sceneBadge').textContent = T(LIGHTS[state.light]).toLocaleUpperCase(state.lang);
  const reviewing=state.phase===7&&state.history.length>0;
  $('sceneMode').textContent=T(reviewing?'reviewLabel':'sceneLabel');
  $('returnScene').hidden=!reviewing;$('motionToggle').hidden=reviewing;
  $('sceneVideo').hidden=reviewing;$('reviewPhoto').hidden=!reviewing;
  if(reviewing&&$('reviewPhoto').dataset.source!==state.history[0].data){$('reviewPhoto').src=state.history[0].data;$('reviewPhoto').dataset.source=state.history[0].data;$('reviewPhoto').alt=T('shot');}
  updateMotionControl();
  drawCamera(); renderRoll();
}
function loadImage(src) { return new Promise((resolve,reject) => { const img = new Image(); img.onload=()=>resolve(img); img.onerror=reject; img.src=src; }); }
function cacheForOffline(urls){
  const worker=offlineRegistration?.active||navigator.serviceWorker?.controller;
  if(worker&&urls.length)worker.postMessage({type:'CACHE_URLS',urls});
}
function cacheSelectedResources(){
  const camera=CAMERA_IDS[state.camera],light=LIGHTS[state.light];
  cacheForOffline([
    `assets/cameras/${camera}-reviewed.jpg`,
    `assets/cameras/${camera}-reviewed-geometry.json`,
    `assets/scene/${light}.png`,
    `assets/scene/${light}.mp4`,
    `assets/scene/${light}-motion.png`,
    'assets/scene/scene.json',
    'assets/scene/focus-motion.png'
  ]);
}
async function registerOfflineSupport(){
  if(document.documentElement.dataset.offline!=='true'||!('serviceWorker' in navigator))return;
  try{
    const registration=await navigator.serviceWorker.register('./sw.js',{scope:'./'});
    await navigator.serviceWorker.ready;offlineRegistration=registration;
    state.offlineReady=true;$('offlineStatus').textContent=T('offlineReady');
    navigator.serviceWorker.addEventListener('message',(event)=>{
      if(event.data?.type==='CACHE_RESULT'&&event.data.cached>0){state.offlineReady=true;$('offlineStatus').textContent=T('offlineReady');}
    });
  }catch(error){console.warn('LuzCam offline cache could not start',error);}
}
async function loadCamera() {
  const id = CAMERA_IDS[state.camera];
  document.querySelector('.camera-stage').dataset.camera=id;
  const [img, geom] = await Promise.all([
    loadImage(`../CameraArt/${id}-reviewed.jpg`),
    fetch(`../CameraArt/${id}-reviewed-geometry.json`).then(r => { if(!r.ok) throw Error('geometry'); return r.json(); })
  ]);
  cameraImage=img; state.geometry=geom; drawCamera();
}
function path(ctx, points) { if (!points?.length) return; ctx.beginPath(); ctx.moveTo(points[0][0],points[0][1]); for (let i=1;i<points.length;i++) ctx.lineTo(points[i][0],points[i][1]); }
function drawBeam(ctx, points, width, strength) {
  if (!points || points.length < 2 || width < .5 || strength <= 0) return;
  path(ctx, points); ctx.lineCap='round'; ctx.lineJoin='round';
  ctx.save(); ctx.globalCompositeOperation='screen'; ctx.shadowColor=`rgba(245,248,231,${.85*strength})`; ctx.shadowBlur=width*1.2; ctx.strokeStyle=`rgba(250,252,239,${.2*strength})`; ctx.lineWidth=width; ctx.stroke();
  ctx.shadowBlur=width*.36; ctx.strokeStyle=`rgba(255,255,246,${.25*strength})`; ctx.lineWidth=Math.max(1,width*.36); ctx.stroke(); ctx.restore();
}
function currentMirror(geom, ratio) {
  const list=geom.mirrorDisplay; if (!list?.length) return null;
  const pos=Math.max(0,Math.min(list.length-1,ratio*(list.length-1))); const lo=Math.floor(pos),hi=Math.min(list.length-1,lo+1),t=pos-lo;
  const interp=(a,b)=>a.map((pt,i)=>pt.map((v,j)=>v+(b[i][j]-v)*t));
  const point=(key)=>list[lo][key]&&list[hi][key]?list[lo][key].map((v,j)=>v+(list[hi][key][j]-v)*t):(t<.5?list[lo][key]:list[hi][key]);
  return {front:interp(list[lo].front,list[hi].front),back:interp(list[lo].back,list[hi].back),hit:point('hit'),bounce:point('bounce')};
}
function polar(radius, angle) { return [radius*Math.cos(angle),radius*Math.sin(angle)]; }
function drawIris(ctx, geom, opening, width, height) {
  const scale=geom.irisVisualScale||1, basis=geom.irisBasis||[1,0,0,1], center=geom.irisDisplay||geom.iris;
  if(!center)return;
  const [x,y]=center,R=37,r=R*Math.max(.035,Math.min(.86,opening)),carrier=geom.irisCarrierVisible!==false;
  ctx.save();ctx.translate(x,y);ctx.transform(basis[0]*scale,basis[1]*scale,basis[2]*scale,basis[3]*scale,0,0);
  if(carrier){
    for(const [dx,dy,colors] of [[3.8,-1.15,['#354047','#202a30','#10191d']],[0,0,['#cccccc','#616b6d','#b8bfc0']]]){
      ctx.save();ctx.translate(dx*scale,dy*scale);const grad=ctx.createLinearGradient(-45,-45,45,45);grad.addColorStop(0,colors[0]);grad.addColorStop(.5,colors[1]);grad.addColorStop(1,colors[2]);
      ctx.beginPath();ctx.arc(0,0,44,0,Math.PI*2);ctx.arc(0,0,36.8,0,Math.PI*2,true);ctx.fillStyle=grad;ctx.fill('evenodd');ctx.strokeStyle='#293338';ctx.lineWidth=.8;ctx.stroke();ctx.restore();
    }
  }
  const hole=new Path2D();for(let i=0;i<7;i++){const p=polar(r,i*2*Math.PI/7);if(i===0)hole.moveTo(...p);else hole.lineTo(...p);}hole.closePath();
  ctx.save();ctx.beginPath();ctx.rect(-60,-60,120,120);ctx.moveTo(...polar(r,0));for(let i=1;i<7;i++)ctx.lineTo(...polar(r,i*2*Math.PI/7));ctx.closePath();ctx.clip('evenodd');
  for(let i=0;i<7;i++){
    const a=i*2*Math.PI/7,step=2*Math.PI/7,start=polar(r,a),next=polar(r,a+step),q1=polar(.8*R,a+1.1),q2=polar(R,a+1.7),grad=ctx.createLinearGradient(q2[0],q2[1],0,0);
    grad.addColorStop(0,'#999');grad.addColorStop(1,'#252525');ctx.beginPath();ctx.moveTo(...start);ctx.lineTo(...next);ctx.quadraticCurveTo(...q1,...q2);
    for(let k=1;k<=24;k++){const p=polar(R,a+1.7-1.25*k/24);ctx.lineTo(...p);}ctx.quadraticCurveTo(...polar(.8*R,a+.1),...start);ctx.closePath();ctx.fillStyle=grad;ctx.fill();ctx.strokeStyle='#151515';ctx.lineWidth=.555;ctx.stroke();
  }
  ctx.restore();
  if(carrier){ctx.fillStyle='#cbd1d2';ctx.strokeStyle='#475357';ctx.lineWidth=.45;for(let i=0;i<7;i++){const p=polar(40,i*2*Math.PI/7+.48);ctx.beginPath();ctx.arc(p[0],p[1],1.1,0,Math.PI*2);ctx.fill();ctx.stroke();}}
  ctx.restore();
}
function curtainLeaves(progress,second=false){
  const height=.37,stride=(1-height)/2,result=[];
  for(let i=2;i>=0;i--){const closed=i*stride,parked=second?-.39-(2-i)*.025:1.02+i*.025;const top=second?parked+(closed-parked)*progress:closed+(parked-closed)*progress;result.push([top,top+height]);}
  return result;
}
function poseAt(phase, seconds, camera){
  const gap=Math.min(1,Math.max(0,seconds/(1/250)));
  if(camera===1&& (phase<2||phase>=6))return {front:1,rear:0};
  if(phase<=2||phase>=6)return {front:0,rear:0};
  if(phase<3){const t=phase-2,front=.35*t;return {front,rear:Math.max(0,front-gap)};}
  if(phase<4){const t=phase-3,end=gap>=1?1:.85;return {front:.35+(end-.35)*t,rear:Math.max(0,.35-gap)+(Math.max(0,end-gap)-Math.max(0,.35-gap))*t};}
  if(phase<5){const t=phase-4,start=gap>=1?1:.85;return {front:start+(1-start)*t,rear:Math.max(0,(start-gap))+(1-Math.max(0,start-gap))*t};}
  if(phase<6){const t=phase-5;return {front:1-t,rear:1-t};}
  return {front:0,rear:0};
}
function drawCurtains(ctx, geom, progress, width, height, compact=false){
  if(compact)return;
  const gate=geom.shutterGate;if(!gate||gate.length!==4)return;
  const at=(u,v)=>[(1-v)*((1-u)*gate[0][0]+u*gate[1][0])+v*((1-u)*gate[3][0]+u*gate[2][0]),(1-v)*((1-u)*gate[0][1]+u*gate[1][1])+v*((1-u)*gate[3][1]+u*gate[2][1])];
  ctx.save();path(ctx,gate);ctx.closePath();ctx.clip();
  for(const [amount,second] of [[progress.front,false],[progress.rear,true]])for(const [top,bottom] of curtainLeaves(amount,second)){
    const poly=[at(0,top),at(1,top),at(1,bottom),at(0,bottom)];path(ctx,poly);ctx.closePath();const grad=ctx.createLinearGradient(poly[0][0],poly[0][1],poly[2][0],poly[2][1]);
    (second?[[0,'#717777'],[.5,'#353e40'],[1,'#4e595a']]:[[0,'#485153'],[.5,'#242c2e'],[1,'#475052']]).forEach(([at,color])=>grad.addColorStop(at,color));ctx.fillStyle=grad;ctx.fill();ctx.beginPath();ctx.moveTo(...at(0,top));ctx.lineTo(...at(1,top));ctx.strokeStyle='#899291';ctx.lineWidth=.7;ctx.stroke();
  }
  if(compact&&progress.sensorActive){path(ctx,gate);ctx.closePath();ctx.fillStyle=`rgba(111,222,225,${.3*progress.sensorActive})`;ctx.fill();}
  ctx.restore();
}
function apertureOpening(s){return Math.max(.035,Math.min(.86,.86*Math.pow(2,-(s.a/(s.thirds?3:1))/2)));}
function paintScreen(ctx, geom, settingNow, review, width, height){
  let quad=state.camera===0?[[988,347.5],[1119,305.5],[1117,452.5],[986.5,501]]:geom.lcd;
  if(!quad?.length)return;
  ctx.save();path(ctx,quad);ctx.closePath();ctx.clip();const [p0,p1,,p3]=quad,ax=(p1[0]-p0[0])/640,ay=(p1[1]-p0[1])/640,bx=(p3[0]-p0[0])/480,by=(p3[1]-p0[1])/480;
  ctx.transform(ax,ay,bx,by,p0[0],p0[1]);ctx.fillStyle='#101617';ctx.fillRect(0,0,640,480);
  if(review&&state.reviewImage?.complete){const img=state.reviewImage;const ratio=Math.min(600/img.width,300/img.height),w=img.width*ratio,h=img.height*ratio;ctx.drawImage(img,(640-w)/2,(380-h)/2,w,h);}
  ctx.fillStyle='#edf0e7';ctx.textAlign='center';ctx.textBaseline='middle';ctx.font='40px NotoMono,monospace';ctx.fillText(review?'PLAY':(state.camera===1?'M · LIVE':'M'),320,38);
  ctx.font='27px NotoMono,monospace';ctx.fillText(`f/${settingNow.f}  ${settingNow.shutter}  ISO ${settingNow.iso}`,320,440);ctx.restore();
}
function phaseForRender(){
  if(!state.transition)return state.visualPhase;
  const t=Math.min(1,(performance.now()-state.transition.start)/state.transition.duration),eased=t*t*(3-2*t);state.visualPhase=state.transition.from+(state.transition.to-state.transition.from)*eased;
  if(t>=1)state.transition=null;else requestAnimationFrame(drawCamera);
  return state.visualPhase;
}
function mechanismContext(id){
  const canvas=$(id),rect=canvas.getBoundingClientRect();if(!rect.width||!rect.height)return null;
  const dpr=Math.min(2,window.devicePixelRatio||1),width=Math.round(rect.width*dpr),height=Math.round(rect.height*dpr);
  if(canvas.width!==width||canvas.height!==height){canvas.width=width;canvas.height=height;}
  const ctx=canvas.getContext('2d');ctx.setTransform(width/110,0,0,height/85,0,0);ctx.clearRect(0,0,110,85);ctx.fillStyle='#fff';ctx.fillRect(0,0,110,85);return ctx;
}
function mechanismTargetPose(step,s,camera){
  const spec=contract.cameras[camera],gap=Math.min(1,Math.max(0,s.seconds/(1/250))),selected=.85*2**(spec.apertureBaseEV/2)/s.opticalF;
  let aperture=selected,front=0,rear=0,sensorActive=0;
  if(camera===2){front=1;sensorActive=step===3?.55:step===4?1:0;}
  else if(camera===1&&(step===0||step>=6))front=1;
  else if(step===3){front=.35;rear=Math.max(0,.35-gap);}
  else if(step===4){front=gap>=1?1:.85;rear=gap>=1?0:Math.max(0,.85-gap);}
  else if(step===5){front=1;rear=1;}
  return {aperture,front,rear,sensorActive};
}
function mechanismPoseAt(phase,s,camera){
  const step=Math.max(0,Math.min(7,phase)),lo=Math.floor(step),hi=Math.min(7,lo+1),t=step-lo,a=mechanismTargetPose(lo,s,camera),b=mechanismTargetPose(hi,s,camera);
  return Object.fromEntries(Object.keys(a).map(key=>[key,a[key]+(b[key]-a[key])*t]));
}
function drawIrisMechanism(ctx,opening){
  const radius=37.4,scale=Math.min(110,85)/90;ctx.save();ctx.translate(55,42.5);ctx.scale(scale,scale);
  const ring=ctx.createLinearGradient(-40,-40,40,40);ring.addColorStop(0,'#ccc');ring.addColorStop(.5,'#616161');ring.addColorStop(1,'#b8b8b8');
  ctx.beginPath();ctx.arc(0,0,radius+7,0,Math.PI*2);ctx.fillStyle=ring;ctx.fill();ctx.strokeStyle='#293338';ctx.lineWidth=1.5;ctx.stroke();
  ctx.beginPath();ctx.arc(0,0,radius,0,Math.PI*2);ctx.fillStyle='#171b1c';ctx.fill();
  const r=radius*Math.max(0,Math.min(.86,opening));
  for(let n=0;n<7;n++){
    const a=n*2*Math.PI/7,step=2*Math.PI/7,start=polar(r,a),next=polar(r,a+step),q1=polar(radius*.8,a+1.1),q2=polar(radius,a+1.7),grad=ctx.createLinearGradient(q2[0],q2[1],0,0);
    grad.addColorStop(0,'#a3a3a3');grad.addColorStop(1,'#474747');ctx.beginPath();ctx.moveTo(...start);ctx.lineTo(...next);ctx.quadraticCurveTo(...q1,...q2);ctx.arc(0,0,radius,a+1.7,a+.45,true);ctx.quadraticCurveTo(...polar(radius*.8,a+.1),...start);ctx.closePath();ctx.fillStyle=grad;ctx.fill();ctx.strokeStyle='#293338';ctx.lineWidth=1;ctx.stroke();
    const pin=polar(radius*.88,a+.48);ctx.beginPath();ctx.arc(...pin,2,0,Math.PI*2);ctx.fillStyle='#ccc';ctx.fill();
  }
  ctx.beginPath();for(let n=0;n<7;n++){const p=polar(r,n*2*Math.PI/7);if(n===0)ctx.moveTo(...p);else ctx.lineTo(...p);}ctx.closePath();ctx.fillStyle='#efeee5';ctx.fill();ctx.strokeStyle='#293338';ctx.lineWidth=.7;ctx.stroke();ctx.restore();
}
function mechanismCurtainLeaves(progress,second=false){
  const height=1/3,result=[];progress=Math.max(0,Math.min(1,progress));
  for(let index=0;index<3;index++){const top=second?(index+1)*progress/3-height:progress+index*(1-progress)/3,bottom=Math.min(1,top+height),clippedTop=Math.max(0,top);if(bottom>clippedTop+1e-9)result.push([clippedTop,bottom,index]);}
  return result;
}
function drawShutterMechanism(ctx,pose,camera,phase){
  const frame={x:8,y:9,w:94,h:67};ctx.fillStyle='#808080';ctx.beginPath();ctx.roundRect(3,4,104,77,4);ctx.fill();
  if(camera===2){
    const active=pose.sensorActive,gradient=ctx.createLinearGradient(frame.x,frame.y,frame.x+frame.w,frame.y+frame.h);
    gradient.addColorStop(0,`rgb(26 ${Math.round((.30+active*.35)*255)} ${Math.round((.36+active*.4)*255)})`);gradient.addColorStop(1,`rgb(20 ${Math.round((.16+active*.2)*255)} ${Math.round((.28+active*.4)*255)})`);ctx.fillStyle=gradient;ctx.fillRect(frame.x,frame.y,frame.w,frame.h);
    ctx.strokeStyle='rgba(255,255,255,.18)';ctx.lineWidth=.5;for(let x=8;x<102;x+=9){ctx.beginPath();ctx.moveTo(x,9);ctx.lineTo(x,76);ctx.stroke();}for(let y=9;y<76;y+=9){ctx.beginPath();ctx.moveTo(8,y);ctx.lineTo(102,y);ctx.stroke();}
    ctx.fillStyle='rgba(255,255,255,.72)';ctx.font='9px NotoMono,monospace';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(active>.1?(state.lang==='en'?'RECORDING':'REGISTRANDO'):'SENSOR',55,42.5);
    if(active){ctx.strokeStyle=`rgba(50,220,255,${active})`;ctx.lineWidth=2;ctx.strokeRect(frame.x,frame.y,frame.w,frame.h);}
  }else{
    ctx.save();ctx.beginPath();ctx.rect(frame.x,frame.y,frame.w,frame.h);ctx.clip();
    for(const [progress,second] of [[pose.front,false],[pose.rear,true]])for(const [top,bottom] of mechanismCurtainLeaves(progress,second).reverse()){
      const y=frame.y+frame.h*top,h=frame.h*(bottom-top),gradient=ctx.createLinearGradient(frame.x,y,frame.x+frame.w,y+h);gradient.addColorStop(0,second?'#696f70':'#454a4c');gradient.addColorStop(1,second?'#343a3c':'#252a2c');ctx.fillStyle=gradient;ctx.fillRect(frame.x,y,frame.w,h);ctx.strokeStyle='#929999';ctx.lineWidth=.8;ctx.beginPath();ctx.moveTo(frame.x,y);ctx.lineTo(frame.x+frame.w,y);ctx.stroke();
    }
    ctx.restore();
  }
  ctx.strokeStyle='#293338';ctx.lineWidth=1.5;ctx.strokeRect(frame.x,frame.y,frame.w,frame.h);
}
function drawSensitivityMechanism(ctx,gain){
  if(!sensitivityTextureCanvas){sensitivityTextureCanvas=document.createElement('canvas');sensitivityTextureCanvas.width=32;sensitivityTextureCanvas.height=24;}
  const pixels=sensitivityTextureCanvas,pctx=pixels.getContext('2d'),image=pctx.createImageData(32,24),amplitude=.012+.034*gain;
  for(let row=0;row<24;row++)for(let col=0;col<32;col++){
    let code=(((row+1)*73856093)^((col+1)*19349663))>>>0;code=Math.imul(code^(code>>>13),1274126177)>>>0;const noise=((code&65535)/65535-.5)*2*amplitude,index=(row*32+col)*4;
    image.data[index]=Math.round(Math.max(0,Math.min(1,.25+noise))*255);image.data[index+1]=Math.round(Math.max(0,Math.min(1,.42+noise))*255);image.data[index+2]=Math.round(Math.max(0,Math.min(1,.47+noise))*255);image.data[index+3]=255;
  }
  pctx.putImageData(image,0,0);ctx.fillStyle='#808080';ctx.beginPath();ctx.roundRect(3,4,104,77,4);ctx.fill();ctx.save();ctx.imageSmoothingEnabled=false;ctx.drawImage(pixels,8,9,94,67);ctx.restore();ctx.strokeStyle='#293338';ctx.lineWidth=1.5;ctx.strokeRect(8,9,94,67);
}
function drawMechanismPreviews(s,phase,camera){
  const pose=mechanismPoseAt(phase,s,camera),iris=mechanismContext('irisMechanism'),shutter=mechanismContext('shutterMechanism'),sensitivity=mechanismContext('sensitivityMechanism');
  if(iris)drawIrisMechanism(iris,pose.aperture);if(shutter)drawShutterMechanism(shutter,pose,camera,phase);if(sensitivity)drawSensitivityMechanism(sensitivity,s.gain);
}
function drawCamera() {
  if (!cameraImage || !state.geometry) return;
  const canvas=$('cameraCanvas'), rect=canvas.getBoundingClientRect(); if (!rect.width || !rect.height) return;
  const dpr=Math.min(2,window.devicePixelRatio||1),w=Math.round(rect.width*dpr),h=Math.round(rect.height*dpr);
  if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;}
  const logicalWidth=1376,logicalHeight=768;
  const ctx=canvas.getContext('2d'); ctx.setTransform(w/logicalWidth,0,0,h/logicalHeight,0,0); ctx.clearRect(0,0,logicalWidth,logicalHeight); ctx.drawImage(cameraImage,0,0,logicalWidth,logicalHeight);
  const g=state.geometry,s=state.shot||(state.phase===7&&state.history.length?state.history[0].setting:setting()),phase=phaseForRender(),illumination=[1,.67,.37][s.light],opening=apertureOpening(s),beamWidth=74*opening*(g.irisVisualScale||1);
  const iris=g.irisDisplay||g.iris,front=g.front,sensorCenter=g.sensor?.reduce((a,p)=>[a[0]+p[0]/g.sensor.length,a[1]+p[1]/g.sensor.length],[0,0]);
  const shutters=poseAt(phase,s.seconds,state.camera),sensorActive=state.camera===2?(phase>3&&phase<5?1:phase>=3&&phase<=5?.55:0):0;
  drawCurtains(ctx,g,shutters,logicalWidth,logicalHeight,state.camera===2);
  if(state.camera===2&&sensorActive){path(ctx,g.shutterGate);ctx.closePath();ctx.fillStyle=`rgba(111,222,225,${.28*sensorActive})`;ctx.fill();}
  if(front&&iris)drawBeam(ctx,[front,iris],Math.max(3,72*(g.irisVisualScale||1)),illumination*.50);
  let mirror=null,mirrorDown=0;
  if(state.camera===0){mirrorDown=phase<1?1:phase<2?2-phase:phase<5?0:phase<6?phase-5:1;mirror=currentMirror(g,mirrorDown);}
  if(mirror){ctx.save();ctx.globalAlpha=.9;const grad=ctx.createLinearGradient(mirror.front[0][0],mirror.front[0][1],mirror.front[2][0],mirror.front[2][1]);grad.addColorStop(0,'#dce4e2');grad.addColorStop(.55,'#839398');grad.addColorStop(1,'#334147');path(ctx,mirror.front);ctx.closePath();ctx.fillStyle=grad;ctx.strokeStyle='#405056';ctx.lineWidth=2;ctx.fill();ctx.stroke();ctx.restore();}
  if(front&&iris){
    if(state.camera===0&&mirror?.hit&&mirrorDown>.999)drawBeam(ctx,[iris,mirror.hit,g.focus,...(g.route||[])],beamWidth,illumination*.55);
    else if(state.camera===0&&mirror?.hit&&mirror.bounce)drawBeam(ctx,[mirror.hit,mirror.bounce],beamWidth,illumination*.45);
    else if(sensorCenter)drawBeam(ctx,[iris,sensorCenter],beamWidth,illumination*(phase>=3&&phase<=5?.55:.25));
  }
  ctx.save();if(g.irisForeground){ctx.beginPath();ctx.rect(0,0,logicalWidth,logicalHeight);ctx.moveTo(g.irisForeground[0][0],g.irisForeground[0][1]);for(const p of g.irisForeground.slice(1))ctx.lineTo(p[0],p[1]);ctx.closePath();ctx.clip('evenodd');}drawIris(ctx,g,opening,logicalWidth,logicalHeight);ctx.restore();
  paintScreen(ctx,g,s,phase>=7,logicalWidth,logicalHeight);
  drawMechanismPreviews(s,phase,state.camera);
}
async function selectLight(index) {
  if(index===state.light||state.capturing||state.loadingLight)return;
  const request=++state.lightRequest;state.loadingLight=true;refresh();
  try{
    if(!posterCache.has(index))posterCache.set(index,await loadImage(`../Scene/${LIGHTS[index]}.png`));
    if(request!==state.lightRequest)return;
    state.light=index;motionAtlasCache.clear();scenePoster=posterCache.get(index);
    const video=$('sceneVideo'),src=`../Scene/${LIGHTS[index]}.mp4`;
    video.pause();video.src=src;video.poster=`../Scene/${LIGHTS[index]}.png`;video.load();
    if(!state.videoPaused)video.play().catch(()=>{});
    cacheSelectedResources();
  }catch(error){console.error('LuzCam could not load scene lighting',error);state.lightRequest++;alert(T('captureError'));}
  finally{if(request===state.lightRequest)state.loadingLight=false;refresh();}
}
function motionFrames(startFrame,seconds){
  const count=seconds>=sceneMeta.period?sceneMeta.frames:seconds>=1/60?17:3;
  return Array.from({length:count},(_,i)=>Math.floor(startFrame+(i+.5)/count*seconds*sceneMeta.fps+.5)%sceneMeta.frames);
}
async function motionAtlas(lightIndex){
  if(!motionAtlasCache.has(lightIndex)){
    const pending=loadImage(`../Scene/${LIGHTS[lightIndex]}-motion.png`);
    motionAtlasCache.clear();motionAtlasCache.set(lightIndex,pending);
  }
  return motionAtlasCache.get(lightIndex);
}
function integrateSceneMotion(base,atlas,box,frames){
  const [x0,y0,x1,y1]=box,width=x1-x0,height=y1-y0;
  const patch=document.createElement('canvas');patch.width=width;patch.height=height;
  const patchCtx=patch.getContext('2d',{willReadFrequently:true});
  const sums=new Float32Array(width*height*3);
  for(const frameIndex of frames){
    patchCtx.clearRect(0,0,width,height);
    patchCtx.drawImage(base,x0,y0,width,height,0,0,width,height);
    patchCtx.drawImage(atlas,0,frameIndex*height,width,height,0,0,width,height);
    const data=patchCtx.getImageData(0,0,width,height).data;
    for(let source=0,target=0;source<data.length;source+=4){
      sums[target++]+=linearLut[data[source]];
      sums[target++]+=linearLut[data[source+1]];
      sums[target++]+=linearLut[data[source+2]];
    }
  }
  const averaged=patchCtx.createImageData(width,height),out=averaged.data,scale=1/frames.length;
  for(let source=0,target=0;source<sums.length;source+=3,target+=4){
    for(let channel=0;channel<3;channel++){
      const value=Math.max(0,Math.min(1,sums[source+channel]*scale));
      const encoded=value<=.0031308?12.92*value:1.055*value**(1/2.4)-.055;
      out[target+channel]=Math.round(encoded*255);
    }
    out[target+3]=255;
  }
  patchCtx.putImageData(averaged,0,0);
  const result=document.createElement('canvas');result.width=960;result.height=540;
  const resultCtx=result.getContext('2d');resultCtx.drawImage(base,0,0);resultCtx.drawImage(patch,x0,y0);
  return result;
}
async function capture(snapshot=setting()) {
  if(state.history.length>=100){alert(T('full'));return false;}
  const video=$('sceneVideo'),s={...snapshot},frame=Math.round((video.currentTime||0)*sceneMeta.fps)%sceneMeta.frames;
  const frames=motionFrames(frame,s.seconds),atlas=await motionAtlas(s.light),box=sceneMeta.lights[LIGHTS[s.light]].box;
  cacheForOffline([`assets/scene/${LIGHTS[s.light]}-motion.png`]);
  const original=integrateSceneMotion(scenePoster,atlas,box,frames);
  const canvas=document.createElement('canvas');canvas.width=960;canvas.height=540;const ctx=canvas.getContext('2d',{willReadFrequently:true});
  const blurRadius=Math.min(10,Math.max(0,9/s.opticalF-.55)*(s.camera===2?.35:1));
  const blurred=document.createElement('canvas');blurred.width=960;blurred.height=540;const blurCtx=blurred.getContext('2d');blurCtx.filter=`blur(${blurRadius}px)`;blurCtx.drawImage(original,0,0);blurCtx.filter='none';
  ctx.drawImage(blurred,0,0);
  const mask=document.createElement('canvas');mask.width=960;mask.height=540;const maskCtx=mask.getContext('2d');
  maskCtx.fillStyle='#fff';maskCtx.beginPath();maskCtx.moveTo(285,195);maskCtx.lineTo(356,195);maskCtx.lineTo(397,397);maskCtx.lineTo(274,397);maskCtx.closePath();maskCtx.fill();
  if(focusMotionImage&&sceneMeta?.focusMotion){const [x0,y0,x1,y1]=sceneMeta.focusMotion.box,w=x1-x0,h=y1-y0;maskCtx.globalCompositeOperation='lighter';for(const frameIndex of frames)maskCtx.drawImage(focusMotionImage,0,frameIndex*h,w,h,x0,y0,w,h);maskCtx.globalCompositeOperation='source-over';}
  const softMask=document.createElement('canvas');softMask.width=960;softMask.height=540;const softCtx=softMask.getContext('2d');softCtx.filter='blur(1px)';softCtx.drawImage(mask,0,0);softCtx.filter='none';
  const sharp=document.createElement('canvas');sharp.width=960;sharp.height=540;const sharpCtx=sharp.getContext('2d');sharpCtx.drawImage(original,0,0);sharpCtx.globalCompositeOperation='destination-in';sharpCtx.drawImage(softMask,0,0);
  ctx.drawImage(sharp,0,0);
  const ev=s.offset;
  const imageData=ctx.getImageData(0,0,canvas.width,canvas.height); const pixels=imageData.data; const factor=2**Math.max(-4,Math.min(4,ev));
  const noiseStrength=Math.max(0,s.gain)*.008*(s.camera===2?1.3:1);let seed=((Math.round((video.currentTime||0)*30)+1)*2654435761^(s.i+1)*1597334677)>>>0;
  for(let i=0;i<pixels.length;i+=4){for(let c=0;c<3;c++){const linear=pixels[i+c]/255;const light=linear<=.04045?linear/12.92:((linear+.055)/1.055)**2.4;const out=Math.max(0,Math.min(1,light*factor));const enc=out<=.0031308?12.92*out:1.055*out**(1/2.4)-.055;seed=(Math.imul(1664525,seed)+1013904223)>>>0;const grain=((seed>>>24)/255-.5)*noiseStrength;pixels[i+c]=Math.max(0,Math.min(255,Math.round(enc*255+grain*255)));}}
  ctx.putImageData(imageData,0,0);
  return {data:canvas.toDataURL('image/jpeg',.84),setting:s,frame,blurFrames:frames.length};
}
function animateToPhase(target){if(reducedMotion?.matches){state.visualPhase=target;state.transition=null;drawCamera();return;}state.transition={from:state.visualPhase,to:target,start:performance.now(),duration:420};requestAnimationFrame(drawCamera);}
async function advance() {
  let target;
  if(state.phase===0||state.phase===7){if(state.history.length>=100){alert(T('full'));return;}const snapshot=setting();state.capturing=true;refresh();try{state.pendingShot=await capture(snapshot);}catch(error){console.error('LuzCam capture failed',error);alert(T('captureError'));state.pendingShot=null;}finally{state.capturing=false;}if(!state.pendingShot){refresh();return;}state.shot=snapshot;target=1;}
  else target=state.phase+1;
  state.phase=target;
  if(target===7){state.pendingShot.setting={...state.shot};state.history.unshift(state.pendingShot);if(state.history.length>100)state.history.length=100;state.rollVersion++;state.pendingShot=null;state.shot=null;state.reviewImage=new Image();state.reviewImage.onload=drawCamera;state.reviewImage.src=state.history[0].data;}
  animateToPhase(target);
  refresh();
}
function stopPlayback(){state.playing=false;clearTimeout(state.timer);state.timer=0;if(contract)refresh();}
function schedule(){if(!state.playing)return;const seconds=state.phase===4?1.2+4*Math.sqrt(state.shot?.seconds??1/125):1.8;state.timer=setTimeout(async()=>{if(state.phase<7){await advance();if(state.phase<7)schedule();else stopPlayback();}else stopPlayback();},seconds*1000);}
function renderRoll(){
  if(renderedRollVersion===state.rollVersion&&renderedRollLanguage===state.lang)return;
  renderedRollVersion=state.rollVersion;renderedRollLanguage=state.lang;
  const root=$('rollGrid');root.replaceChildren();
  if(!state.history.length){const empty=document.createElement('div');empty.className='empty-roll';empty.innerHTML=`<span>⌁</span><p>${T('empty')}</p>`;root.append(empty);return;}
  for(const item of state.history){
    const card=document.createElement('div');card.className='shot-card';
    const button=document.createElement('button');button.className='shot';button.type='button';button.setAttribute('aria-label',`${T('shot')}: f/${item.setting.f}, ${item.setting.shutter}, ISO ${item.setting.iso}`);
    const image=document.createElement('img');image.src=item.data;image.alt='';const caption=document.createElement('span');caption.textContent=`f/${item.setting.f} · ${item.setting.shutter} · ${item.setting.iso}`;button.append(image,caption);button.addEventListener('click',()=>showPhoto(item));
    const remove=document.createElement('button');remove.className='shot-remove';remove.type='button';remove.textContent='×';remove.setAttribute('aria-label',`${T('remove')}: f/${item.setting.f}, ${item.setting.shutter}, ISO ${item.setting.iso}`);remove.title=T('remove');remove.addEventListener('click',()=>removePhoto(item));
    card.append(button,remove);root.append(card);
  }
}
function removePhoto(item){
  const index=state.history.indexOf(item);if(index<0)return;
  state.history.splice(index,1);state.rollVersion++;
  if(state.phase===7&&index===0){
    if(state.history.length){state.reviewImage=new Image();state.reviewImage.onload=drawCamera;state.reviewImage.src=state.history[0].data;}
    else{state.phase=0;state.reviewImage=null;animateToPhase(0);}
  }
  refresh();
}
function showPhoto(item){const overlay=document.createElement('dialog');overlay.className='photo-dialog';overlay.innerHTML=`<form method="dialog"><button class="dialog-close" aria-label="${T('close')}" title="${T('close')}">×</button><img src="${item.data}" alt="${T('shot')}"><p>f/${item.setting.f} · ${item.setting.shutter} · ISO ${item.setting.iso}</p></form>`;document.body.append(overlay);overlay.showModal();overlay.addEventListener('close',()=>overlay.remove(),{once:true});}
let scenePoster;
const posterCache = new Map();
function bind(){
  $('language').addEventListener('change',e=>{state.lang=e.target.value;applyLanguage();});
  $('stepByStep').addEventListener('change',e=>{state.stepByStep=e.target.checked;if(state.stepByStep)stopPlayback();else if(state.phase>0&&state.phase<7){state.playing=true;refresh();schedule();}});
  $('thirds').addEventListener('change',e=>{state.thirds=e.target.checked;state.a=Math.round(state.a*(state.thirds?3:1/3));state.s=Math.round(state.s*(state.thirds?3:1/3));state.i=Math.round(state.i*(state.thirds?3:1/3));refresh();});
  const preview=$('mechanismPreview'),stage=$('cameraCanvas').parentElement;
  const previewIds={aperture:'aperture',shutter:'shutter',iso:'iso'};
  function showPreview(id){stage.dataset.preview=id;stage.classList.add('show-mechanism');preview.setAttribute('aria-hidden','false');}
  function hidePreview(){stage.classList.remove('show-mechanism');delete stage.dataset.preview;preview.setAttribute('aria-hidden','true');}
  for(const [id,key] of [['aperture','a'],['shutter','s'],['iso','i']]){
    const control=$(id);
    control.addEventListener('input',e=>{state[key]=+e.target.value;refresh();});
    control.addEventListener('pointerenter',()=>showPreview(previewIds[id]));
    control.addEventListener('pointerleave',()=>{if(!control.matches(':focus-visible'))hidePreview();});
    control.addEventListener('focus',()=>showPreview(previewIds[id]));
    control.addEventListener('blur',()=>{if(!control.matches(':hover'))hidePreview();});
  }
  document.querySelectorAll('.camera-choice').forEach(b=>b.addEventListener('click',async()=>{
    if(state.phase>0&&state.phase<7)return;
    const oldF=setting().opticalF,nextCamera=+b.dataset.camera,divisor=state.thirds?3:1;
    state.camera=nextCamera;
    const values=activeApertures(),base=contract.cameras[nextCamera].apertureBaseEV;
    state.a=values.reduce((best,value,index)=>Math.abs(Math.log2(2**((base+index/divisor)/2)/oldF))<Math.abs(Math.log2(2**((base+best/divisor)/2)/oldF))?index:best,0);
    state.phase=0;state.pendingShot=null;state.shot=null;state.reviewImage=null;cameraImage=null;state.geometry=null;animateToPhase(0);refresh();await loadCamera();refresh();
  }));
  document.querySelectorAll('.light-tab').forEach(b=>b.addEventListener('click',()=>selectLight(+b.dataset.light)));
  $('motionToggle').addEventListener('click',()=>{state.videoPaused=!state.videoPaused;const video=$('sceneVideo');if(state.videoPaused)video.pause();else video.play().catch(()=>{});updateMotionControl();$('motionToggle').setAttribute('aria-pressed',String(state.videoPaused));});
  $('returnScene').addEventListener('click',()=>{state.phase=0;state.shot=null;state.pendingShot=null;animateToPhase(0);refresh();});
  $('play').addEventListener('click',async()=>{if(state.playing){stopPlayback();refresh();return;}if(state.phase===7)state.phase=0;await advance();if(state.phase<7&&!state.stepByStep){state.playing=true;refresh();schedule();}});
  $('next').addEventListener('click',async()=>{stopPlayback();await advance();});
  $('previous').addEventListener('click',()=>{stopPlayback();state.phase=Math.max(0,state.phase-1);if(state.phase===0){state.shot=null;state.pendingShot=null;}animateToPhase(state.phase);refresh();});
  $('clearRoll').addEventListener('click',()=>{if(!state.history.length)return;if(confirm(T('clearConfirm').replace('{count}',state.history.length))){state.history=[];state.rollVersion++;if(state.phase===7){state.phase=0;state.reviewImage=null;animateToPhase(0);}refresh();}});
  resizeObserver=new ResizeObserver(drawCamera);resizeObserver.observe($('cameraCanvas'));
}
async function init(){
  try{
    [contract,ranges,dictionary,scenePoster,sceneMeta,focusMotionImage]=await Promise.all([
      fetch(DATA.contract).then(r=>r.json()),fetch(DATA.ranges).then(r=>r.json()),fetch(DATA.translations).then(r=>r.json()),loadImage('../Scene/day.png'),fetch(DATA.scene).then(r=>r.json()),loadImage('../Scene/focus-motion.png')
    ]);
    document.querySelectorAll('[data-camera]').forEach((b,i)=>{b.setAttribute('aria-label',contract.cameras[i].name);});
    $('thirds').checked=false;
    bind();applyLanguage();await loadCamera();
    $('sceneVideo').src='../Scene/day.mp4';
    reducedMotion=matchMedia('(prefers-reduced-motion: reduce)');
    if (reducedMotion.matches) { state.videoPaused=true; updateMotionControl(); $('motionToggle').setAttribute('aria-pressed','true'); }
    else $('sceneVideo').play().catch(()=>{});
    await registerOfflineSupport();cacheSelectedResources();
  }catch(error){console.error('LuzCam could not load local resources',error);document.body.innerHTML='<main style="max-width:680px;margin:12vh auto;padding:24px;font:16px Arial;color:#263132"><h1>LuzCam no ha podido cargar sus recursos</h1><p>Abre esta aplicación desde el servidor local indicado en Web/LEEME.md. No funciona al abrir el archivo directamente desde el disco.</p></main>';}
}
init();
