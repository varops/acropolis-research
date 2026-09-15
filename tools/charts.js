(function(){
const css=()=>getComputedStyle(document.documentElement);
const tok=n=>css().getPropertyValue(n).trim();
function draw(el){
  const spec=CHARTS[el.dataset.chart]; const canvas=el.querySelector('canvas'); const dpr=window.devicePixelRatio||1;
  const W=el.clientWidth||700; const ink=tok('--ink'), ink2=tok('--ink2'), muted=tok('--muted'), rule=tok('--rule'), panel=tok('--panel');
  const series=[tok('--s1'),tok('--s2'),tok('--s3'),tok('--s4')];
  const L=Math.min(300,Math.max(150,W*0.36)), R=54, T=8, B=26, bh=spec.kind==='bars'?18:14, gap=spec.kind==='bars'?6:3, ggap=14;
  const rows=spec.kind==='bars'?spec.groups.flatMap((g,gi)=>[{label:g[0],head:true}].concat(g[1].map(([l,v],ri)=>({label:l,vals:[v],color:spec.colorByIndex?ri:(spec.groupColors?spec.groupColors[gi]:0)})))):spec.rows.map(([l,vals])=>({label:l,vals}));
  const nser=spec.kind==='bars'?1:spec.series.length;
  let y=T; const pos=[]; rows.forEach(r=>{ if(r.head){y+=ggap;pos.push({r,y});y+=16;return;} pos.push({r,y}); y+=nser*bh+(nser-1)*gap+ (spec.kind==='bars'?gap:8); });
  const H=y+B;
  canvas.width=W*dpr; canvas.height=H*dpr; canvas.style.height=H+'px'; const c=canvas.getContext('2d'); c.scale(dpr,dpr);
  c.font='12px '+tok('--sans'); const x=v=>L+(v/spec.max)*(W-L-R);
  [0,25,50,75,100].forEach(v=>{c.strokeStyle=rule;c.lineWidth=1;c.beginPath();c.moveTo(x(v)+.5,T);c.lineTo(x(v)+.5,H-B+4);c.stroke();c.fillStyle=muted;c.font='11px '+tok('--mono');c.textAlign='center';c.fillText(v,x(v),H-8);});
  c.fillStyle=muted;c.font='11px '+tok('--mono');c.textAlign='left';c.fillText(spec.unit,8,H-8);
  pos.forEach(({r,y})=>{
    if(r.head){c.fillStyle=ink2;c.font='600 12px '+tok('--sans');c.textAlign='left';c.fillText(r.label,8,y+12);return;}
    c.fillStyle=ink;c.font='12.5px '+tok('--sans');c.textAlign='right';
    // wrap label into two lines if long
    const words=r.label.split(' ');let lines=[''];words.forEach(w=>{const t=(lines[lines.length-1]+' '+w).trim();if(c.measureText(t).width>L-16&&lines[lines.length-1]){lines.push(w);}else lines[lines.length-1]=t;});
    const rowH=nser*bh+(nser-1)*gap; const ly=y+rowH/2+4-(lines.length-1)*7; lines.forEach((ln,i)=>c.fillText(ln,L-10,ly+i*14));
    r.vals.forEach((v,i)=>{const by=y+i*(bh+gap); const ci=(r.color!==undefined)?r.color:i; const w=Math.max(x(v)-x(0),2);
      c.beginPath(); c.roundRect(x(0)+(ci<0?.5:0),by+(ci<0?.5:0),w-(ci<0?1:0),bh-(ci<0?1:0),[0,4,4,0]); if(ci<0){c.strokeStyle=series[0];c.lineWidth=1.5;c.stroke();}else{c.fillStyle=series[ci];c.fill();}
      c.fillStyle=ink;c.font='11.5px '+tok('--mono');c.textAlign='left';c.fillText(v.toFixed(1),x(v)+6,by+bh/2+4);});
  });
  c.strokeStyle=tok('--muted');c.beginPath();c.moveTo(x(0)+.5,T);c.lineTo(x(0)+.5,H-B+4);c.stroke();
  const items=spec.kind!=='bars'?spec.series.map((s,i)=>[s,i]):(spec.legend||[]); if(items.length&&!el.parentNode.querySelector('.legend')){const d=document.createElement('div');d.className='legend';d.innerHTML=items.map(([s,i])=>`<span><i style="${i<0?('border:1.5px solid '+series[0]+';background:transparent'):('background:'+series[i])}"></i>${s}</span>`).join('');el.parentNode.insertBefore(d,el);}
}
function all(){document.querySelectorAll('.chart').forEach(draw);}
all(); let t; window.addEventListener('resize',()=>{clearTimeout(t);t=setTimeout(all,120);});
if(window.matchMedia){window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change',all);}
new MutationObserver(all).observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});
})();
