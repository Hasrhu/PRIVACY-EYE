'use client'
import React, { useEffect, useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '@/contexts/AuthContext'
import { GlassNavbar } from '@/components/layout/GlassNavbar'
import { Footer } from '@/components/layout/Footer'
import { Eye, ArrowRight } from 'lucide-react'

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()
  const { isAuthenticated, isLoading } = useAuth()
  const [showFallback, setShowFallback] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => {
      setShowFallback(true)
    }, 800)
    return () => clearTimeout(timer)
  }, [])

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      const target = pathname ? `/auth/login?next=${encodeURIComponent(pathname)}` : '/auth/login'
      router.replace(target)
      const forceTimer = setTimeout(() => {
        if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/auth/')) {
          window.location.href = target
        }
      }, 1000)
      return () => clearTimeout(forceTimer)
    }
  }, [isAuthenticated, isLoading, pathname, router])

  if (isLoading || !isAuthenticated) {
    const loginUrl = pathname ? `/auth/login?next=${encodeURIComponent(pathname)}` : '/auth/login'
    return (
      <div className="flex items-center justify-center min-h-screen bg-canvas text-white">
        <div className="flex flex-col items-center gap-4 p-8 max-w-sm text-center">
          <div className="w-14 h-14 rounded-2xl glass-card flex items-center justify-center border border-brand-blue/30 shadow-glow-blue animate-pulse">
            <Eye className="w-7 h-7 text-brand-blue" />
          </div>
          <div className="space-y-1">
            <p className="text-xs uppercase tracking-widest text-white/70 font-mono font-semibold">
              Securing Session...
            </p>
            <p className="text-xs text-white/50">
              Please sign in to access Privacy Eye features.
            </p>
          </div>

          <Link
            href={loginUrl}
            className="mt-2 px-5 py-2.5 rounded-xl bg-brand-blue text-white font-mono text-xs font-semibold hover:bg-brand-blue/80 transition-all shadow-glow-blue flex items-center gap-2"
          >
            <span>Sign In to Continue</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col bg-canvas text-white selection:bg-brand-blue/30">
      <GlassNavbar />
      <main className="flex-1 pt-28 pb-16 px-4 md:px-8 max-w-7xl mx-auto w-full">
        {children}
      </main>
      <Footer />
    </div>
  )
}
