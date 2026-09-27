'use client'
import { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { Image, Video, Music, Trash2, FileText, Search } from 'lucide-react'
import { format } from 'date-fns'
import { analysisApi, getErrorMessage } from '@/lib/api'
import type { Analysis } from '@/types'
import { RISK_CONFIG } from '@/types'
import toast from 'react-hot-toast'
import Link from 'next/link'
import Cookies from 'js-cookie'

export default function HistoryPage() {
  const router = useRouter()
  const [items, setItems] = useState<Analysis[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage]   = useState(1)
  const [filter, setFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const PER = 15

  const load = useCallback(async (p: number, mt?: string) => {
    setLoading(true)
    try {
      const res = await analysisApi.getHistory(p, PER, mt || undefined)
      setItems(res.data.items); setTotal(res.data.total)
    } catch { router.push('/auth/login') }
    finally { setLoading(false) }
  }, [router])

  useEffect(() => {
    if (!Cookies.get('access_token')) { router.push('/auth/login'); return }
    load(page, filter)
  }, [load, page, filter, router])

  const handleDelete = async (id: string) => {
    try { await analysisApi.deleteAnalysis(id); setItems(p => p.filter(a => a.id !== id)); setTotal(t => t-1); toast.success('Deleted') }
    catch (e) { toast.error(getErrorMessage(e)) }
  }

  const totalPages = Math.ceil(total / PER)

  return (
    <div className="p-8" style={{ background:'#0a0a0a', minHeight:'100vh' }}>
      <div className="flex items-center justify-between mb-8">
        <div>
          <p className="section-label mb-1">All Scans</p>
          <h1 className="text-3xl font-black text-white">Scan History</h1>
          <p className="text-sm mt-1" style={{ color:'#6b7280' }}>{total} total analyses</p>
        </div>
        <div className="flex gap-2">
          {['', 'IMAGE', 'VIDEO', 'AUDIO'].map(t => (
            <button key={t} onClick={() => { setFilter(t); setPage(1) }}
              className="text-xs font-bold uppercase tracking-wide2 px-3 py-2 rounded-lg transition-all"
              style={{ background: filter===t ? '#dc2626' : '#1a1a1a', color: filter===t ? '#fff' : '#6b7280', border: '1px solid', borderColor: filter===t ? '#dc2626' : 'rgba(255,255,255,0.06)' }}
            >{t || 'All'}</button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-20">
          <div className="spinner w-8 h-8" style={{ borderTopColor: '#dc2626' }} />
        </div>
      ) : items.length === 0 ? (
        <div className="card p-16 text-center">
          <Search className="w-10 h-10 mx-auto mb-3" style={{ color:'#374151' }} />
          <p className="font-semibold" style={{ color:'#6b7280' }}>No scans found</p>
        </div>
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full">
            <thead>
              <tr style={{ borderBottom:'1px solid rgba(255,255,255,0.04)' }}>
                {['File','Type','Risk','Probability','Confidence','Date',''].map(h => (
                  <th key={h} className="text-left px-5 py-3 text-xs font-bold uppercase tracking-wide2" style={{ color:'#374151' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {items.map((a, i) => {
                const risk = RISK_CONFIG[a.risk_level || 'UNDETERMINED']
                const bc   = `badge-${(a.risk_level||'undetermined').toLowerCase()}`
                return (
                  <motion.tr key={a.id}
                    initial={{ opacity:0, y:8 }} animate={{ opacity:1, y:0 }} transition={{ delay: i*0.03 }}
                    className="group transition-colors cursor-pointer"
                    style={{ borderBottom:'1px solid rgba(255,255,255,0.02)' }}
                    onMouseEnter={e=>(e.currentTarget.style.background='#111111')}
                    onMouseLeave={e=>(e.currentTarget.style.background='transparent')}
                  >
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-2">
                        {a.media_type==='IMAGE'&&<Image className="w-3.5 h-3.5 flex-shrink-0" style={{color:'#6b7280'}}/>}
                        {a.media_type==='VIDEO'&&<Video className="w-3.5 h-3.5 flex-shrink-0" style={{color:'#6b7280'}}/>}
                        {a.media_type==='AUDIO'&&<Music className="w-3.5 h-3.5 flex-shrink-0" style={{color:'#6b7280'}}/>}
                        <span className="text-sm text-white font-medium truncate max-w-[180px]">{a.original_filename}</span>
                      </div>
                    </td>
                    <td className="px-5 py-3.5 text-xs font-mono" style={{color:'#6b7280'}}>{a.media_type}</td>
                    <td className="px-5 py-3.5"><span className={bc}>{risk.emoji} {risk.label}</span></td>
                    <td className="px-5 py-3.5 text-xs font-mono" style={{color:'#9ca3af'}}>
                      {a.synthetic_probability!=null?`${(a.synthetic_probability*100).toFixed(1)}%`:'—'}
                    </td>
                    <td className="px-5 py-3.5 text-xs font-mono" style={{color:'#9ca3af'}}>
                      {a.confidence!=null?`${(a.confidence*100).toFixed(0)}%`:'—'}
                    </td>
                    <td className="px-5 py-3.5 text-xs font-mono" style={{color:'#6b7280'}}>{format(new Date(a.created_at),'MMM d, HH:mm')}</td>
                    <td className="px-5 py-3.5">
                      <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        <Link href={`/dashboard/analysis/${a.id}`} className="btn-ghost-red text-xs py-1 px-2"><FileText className="w-3.5 h-3.5"/></Link>
                        <button onClick={()=>handleDelete(a.id)} className="btn-ghost-red text-xs py-1 px-2" style={{color:'#dc2626'}}><Trash2 className="w-3.5 h-3.5"/></button>
                      </div>
                    </td>
                  </motion.tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-6">
          {Array.from({length:totalPages},(_,i)=>i+1).map(p=>(
            <button key={p} onClick={()=>setPage(p)}
              className="w-9 h-9 rounded-lg text-sm font-bold transition-all"
              style={{ background:p===page?'#dc2626':'#1a1a1a', color:p===page?'#fff':'#6b7280', border:'1px solid', borderColor:p===page?'#dc2626':'rgba(255,255,255,0.06)' }}
            >{p}</button>
          ))}
        </div>
      )}
    </div>
  )
}
