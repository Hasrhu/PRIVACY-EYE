'use client'
import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { ArrowLeft, AlertTriangle, Download, FileText, Shield, CheckCircle } from 'lucide-react'
import { format } from 'date-fns'
import { analysisApi, reportsApi, getErrorMessage } from '@/lib/api'
import type { Analysis, Report } from '@/types'
import { RISK_CONFIG } from '@/types'
import toast from 'react-hot-toast'
import Cookies from 'js-cookie'

export default function AnalysisDetailPage() {
  const { id }  = useParams<{ id: string }>()
  const router  = useRouter()
  const [a, setA]         = useState<Analysis | null>(null)
  const [report, setReport] = useState<Report | null>(null)
  const [genLoading, setGenLoading] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!Cookies.get('access_token')) { router.push('/auth/login'); return }
    analysisApi.getAnalysis(id).then(r => setA(r.data)).catch(() => router.push('/dashboard/history')).finally(() => setLoading(false))
    reportsApi.get(id).then(r => setReport(r.data)).catch(() => {})
  }, [id, router])

  const genReport = async () => {
    setGenLoading(true)
    try { const r = await reportsApi.generate(id); setReport(r.data); toast.success('Report generated!') }
    catch (e) { toast.error(getErrorMessage(e)) }
    finally { setGenLoading(false) }
  }

  const downloadReport = async () => {
    try {
      const r = await reportsApi.downloadJson(id)
      const url = URL.createObjectURL(r.data)
      const el = document.createElement('a'); el.href=url; el.download=`privacy-eye-report-${id.slice(0,8)}.json`; el.click()
      URL.revokeObjectURL(url)
    } catch (e) { toast.error(getErrorMessage(e)) }
  }

  if (loading || !a) return (
    <div className="flex items-center justify-center h-screen">
      <div className="spinner w-8 h-8" style={{ borderTopColor:'#dc2626' }} />
    </div>
  )

  const risk = RISK_CONFIG[a.risk_level || 'UNDETERMINED']
  const bc   = `badge-${(a.risk_level||'undetermined').toLowerCase()}`

  return (
    <div className="p-8" style={{ background:'#0a0a0a', minHeight:'100vh' }}>
      <Link href="/dashboard/history" className="btn-ghost-red mb-6 inline-flex">
        <ArrowLeft className="w-4 h-4"/> Back to History
      </Link>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Main result */}
        <div className="lg:col-span-2 space-y-5">
          {/* Risk banner */}
          <motion.div className="rounded-xl p-6" initial={{opacity:0,y:16}} animate={{opacity:1,y:0}}
            style={{ background: a.risk_level==='CRITICAL'||a.risk_level==='HIGH' ? 'rgba(220,38,38,0.08)' : '#111111', border:`1px solid ${risk.color}40` }}>
            <div className="flex items-center gap-4">
              <span className="text-4xl">{risk.emoji}</span>
              <div>
                <span className={bc}>{risk.label}</span>
                <h2 className="text-2xl font-black text-white mt-1">{a.original_filename}</h2>
                <p className="text-xs font-mono mt-1" style={{color:'#6b7280'}}>
                  {a.media_type} · {format(new Date(a.created_at),'MMM d yyyy, HH:mm:ss')}
                </p>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-4 mt-5">
              {[
                ['Synthetic Probability', a.synthetic_probability!=null?`${(a.synthetic_probability*100).toFixed(1)}%`:'N/A'],
                ['Confidence',           a.confidence!=null?`${(a.confidence*100).toFixed(0)}%`:'N/A'],
                ['Processing Time',      a.processing_ms?`${a.processing_ms}ms`:'N/A'],
              ].map(([k,v])=>(
                <div key={k} className="p-3 rounded-lg" style={{background:'#1a1a1a'}}>
                  <div className="text-xs font-bold uppercase tracking-wide2 mb-1" style={{color:'#6b7280'}}>{k}</div>
                  <div className="font-display text-xl" style={{color:risk.color}}>{v as string}</div>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Explanation */}
          {a.explanation && (
            <div className="card p-5">
              <p className="section-label mb-3">Analysis Summary</p>
              <p className="text-sm leading-relaxed" style={{color:'#9ca3af'}}>{a.explanation}</p>
            </div>
          )}

          {/* Signals */}
          {a.signals.length > 0 && (
            <div className="card p-5">
              <p className="section-label mb-4">Detected Signals ({a.signals.length})</p>
              <div className="space-y-3">
                {a.signals.map(s => (
                  <div key={s.signal_key} className="flex items-start gap-3 p-4 rounded-xl" style={{background:'#1a1a1a'}}>
                    <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" style={{color: s.severity==='high'?'#dc2626':s.severity==='medium'?'#f59e0b':'#6b7280'}}/>
                    <div className="flex-1">
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-sm font-bold text-white">{s.signal_label}</p>
                        {s.score!=null && <span className="text-xs font-mono font-bold" style={{color:'#dc2626'}}>{(s.score*100).toFixed(0)}%</span>}
                      </div>
                      {s.description && <p className="text-xs mt-1 leading-relaxed" style={{color:'#6b7280'}}>{s.description}</p>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right panel */}
        <div className="space-y-5">
          {/* File info */}
          <div className="card p-5">
            <p className="section-label mb-4">File Information</p>
            <div className="space-y-2.5">
              {[
                ['Filename',    a.original_filename],
                ['SHA-256',     a.file_sha256?`${a.file_sha256.slice(0,12)}…`:'N/A'],
                ['Size',        `${(a.file_size_bytes/1024).toFixed(1)} KB`],
                ['MIME Type',   a.mime_type||'N/A'],
                ['Media Deleted', a.media_deleted?'✓ Immediately':'No'],
              ].map(([k,v])=>(
                <div key={k} className="flex justify-between text-xs" style={{borderBottom:'1px solid rgba(255,255,255,0.04)', paddingBottom:'8px'}}>
                  <span style={{color:'#6b7280'}}>{k}</span>
                  <span className="font-mono text-right max-w-[140px] truncate" style={{color:'#9ca3af'}}>{v as string}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Report */}
          {report ? (
            <div className="card-red p-5">
              <div className="flex items-center gap-2 mb-4">
                <CheckCircle className="w-4 h-4" style={{color:'#10b981'}}/>
                <p className="section-label" style={{color:'#10b981'}}>Report Ready</p>
              </div>
              {report.summary && <p className="text-xs leading-relaxed mb-4" style={{color:'#9ca3af'}}>{report.summary}</p>}
              {report.recommendations && (
                <div className="text-xs leading-relaxed whitespace-pre-line mb-4" style={{color:'#6b7280'}}>{report.recommendations}</div>
              )}
              <button onClick={downloadReport} className="btn-outline w-full justify-center text-xs py-2.5" style={{width:'100%'}}>
                <Download className="w-3.5 h-3.5"/> Download JSON
              </button>
            </div>
          ) : (
            <div className="card p-5">
              <div className="flex items-center gap-2 mb-3">
                <FileText className="w-4 h-4" style={{color:'#dc2626'}}/>
                <p className="section-label">Evidence Report</p>
              </div>
              <p className="text-xs mb-4" style={{color:'#6b7280'}}>Generate an AI-powered evidence report explaining the findings in plain language.</p>
              <button onClick={genReport} disabled={genLoading} className="btn-red w-full justify-center text-xs py-2.5" style={{width:'100%'}}>
                {genLoading ? <><span className="spinner w-3.5 h-3.5"/>Generating…</> : <><Shield className="w-3.5 h-3.5"/>Generate Report</>}
              </button>
            </div>
          )}

          {/* Privacy note */}
          <div className="p-4 rounded-xl text-xs" style={{background:'rgba(220,38,38,0.05)', border:'1px solid rgba(220,38,38,0.15)', color:'#6b7280', lineHeight:'1.6'}}>
            Results are probabilistic indicators only. Privacy Eye does not claim 100% accuracy. Do not use as sole basis for legal action.
          </div>
        </div>
      </div>
    </div>
  )
}
