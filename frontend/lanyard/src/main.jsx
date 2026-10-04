import React, {Component, Suspense, useEffect, useState} from 'react';
import {createRoot} from 'react-dom/client';
import Lanyard from './Lanyard';
import {selectRank} from './rank';
import './dashboard.css';

const icons = import.meta.glob('./ranks/*.png', {eager: true, query: '?url', import: 'default'});
const host = document.getElementById('dashboard-rank-lanyard');
const iconFor = tier => icons[`./ranks/${tier}.png`];
function storedProfile() {
  try { return JSON.parse(localStorage.getItem('rlhub:trackerProfile')); } catch (_) { return null; }
}
class SceneBoundary extends Component {
  state = {failed: false};
  static getDerivedStateFromError() { return {failed: true}; }
  componentDidCatch() { host.dataset.scene = 'fallback'; }
  render() { return this.state.failed ? this.props.fallback : this.props.children; }
}
function App() {
  const [profile, setProfile] = useState(storedProfile);
  const [playlist, setPlaylist] = useState(() => {
    try { const mode = localStorage.getItem('rlhub:lanyardPlaylist'); return ['1v1','2v2','3v3'].includes(mode) ? mode : '2v2'; } catch (_) { return '2v2'; }
  });
  const [visible, setVisible] = useState(!document.hidden && !window.RL_HUB_MOTION_PAUSED);
  const [reduced, setReduced] = useState(matchMedia('(prefers-reduced-motion: reduce)').matches);
  const [front, setFront] = useState(null);
  const rank = selectRank(profile, playlist);
  useEffect(() => {
    const changeMode = event => {if (['1v1','2v2','3v3'].includes(event.detail)) setPlaylist(event.detail);};
    window.addEventListener('rlhub:playlist', changeMode);
    return () => window.removeEventListener('rlhub:playlist', changeMode);
  }, []);
  useEffect(() => {
    const query = matchMedia('(prefers-reduced-motion: reduce)');
    const motion = e => setReduced(e.matches);
    const visibility = () => setVisible(!document.hidden && !window.RL_HUB_MOTION_PAUSED);
    const storage = () => setProfile(storedProfile());
    query.addEventListener('change', motion);
    document.addEventListener('visibilitychange', visibility);
    window.addEventListener('rlhub:motion', visibility);
    window.addEventListener('storage', storage);
    let active = true;
    const poll = async () => {
      if (document.hidden) return;
      try {
        const response = await fetch('./api/dashboard-ranks');
        if (!response.ok) return;
        const data = await response.json();
        if (active && data.profile) setProfile(data.profile);
      } catch (_) { /* Last fetched profile remains available offline. */ }
    };
    poll(); const timer = setInterval(poll, 10000);
    return () => { active = false; clearInterval(timer); query.removeEventListener('change', motion); document.removeEventListener('visibilitychange', visibility); window.removeEventListener('rlhub:motion', visibility); window.removeEventListener('storage', storage); };
  }, []);
  useEffect(() => {
    let active = true;
    const image = new Image();
    image.onload = () => {
      if (!active) return;
      const canvas = document.createElement('canvas'); canvas.width = 600; canvas.height = 900;
      const ctx = canvas.getContext('2d');
      const gradient = ctx.createLinearGradient(0,0,600,900); gradient.addColorStop(0,'#193e50'); gradient.addColorStop(1,'#061020');
      ctx.fillStyle = gradient; ctx.fillRect(0,0,600,900);
      ctx.fillStyle = '#59f0d4'; ctx.fillRect(40,40,520,5);
      ctx.font = 'bold 44px sans-serif'; ctx.textAlign = 'center'; ctx.fillText('RL HUB',300,115);
      const scale = Math.min(470/image.width,470/image.height);
      ctx.drawImage(image,300-image.width*scale/2,230+(470-image.height*scale)/2,image.width*scale,image.height*scale);
      ctx.fillStyle = '#f3f8ff'; ctx.font = 'bold 28px sans-serif'; ctx.fillText(rank.known ? rank.rank.replace(/ Division .*/, '') : 'READY TO PLAY',300,760);
      ctx.fillStyle = '#9fbbc9'; ctx.font = '26px sans-serif'; ctx.fillText(`${playlist}${rank.mmr === null ? '' : `  ·  ${rank.mmr} MMR`}`,300,815);
      setFront(canvas.toDataURL());
    };
    image.src = iconFor(rank.tier);
    return () => {active = false;};
  }, [rank.rank, rank.mmr, rank.tier, rank.known, playlist]);
  const fallback = <div className="rank-card-static"><img src={iconFor(rank.tier)} alt=""/><strong>{rank.known ? rank.rank : 'RL Hub'}</strong></div>;
  host.dataset.rank = rank.rank;
  host.dataset.tier = rank.tier;
  return <>
    <div className="rank-mode" role="group" aria-label="Rank på kortet">{['1v1','2v2','3v3'].map(mode => <button key={mode} type="button" aria-pressed={mode === playlist} onClick={() => {setPlaylist(mode); try {localStorage.setItem('rlhub:lanyardPlaylist',mode);} catch (_) {}window.dispatchEvent(new CustomEvent('rlhub:playlist',{detail:mode}));}}>{mode}</button>)}</div>
    <div className={`rank-scene ${reduced ? '' : 'rank-scene-enter'}`} aria-hidden="true">
      {visible && front && !reduced ? <SceneBoundary fallback={fallback}><Suspense fallback={fallback}><Lanyard position={[0,0,20]} fov={12} gravity={[0,-40,0]} frontImage={front} backImage={front} imageFit="cover" lanyardWidth={1}/></Suspense></SceneBoundary> : fallback}
    </div>
    <div className="rank-caption"><strong>{rank.rank}</strong><span>{rank.name ? `${rank.name} · ` : ''}{playlist}{rank.mmr === null ? '' : ` · ${rank.mmr} MMR`}</span>{!rank.known ? <a href="./profile.html">Hent rank →</a> : <small>Sist hentede rank</small>}</div>
  </>;
}
createRoot(host).render(<App/>);
