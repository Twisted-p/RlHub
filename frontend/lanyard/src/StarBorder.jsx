'use client';

import './StarBorder.css';

const StarBorder = ({
  as: Component = 'button',
  className = '',
  color = 'white',
  speed = '6s',
  thickness = 1,
  backgroundColor = '#000000',
  textColor = '#ffffff',
  borderColor = '#222222',
  children,
  ...rest
}) => {
  return (
    <Component
      className={`star-border-container ${className}`}
      style={{ padding: `${thickness}px 0`, ...rest.style }}
      {...rest}
    >
      <div className="border-gradient-bottom" aria-hidden="true"
        style={{ background: `radial-gradient(circle, ${color}, transparent 10%)`, animationDuration: speed }} />
      <div className="border-gradient-top" aria-hidden="true"
        style={{ background: `radial-gradient(circle, ${color}, transparent 10%)`, animationDuration: speed }} />
      <div className="inner-content" style={{ background: backgroundColor, color: textColor, borderColor }}>
        {children}
      </div>
    </Component>
  );
};

export default StarBorder;
