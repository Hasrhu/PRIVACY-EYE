'use client'
import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Upload, Shield, AlertTriangle, CheckCircle, HelpCircle, FileText, Download } from 'lucide-react'
import { analysisApi, reportsApi, getErrorMessage } from '@/lib/api'
import type { Analysis, Report } from '@/types'
import { RISK_CONFIG, MEDIA_TYPE_CONFIG } from '@/types'
import toast from 'react-hot-toast'
import clsx from 'clsx'

type Step = 'upload' | 'processing' | 'result'

interface Props {
  type: 'IMAGE' | 'VIDEO' | 'AUDIO'
  onClose: () => void
  onComplete: (a: Analysis) => void
}

export default function ScannerModal({ type, onClose, onComplete }: Props) {
  const [step, setStep] = useState<Step>('upload')
  const [file, setFile] = useState<File | null>(null)
  const [analysis, setAnalysis] = useState<Analysis | null>(null)
  const [report, setReport] = useState<Report | null>(null)
  const [generating, setGenerating] = useState(false)

  const config = MEDIA_TYPE_CONFIG[type]

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted.length > 0) setFile(accepted[0])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: config.accept,
    maxSize: config.maxMB * 1024 * 1024,
    multiple: false,
    onDropRejected: (files) => {
      const err = files[0]?.errors[0]
      if (err?.code === 'file-too-large') toast.error(`File too large. Max ${config.maxMB}MB.`)
      else toast.error('Unsupported file type.')
    },
  })

  const handleAnalyze = async () => {
    if (!file) return
    setStep('processing')
    try {
      let res
      if (type === 'IMAGE') res = await analysisApi.analyzeImage(file)
      else if (type === 'VIDEO') res = await analysisApi.analyzeVideo(file)
      else res = await analysisApi.analyzeAudio(file)

      setAnalysis(res.data)
      setStep('result')
      onComplete(res.data)
    } catch (err) {
      toast.error(getErrorMessage(err))
      setStep('upload')
    }
  }

  const handleGenerateReport = async () => {
    if (!analysis) return
    setGenerating(true)
    try {
      const res = await reportsApi.generate(analysis.id)
      setReport(res.data)
      toast.success('Report generated!')
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setGenerating(false)
    }
  }

  const handleDownloadReport = async () => {
    if (!analysis) return
    try {
      const res = await reportsApi.downloadJson(analysis.id)
      const url = URL.createObjectURL(res.data)
      const a = document.createElement('a')
      a.href = url
      a.download = `privacy-eye-report-${analysis.id.slice(0, 8)}.json`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      toast.error(getErrorMessage(err))
    }
  }

  const risk = analysis?.risk_level ? RISK_CONFIG[analysis.risk_level] : null

  return (
    <AnimatePresence>
      <motion.div
        className="fixed inset-0 z-50 flex items-center justify-center p-4"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
      >
        {/* Backdrop */}
        <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />

        <motion.div
          className="relative rounded-3xl w-full max-w-2xl max-h-[90vh] overflow-y-auto glass-floating border border-white/16 shadow-glass-floating p-2"
          initial={{ scale: 0.92, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.92, opacity: 0 }}
          transition={{ type: 'spring', damping: 25 }}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-white/8">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-brand-500/20 flex items-center justify-center">
                <Shield className="w-5 h-5 text-brand-400" />
              </div>
              <div>
                <h2 className="font-semibold text-white">Scan {config.label}</h2>
                <p className="text-xs text-slate-500">Privacy Eye Analysis</p>
              </div>
            </div>
            <button onClick={onClose} className="text-slate-500 hover:text-white transition-colors">
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="p-6">
            {/* Step: Upload */}
            {step === 'upload' && (
              <div className="space-y-6">
                <div
                  {...getRootProps()}
                  className={clsx(
                    'border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all duration-200',
                    isDragActive
                      ? 'border-brand-500 bg-brand-500/10'
                      : 'border-white/10 hover:border-brand-500/50 hover:bg-white/3',
                    file ? 'border-emerald-500/50 bg-emerald-500/5' : ''
                  )}
                >
                  <input {...getInputProps()} />
                  {file ? (
                    <div>
                      <CheckCircle className="w-10 h-10 text-emerald-400 mx-auto mb-3" />
                      <p className="font-medium text-white">{file.name}</p>
                      <p className="text-sm text-slate-500 mt-1">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                      <p className="text-xs text-slate-600 mt-2">Click or drop to replace</p>
                    </div>
                  ) : (
                    <div>
                      <Upload className="w-10 h-10 text-slate-600 mx-auto mb-3" />
                      <p className="font-medium text-white mb-1">
                        {isDragActive ? 'Drop it here' : `Drop your ${config.label.toLowerCase()} here`}
                      </p>
                      <p className="text-sm text-slate-500">or click to browse</p>
                      <p className="text-xs text-slate-600 mt-2">
                        {Object.values(config.accept).flat().join(', ')} · Max {config.maxMB}MB
                      </p>
                    </div>
                  )}
                </div>

                <div className="flex items-start gap-3 p-4 rounded-xl bg-brand-500/5 border border-brand-500/15">
                  <Shield className="w-4 h-4 text-brand-400 mt-0.5 flex-shrink-0" />
                  <p className="text-xs text-slate-400 leading-relaxed">
                    <span className="text-brand-300 font-medium">Privacy protected:</span> Your file is analyzed in memory and immediately deleted. We never store your media.
                  </p>
                </div>

                <button onClick={handleAnalyze} disabled={!file} className="btn-primary w-full justify-center py-3">
                  <Shield className="w-4 h-4" />
                  Analyze with Privacy Eye
                </button>
              </div>
            )}

            {/* Step: Processing */}
            {step === 'processing' && (
              <div className="py-12 text-center space-y-6">
                <div className="relative w-20 h-20 mx-auto">
                  <div className="w-20 h-20 rounded-full border-2 border-brand-500/20 flex items-center justify-center">
                    <Shield className="w-9 h-9 text-brand-400" />
                  </div>
                  <div className="absolute inset-0 rounded-full border-2 border-t-brand-500 border-transparent animate-spin" />
                  {/* Scan line */}
                  <div className="absolute inset-0 overflow-hidden rounded-full">
                    <div className="w-full h-0.5 bg-gradient-to-r from-transparent via-brand-500 to-transparent absolute animate-scan-line" />
                  </div>
                </div>
                <div>
                  <h3 className="font-semibold text-white text-lg">Analyzing…</h3>
                  <p className="text-slate-400 text-sm mt-1">Running forensic analysis and ML pipeline</p>
                </div>
                <div className="space-y-2 text-left max-w-xs mx-auto">
                  {['Extracting metadata', 'Running forensic analysis', 'Processing signals', 'Computing risk score'].map((s, i) => (
                    <div key={s} className="flex items-center gap-2 text-sm text-slate-500">
                      <div className="w-4 h-4 rounded-full border border-brand-500/40 border-t-brand-500 animate-spin" style={{ animationDelay: `${i * 0.2}s` }} />
                      {s}
                    </div>
                  ))}
                </div>
                <p className="text-xs text-slate-600">Your file will be deleted immediately after analysis</p>
              </div>
            )}

            {/* Step: Result */}
            {step === 'result' && analysis && risk && (
              <div className="space-y-6">
                {/* Risk banner */}
                <div className={clsx('rounded-2xl p-5 border', risk.className)}>
                  <div className="flex items-center gap-3">
                    <span className="text-3xl">{risk.emoji}</span>
                    <div>
                      <div className="font-bold text-lg">{risk.label}</div>
                      <div className="text-sm opacity-80">
                        Synthetic probability: {analysis.synthetic_probability != null ? `${(analysis.synthetic_probability * 100).toFixed(1)}%` : 'N/A'}
                        {' · '}
                        Confidence: {analysis.confidence != null ? `${(analysis.confidence * 100).toFixed(0)}%` : 'N/A'}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Explanation */}
                {analysis.explanation && (
                  <div className="glass rounded-xl p-4">
                    <h3 className="text-sm font-semibold text-slate-300 mb-2">Analysis Summary</h3>
                    <p className="text-sm text-slate-400 leading-relaxed">{analysis.explanation}</p>
                  </div>
                )}

                {/* Signals */}
                {analysis.signals.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-slate-300 mb-3">
                      Detected Signals ({analysis.signals.length})
                    </h3>
                    <div className="space-y-2">
                      {analysis.signals.map((s) => (
                        <div key={s.signal_key} className="glass rounded-xl p-3">
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex items-start gap-2">
                              <AlertTriangle className={clsx('w-4 h-4 mt-0.5 flex-shrink-0', {
                                'text-red-400':    s.severity === 'high',
                                'text-amber-400':  s.severity === 'medium',
                                'text-slate-400':  s.severity === 'low',
                              })} />
                              <div>
                                <p className="text-sm font-medium text-white">{s.signal_label}</p>
                                {s.description && <p className="text-xs text-slate-500 mt-0.5">{s.description}</p>}
                              </div>
                            </div>
                            {s.score != null && (
                              <span className="text-xs text-slate-500 shrink-0">{(s.score * 100).toFixed(0)}%</span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* File metadata */}
                <div className="glass rounded-xl p-4 space-y-1.5">
                  <h3 className="text-sm font-semibold text-slate-300 mb-2">File Information</h3>
                  {[
                    ['Filename', analysis.original_filename],
                    ['SHA-256', analysis.file_sha256 ? `${analysis.file_sha256.slice(0, 16)}…` : 'N/A'],
                    ['Size', `${(analysis.file_size_bytes / 1024).toFixed(1)} KB`],
                    ['Media deleted', analysis.media_deleted ? '✓ Immediately' : 'Processing…'],
                    ['Processing time', analysis.processing_ms ? `${analysis.processing_ms}ms` : 'N/A'],
                  ].map(([k, v]) => (
                    <div key={k} className="flex justify-between text-xs">
                      <span className="text-slate-500">{k}</span>
                      <span className="text-slate-300 font-mono">{v}</span>
                    </div>
                  ))}
                </div>

                {/* Report */}
                {report ? (
                  <div className="glass rounded-xl p-4 border border-emerald-500/20">
                    <div className="flex items-center gap-2 mb-3">
                      <FileText className="w-4 h-4 text-emerald-400" />
                      <span className="text-sm font-semibold text-emerald-400">Report Generated</span>
                    </div>
                    {report.summary && <p className="text-sm text-slate-400 mb-3">{report.summary}</p>}
                    {report.recommendations && (
                      <div className="text-xs text-slate-400 whitespace-pre-line">{report.recommendations}</div>
                    )}
                    <button onClick={handleDownloadReport} className="btn-ghost text-xs mt-3 text-emerald-400">
                      <Download className="w-3.5 h-3.5" /> Download JSON Report
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={handleGenerateReport}
                    disabled={generating}
                    className="btn-primary w-full justify-center"
                  >
                    {generating ? (
                      <span className="flex items-center gap-2">
                        <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        Generating AI Report…
                      </span>
                    ) : (
                      <><FileText className="w-4 h-4" /> Generate Evidence Report</>
                    )}
                  </button>
                )}

                <p className="text-xs text-slate-600 text-center">
                  Results are probabilistic indicators only. Privacy Eye does not guarantee 100% accuracy.
                </p>
              </div>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}
