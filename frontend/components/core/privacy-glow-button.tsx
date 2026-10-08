'use client';

import React from 'react';
import { GlowEffect } from './glow-effect';

interface PrivacyGlowButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
  variant?: 'primary' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  icon?: React.ReactNode;
  fullWidth?: boolean;
}

export function PrivacyGlowButton({
  children,
  variant = 'primary',
  size = 'md',
  icon,
  fullWidth = false,
  className = '',
  ...props
}: PrivacyGlowButtonProps) {
  const isDanger = variant === 'danger';
  const colors = isDanger ? ['#F90202', '#C010ED'] : ['#13D2E8', '#C010ED'];
  
  const sizeClasses = {
    sm: 'px-4 py-2 text-xs',
    md: 'px-6 py-3 text-sm',
    lg: 'px-8 py-4 text-base',
  };

  return (
    <div className={`relative inline-block ${fullWidth ? 'w-full' : ''} ${className}`}>
      <GlowEffect 
        colors={colors} 
        mode="colorShift" 
        blur="soft" 
        duration={5} 
        scale={1.05} 
      />
      <button
        className={`
          relative w-full flex items-center justify-center gap-2 
          bg-[#050505] text-white font-semibold tracking-wide
          border border-[rgba(19,210,232,0.35)] rounded-xl
          hover:bg-[rgba(19,210,232,0.05)] hover:border-[rgba(19,210,232,0.5)]
          focus:outline-none focus:ring-2 focus:ring-[#13D2E8]/50
          active:scale-[0.98]
          transition-all duration-200 ease-in-out
          disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100
          ${sizeClasses[size]}
          ${isDanger ? 'border-[rgba(249,2,2,0.35)] hover:bg-[rgba(249,2,2,0.05)] hover:border-[rgba(249,2,2,0.5)] focus:ring-[#F90202]/50' : ''}
        `}
        {...props}
      >
        {icon && <span className="flex-shrink-0">{icon}</span>}
        {children}
      </button>
    </div>
  );
}
