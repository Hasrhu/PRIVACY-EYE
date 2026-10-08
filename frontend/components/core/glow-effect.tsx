'use client';

import React, { useEffect, useState } from 'react';

interface GlowEffectProps {
  colors?: string[];
  mode?: 'colorShift' | 'pulse' | 'static';
  blur?: 'soft' | 'medium' | 'strong';
  duration?: number;
  scale?: number;
  className?: string;
}

export function GlowEffect({
  colors = ['#13D2E8', '#C010ED'],
  mode = 'colorShift',
  blur = 'soft',
  duration = 5,
  scale = 1,
  className = '',
}: GlowEffectProps) {
  const [isReducedMotion, setIsReducedMotion] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setIsReducedMotion(mediaQuery.matches);

    const handleChanges = (e: MediaQueryListEvent) => {
      setIsReducedMotion(e.matches);
    };

    mediaQuery.addEventListener('change', handleChanges);
    return () => mediaQuery.removeEventListener('change', handleChanges);
  }, []);

  const blurValue = blur === 'soft' ? '30px' : blur === 'medium' ? '50px' : '80px';
  const effectiveMode = isReducedMotion ? 'static' : mode;
  
  // Base style
  const baseStyle: React.CSSProperties = {
    position: 'absolute',
    inset: 0,
    zIndex: -1,
    borderRadius: 'inherit',
    filter: `blur(${blurValue})`,
    opacity: 0.6,
    transform: `scale(${scale})`,
    transition: 'all 0.3s ease',
  };

  if (effectiveMode === 'static') {
    return (
      <div 
        className={`pointer-events-none ${className}`}
        style={{
          ...baseStyle,
          background: `linear-gradient(135deg, ${colors[0]} 0%, ${colors[1] || colors[0]} 100%)`,
        }}
      />
    );
  }

  return (
    <div className={`pointer-events-none overflow-visible ${className}`} style={{ position: 'absolute', inset: 0, zIndex: -1 }}>
      <div
        style={{
          ...baseStyle,
          background: `linear-gradient(270deg, ${colors.join(', ')}, ${colors[0]})`,
          backgroundSize: '200% 200%',
          animation: `shiftColors ${duration}s ease infinite`,
        }}
      />
      <style dangerouslySetInnerHTML={{
        __html: `
          @keyframes shiftColors {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
          }
        `
      }} />
    </div>
  );
}
