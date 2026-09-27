'use client'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { Eye, LayoutDashboard, Clock, FileText, Settings, LogOut, Shield, Camera } from 'lucide-react'
import { authApi } from '@/lib/api'
import clsx from 'clsx'

const NAV = [
  { href: '/dashboard',            icon: LayoutDashboard, label: 'Dashboard' },
  { href: '/dashboard/live-scan',   icon: Camera,          label: 'Live Camera', badge: 'LIVE' },
  { href: '/dashboard/history',    icon: Clock,           label: 'Scan History' },
  { href: '/dashboard/reports',    icon: FileText,        label: 'Reports' },
  { href: '/dashboard/settings',   icon: Settings,        label: 'Settings' },
]

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const router   = useRouter()

  const handleLogout = () => { authApi.logout(); router.push('/') }

  return (
    <div className="flex min-h-screen" style={{ background: '#0a0a0a' }}>
      {/* ── Sidebar ─────────────────────────────────────────────── */}
      <aside className="w-56 flex-shrink-0 flex flex-col fixed h-full z-30" style={{ background: '#111111', borderRight: '1px solid rgba(255,255,255,0.04)' }}>
        {/* Logo */}
        <Link href="/dashboard" className="flex items-center gap-3 px-5 py-5" style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
          <div className="w-7 h-7 rounded flex items-center justify-center" style={{ background: '#dc2626' }}>
            <Eye className="w-4 h-4 text-white" />
          </div>
          <span className="font-display text-lg tracking-wider text-white">PRIVACY EYE</span>
        </Link>

        {/* Status pill */}
        <div className="mx-4 mt-4 flex items-center gap-2.5 px-3 py-2.5 rounded-lg" style={{ background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)' }}>
          <span className="dot-red" style={{ background: '#10b981', boxShadow: 'none', animation: 'none', width: 7, height: 7, borderRadius: '50%', display: 'inline-block' }} />
          <span className="text-xs font-bold uppercase tracking-wide2" style={{ color: '#10b981' }}>Protection Active</span>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-0.5">
          {NAV.map(item => {
            const active = pathname === item.href
            return (
              <Link key={item.href} href={item.href}
                className={clsx('flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-semibold transition-all', active ? 'text-white' : 'text-gray-500 hover:text-white hover:bg-white/3')}
                style={active ? { background: 'rgba(220,38,38,0.12)', color: '#fff', borderLeft: '3px solid #dc2626', paddingLeft: '9px' } : {}}
              >
                <item.icon className="w-4 h-4 flex-shrink-0" style={active ? { color: '#dc2626' } : {}} />
                <span className="flex-1">{item.label}</span>
                {item.badge && (
                  <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-red-600/20 text-red-400 font-bold border border-red-600/40 animate-pulse">
                    {item.badge}
                  </span>
                )}
              </Link>
            )
          })}
        </nav>

        {/* Footer */}
        <div className="p-4" style={{ borderTop: '1px solid rgba(255,255,255,0.04)' }}>
          <button onClick={handleLogout} className="btn-ghost-red w-full text-sm" style={{ justifyContent: 'flex-start' }}>
            <LogOut className="w-4 h-4" /> Sign Out
          </button>
        </div>
      </aside>

      {/* ── Content ─────────────────────────────────────────────── */}
      <main className="flex-1 ml-56 min-h-screen">
        {children}
      </main>
    </div>
  )
}
