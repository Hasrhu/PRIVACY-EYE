'use client'
import React, { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { motion } from 'framer-motion'
import {
  FileText,
  Download,
  ArrowLeft,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  Eye,
  CheckCircle2,
  XCircle,
  Clock,
  ExternalLink,
  Trash2,
  Cpu,
  Layers,
  Image as ImageIcon,
  UserCheck,
  UserX,
  Smartphone,
  Timer,
  Lock,
} from 'lucide-react'
import toast from 'react-hot-toast'
import Cookies from 'js-cookie'

import { scanReportsApi, getErrorMessage } from '@/lib/api'
import type { ScanReport } from '@/types'
import { GlassCard } from '@/components/ui/GlassCard'
import { GlassButton } from '@/components/ui/GlassButton'
import { GlassBadge } from '@/components/ui/GlassBadge'
import { ConfidenceRing } from '@/components/ui/ConfidenceRing'

export default function ReportDetailPage() {
  const params = useParams()
  const router = useRouter()
  const reportId = params?.id as string

  const [report, setReport] = useState<ScanReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [faceBlobUrl, setFaceBlobUrl] = useState<string | null>(null)
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false)
  const [isDownloadingJpg, setIsDownloadingJpg] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  useEffect(() => {
    if (!Cookies.get('access_token')) {
      router.push('/auth/login')
      return
    }

    if (!reportId) return

    setLoading(true)
    scanReportsApi
      .get(reportId)
      .then(async (res) => {
        setReport(res.data)
        // If face capture is stored, fetch authenticated blob URL
        if (res.data.has_face_capture && res.data.face_capture_available) {
          try {
            const faceRes = await scanReportsApi.downloadFace(res.data.id)
            const objUrl = window.URL.createObjectURL(new Blob([faceRes.data], { type: 'image/jpeg' }))
            setFaceBlobUrl(objUrl)
          } catch {
            // face preview fallback
          }
        }
      })
      .catch((err) => {
        toast.error(getErrorMessage(err))
      })
      .finally(() => setLoading(false))

    return () => {
      if (faceBlobUrl) {
        window.URL.revokeObjectURL(faceBlobUrl)
      }
    }
  }, [reportId, router])

  const handleDownloadPdf = async () => {
    if (!report) return
    setIsDownloadingPdf(true)
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
      setIsDownloadingPdf(false)
    }
  }

  const handleDownloadJpg = async () => {
    if (!report) return
    setIsDownloadingJpg(true)
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
      setIsDownloadingJpg(false)
    }
  }

  const handleDelete = async () => {
    if (!report) return
    const confirmed = window.confirm(`Permanently delete report ${report.report_number} and all associated evidence?`)
    if (!confirmed) return

    setIsDeleting(true)
    try {
      await scanReportsApi.delete(report.id)
      toast.success('Report deleted successfully.')
      router.push('/dashboard/reports')
    } catch (err) {
      toast.error(getErrorMessage(err))
      setIsDeleting(false)
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 space-y-3">
        <div className="w-8 h-8 rounded-full border-2 border-brand-blue border-t-transparent animate-spin" />
        <p className="text-xs font-mono uppercase text-white/50">Decrypting & Retrieving Dossier...</p>
      </div>
    )
  }

  if (!report) {
    return (
      <GlassCard variant="elevated" className="max-w-xl mx-auto py-16 text-center space-y-4">
        <FileText className="w-12 h-12 mx-auto text-white/20" />
        <h2 className="text-xl font-bold text-white">Report Not Found</h2>
        <p className="text-xs text-white/60">
          The requested audit record may have been purged or belongs to another authorized namespace.
        </p>
        <Link href="/dashboard/reports">
          <GlassButton variant="primary" size="sm" icon={<ArrowLeft className="w-4 h-4" />}>
            Back to Reports
          </GlassButton>
        </Link>
      </GlassCard>
    )
  }

  const conf = report.confidence
  const statusColor =
    conf >= 80 && !report.assessment.includes('REPLAY')
      ? 'safe'
      : conf >= 60 && !report.assessment.includes('REPLAY')
      ? 'warning'
      : 'danger'

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-16">
      {/* ── TOP NAVIGATION & ACTION BAR ── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-white/6">
        <div className="space-y-1">
          <Link
            href="/dashboard/reports"
            className="inline-flex items-center gap-1.5 text-xs text-white/50 hover:text-brand-blue transition-colors font-mono"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to Reports Catalog
          </Link>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-white">
              {report.report_number}
            </h1>
            <GlassBadge status={statusColor} label={report.report_status} />
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <GlassButton
            variant="primary"
            size="sm"
            onClick={handleDownloadPdf}
            isLoading={isDownloadingPdf}
            icon={<Download className="w-3.5 h-3.5" />}
            className="shadow-glow-blue"
          >
            Download PDF
          </GlassButton>
          <GlassButton
            variant="secondary"
            size="sm"
            onClick={handleDownloadJpg}
            isLoading={isDownloadingJpg}
            icon={<ImageIcon className="w-3.5 h-3.5" />}
          >
            Download JPG
          </GlassButton>
          <GlassButton
            variant="danger"
            size="sm"
            onClick={handleDelete}
            isLoading={isDeleting}
            icon={<Trash2 className="w-3.5 h-3.5" />}
          >
            Delete
          </GlassButton>
        </div>
      </div>

      {/* ── METADATA STRIP ── */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
        <div className="p-3.5 rounded-2xl bg-white/4 border border-white/8 space-y-1">
          <span className="text-white/40 block">SESSION ID</span>
          <p className="text-white font-bold truncate">{report.live_session_id}</p>
        </div>
        <div className="p-3.5 rounded-2xl bg-white/4 border border-white/8 space-y-1">
          <span className="text-white/40 block">DATE & TIME (UTC)</span>
          <p className="text-white font-bold">{new Date(report.created_at).toLocaleString()}</p>
        </div>
        <div className="p-3.5 rounded-2xl bg-white/4 border border-white/8 space-y-1">
          <span className="text-white/40 block">PROCESSING LOCATION</span>
          <p className="text-brand-blue font-bold truncate">{report.processing_location}</p>
        </div>
        <div className="p-3.5 rounded-2xl bg-white/4 border border-white/8 space-y-1">
          <span className="text-white/40 block">INPUT QUALITY</span>
          <p className="text-status-safe font-bold">{report.input_quality}</p>
        </div>
      </div>

      {/* ── VISUAL EVIDENCE & PRIMARY ASSESSMENT HERO ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Face Evidence (5 Cols) */}
        <div className="lg:col-span-5">
          <GlassCard variant="elevated" className="p-6 space-y-4 h-full flex flex-col justify-between">
            <div className="space-y-1">
              <span className="text-[10px] font-mono uppercase tracking-wider text-white/40 block">
                Representative Frame
              </span>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Visual Evidence
              </h3>
            </div>

            <div className="w-full aspect-square rounded-2xl overflow-hidden bg-black/40 border border-white/10 flex items-center justify-center relative">
              {faceBlobUrl ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={faceBlobUrl}
                  alt="Captured face evidence"
                  className="w-full h-full object-cover"
                />
              ) : report.has_face_capture ? (
                <div className="flex flex-col items-center gap-2 text-white/40">
                  <Eye className="w-8 h-8" />
                  <span className="text-xs font-mono">Face Image Encrypted</span>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-2 text-center p-6 text-white/50">
                  <UserX className="w-10 h-10 text-white/30" />
                  <p className="text-xs font-bold text-white">Zero-Biometric Storage Enforced</p>
                  <p className="text-[11px] text-white/40 max-w-xs">
                    Per user privacy preference, raw facial frame was discarded immediately following cryptographic inference.
                  </p>
                </div>
              )}
            </div>

            <div className="text-[11px] font-mono text-white/50 flex justify-between items-center pt-1 border-t border-white/6">
              <span>Target: {report.target_face_id || 'Face 1'}</span>
              <span>Faces Observed: {report.faces_detected_count}</span>
            </div>
          </GlassCard>
        </div>

        {/* Right: Assessment Showcase (7 Cols) */}
        <div className="lg:col-span-7">
          <GlassCard variant="elevated" className="p-6 space-y-6 h-full flex flex-col justify-between">
            <div className="flex items-center justify-between pb-3 border-b border-white/6">
              <span className="text-xs font-mono uppercase tracking-wider text-white/40">
                Authoritative Model Assessment
              </span>
              <GlassBadge
                status={statusColor}
                label={`${report.reliability.toUpperCase()} RELIABILITY`}
              />
            </div>

            <div className="flex items-center gap-6">
              <ConfidenceRing
                value={conf}
                size={120}
                strokeWidth={10}
                status={statusColor}
              />
              <div className="space-y-2 flex-1">
                <span className="text-xs uppercase font-mono tracking-widest text-brand-cyan font-bold block">
                  AUTHENTICITY VERDICT
                </span>
                <h2 className="text-2xl md:text-3xl font-extrabold tracking-tight text-white leading-tight">
                  {report.category_label || report.assessment.replace(/_/g, ' ')}
                </h2>
                <p className="text-xs text-white/70 leading-relaxed">
                  {report.explanation || 'Multi-signal neural biometric analysis completed.'}
                </p>
              </div>
            </div>

            {/* Why reasons box */}
            {report.why_reasons && report.why_reasons.length > 0 && (
              <div className="p-4 rounded-2xl bg-white/4 border border-white/8 space-y-2">
                <span className="text-[11px] font-mono uppercase font-bold text-brand-cyan block">
                  Why this confidence was assigned:
                </span>
                <ul className="space-y-1.5 text-xs text-white/80">
                  {report.why_reasons.map((r, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-status-safe font-bold">✓</span>
                      <span>{r}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </GlassCard>
        </div>
      </div>

      {/* ── TEST RESULTS AUDIT MATRIX ── */}
      <GlassCard variant="elevated" className="space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-white/6">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-brand-cyan" />
            <h3 className="text-sm font-bold uppercase tracking-wider text-white">
              Verification Test Results Matrix
            </h3>
          </div>
          <span className="text-xs font-mono text-white/50">
            {report.tests.filter((t) => t.status === 'PASS').length} of {report.tests.length} Passed
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-white/8 text-white/40 uppercase">
                <th className="py-2.5 px-3 font-semibold">Test Name</th>
                <th className="py-2.5 px-3 font-semibold">Status</th>
                <th className="py-2.5 px-3 font-semibold">Score</th>
                <th className="py-2.5 px-3 font-semibold">Technical Finding</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/4">
              {report.tests.map((test) => {
                const isPass = test.status === 'PASS'
                const isWarn = test.status === 'WARNING'
                const isFail = test.status === 'FAIL'
                const badgeStatus = isPass ? 'safe' : isWarn ? 'warning' : isFail ? 'danger' : 'neutral'

                return (
                  <tr key={test.id} className="hover:bg-white/2 transition-colors">
                    <td className="py-3 px-3 font-bold text-white">{test.test_name}</td>
                    <td className="py-3 px-3">
                      <GlassBadge status={badgeStatus} label={test.status} />
                    </td>
                    <td className="py-3 px-3 text-white/70">
                      {test.score !== null && test.score !== undefined ? `${(test.score * 100).toFixed(0)}%` : '—'}
                    </td>
                    <td className="py-3 px-3 text-white/80 font-sans">{test.message || '—'}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </GlassCard>

      {/* ── FORENSIC SIGNALS TABLE ── */}
      <GlassCard variant="elevated" className="space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-white/6">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-brand-blue" />
            <h3 className="text-sm font-bold uppercase tracking-wider text-white">
              Detected Forensic Biometric Signals
            </h3>
          </div>
          <span className="text-xs font-mono text-white/50">
            {report.signals.length} Signals Captured
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          {report.signals.map((sig) => (
            <div
              key={sig.id}
              className="p-3.5 rounded-2xl bg-white/4 border border-white/8 space-y-1.5"
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-brand-blue font-bold uppercase">{sig.signal_name}</span>
                <span
                  className={`px-2 py-0.5 rounded-md font-mono text-[10px] font-bold ${
                    sig.signal_status === 'PASS'
                      ? 'bg-status-safe/20 text-status-safe'
                      : sig.signal_status === 'WARNING'
                      ? 'bg-status-warning/20 text-status-warning'
                      : 'bg-brand-blue/20 text-brand-blue'
                  }`}
                >
                  {sig.signal_value}
                </span>
              </div>
              <p className="text-white/70 text-[11px] leading-relaxed">
                {sig.signal_explanation}
              </p>
            </div>
          ))}
        </div>
      </GlassCard>

      {/* ── MODEL GOVERNANCE & ARCHITECTURE LINEAGE ── */}
      <GlassCard variant="base" className="space-y-3">
        <div className="flex items-center gap-2 pb-2 border-b border-white/6">
          <Cpu className="w-4 h-4 text-brand-violet" />
          <h3 className="text-xs font-bold uppercase font-mono tracking-wider text-white">
            Model Governance & Cryptographic Traceability
          </h3>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
          <div>
            <span className="text-white/40 block text-[10px]">CORE MODEL</span>
            <p className="text-white font-bold">{report.model_name} ({report.model_version})</p>
          </div>
          <div>
            <span className="text-white/40 block text-[10px]">PREPROCESSING</span>
            <p className="text-white font-bold">{report.preprocessing_version}</p>
          </div>
          <div>
            <span className="text-white/40 block text-[10px]">FUSION ENGINE</span>
            <p className="text-white font-bold">{report.fusion_version}</p>
          </div>
          <div>
            <span className="text-white/40 block text-[10px]">CALIBRATION</span>
            <p className="text-white font-bold">{report.calibration_version}</p>
          </div>
        </div>
      </GlassCard>

      {/* ── STATUTORY SECURITY NOTICE ── */}
      <p className="text-[11px] text-white/40 text-center max-w-3xl mx-auto leading-relaxed font-mono">
        STATUTORY NOTICE: Privacy Eye provides a probabilistic authenticity assessment derived from multi-signal mathematical algorithms. Results can contain false positives and false negatives under non-standard lighting or occlusion and should not be treated as absolute proof of identity or malice.
      </p>
    </div>
  )
}
