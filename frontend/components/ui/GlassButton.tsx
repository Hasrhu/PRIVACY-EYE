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
    danger: 'bg-status-danger/20 text-status-danger border border-status-danger/40 hover:bg-status-danger/30',
  }[variant]

  const sizeStyles = {
    sm: 'text-xs px-3 py-1.5 rounded-xl',
    md: 'text-sm px-5 py-2.5 rounded-2xl',
    lg: 'text-base px-7 py-3.5 rounded-2xl font-semibold',
  }[size]

  return (
    <button
      className={clsx(
        variantStyles,
        sizeStyles,
        'transition-all duration-200 inline-flex items-center justify-center gap-2 select-none',
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
}

export default GlassButton
