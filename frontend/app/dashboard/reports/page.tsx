'use client'
import React, { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import {
  FileText,
  Download,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  ExternalLink,
  Clock,
  Sparkles,
  Lock,
  Layers,
  X,
  Trash2,
  Search,
  Eye,
  Camera,
  UserX,
  CheckCircle2,
  Image as ImageIcon,
} from 'lucide-react'
import { format } from 'date-fns'
import toast from 'react-hot-toast'
import Cookies from 'js-cookie'

import { analysisApi, reportsApi, scanReportsApi, getErrorMessage } from '@/lib/api'
import type { Analysis, Report, ScanReport } from '@/types'
import { RISK_CONFIG } from '@/types'
import { GlassCard } from '@/components/ui/GlassCard'
import { GlassButton } from '@/components/ui/GlassButton'
import { GlassBadge } from '@/components/ui/GlassBadge'

type TabFilter = 'ALL' | 'LIVE_SCANS' | 'LIKELY_HUMAN' | 'SUSPICIOUS' | 'UNDETERMINED'

export default function ReportsPage() {
  const router = useRouter()
  const [scanReports, setScanReports] = useState<ScanReport[]>([])
  const [mediaItems, setMediaItems] = useState<Analysis[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<TabFilter>('ALL')
  const [searchQuery, setSearchQuery] = useState('')
  const [activeReportDoc, setActiveReportDoc] = useState<{ analysis: Analysis; report?: Report } | null>(null)
  const [generatingId, setGeneratingId] = useState<string | null>(null)
  const [downloadingId, setDownloadingId] = useState<string | null>(null)

  const loadAllReports = async () => {
    setLoading(true)
    try {
      const [scanRes, mediaRes] = await Promise.allSettled([
        scanReportsApi.list({ per_page: 50 }),
        analysisApi.getHistory(1, 50),
      ])

      if (scanRes.status === 'fulfilled') {
        setScanReports(scanRes.value.data.items || [])
      }
      if (mediaRes.status === 'fulfilled') {
        setMediaItems(mediaRes.value.data.items?.filter((a: Analysis) => a.status === 'COMPLETE') || [])
      }
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!Cookies.get('access_token')) {
      router.push('/auth/login')
      return
    }
    loadAllReports()
  }, [router])

  // Scan Report Actions
  const handleDownloadPdf = async (report: ScanReport) => {
    setDownloadingId(`pdf_${report.id}`)
    try {
      const res = await scanReportsApi.downloadPdf(report.id)
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `${report.report_number}_forensic_dossier.pdf`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      toast.success('PDF report downloaded!')
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setDownloadingId(null)
    }
  }

  const handleDownloadJpg = async (report: ScanReport) => {
    setDownloadingId(`jpg_${report.id}`)
    try {
      const res = await scanReportsApi.downloadJpg(report.id)
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'image/jpeg' }))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `${report.report_number}_audit_card.jpg`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      toast.success('JPG report downloaded!')
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setDownloadingId(null)
    }
  }

  const handleDeleteScanReport = async (report: ScanReport) => {
    const ok = window.confirm(`Permanently delete report ${report.report_number} and all associated files?`)
    if (!ok) return

    try {
      await scanReportsApi.delete(report.id)
      setScanReports((prev) => prev.filter((r) => r.id !== report.id))
      toast.success('Report deleted successfully.')
    } catch (err) {
      toast.error(getErrorMessage(err))
    }
  }

  // Legacy Media Analysis Report Actions
  const handleGenerateMediaReport = async (id: string, a: Analysis) => {
    setGeneratingId(id)
    try {
      const res = await reportsApi.generate(id)
      toast.success('Security report generated!')
      setActiveReportDoc({ analysis: a, report: res.data })
    } catch (e) {
      toast.error(getErrorMessage(e))
    } finally {
      setGeneratingId(null)
    }
  }

  const handleOpenDoc = async (a: Analysis) => {
    try {
      const rep = await reportsApi.get(a.id)
      setActiveReportDoc({ analysis: a, report: rep.data })
    } catch {
      setActiveReportDoc({ analysis: a })
    }
  }

  const handleDownloadMediaJson = async (id: string) => {
    try {
      const res = await reportsApi.downloadJson(id)
      const url = URL.createObjectURL(res.data)
      const el = document.createElement('a')
      el.href = url
      el.download = `privacy-eye-report-${id.slice(0, 8)}.json`
      el.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      toast.error(getErrorMessage(e))
    }
  }

  // Filter scan reports
  const filteredScanReports = scanReports.filter((r) => {
    const matchesSearch =
      !searchQuery ||
      r.report_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.assessment.toLowerCase().includes(searchQuery.toLowerCase())

    if (!matchesSearch) return false

    if (activeTab === 'ALL' || activeTab === 'LIVE_SCANS') return true
    if (activeTab === 'LIKELY_HUMAN') {
      return r.assessment.includes('REAL') || r.assessment.includes('LIKELY')
    }
    if (activeTab === 'SUSPICIOUS') {
      return (
        r.assessment.includes('REPLAY') ||
        r.assessment.includes('SUSPICIOUS') ||
        r.assessment.includes('NOT_LIKELY')
      )
    }
    if (activeTab === 'UNDETERMINED') {
      return (
        r.assessment.includes('UNABLE') ||
        r.assessment.includes('CLARITY') ||
        r.assessment.includes('NO_FACE')
      )
    }
    return true
  })

  // Filter media analyses
  const filteredMediaItems = mediaItems.filter((m) => {
    if (activeTab === 'LIVE_SCANS') return false
    const matchesSearch =
      !searchQuery ||
      m.original_filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (m.risk_level || '').toLowerCase().includes(searchQuery.toLowerCase())

    if (!matchesSearch) return false
    if (activeTab === 'ALL') return true
    if (activeTab === 'LIKELY_HUMAN') return m.risk_level === 'LOW'
    if (activeTab === 'SUSPICIOUS') return m.risk_level === 'HIGH' || m.risk_level === 'CRITICAL' || m.risk_level === 'SUSPICIOUS'
    if (activeTab === 'UNDETERMINED') return m.risk_level === 'UNDETERMINED'
    return true
  })

  const totalFilteredCount = filteredScanReports.length + filteredMediaItems.length

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-16">
      {/* ── HEADER ── */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <FileText className="w-4 h-4 text-brand-blue" />
            <span className="text-xs uppercase font-mono tracking-widest text-brand-blue">
              Forensic Evidence Dossiers
            </span>
          </div>
          <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-white">
            SECURITY REPORTS
          </h1>
          <p className="text-sm text-white/60 mt-1">
            Audit-grade authenticity dossiers, representative face captures, and verifiable JPG/PDF exports.
          </p>
        </div>

        <Link href="/dashboard/live-scan">
          <GlassButton variant="primary" size="sm" icon={<Camera className="w-4 h-4" />}>
            New Live Scan
          </GlassButton>
        </Link>
      </div>

      {/* ── SEARCH & FILTER TABS (Section 60 & 61) ── */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
          {(
            [
              { key: 'ALL', label: 'All Reports' },
              { key: 'LIVE_SCANS', label: 'Live Scans' },
              { key: 'LIKELY_HUMAN', label: 'Likely Human' },
              { key: 'SUSPICIOUS', label: 'Suspicious / Replay' },
              { key: 'UNDETERMINED', label: 'Unable to Determine' },
            ] as const
          ).map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-3.5 py-1.5 rounded-full text-xs font-mono transition-all ${
                activeTab === tab.key
                  ? 'bg-brand-blue text-white shadow-glow-blue font-bold'
                  : 'glass-surface text-white/60 hover:text-white hover:bg-white/8'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="relative w-full md:w-64">
          <Search className="w-3.5 h-3.5 text-white/40 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search report ID or result..."
            className="w-full bg-white/4 border border-white/8 rounded-2xl pl-9 pr-3 py-1.5 text-xs text-white placeholder-white/40 focus:outline-none focus:border-brand-blue/50 font-mono"
          />
        </div>
      </div>

      {/* ── CATALOG LISTING ── */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-24 space-y-3">
          <div className="w-8 h-8 rounded-full border-2 border-brand-blue border-t-transparent animate-spin" />
          <p className="text-xs font-mono uppercase text-white/50">Compiling Report Catalog...</p>
        </div>
      ) : totalFilteredCount === 0 ? (
        <GlassCard variant="elevated" className="py-20 text-center space-y-3">
          <FileText className="w-10 h-10 mx-auto text-white/20" />
          <p className="text-sm font-semibold text-white/60">No reports matched your current filter criteria.</p>
          <Link href="/dashboard/live-scan">
            <GlassButton variant="primary" size="sm">
              Start Live Camera Scan
            </GlassButton>
          </Link>
        </GlassCard>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* 1. Live Camera Scan Reports (Cards from Section 36 & 69) */}
          {filteredScanReports.map((report) => {
            const conf = report.confidence
            const isSafe = conf >= 80 && !report.assessment.includes('REPLAY')
            const isWarn = conf >= 60 && !report.assessment.includes('REPLAY')
            const badgeStatus = isSafe ? 'safe' : isWarn ? 'warning' : 'danger'

            return (
              <GlassCard
                key={report.id}
                variant="elevated"
                className="p-5 space-y-4 hover:border-brand-blue/40 transition-all border border-white/8"
              >
                {/* Header row */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded-md bg-brand-cyan/20 text-brand-cyan font-mono text-[10px] font-bold">
                      {report.report_number}
                    </span>
                    <span className="text-[10px] font-mono text-white/40">
                      {format(new Date(report.created_at), 'dd MMM yyyy')}
                    </span>
                  </div>
                  <GlassBadge status={badgeStatus} label={report.assessment.replace(/_/g, ' ')} />
                </div>

                {/* Face thumbnail + Assessment breakdown */}
                <div className="flex items-start gap-4">
                  <div className="w-20 h-20 rounded-2xl overflow-hidden bg-black/40 border border-white/10 flex items-center justify-center flex-shrink-0 relative">
                    {report.has_face_capture ? (
                      <div className="flex flex-col items-center justify-center text-brand-cyan">
                        <Eye className="w-6 h-6" />
                        <span className="text-[9px] font-mono mt-1 text-white/60">Evidence</span>
                      </div>
                    ) : (
                      <div className="flex flex-col items-center justify-center text-white/40">
                        <UserX className="w-6 h-6" />
                        <span className="text-[8px] font-mono mt-1">Zero Retain</span>
                      </div>
                    )}
                  </div>

                  <div className="space-y-1.5 flex-1 min-w-0">
                    <h3 className="text-base font-extrabold text-white truncate">
                      {report.category_label || report.assessment.replace(/_/g, ' ')}
                    </h3>
                    <div className="flex items-center gap-3 text-xs font-mono">
                      <span className="text-brand-cyan font-bold">{conf.toFixed(1)}% Confidence</span>
                      <span className="text-white/40">•</span>
                      <span className="text-white/60">{report.reliability}</span>
                    </div>

                    {/* Quick Reasons List */}
                    <div className="text-[11px] text-white/60 space-y-0.5 pt-1">
                      {report.why_reasons && report.why_reasons.slice(0, 2).map((r, i) => (
                        <div key={i} className="flex items-center gap-1.5 truncate">
                          <span className="text-status-safe font-bold">✓</span>
                          <span className="truncate">{r}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Bottom Action Buttons */}
                <div className="pt-3 flex items-center justify-between border-t border-white/6">
                  <span className="text-[10px] font-mono text-white/40 uppercase">
                    Model: {report.model_name.slice(0, 15)}
                  </span>

                  <div className="flex items-center gap-1.5">
                    <Link href={`/dashboard/reports/${report.id}`}>
                      <GlassButton variant="primary" size="sm">
                        View
                      </GlassButton>
                    </Link>
                    <button
                      onClick={() => handleDownloadPdf(report)}
                      disabled={downloadingId === `pdf_${report.id}`}
                      className="px-2.5 py-1 rounded-xl glass-surface hover:bg-white/10 text-xs font-mono text-white/80 hover:text-white flex items-center gap-1"
                      title="Download Official PDF Dossier"
                    >
                      <Download className="w-3 h-3 text-brand-blue" />
                      PDF
                    </button>
                    <button
                      onClick={() => handleDownloadJpg(report)}
                      disabled={downloadingId === `jpg_${report.id}`}
                      className="px-2.5 py-1 rounded-xl glass-surface hover:bg-white/10 text-xs font-mono text-white/80 hover:text-white flex items-center gap-1"
                      title="Download JPG Audit Card"
                    >
                      <ImageIcon className="w-3 h-3 text-brand-cyan" />
                      JPG
                    </button>
                    <button
                      onClick={() => handleDeleteScanReport(report)}
                      className="p-1.5 rounded-xl hover:bg-status-danger/20 text-white/40 hover:text-status-danger transition-colors"
                      title="Delete Report"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </GlassCard>
            )
          })}

          {/* 2. Media Analysis Reports */}
          {filteredMediaItems.map((item) => {
            const risk = RISK_CONFIG[item.risk_level || 'UNDETERMINED']
            const badgeStatus =
              item.risk_level === 'LOW'
                ? 'safe'
                : item.risk_level === 'SUSPICIOUS'
                ? 'warning'
                : item.risk_level === 'HIGH' || item.risk_level === 'CRITICAL'
                ? 'danger'
                : 'undetermined'

            return (
              <GlassCard
                key={item.id}
                variant="elevated"
                className="p-5 space-y-4 hover:border-brand-blue/30 transition-all cursor-pointer border border-white/8"
                onClick={() => handleOpenDoc(item)}
              >
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono text-white/40 uppercase">
                    ID: {item.id.slice(0, 12)}...
                  </span>
                  <GlassBadge status={badgeStatus} label={risk.label} />
                </div>

                <div>
                  <h3 className="text-base font-bold text-white truncate">{item.original_filename}</h3>
                  <p className="text-xs text-white/50 mt-1">
                    {format(new Date(item.created_at), 'dd MMM yyyy HH:mm')} · {item.media_type}
                  </p>
                </div>

                <div className="pt-2 flex items-center justify-between border-t border-white/6">
                  <span className="text-xs font-mono text-white/60">
                    Confidence: {item.confidence !== null ? `${Math.round(item.confidence * 100)}%` : '—'}
                  </span>

                  <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                    <GlassButton
                      variant="secondary"
                      size="sm"
                      onClick={() => handleGenerateMediaReport(item.id, item)}
                      isLoading={generatingId === item.id}
                      icon={<FileText className="w-3.5 h-3.5" />}
                    >
                      Open Report
                    </GlassButton>
                    <button
                      onClick={() => handleDownloadMediaJson(item.id)}
                      className="p-2 rounded-xl glass-surface hover:bg-white/10 text-white/60 hover:text-white"
                      title="Download JSON"
                    >
                      <Download className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </GlassCard>
            )
          })}
        </div>
      )}

      {/* ── LEGACY MEDIA ANALYSIS REPORT MODAL ── */}
      <AnimatePresence>
        {activeReportDoc && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-canvas/80 backdrop-blur-xl">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="w-full max-w-3xl max-h-[92vh] rounded-4xl glass-floating border border-white/18 p-8 md:p-10 space-y-6 shadow-glass-floating overflow-y-auto"
            >
              <div className="flex items-center justify-between pb-4 border-b border-white/10">
                <div className="flex items-center gap-2.5">
                  <FileText className="w-5 h-5 text-brand-blue" />
                  <span className="font-mono text-xs text-white/70 uppercase">
                    Forensic Media Audit · {activeReportDoc.analysis.id.slice(0, 12)}
                  </span>
                </div>
                <button
                  onClick={() => setActiveReportDoc(null)}
                  className="p-1.5 rounded-xl hover:bg-white/10 text-white/50 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="space-y-4">
                <h2 className="text-xl font-bold text-white">
                  {activeReportDoc.analysis.original_filename}
                </h2>
                <p className="text-xs text-white/70 leading-relaxed">
                  {activeReportDoc.report?.summary || activeReportDoc.analysis.explanation}
                </p>
              </div>

              <div className="pt-4 flex justify-end gap-3 border-t border-white/10">
                <button
                  onClick={() => handleDownloadMediaJson(activeReportDoc.analysis.id)}
                  className="px-4 py-2 rounded-xl glass-surface hover:bg-white/10 text-xs font-mono text-white flex items-center gap-2"
                >
                  <Download className="w-3.5 h-3.5" />
                  Download JSON
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  )
}
