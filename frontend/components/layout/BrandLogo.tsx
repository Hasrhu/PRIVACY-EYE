import React from 'react'
import Link from 'next/link'
import clsx from 'clsx'

interface BrandLogoProps {
  href?: string
  size?: 'sm' | 'md' | 'lg'
  showText?: boolean
  className?: string
}

export const BrandLogo: React.FC<BrandLogoProps> = ({
  href = '/',
  size = 'md',
  showText = true,
  className,
}) => {
  const iconSizes = {
    sm: 'w-7 h-7',
    md: 'w-9 h-9',
    lg: 'w-12 h-12',
  }[size]

  const textSizes = {
    sm: 'text-sm tracking-wider',
    md: 'text-base tracking-wider',
    lg: 'text-xl tracking-widest',
  }[size]

  const content = (
    <div className={clsx('inline-flex items-center gap-2.5 group select-none', className)}>
      {/* Abstract Eye + Shield + AI Geometric Glyph */}
      <div
        className={clsx(
          iconSizes,
          'relative flex items-center justify-center rounded-2xl bg-gradient-to-br from-brand-blue/25 via-brand-violet/20 to-transparent border border-white/20 shadow-glass transition-all duration-300 group-hover:border-brand-blue/50 group-hover:shadow-glow-blue overflow-hidden'
        )}
      >
        {/* Ambient inner glow */}
        <div className="absolute inset-0 bg-radial-gradient from-brand-blue/30 to-transparent opacity-60" />
        
        {/* Shield outline */}
        <svg
          className="w-5 h-5 text-brand-blue group-hover:text-white transition-colors duration-300 relative z-10"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          {/* Shield path */}
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
          {/* Eye aperture iris in center */}
          <circle cx="12" cy="11" r="2.5" fill="currentColor" />
          <path d="M7 11c1.5-2.5 3.5-3.5 5-3.5s3.5 1 5 3.5c-1.5 2.5-3.5 3.5-5 3.5s-3.5-1-5-3.5z" strokeWidth="1.5" />
        </svg>
      </div>

      {showText && (
        <div className="flex flex-col">
          <span className={clsx('font-bold text-white tracking-widest font-sans', textSizes)}>
            PRIVACY<span className="text-brand-blue ml-1.5 font-extrabold">EYE</span>
          </span>
          <span className="text-[9px] uppercase tracking-widest text-white/40 font-mono -mt-0.5">
            AUTHENTICITY ENGINE
          </span>
        </div>
      )}
    </div>
  )

  if (href) {
    return <Link href={href}>{content}</Link>
  }

  return content
}

export default BrandLogo
