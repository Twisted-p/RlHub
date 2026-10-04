import React, { useLayoutEffect, useRef } from 'react';
import { createRoot } from 'react-dom/client';
import StarBorder from './StarBorder';

function GoalBorder({ content }) {
  const holder = useRef(null);
  useLayoutEffect(() => { holder.current.append(content); }, [content]);
  return <StarBorder as="div" className="goal-star-border" color="#55efd5" speed="5s"
    thickness={2} backgroundColor="#0e1a27" textColor="inherit" borderColor="rgba(255,255,255,.08)">
    <div className="goal-star-content" ref={holder} />
  </StarBorder>;
}

const cards = document.getElementById('goals-cards');
if (cards) {
  function mount() {
    cards.querySelectorAll('.goal-card:not(.star-border-mounted)').forEach(card => {
      const content = document.createDocumentFragment();
      while (card.firstChild) content.append(card.firstChild);
      const root = document.createElement('div');
      root.className = 'goal-star-root';
      card.append(root);
      card.classList.add('star-border-mounted');
      createRoot(root).render(<GoalBorder content={content} />);
    });
  }
  new MutationObserver(mount).observe(cards, { childList: true });
  mount();
  const pause = () => document.body.classList.toggle('goal-stars-paused', document.hidden);
  document.addEventListener('visibilitychange', pause);
  pause();
}
