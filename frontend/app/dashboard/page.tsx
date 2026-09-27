'use client'
import { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { Image, Video, Music, Upload, RefreshCw, FileText, Trash2, AlertTriangle, CheckCircle, HelpCircle, Eye, Camera } from 'lucide-react'
import { format } from 'date-fns'
import { authApi, analysisApi, getErrorMessage } from '@/lib/api'
import type { User, DashboardStats, Analysis } from '@/types'
import { RISK_CONFIG } from '@/types'
import toast from 'react-hot-toast'
import ScannerModal from '@/components/ScannerModal'
import Cookies from 'js-cookie'
import clsx from 'clsx'

export default function DashboardPage() {
  const router = useRouter()
  const [user, setUser]       = useState<User | null>(null)
  const [stats, setStats]     = useState<DashboardStats | null>(null)
  const [history, setHistory] = useState<Analysis[]>([])
  const [loading, setLoading] = useState(true)
  const [scannerOpen, setScannerOpen]   = useState(false)
  const [scannerType, setScannerType]   = useState<'IMAGE'|'VIDEO'|'AUDIO'>('IMAGE')

  const fetchData = useCallback(async () => {
    try {
      const [uRes, sRes, hRes] = await Promise.all([
        authApi.me(),
        analysisApi.getStats(),
        analysisApi.getHistory(1, 8),
      ])
      setUser(uRes.data)
      setStats(sRes.data)
      setHistory(hRes.data.items)
    } catch { router.push('/auth/login') }
    finally  { setLoading(false) }
  }, [router])

  useEffect(() => {
    if (!Cookies.get('access_token')) { router.push('/auth/login'); return }
    fetchData()
  }, [fetchData, router])

  const openScanner = (t: 'IMAGE'|'VIDEO'|'AUDIO') => { setScannerType(t); setScannerOpen(true) }
  const onScanDone  = (a: Analysis) => { setHistory(p => [a, ...p.slice(0,7)]); fetchData() }

  const handleDelete = async (id: string) => {
    try { await analysisApi.deleteAnalysis(id); setHistory(p => p.filter(a => a.id !== id)); toast.success('Deleted') }
    catch (e) { toast.error(getErrorMessage(e)) }
  }

  if (loading) return (
    <div className="flex items-center justify-center h-screen">
      <div className="text-center space-y-4">
        <div className="scan-ring w-14 h-14 mx-auto">
          <Eye className="w-7 h-7" style={{ color: '#dc2626' }} />
        </div>
        <p className="text-xs font-semibold uppercase tracking-wide3" style={{ color: '#6b7280' }}>Loading Privacy Eye…</p>
      </div>
    </div>
  )

  const pct = stats ? Math.min(100, (stats.scans_this_month / stats.scans_limit) * 100) : 0

  return (
    <div className="p-8" style={{ background: '#0a0a0a', minHeight: '100vh' }}>
      {/* Header */}
      <div className="flex items-center justify-between mb-10">
        <div>
          <p className="section-label mb-1">Overview</p>
          <h1 className="text-3xl font-black text-white">Dashboard</h1>
          {user && <p className="text-sm mt-1" style={{ color: '#6b7280' }}>Welcome back, <span className="text-white font-semibold">{user.full_name?.split(' ')[0] || user.email}</span></p>}
        </div>
        <button onClick={fetchData} className="btn-ghost-red"><RefreshCw className="w-4 h-4" /></button>
      </div>

      {/* Scan usage bar */}
      {stats && (
        <div className="card p-5 mb-8 flex items-center gap-6">
          <div className="flex-1">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold uppercase tracking-wide2" style={{ color: '#9ca3af' }}>Monthly Scans Used</span>
              <span className="text-xs font-mono font-bold text-white">{stats.scans_this_month} / {stats.scans_limit}</span>
            </div>
            <div className="h-1.5 rounded-full overflow-hidden" style={{ background: '#1a1a1a' }}>
              <div className="h-full rounded-full transition-all duration-500" style={{ width: `${pct}%`, background: pct > 80 ? '#dc2626' : '#10b981' }} />
            </div>
          </div>
          <Link href="/auth/register" className="btn-red text-xs py-2 px-4">Upgrade</Link>
        </div>
      )}

      {/* Stat cards */}
      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-10">
          {[
            { label: 'Total Scanned',  value: stats.total_scanned, icon: Eye,           color: '#9ca3af',  bg: '#1a1a1a' },
            { label: 'Suspicious',     value: stats.suspicious,    icon: AlertTriangle,  color: '#f59e0b',  bg: 'rgba(245,158,11,0.08)' },
            { label: 'Low Risk',       value: stats.low_risk,      icon: CheckCircle,    color: '#10b981',  bg: 'rgba(16,185,129,0.08)' },
            { label: 'Undetermined',   value: stats.undetermined,  icon: HelpCircle,     color: '#6b7280',  bg: '#1a1a1a' },
          ].map((c, i) => (
            <motion.div key={c.label} className="card p-5" initial={{ opacity:0, y:16 }} animate={{ opacity:1, y:0 }} transition={{ delay: i*0.07 }}>
              <div className="w-9 h-9 rounded-lg flex items-center justify-center mb-3" style={{ background: c.bg }}>
                <c.icon className="w-5 h-5" style={{ color: c.color }} />
              </div>
              <div className="font-display text-4xl" style={{ color: c.color === '#9ca3af' ? '#fff' : c.color }}>{c.value}</div>
              <div className="text-xs font-semibold uppercase tracking-wide2 mt-1" style={{ color: '#6b7280' }}>{c.label}</div>
            </motion.div>
          ))}
        </div>
      )}

      {/* Live Camera Authenticity Banner */}
      <div className="card p-6 mb-10 border border-red-600/30 flex flex-col md:flex-row items-center justify-between gap-6" style={{ background: 'linear-gradient(90deg, rgba(220,38,38,0.12) 0%, rgba(17,17,17,1) 100%)' }}>
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-red-600 animate-pulse" />
            <span className="text-xs font-mono uppercase tracking-widest text-red-500 font-bold">New Biometric Defense</span>
          </div>
          <h2 className="font-display text-2xl text-white tracking-wide">LIVE CAMERA FACE AUTHENTICITY SCAN</h2>
          <p className="text-xs text-gray-400 max-w-xl">
            Real-time multi-signal analysis using YuNet deep landmarks, Moiré screen rasterization detection, face-swap boundary inspection, and active challenge liveness.
          </p>
        </div>
        <Link href="/dashboard/live-scan" className="btn-red text-xs py-3 px-6 flex items-center gap-2 flex-shrink-0">
          <Camera className="w-4 h-4" /> Open Live Camera
        </Link>
      </div>

      {/* Quick Scan */}
      <div className="mb-10">
        <p className="section-label mb-4">Quick Scan</p>
        <div className="grid grid-cols-3 gap-4">
          {[
            { type: 'IMAGE' as const, label: 'Scan Image', Icon: Image,  sub: 'JPG · PNG · WEBP' },
            { type: 'VIDEO' as const, label: 'Scan Video', Icon: Video,  sub: 'MP4 · MOV · WEBM' },
            { type: 'AUDIO' as const, label: 'Scan Audio', Icon: Music,  sub: 'MP3 · WAV · FLAC' },
          ].map(a => (
            <motion.button key={a.type} onClick={() => openScanner(a.type)}
              className="card-hover p-7 text-left group"
              whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.98 }}
            >
              <div className="w-11 h-11 rounded-xl flex items-center justify-center mb-4 transition-colors" style={{ background: 'rgba(220,38,38,0.1)' }}>
                <a.Icon className="w-5 h-5 transition-colors group-hover:text-white" style={{ color: '#dc2626' }} />
              </div>
              <div className="text-xs font-bold uppercase tracking-wide2 mb-1" style={{ color: '#dc2626' }}>UPLOAD & ANALYZE</div>
              <div className="font-bold text-white">{a.label}</div>
              <div className="text-xs mt-1 font-mono" style={{ color: '#6b7280' }}>{a.sub}</div>
              <div className="flex items-center gap-1.5 mt-4 text-xs font-semibold opacity-0 group-hover:opacity-100 transition-opacity" style={{ color: '#dc2626' }}>
                <Upload className="w-3.5 h-3.5" /> Click to upload
              </div>
            </motion.button>
          ))}
        </div>
      </div>

      {/* Recent scans table */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <p className="section-label">Recent Scans</p>
          <Link href="/dashboard/history" className="btn-ghost-red text-xs">View all →</Link>
        </div>

        {history.length === 0 ? (
          <div className="card p-14 text-center">
            <Eye className="w-10 h-10 mx-auto mb-3" style={{ color: '#374151' }} />
            <p className="text-sm font-semibold" style={{ color: '#6b7280' }}>No scans yet.</p>
            <p className="text-xs mt-1" style={{ color: '#374151' }}>Upload a file above to get started.</p>
          </div>
        ) : (
          <div className="card overflow-hidden">
            <table className="w-full">
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                  {['File', 'Type', 'Risk', 'Confidence', 'Date', ''].map(h => (
                    <th key={h} className="text-left px-5 py-3 text-xs font-bold uppercase tracking-wide2" style={{ color: '#374151' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {history.map(a => {
                  const risk = RISK_CONFIG[a.risk_level || 'UNDETERMINED']
                  const badgeClass = `badge-${(a.risk_level || 'undetermined').toLowerCase()}`
                  return (
                    <tr key={a.id} className="group transition-colors" style={{ borderBottom: '1px solid rgba(255,255,255,0.02)' }}
                      onMouseEnter={e => (e.currentTarget.style.background = '#111111')}
                      onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                    >
                      <td className="px-5 py-3.5">
                        <div className="flex items-center gap-2">
                          {a.media_type === 'IMAGE' && <Image className="w-3.5 h-3.5 flex-shrink-0" style={{ color: '#6b7280' }} />}
                          {a.media_type === 'VIDEO' && <Video className="w-3.5 h-3.5 flex-shrink-0" style={{ color: '#6b7280' }} />}
                          {a.media_type === 'AUDIO' && <Music className="w-3.5 h-3.5 flex-shrink-0" style={{ color: '#6b7280' }} />}
                          <span className="text-sm text-white truncate max-w-[160px] font-medium">{a.original_filename}</span>
                        </div>
                      </td>
                      <td className="px-5 py-3.5 text-xs font-mono" style={{ color: '#6b7280' }}>{a.media_type}</td>
                      <td className="px-5 py-3.5"><span className={badgeClass}>{risk.emoji} {risk.label}</span></td>
                      <td className="px-5 py-3.5 text-xs font-mono" style={{ color: '#9ca3af' }}>
                        {a.confidence != null ? `${(a.confidence*100).toFixed(0)}%` : '—'}
                      </td>
                      <td className="px-5 py-3.5 text-xs font-mono" style={{ color: '#6b7280' }}>{format(new Date(a.created_at), 'MMM d, HH:mm')}</td>
                      <td className="px-5 py-3.5">
                        <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                          <Link href={`/dashboard/analysis/${a.id}`} className="btn-ghost-red text-xs py-1 px-2">
                            <FileText className="w-3.5 h-3.5" />
                          </Link>
                          <button onClick={() => handleDelete(a.id)} className="btn-ghost-red text-xs py-1 px-2" style={{ color: '#dc2626' }}>
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {scannerOpen && (
        <ScannerModal type={scannerType} onClose={() => setScannerOpen(false)} onComplete={onScanDone} />
      )}
    </div>
  )
}
