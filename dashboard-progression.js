(() => {
  const el = id => document.getElementById(`progress-${id}`);
  const svgNS = 'http://www.w3.org/2000/svg';
  const date = value => new Intl.DateTimeFormat('nb-NO',{day:'2-digit',month:'short',timeZone:'Europe/Oslo'}).format(new Date(value));
  const signed = n => n === null ? '—' : `${n>0?'+':''}${n}`;
  let mode = '2v2', days = '90', request = 0;
  let chartKey = '';
  try { const saved=localStorage.getItem('rlhub:lanyardPlaylist'); if(['1v1','2v2','3v3'].includes(saved)) mode=saved; } catch (_) {}
  el('mode').value = mode;
  function node(tag, attrs={}, text='') {
    const result=document.createElementNS(svgNS,tag);
    Object.entries(attrs).forEach(([key,value])=>result.setAttribute(key,value));
    if(text) result.textContent=text;
    return result;
  }
  function chart(data) {
    const key=JSON.stringify([mode,days,data.points,data.current?.rank]);
    if (key===chartKey) return;
    chartKey=key;
    const points=data.points;
    el('chart').replaceChildren();
    el('table').replaceChildren();
    if (!points.length) {el('empty').hidden=false;el('empty').textContent=data.current ? 'Ingen målinger i valgt periode. Velg en lengre periode.' : 'Hent rank i Profile for å starte progresjonsgrafen.';return;}
    el('empty').hidden=true;
    const w=940,h=310,left=60,right=14,top=24,bottom=38;
    const min=Math.max(0,Math.floor((Math.min(...points.map(p=>p.mmr))-65)/50)*50);
    const max=Math.max(min+150,Math.ceil((Math.max(...points.map(p=>p.mmr))+65)/50)*50);
    const first=Date.parse(points[0].at),last=Date.parse(points.at(-1).at);
    const x=p=>first===last ? (left+w-right)/2 : left+(Date.parse(p.at)-first)/(last-first)*(w-left-right);
    const y=n=>h-bottom-(n-min)/(max-min)*(h-top-bottom);
    const svg=node('svg',{viewBox:`0 0 ${w} ${h}`,role:'img','aria-label':`MMR-progresjon for ${mode}: ${points.length} faktiske rankmålinger.`,preserveAspectRatio:'xMidYMid meet'});
    data.bands.forEach((band,i)=>{
      if(band.high<=min||band.low>=max) return;
      const upper=y(Math.min(max,band.high)),lower=y(Math.max(min,band.low));
      svg.append(node('rect',{x:left,y:upper,width:w-left-right,height:lower-upper,fill:i>=15?'#6554a5':'#1764a0',opacity:i%2?.17:.28}));
      if(lower-upper>20)svg.append(node('text',{x:left+12,y:upper+16,fill:'#8199b9','font-size':11},band.rank));
    });
    const step=Math.max(50,Math.ceil((max-min)/5/50)*50);
    for(let n=Math.ceil(min/step)*step;n<=max;n+=step){svg.append(node('line',{x1:left,x2:w-right,y1:y(n),y2:y(n),stroke:'#2b4567','stroke-width':1}));svg.append(node('text',{x:left-12,y:y(n)+4,'text-anchor':'end',fill:'#a5bbd4','font-size':11},String(n)));}
    const plot=points.map(p=>`${x(p)},${y(p.mmr)}`).join(' ');
    if(points.length>1)svg.append(node('polyline',{points:plot,fill:'none',stroke:'#ffa629','stroke-width':2.5,'stroke-linejoin':'round'}));
    // Limit interactive markers for long histories while retaining every observation in the line.
    const stride=Math.max(1,Math.ceil(points.length/150));
    points.forEach((p,index)=>{
      if(index%stride && index!==points.length-1)return;
      const dot=node('circle',{cx:x(p),cy:y(p.mmr),r:points.length===1?5:3,fill:'#ffb33e',tabindex:0,'aria-label':`${date(p.at)}: ${p.mmr} MMR, ${p.rank}`});
      dot.append(node('title',{},`${new Date(p.at).toLocaleString('nb-NO')} · ${p.mmr} MMR · ${p.rank}`));svg.append(dot);
    });
    const labels=points.length===1?[points[0]]:[points[0],points[Math.floor((points.length-1)/2)],points.at(-1)];
    labels.forEach(p=>svg.append(node('text',{x:x(p),y:h-10,'text-anchor':'middle',fill:'#a5bbd4','font-size':11},date(p.at))));
    el('chart').append(svg);
    points.slice(-100).reverse().forEach(p=>{const row=document.createElement('tr');[new Date(p.at).toLocaleString('nb-NO'),p.mmr,p.rank].forEach(value=>{const cell=document.createElement('td');cell.textContent=value;row.append(cell);});el('table').append(row);});
  }
  function render(data) {
    el('rank').textContent=data.current?.rank || 'Ingen rank hentet';
    el('mmr').textContent=data.current?.mmr ?? '—';
    el('delta').textContent=`${signed(data.delta)} MMR`;
    el('samples').textContent=data.points.length;
    const tip=RLProgression.advice(data);
    el('tip-title').textContent=tip.title;el('tip-copy').textContent=tip.text;el('tip-reason').textContent=tip.reason;
    el('tip-action').textContent=tip.action;el('tip-action').href=tip.href;
    el('notice').textContent=data.points.length===1 ? 'Første måling er lagret. Kurven vises når appen har minst to rankmålinger.' : data.points.length ? `Faktiske rankmålinger fra ${date(data.points[0].at)}. Linjen forbinder målingene; den viser ikke hver kamp.` : 'Historikken starter ved første lagrede rankmåling.';
    el('status').textContent='';chart(data);
  }
  async function refresh() {
    const token=++request;
    try {const response=await fetch(`./api/progression?playlist=${mode}&days=${days}`);if(!response.ok)throw Error();const data=await response.json();if(token===request)render(data);}
    catch(_){if(token===request)el('status').textContent='Progresjonen kunne ikke oppdateres. Prøver igjen automatisk.';}
  }
  el('mode').addEventListener('change',()=>{mode=el('mode').value;try{localStorage.setItem('rlhub:lanyardPlaylist',mode);}catch(_){}window.dispatchEvent(new CustomEvent('rlhub:playlist',{detail:mode}));refresh();});
  el('period').addEventListener('change',()=>{days=el('period').value;refresh();});
  window.addEventListener('rlhub:playlist',event=>{if(['1v1','2v2','3v3'].includes(event.detail)&&mode!==event.detail){mode=event.detail;el('mode').value=mode;refresh();}});
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh();});
  refresh();setInterval(()=>{if(!document.hidden)refresh();},10000);
})();
