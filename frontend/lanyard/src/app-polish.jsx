import React, { Component, useEffect, useLayoutEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import Aurora from './components/Aurora';
import CountUp from './components/CountUp';
import TiltedCard from './components/TiltedCard';
import SpotlightCard from './components/SpotlightCard';
import './app-polish.css';

const reduced = matchMedia('(prefers-reduced-motion: reduce)');
const coarse = matchMedia('(pointer: coarse)');
function useMotion() {
  const [enabled, setEnabled] = useState(!reduced.matches && !window.RL_HUB_MOTION_PAUSED);
  useEffect(() => { const update = () => setEnabled(!reduced.matches && !window.RL_HUB_MOTION_PAUSED); reduced.addEventListener('change', update); window.addEventListener('rlhub:motion', update); return () => {reduced.removeEventListener('change', update);window.removeEventListener('rlhub:motion', update);}; }, []);
  return enabled;
}
class GraphicsFallback extends Component {
  state = {failed:false};
  static getDerivedStateFromError() {return {failed:true};}
  render() { return this.state.failed ? <div className="polish-aurora-static" /> : this.props.children; }
}
function HeaderAurora({header}) {
  const motion = useMotion();
  const [focused, setFocused] = useState(document.hasFocus() && !document.hidden);
  const [visible, setVisible] = useState(true);
  useEffect(() => {
    const focus = () => setFocused(!document.hidden);
    const blur = () => setFocused(false);
    const visibility = () => setFocused(!document.hidden && document.hasFocus());
    window.addEventListener('focus', focus);window.addEventListener('blur', blur);document.addEventListener('visibilitychange', visibility);
    const observer = new IntersectionObserver(([entry]) => setVisible(entry.isIntersecting));observer.observe(header);
    return () => {window.removeEventListener('focus',focus);window.removeEventListener('blur',blur);document.removeEventListener('visibilitychange',visibility);observer.disconnect();};
  }, [header]);
  const active = motion && focused && visible;
  return <div className="polish-aurora" data-state={active ? 'running':'paused'}>
    {active ? <GraphicsFallback><Aurora colorStops={['#3de0ce','#467bde','#9971d8']} speed={.35} amplitude={.8} blend={.65} /></GraphicsFallback> : <div className="polish-aurora-static" />}
  </div>;
}
function Spotlight({content}) {
  const holder = useRef(null);
  useLayoutEffect(() => {holder.current.append(content);}, [content]);
  return <SpotlightCard className="polish-spotlight" spotlightColor="rgba(85,239,213,.22)"><div className="polish-spotlight-content" ref={holder} /></SpotlightCard>;
}
function CarTilt({src,alt}) {
  const motion = useMotion();
  return motion && !coarse.matches ? <TiltedCard imageSrc={src} altText={alt} containerHeight="100%" imageHeight="100%" imageWidth="100%" rotateAmplitude={7} scaleOnHover={1.035} showMobileWarning={false} showTooltip={false} /> : <img src={src} alt={alt} />;
}
const roots = new Map();
function decorate() {
  for (const [node, root] of roots) if (!node.isConnected) {root.unmount();roots.delete(node);}
  document.querySelectorAll('.pack-card:not(.polish-mounted),.settings-value:not(.polish-mounted)').forEach(card => {
    const content = document.createDocumentFragment();while(card.firstChild)content.append(card.firstChild);
    const container = document.createElement('div');container.className='polish-spotlight-root';card.append(container);card.classList.add('polish-mounted');
    const root=createRoot(container);roots.set(card,root);root.render(<Spotlight content={content} />);
  });
  document.querySelectorAll('.garage-card-image:not(.polish-mounted)').forEach(slot => {
    const image=slot.querySelector('img');if(!image)return;
    const container=document.createElement('span');container.className='polish-tilt-root';slot.classList.add('polish-mounted');image.replaceWith(container);
    const root=createRoot(container);roots.set(slot,root);root.render(<CarTilt src={image.src} alt={image.alt} />);
  });
}
// Observe only collections that can be rebuilt by the existing app controllers.
document.querySelectorAll('#packs-grid,#settings-values,#settings-deadzone-values,#garage-grid').forEach(collection => {
  new MutationObserver(decorate).observe(collection,{childList:true});
});
decorate();

function Counter({from,to,suffix,clock}) {
  const motion=useMotion();
  const formatter=clock ? value => {const seconds=Math.round(value);return `${Math.floor(seconds/60)}:${String(seconds%60).padStart(2,'0')}`;} : undefined;
  return motion ? <><CountUp from={from} to={to} duration={.6} formatter={formatter} />{suffix}</> : <>{clock ? formatter(to):to}{suffix}</>;
}
function animateNumber(node) {
  if(!node)return;
  const wrapper=document.createElement('span');wrapper.className='polish-number-wrap';wrapper.style.color=getComputedStyle(node).color;node.before(wrapper);wrapper.append(node);
  const display=document.createElement('span');display.className='polish-number-display';display.setAttribute('aria-hidden','true');wrapper.append(display);
  const root=createRoot(display);let previous=null,last='';
  function update() {
    const text=node.textContent;
    if(text===last)return;last=text;
    const clock=node.id==='session-training';
    const time=clock && text.match(/^(\d+):(\d{2})$/);
    const number=!clock && text.match(/^(\d+)(.*)$/s);
    const value=time ? Number(time[1])*60+Number(time[2]) : number ? Number(number[1]) : null;
    if(value===null){node.classList.remove('polish-number-original');display.hidden=true;previous=null;return;}
    display.style.font=getComputedStyle(node).font;
    if(!node.classList.contains('polish-number-original')) display.style.color=getComputedStyle(node).color;
    node.classList.add('polish-number-original');display.hidden=false;
    root.render(<Counter from={previous ?? value} to={value} suffix={number?.[2] || ''} clock={clock} />);previous=value;
  }
  new MutationObserver(update).observe(node,{childList:true,characterData:true,subtree:true});update();
}
if(document.body.dataset.page==='dashboard') {
  ['progress-mmr','progress-samples','session-score','session-training','session-results'].forEach(id=>animateNumber(document.getElementById(id)));
  const header=document.querySelector('.page-header');
  if(header){const container=document.createElement('div');container.className='polish-aurora-root';container.setAttribute('aria-hidden','true');header.append(container);header.classList.add('polish-aurora-header');createRoot(container).render(<HeaderAurora header={header} />);}
}
