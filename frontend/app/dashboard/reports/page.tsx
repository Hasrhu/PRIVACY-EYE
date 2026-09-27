'use client'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { FileText, Download, RefreshCw } from 'lucide-react'
import { format } from 'date-fns'
import { analysisApi, reportsApi, getErrorMessage } from '@/lib/api'
import type { Analysis } from '@/types'
import { RISK_CONFIG } from '@/types'
import toast from 'react-hot-toast'
import Link from 'next/link'
import Cookies from 'js-cookie'

export default function ReportsPage() {
  const router = useRouter()
  const [items, setItems]   = useState<Analysis[]>([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState<string | null>(null)

  useEffect(() => {
    if (!Cookies.get('access_token')) { router.push('/auth/login'); return }
    analysisApi.getHistory(1, 50).then(r => setItems(r.data.items.filter((a: Analysis) => a.status === 'COMPLETE'))).finally(() => setLoading(false))
  }, [router])

  const generate = async (id: string) => {
    setGenerating(id)
    try { await reportsApi.generate(id); toast.success('Report generated!') }
    catch (e) { toast.error(getErrorMessage(e)) }
    finally { setGenerating(null) }
  }

  const download = async (id: string) => {
    try {
      const r = await reportsApi.downloadJson(id)
      const url = URL.createObjectURL(r.data)
      const el = document.createElement('a'); el.href = url; el.download = `privacy-eye-report-${id.slice(0, 8)}.json`; el.click()
      URL.revokeObjectURL(url)
    } catch (e) { toast.error(getErrorMessage(e)) }
  }

  return (
    <div className="p-8" style={{ background: '#0a0a0a', minHeight: '100vh' }}>
      <div className="mb-8">
        <p className="section-label mb-1">Evidence</p>
        <h1 className="text-3xl font-black text-white">Reports</h1>
        <p className="text-sm mt-1" style={{ color: '#6b7280' }}>Generate and download AI-powered evidence reports for completed analyses.</p>
      </div>

      {loading ? (
        <div className="flex justify-center py-20"><div className="spinner w-8 h-8" style={{ borderTopColor: '#dc2626' }} /></div>
      ) : items.length === 0 ? (
        <div className="card p-16 text-center">
          <FileText className="w-10 h-10 mx-auto mb-3" style={{ color: '#374151' }} />
          <p className="font-semibold" style={{ color: '#6b7280' }}>No completed analyses yet.</p>
          <Link href="/dashboard" className="btn-red mt-4 inline-flex">Go Scan Something</Link>
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((a, i) => {
            const risk = RISK_CONFIG[a.risk_level || 'UNDETERMINED']
            const bc   = `badge-${(a.risk_level || 'undetermined').toLowerCase()}`
            return (
              <motion.div key={a.id} className="card p-5 flex items-center gap-4"
                initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }}>
                <div className="text-2xl">{risk.emoji}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-0.5">
                    <span className="font-bold text-white truncate text-sm">{a.original_filename}</span>
                    <span className={bc}>{risk.label}</span>
                  </div>
                  <p className="text-xs font-mono" style={{ color: '#6b7280' }}>
                    {a.media_type} · {format(new Date(a.created_at), 'MMM d, yyyy HH:mm')}
                    {a.synthetic_probability != null && ` · ${(a.synthetic_probability * 100).toFixed(1)}% synthetic probability`}
                  </p>
                </div>
                <div className="flex gap-2 flex-shrink-0">
                  <button onClick={() => generate(a.id)} disabled={generating === a.id} className="btn-red text-xs py-2 px-4">
                    {generating === a.id ? <><RefreshCw className="w-3.5 h-3.5 animate-spin" /> Generating…</> : <><FileText className="w-3.5 h-3.5" /> Generate</>}
                  </button>
                  <button onClick={() => download(a.id)} className="btn-outline text-xs py-2 px-3">
                    <Download className="w-3.5 h-3.5" />
                  </button>
                </div>
              </motion.div>
            )
          })}
        </div>
      )}
    </div>
  )
}
