import React from 'react'
import clsx from 'clsx'
import { Loader2 } from 'lucide-react'

interface GlassButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  isLoading?: boolean
  icon?: React.ReactNode
  children: React.ReactNode
}

import { GlowEffect } from '../core/glow-effect'

export const GlassButton: React.FC<GlassButtonProps> = ({
  variant = 'primary',
  size = 'md',
  isLoading = false,
  icon,
  children,
  className,
  disabled,
  ...props
}) => {
  const variantStyles = {
    primary: 'btn-primary',
    secondary: 'btn-secondary',
    ghost: 'btn-ghost',
    danger: 'bg-[rgba(249,2,2,0.1)] text-[#F90202] border border-[#F90202]/40 hover:bg-[#F90202]/20',
  }[variant]

  const sizeStyles = {
    sm: 'text-xs px-3 py-1.5 rounded-xl',
    md: 'text-sm px-5 py-2.5 rounded-2xl',
    lg: 'text-base px-7 py-3.5 rounded-2xl font-semibold',
  }[size]

  const buttonElement = (
    <button
      className={clsx(
        variantStyles,
        sizeStyles,
        'transition-all duration-200 inline-flex items-center justify-center gap-2 select-none relative w-full',
        isLoading && 'opacity-70 pointer-events-none',
        className
      )}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <Loader2 className="w-4 h-4 animate-spin text-current" />
      ) : (
        icon && <span className="flex-shrink-0">{icon}</span>
      )}
      <span>{children}</span>
    </button>
  )

  if (variant === 'primary' || variant === 'danger') {
    const isDanger = variant === 'danger'
    const colors = isDanger ? ['#F90202', '#C010ED'] : ['#13D2E8', '#C010ED']
    return (
      <div className={`relative inline-block ${className?.includes('w-full') ? 'w-full' : ''}`}>
        <GlowEffect 
          colors={colors} 
          mode="colorShift" 
          blur="soft" 
          duration={5} 
          scale={1.05} 
        />
        {buttonElement}
      </div>
    )
  }

  return buttonElement
}

export default GlassButton
