'use client'
import React, { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Cookies from 'js-cookie'
import { GlassNavbar } from '@/components/layout/GlassNavbar'
import { Footer } from '@/components/layout/Footer'
import { Eye } from 'lucide-react'

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  useEffect(() => {
    const token = Cookies.get('access_token')
    if (!token) {
      router.push('/auth/login')
    } else {
      setIsAuthenticated(true)
    }
  }, [router])

  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-canvas">
        <div className="flex flex-col items-center gap-3">
          <div className="w-12 h-12 rounded-2xl glass-card flex items-center justify-center border border-brand-blue/30 shadow-glow-blue animate-pulse">
            <Eye className="w-6 h-6 text-brand-blue" />
          </div>
          <p className="text-xs uppercase tracking-widest text-white/50 font-mono">
            Securing Session...
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col bg-canvas text-white selection:bg-brand-blue/30">
      {/* Floating Glass Navigation */}
      <GlassNavbar />

      {/* Main Page Canvas with Top Clearance for Floating Navbar */}
      <main className="flex-1 pt-28 pb-16 px-4 md:px-8 max-w-7xl mx-auto w-full">
        {children}
      </main>

      {/* Minimal Cybersecurity Footer */}
      <Footer />
    </div>
  )
}
