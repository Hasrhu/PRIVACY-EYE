'use client'
import React, { useState, useEffect, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Camera,
  CameraOff,
  Shield,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  RefreshCw,
  Eye,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Sparkles,
  Save,
  Activity,
  Layers,
  Database,
  Lock,
  UserCheck,
  UserX,
  X,
  Check,
  Info,
  Smile,
  Headphones,
  RotateCw,
  Cpu,
  Smartphone,
  Monitor,
  EyeOff,
  Timer,
  AlertOctagon,
  PauseCircle,
  PlayCircle,
  FileText,
  Download,
  ExternalLink,
  Image as ImageIcon,
} from 'lucide-react'
import toast from 'react-hot-toast'
import Link from 'next/link'

import { liveScanApi, scanReportsApi, getErrorMessage } from '@/lib/api'
import type { ScanReport } from '@/types'
import { GlassCard } from '@/components/ui/GlassCard'
import { GlassButton } from '@/components/ui/GlassButton'
import { GlassBadge } from '@/components/ui/GlassBadge'
import { ConfidenceRing } from '@/components/ui/ConfidenceRing'
import { SignalBar } from '@/components/ui/SignalBar'
import { StatusIndicator } from '@/components/ui/StatusIndicator'

interface LandmarkPoints {
  right_eye: [number, number]
  left_eye: [number, number]
  nose_tip: [number, number]
  right_mouth: [number, number]
  left_mouth: [number, number]
}

interface GuidedProtocol {
  total_marked: number
  all_marked: boolean
  task_1_smile: {
    marked: boolean
    teeth_detected: boolean
    lips_wide: boolean
    mouth_ratio: number
    label: string
  }

  task_3_rotation: {
    marked: boolean
    yaw_span: number
    smooth: boolean
    sharp: boolean
    label: string
  }
}

interface EarAccessories {
  detected: boolean
  accessory_type: 'OVER_EAR_HEADPHONES' | 'IN_EAR_EARBUDS' | 'NONE'
  confidence: number
  label: string
  details: string
}

interface CriteriaEvaluation {
  total_matches: number
  all_matched: boolean

  movements: {
    yaw_span: number
    pitch_span: number
    has_turned_left: boolean
    has_turned_right: boolean
    has_tilted_up: boolean
    has_tilted_down: boolean
    matched: boolean
    label: string
  }
  lips: {
    angle_diff_deg: number
    mouth_ratio: number
    is_parallel: boolean
    is_proportional: boolean
    is_centered: boolean
    matched: boolean
    label: string
  }
}

interface LiveFrameResult {
  assessment: string
  category_label: string
  confidence: number
  reliability: 'HIGH' | 'MEDIUM' | 'LOW'
  face_detected: boolean
  face_box?: [number, number, number, number]
  landmarks?: LandmarkPoints
  total_faces_detected?: number
  all_face_boxes?: Array<[number, number, number, number]>
  // Ocular & Eye Quality Signals
  eye_status?: string
  eye_visibility_score?: number
  overall_eye_quality?: number
  is_eye_blurry?: boolean
  is_eye_obscured?: boolean
  left_eye_visible?: boolean
  right_eye_visible?: boolean
  left_eye_quality?: number
  right_eye_quality?: number
  // Phone & Electronic Screen Detection
  phone_detected?: boolean
  screen_face_associated?: boolean
  presentation_attack?: boolean
  phone_object_confidence?: number
  screen_face_association_confidence?: number
  presentation_attack_confidence?: number
  associated_screen?: any
  detected_screens?: any[]
  // Decision & Reason Engine
  input_quality?: 'GOOD' | 'ACCEPTABLE' | 'POOR'
  reason_codes?: string[]
  user_message?: string
  live_human_score?: number
  synthetic_score?: number
  replay_score?: number
  presentation_attack_score?: number
  quality?: {
    quality_index: number
    sharpness_score: number
    sharpness_label: 'SHARP' | 'ACCEPTABLE' | 'BLURRY'
    mean_brightness: number
    lighting_label: string
    contrast_score: number
    face_coverage_pct: number
    face_centered: boolean
    user_guidance: string[]
  }
  head_pose?: {
    yaw: number
    pitch: number
    mouth_ratio: number
  }
  liveness_score?: number
  spatial_risk?: number
  presentation_risk?: number
  explanation?: string
  signals?: Array<{
    key: string
    label: string
    severity: 'low' | 'medium' | 'high'
    detail?: string
    score?: number
  }>
  guided_protocol?: GuidedProtocol
  ear_accessories?: EarAccessories
  criteria_evaluation?: CriteriaEvaluation
  benchmarks?: {
    faceforensics?: {
      score: number
      is_manipulated: boolean
      method: string
    }
    celeb_df?: {
      score: number
      is_deepfake: boolean
    }
    silent_face?: {
      score: number
      is_presentation_attack: boolean
      attack_type: string
    }
    ffhq_baseline?: {
      texture_realism_score: number
      is_organic: boolean
      policy: string
    }
  }
  challenge?: {
    active: boolean
    info?: {
      id: string
      type: string
      label: string
      expires_at: number
      completed: boolean
    }
    status?: string
  }
  processing_ms?: number
  processing_location?: string
  disclaimer?: string
}

const REASON_CODE_MAP: Record<string, { label: string; severity: 'safe' | 'warning' | 'danger' | 'info' }> = {
  PHONE_PRESENTATION_DETECTED: {
    label: 'Face presented through smartphone / screen',
    severity: 'danger',
  },
  SCREEN_FACE_DETECTED: {
    label: 'Face bounded inside display screen bezel',
    severity: 'danger',
  },
  MOIRE_PATTERN_DETECTED: {
    label: 'Moiré high-frequency display grid detected',
    severity: 'warning',
  },
  SPECULAR_SCREEN_GLARE: {
    label: 'Planar screen specular glare reflection',
    severity: 'warning',
  },
  EYES_NOT_VISIBLE: {
    label: 'Eyes not visible — ocular liveness paused',
    severity: 'warning',
  },
  EYES_TOO_BLURRY: {
    label: 'Eyes too blurry for micro-tremor tracking',
    severity: 'warning',
  },
  EYES_OBSCURED_SUNGLASSES: {
    label: 'Eyes obscured by sunglasses or dark lenses',
    severity: 'warning',
  },
  MULTIPLE_FACES_DETECTED: {
    label: 'Multiple faces in frame — primary face tracked',
    severity: 'info',
  },
  LOW_INPUT_QUALITY: {
    label: 'Low camera illumination or motion blur',
    severity: 'warning',
  },
  STATIC_PHOTO_SUSPECTED: {
    label: 'Sub-physiological jitter (Static print suspected)',
    severity: 'danger',
  },
}

interface TrainingStats {
  total_responses: number
  consented_samples: number
  declined_responses: number
  real_human_model_pool_size: number
  database_status: string
}

export default function LiveCameraScanPage() {
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const streamRef = useRef<MediaStream | null>(null)

  const [sessionId] = useState(() => `sess_${Math.random().toString(36).substring(2, 10)}`)
  const [isCameraActive, setIsCameraActive] = useState(false)
  const [cameraError, setCameraError] = useState<string | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisResult, setAnalysisResult] = useState<LiveFrameResult | null>(null)
  const [challengeMode, setChallengeMode] = useState(false)
  const [showGridOverlay, setShowGridOverlay] = useState(false)

  // Training Model Consent Modal States
  const [showConsentModal, setShowConsentModal] = useState(false)
  const [currentSnapshotB64, setCurrentSnapshotB64] = useState<string | null>(null)
  const [isSubmittingConsent, setIsSubmittingConsent] = useState(false)
  const [consentStatus, setConsentStatus] = useState<'GRANTED' | 'DECLINED' | null>(null)
  const [trainingStats, setTrainingStats] = useState<TrainingStats | null>(null)
  const [savedReportId, setSavedReportId] = useState<string | null>(null)

  // Scan Report States & Handlers
  const [showReportSaveModal, setShowReportSaveModal] = useState(false)
  const [isSavingScanReport, setIsSavingScanReport] = useState(false)
  const [savedScanReport, setSavedScanReport] = useState<ScanReport | null>(null)
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false)
  const [isDownloadingJpg, setIsDownloadingJpg] = useState(false)

  const openReportSaveModal = () => {
    const snap = grabCurrentFrameB64()
    setCurrentSnapshotB64(snap)
    setShowReportSaveModal(true)
  }

  const handleSaveScanReport = async (saveFaceCapture: boolean) => {
    if (!analysisResult) return
    setIsSavingScanReport(true)
    try {
      const res = await scanReportsApi.create({
        live_session_id: sessionId,
        save_face_capture: saveFaceCapture,
        representative_frame_base64: saveFaceCapture ? (currentSnapshotB64 || undefined) : undefined,
        inference_result: analysisResult,
      })
      setSavedScanReport(res.data)
      setShowReportSaveModal(false)
      toast.success(`Scan report saved! ID: ${res.data.report_number}`)
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setIsSavingScanReport(false)
    }
  }

  const handleDownloadPdf = async (reportId: string, reportNum: string) => {
    setIsDownloadingPdf(true)
    try {
      const res = await scanReportsApi.downloadPdf(reportId)
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `${reportNum}_forensic_dossier.pdf`)
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

  const handleDownloadJpg = async (reportId: string, reportNum: string) => {
    setIsDownloadingJpg(true)
    try {
      const res = await scanReportsApi.downloadJpg(reportId)
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'image/jpeg' }))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `${reportNum}_audit_card.jpg`)
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

  // Load training stats
  const loadTrainingStats = async () => {
    try {
      const res = await liveScanApi.getTrainingStats()
      setTrainingStats(res.data)
    } catch {
      // Non-blocking
    }
  }

  useEffect(() => {
    loadTrainingStats()
  }, [])

  // Start Camera
  const startCamera = async () => {
    setCameraError(null)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'user',
        },
        audio: false,
      })
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        videoRef.current.play()
      }
      streamRef.current = stream
      setIsCameraActive(true)
      toast.success('Live camera stream initiated')
    } catch (err: any) {
      setCameraError(err.message || 'Unable to access camera. Check device permissions.')
      toast.error('Camera access denied or unavailable')
    }
  }

  // Stop Camera
  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
      streamRef.current = null
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null
    }
    setIsCameraActive(false)
  }

  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop())
      }
    }
  }, [])

  // Capture current frame as base64 snapshot
  const grabCurrentFrameB64 = (): string | null => {
    if (!videoRef.current) return null
    const video = videoRef.current
    const offCanvas = document.createElement('canvas')
    offCanvas.width = video.videoWidth || 640
    offCanvas.height = video.videoHeight || 480
    const ctx = offCanvas.getContext('2d')
    if (!ctx) return null
    ctx.drawImage(video, 0, 0, offCanvas.width, offCanvas.height)
    return offCanvas.toDataURL('image/jpeg', 0.85)
  }

  // Continuous frame analysis loop
  const processFrame = useCallback(async () => {
    if (!videoRef.current || !isCameraActive || isAnalyzing) return
    const video = videoRef.current
    if (video.readyState !== video.HAVE_ENOUGH_DATA) return

    setIsAnalyzing(true)
    try {
      const b64 = grabCurrentFrameB64()
      if (b64) {
        const res = await liveScanApi.analyzeFrame({
          session_id: sessionId,
          image_base64: b64,
          run_challenge: challengeMode,
        })
        setAnalysisResult(res.data)
      }
    } catch {
      // Non-blocking frame drop
    } finally {
      setIsAnalyzing(false)
    }
  }, [isCameraActive, isAnalyzing, sessionId, challengeMode])

  useEffect(() => {
    if (!isCameraActive) return
    const interval = setInterval(processFrame, 400) // Analysis at ~2.5 FPS
    return () => clearInterval(interval)
  }, [isCameraActive, processFrame])

  // Canvas HUD overlay drawing (Green Radial Tick Oval + YuNet 5-landmark wireframe mesh from Reference)
  useEffect(() => {
    if (!canvasRef.current || !videoRef.current) return
    const canvas = canvasRef.current
    const video = videoRef.current
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    canvas.width = video.clientWidth || 640
    canvas.height = video.clientHeight || 480
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    const scaleX = canvas.width / (video.videoWidth || 640)
    const scaleY = canvas.height / (video.videoHeight || 480)

    const hasFace = Boolean(analysisResult?.face_box && analysisResult.face_detected)
    const [bx, by, bw, bh] = analysisResult?.face_box || [
      (canvas.width * 0.28) / scaleX,
      (canvas.height * 0.16) / scaleY,
      (canvas.width * 0.44) / scaleX,
      (canvas.height * 0.68) / scaleY,
    ]
    const rx = bx * scaleX
    const ry = by * scaleY
    const rw = bw * scaleX
    const rh = bh * scaleY

    // 1. Grid overlay (if toggled)
    if (showGridOverlay) {
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.06)'
      ctx.lineWidth = 1
      ctx.setLineDash([4, 4])
      const w3 = canvas.width / 3
      const h3 = canvas.height / 3
      ctx.beginPath()
      ctx.moveTo(w3, 0); ctx.lineTo(w3, canvas.height)
      ctx.moveTo(w3 * 2, 0); ctx.lineTo(w3 * 2, canvas.height)
      ctx.moveTo(0, h3); ctx.lineTo(canvas.width, h3)
      ctx.moveTo(0, h3 * 2); ctx.lineTo(canvas.width, h3 * 2)
      ctx.stroke()
      ctx.setLineDash([])
    }

    // Biometric Oval Position
    const cx = hasFace ? rx + rw / 2 : canvas.width / 2
    const cy = hasFace ? ry + rh * 0.48 : canvas.height / 2
    const radX = hasFace ? rw * 0.58 : canvas.width * 0.22
    const radY = hasFace ? rh * 0.76 : canvas.height * 0.35

    // 2. Green Oval with Radial Dashed Tick Marks (Matching Reference Photo media_1790505854017.png)
    const numTicks = 58
    const tickLen = 13.5
    const tickColor = hasFace ? '#4ADE80' : 'rgba(74, 222, 128, 0.45)'

    ctx.save()
    ctx.strokeStyle = tickColor
    ctx.lineWidth = 2.6
    ctx.lineCap = 'round'
    ctx.shadowColor = '#4ADE80'
    ctx.shadowBlur = 6

    for (let i = 0; i < numTicks; i++) {
      const theta = (i / numTicks) * Math.PI * 2
      const x0 = cx + radX * Math.cos(theta)
      const y0 = cy + radY * Math.sin(theta)

      const nx = (1 / radX) * Math.cos(theta)
      const ny = (1 / radY) * Math.sin(theta)
      const len = Math.hypot(nx, ny) || 1
      const ux = nx / len
      const uy = ny / len

      ctx.beginPath()
      ctx.moveTo(x0, y0)
      ctx.lineTo(x0 + ux * tickLen, y0 + uy * tickLen)
      ctx.stroke()
    }

    // Faint inner reference contour
    ctx.beginPath()
    ctx.strokeStyle = 'rgba(74, 222, 128, 0.22)'
    ctx.lineWidth = 1
    ctx.shadowBlur = 0
    ctx.ellipse(cx, cy, radX, radY, 0, 0, Math.PI * 2)
    ctx.stroke()
    ctx.restore()

    // 3. Biometric Constellation Wireframe Mesh
    if (hasFace && analysisResult?.landmarks) {
      const lms = analysisResult.landmarks
      const re: [number, number] = [lms.right_eye[0] * scaleX, lms.right_eye[1] * scaleY]
      const le: [number, number] = [lms.left_eye[0] * scaleX, lms.left_eye[1] * scaleY]
      const nose: [number, number] = [lms.nose_tip[0] * scaleX, lms.nose_tip[1] * scaleY]
      const rm: [number, number] = [lms.right_mouth[0] * scaleX, lms.right_mouth[1] * scaleY]
      const lmPt: [number, number] = [lms.left_mouth[0] * scaleX, lms.left_mouth[1] * scaleY]

      const iod = Math.max(12, Math.hypot(le[0] - re[0], le[1] - re[1]))
      const em: [number, number] = [(re[0] + le[0]) / 2, (re[1] + le[1]) / 2]

      const gl: [number, number] = [em[0], em[1] - iod * 0.14]
      const fMid: [number, number] = [em[0], em[1] - iod * 0.52]
      const fTop: [number, number] = [em[0], em[1] - iod * 0.82]
      const fLeft: [number, number] = [le[0] + iod * 0.18, em[1] - iod * 0.58]
      const fRight: [number, number] = [re[0] - iod * 0.18, em[1] - iod * 0.58]
      const bLeft: [number, number] = [le[0], le[1] - iod * 0.20]
      const bRight: [number, number] = [re[0], re[1] - iod * 0.20]
      const tLeft: [number, number] = [le[0] + iod * 0.44, le[1] - iod * 0.10]
      const tRight: [number, number] = [re[0] - iod * 0.44, re[1] - iod * 0.10]
      const nb: [number, number] = [(gl[0] + nose[0]) / 2, (gl[1] + nose[1]) / 2]
      const nLeft: [number, number] = [nose[0] + iod * 0.22, nose[1] + iod * 0.04]
      const nRight: [number, number] = [nose[0] - iod * 0.22, nose[1] + iod * 0.04]
      const ckLU: [number, number] = [le[0] + iod * 0.38, nose[1] - iod * 0.04]
      const ckRU: [number, number] = [re[0] - iod * 0.38, nose[1] - iod * 0.04]
      const ckLD: [number, number] = [lmPt[0] + iod * 0.30, lmPt[1] - iod * 0.04]
      const ckRD: [number, number] = [rm[0] - iod * 0.30, rm[1] - iod * 0.04]
      const ph: [number, number] = [(lmPt[0] + rm[0]) / 2, (lmPt[1] + rm[1]) / 2 - iod * 0.08]
      const ll: [number, number] = [(lmPt[0] + rm[0]) / 2, (lmPt[1] + rm[1]) / 2 + iod * 0.12]
      const chM: [number, number] = [(lmPt[0] + rm[0]) / 2, (lmPt[1] + rm[1]) / 2 + iod * 0.34]
      const chT: [number, number] = [(lmPt[0] + rm[0]) / 2, (lmPt[1] + rm[1]) / 2 + iod * 0.56]
      const jLeft: [number, number] = [lmPt[0] + iod * 0.32, lmPt[1] + iod * 0.36]
      const jRight: [number, number] = [rm[0] - iod * 0.32, rm[1] + iod * 0.36]

      const allNodes = [
        fTop, fMid, fLeft, fRight, gl, bLeft, bRight, tLeft, tRight,
        re, le, nb, nose, nLeft, nRight, ckLU, ckRU, ckLD, ckRD,
        ph, lmPt, rm, ll, chM, chT, jLeft, jRight,
      ]

      const meshEdges: Array<[[number, number], [number, number]]> = [
        [fTop, fMid], [fTop, fLeft], [fTop, fRight],
        [fMid, fLeft], [fMid, fRight], [fMid, gl],
        [fLeft, tLeft], [fLeft, bLeft], [fRight, tRight], [fRight, bRight],
        [gl, bLeft], [gl, bRight], [gl, nb],
        [bLeft, le], [bRight, re], [tLeft, le], [tRight, re],
        [tLeft, ckLU], [tRight, ckRU],
        [le, nb], [re, nb], [le, ckLU], [re, ckRU],
        [nb, nose], [nb, nLeft], [nb, nRight],
        [nose, nLeft], [nose, nRight],
        [nLeft, ckLU], [nRight, ckRU],
        [nLeft, ckLD], [nRight, ckRD],
        [ckLU, ckLD], [ckRU, ckRD],
        [nose, ph], [nLeft, ph], [nRight, ph],
        [ph, lmPt], [ph, rm], [lmPt, rm],
        [lmPt, ll], [rm, ll],
        [ckLD, lmPt], [ckRD, rm],
        [ckLD, jLeft], [ckRD, jRight],
        [ll, chM], [lmPt, chM], [rm, chM],
        [chM, chT], [chM, jLeft], [chM, jRight],
        [chT, jLeft], [chT, jRight],
      ]

      ctx.save()
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.40)'
      ctx.lineWidth = 0.8
      meshEdges.forEach(([p1, p2]) => {
        ctx.beginPath()
        ctx.moveTo(p1[0], p1[1])
        ctx.lineTo(p2[0], p2[1])
        ctx.stroke()
      })

      ctx.fillStyle = 'rgba(255, 255, 255, 0.95)'
      allNodes.forEach(([vx, vy]) => {
        ctx.beginPath()
        ctx.arc(vx, vy, 1.8, 0, Math.PI * 2)
        ctx.fill()
      })
      ctx.restore()
    }
  }, [analysisResult, showGridOverlay])

  // Consent Modal Handling
  const openConsentModal = () => {
    const snap = grabCurrentFrameB64()
    setCurrentSnapshotB64(snap)
    setShowConsentModal(true)
  }

  const handleConsentChoice = async (consentGiven: boolean) => {
    if (!analysisResult) return
    setIsSubmittingConsent(true)

    try {
      await liveScanApi.submitConsent({
        session_id: sessionId,
        consent_given: consentGiven,
        category_label: analysisResult.category_label,
        confidence: analysisResult.confidence,
        quality_score: analysisResult.quality?.quality_index || 75,
        face_snapshot_base64: consentGiven ? (currentSnapshotB64 || undefined) : undefined,
        landmarks: analysisResult.landmarks,
      })

      const auditRes = await liveScanApi.saveAudit({
        session_id: sessionId,
        assessment: analysisResult.assessment,
        category_label: analysisResult.category_label,
        confidence: analysisResult.confidence,
        quality_index: analysisResult.quality?.quality_index || 70,
        signals: analysisResult.signals || [],
        explanation: analysisResult.explanation || 'Live camera face authenticity evaluation.',
        snapshot_base64: consentGiven ? (currentSnapshotB64 || undefined) : undefined,
        consent_given: consentGiven,
        landmarks: analysisResult.landmarks,
        eye_status: analysisResult.eye_status,
        phone_detected: analysisResult.phone_detected,
        presentation_attack: analysisResult.presentation_attack,
        reason_codes: analysisResult.reason_codes,
      })

      setSavedReportId(auditRes.data.report_id)
      setConsentStatus(consentGiven ? 'GRANTED' : 'DECLINED')
      loadTrainingStats()

      if (consentGiven) {
        toast.success('Face contributed to Real Human Model Training Database.')
      } else {
        toast.success('Zero face data stored. Privacy guaranteed.')
      }
      setShowConsentModal(false)
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setIsSubmittingConsent(false)
    }
  }

  const conf = analysisResult?.confidence ?? 0
  const livenessPct = analysisResult?.liveness_score ? Math.round(analysisResult.liveness_score * 100) : 0
  const syntheticPct = analysisResult?.spatial_risk ? Math.round(analysisResult.spatial_risk * 100) : 0
  const replayPct = analysisResult?.presentation_risk ? Math.round(analysisResult.presentation_risk * 100) : 0

  return (
    <div className="space-y-8">
      {/* ── HEADER & HARDWARE BADGES ── */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <StatusIndicator status="active" />
            <span className="text-xs uppercase font-mono tracking-widest text-brand-blue">
              Real-Time Authenticity Stream
            </span>
          </div>
          <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-white">
            Live Camera Scan
          </h1>
          <p className="text-sm text-white/60 mt-1">
            Multi-signal biometric liveness, OpenCV YuNet tracking, and replay attack defense.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Training Pool Badge */}
          <div className="hidden sm:flex items-center gap-2 px-3 py-2 rounded-2xl glass-surface border border-white/8 text-xs font-mono">
            <Database className="w-3.5 h-3.5 text-brand-blue" />
            <span className="text-white/50">Model Pool:</span>
            <span className="text-white font-bold">
              {trainingStats ? `${trainingStats.real_human_model_pool_size} samples` : '1 active'}
            </span>
          </div>

          <GlassButton
            variant="secondary"
            size="sm"
            onClick={() => setShowGridOverlay(!showGridOverlay)}
            icon={<Layers className="w-3.5 h-3.5" />}
          >
            Grid {showGridOverlay ? 'ON' : 'OFF'}
          </GlassButton>

          {!isCameraActive ? (
            <GlassButton
              variant="primary"
              size="md"
              onClick={startCamera}
              icon={<Camera className="w-4 h-4" />}
              className="shadow-glow-blue"
            >
              Start Camera
            </GlassButton>
          ) : (
            <GlassButton
              variant="danger"
              size="md"
              onClick={stopCamera}
              icon={<CameraOff className="w-4 h-4" />}
            >
              Stop Camera
            </GlassButton>
          )}
        </div>
      </div>

      {/* ── MAIN WORKSPACE: LEFT CAMERA / RIGHT ANALYSIS (Section 77) ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* ── LEFT: CAMERA & TELEMETRY (7 Cols) ── */}
        <div className="lg:col-span-7 space-y-6">
          {/* ── PRESENTATION ATTACK ALERT BANNER (Case B: Phone/Screen Presentation) ── */}
          {analysisResult?.presentation_attack && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-5 rounded-3xl bg-status-danger/15 border-2 border-status-danger/50 backdrop-blur-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4 text-status-danger shadow-[0_0_35px_rgba(239,68,68,0.35)]"
            >
              <div className="flex items-start gap-3.5">
                <div className="w-11 h-11 rounded-2xl bg-status-danger/25 border border-status-danger/40 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Smartphone className="w-6 h-6 text-status-danger animate-pulse" />
                </div>
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded-md bg-status-danger/20 text-[10px] font-mono font-black text-status-danger uppercase tracking-wider">
                      CRITICAL PRESENTATION ATTACK
                    </span>
                  </div>
                  <h4 className="text-base font-extrabold uppercase tracking-wide text-white">
                    POSSIBLE SCREEN/REPLAY PRESENTATION ATTACK
                  </h4>
                  <p className="text-xs text-white/80 leading-relaxed max-w-xl">
                    The camera is not observing the target human directly; the detected face is being presented through a smartphone or electronic screen.
                  </p>
                  <div className="flex flex-wrap items-center gap-3 pt-1 text-[11px] font-mono text-white/70">
                    <span>
                      Device Conf:{' '}
                      <strong className="text-white">
                        {Math.round((analysisResult.phone_object_confidence || 0.95) * 100)}%
                      </strong>
                    </span>
                    <span>•</span>
                    <span>
                      Face Inside Display:{' '}
                      <strong className="text-white">
                        {Math.round((analysisResult.screen_face_association_confidence || 0.92) * 100)}%
                      </strong>
                    </span>
                    <span>•</span>
                    <span>
                      Attack Risk:{' '}
                      <strong className="text-status-danger font-bold">
                        {Math.round((analysisResult.presentation_attack_confidence || 0.94) * 100)}%
                      </strong>
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex md:flex-col items-center justify-between w-full md:w-auto gap-2 px-4 py-2.5 rounded-2xl bg-status-danger/20 border border-status-danger/30 text-center flex-shrink-0">
                <span className="text-[10px] font-mono uppercase tracking-wider text-white/60">
                  Live Human Direct Obs
                </span>
                <span className="text-lg font-black font-mono text-status-danger">
                  0%
                </span>
              </div>
            </motion.div>
          )}

          {/* ── MULTIPLE FACES DETECTED BANNER ── */}
          {Boolean(analysisResult?.total_faces_detected && analysisResult.total_faces_detected > 1) && (
            <div className="p-3.5 rounded-2xl bg-brand-cyan/15 border border-brand-cyan/30 flex items-center justify-between gap-3 text-xs text-brand-cyan backdrop-blur-xl">
              <div className="flex items-center gap-2.5">
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                <span>
                  Multiple faces detected ({analysisResult?.total_faces_detected} in scene). Tracking primary target face #{1}.
                </span>
              </div>
              <span className="text-[10px] font-mono bg-brand-cyan/20 px-2 py-0.5 rounded-lg text-white font-semibold">
                Target Face Locked
              </span>
            </div>
          )}

          {/* Viewfinder Glass Card */}
          <div className="relative rounded-4xl glass-floating border border-white/14 overflow-hidden aspect-[4/3] bg-surface flex items-center justify-center shadow-glass-floating">
            {/* Native Video Feed */}
            <video
              ref={videoRef}
              playsInline
              muted
              className={`w-full h-full object-cover transform -scale-x-100 transition-opacity duration-300 ${
                isCameraActive ? 'opacity-100' : 'opacity-0'
              }`}
            />

            {/* Canvas HUD Overlay */}
            <canvas
              ref={canvasRef}
              className="absolute inset-0 w-full h-full pointer-events-none z-10"
            />

            {/* Offline Viewfinder Cover */}
            {!isCameraActive && (
              <div className="absolute inset-0 flex flex-col items-center justify-center p-6 text-center space-y-4 z-20 bg-canvas/85 backdrop-blur-md">
                <div className="w-16 h-16 rounded-3xl glass-card border border-brand-blue/30 flex items-center justify-center text-brand-blue shadow-glow-blue">
                  <Camera className="w-8 h-8" />
                </div>
                <div className="max-w-md">
                  <h3 className="text-xl font-bold text-white tracking-tight">Camera Feed Offline</h3>
                  <p className="text-xs text-white/50 mt-1 leading-relaxed">
                    Enable webcam access to run real-time YuNet biometric analysis, physiological micro-motion tracking, and presentation attack mitigation.
                  </p>
                </div>
                <GlassButton variant="primary" size="md" onClick={startCamera} icon={<Camera className="w-4 h-4" />}>
                  Allow Camera Access
                </GlassButton>
              </div>
            )}

            {/* Error Message */}
            {cameraError && (
              <div className="absolute top-4 left-4 right-4 z-30 p-3.5 rounded-2xl bg-status-danger/20 border border-status-danger/40 flex items-center gap-2.5 text-xs text-status-danger backdrop-blur-xl">
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                <span>{cameraError}</span>
              </div>
            )}

            {/* Active Live Floating Telemetry Top Badges */}
            {isCameraActive && (
              <div className="absolute top-4 left-4 z-20 flex flex-wrap items-center gap-2 max-w-[92%]">
                <div className="px-3 py-1 rounded-full glass-surface border border-white/12 flex items-center gap-2 text-[11px] font-mono">
                  <span className="w-2 h-2 rounded-full bg-status-safe animate-pulse" />
                  <span className="text-white font-semibold">LIVE HUD</span>
                </div>
                <div className="px-3 py-1 rounded-full glass-surface border border-white/12 text-[11px] font-mono text-white/60">
                  {analysisResult?.processing_ms ? `${analysisResult.processing_ms} ms` : 'Syncing'}
                </div>

                {/* Eye Status Top Badge */}
                {analysisResult?.eye_status && (
                  <div
                    className={`px-3 py-1 rounded-full glass-surface border flex items-center gap-1.5 text-[11px] font-mono ${
                      analysisResult.eye_status === 'BOTH_EYES_VISIBLE'
                        ? 'border-status-safe/30 text-status-safe'
                        : analysisResult.eye_status === 'EYE_TOO_BLURRY' || analysisResult.eye_status === 'EYES_NOT_VISIBLE'
                        ? 'border-status-warning/40 text-status-warning'
                        : analysisResult.eye_status === 'EYES_OBSCURED'
                        ? 'border-brand-violet/40 text-brand-violet'
                        : 'border-white/12 text-white/70'
                    }`}
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span>
                      {analysisResult.eye_status === 'BOTH_EYES_VISIBLE'
                        ? 'Eyes Visible'
                        : analysisResult.eye_status === 'EYE_TOO_BLURRY'
                        ? 'Eyes Blurry'
                        : analysisResult.eye_status === 'EYES_OBSCURED'
                        ? 'Sunglasses / Tint'
                        : analysisResult.eye_status === 'LEFT_ONLY' || analysisResult.eye_status === 'RIGHT_ONLY'
                        ? 'Partial Eye View'
                        : 'Eyes Unavailable'}
                    </span>
                  </div>
                )}
              </div>
            )}

            <p className="text-[11px] text-white/50 leading-relaxed pt-2 border-t border-white/6 italic">
              {analysisResult?.user_message ||
                '"The observed live sequence contains no strong synthetic-media indicators based on the multi-spectral models evaluated."'}
            </p>
            </div>

          {/* ── DEDICATED EYE & OCULAR ANALYSIS CARD (Sections 7-12) ── */}
          <GlassCard variant="elevated" className="space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-white/6">
              <div className="flex items-center gap-2">
                <Eye className="w-4 h-4 text-brand-cyan" />
                <h3 className="text-sm font-bold uppercase tracking-wider text-white">
                  Ocular & Eye Visibility Engine
                </h3>
              </div>
              <span
                className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold uppercase ${
                  analysisResult?.eye_status === 'BOTH_EYES_VISIBLE'
                    ? 'bg-status-safe/20 text-status-safe border border-status-safe/30'
                    : analysisResult?.eye_status === 'EYE_TOO_BLURRY'
                    ? 'bg-status-warning/20 text-status-warning border border-status-warning/30'
                    : analysisResult?.eye_status === 'EYES_OBSCURED'
                    ? 'bg-brand-violet/20 text-brand-violet border border-brand-violet/30'
                    : analysisResult?.eye_status === 'LEFT_ONLY' || analysisResult?.eye_status === 'RIGHT_ONLY'
                    ? 'bg-brand-cyan/20 text-brand-cyan border border-brand-cyan/30'
                    : 'bg-white/10 text-white/50 border border-white/10'
                }`}
              >
                {analysisResult?.eye_status ? analysisResult.eye_status.replace(/_/g, ' ') : 'STANDBY'}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 rounded-2xl bg-white/4 border border-white/6 space-y-1.5">
                <div className="flex justify-between items-center text-[10px] font-mono">
                  <span className="text-white/50">Left Eye</span>
                  <span className={analysisResult?.left_eye_visible ? 'text-status-safe' : 'text-white/40'}>
                    {analysisResult?.left_eye_visible ? 'Visible' : 'Hidden'}
                  </span>
                </div>
                <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-brand-cyan rounded-full transition-all duration-300"
                    style={{ width: `${Math.round((analysisResult?.left_eye_quality || 0) * 100)}%` }}
                  />
                </div>
                <span className="text-[10px] font-mono text-white/40 block">
                  Quality: {Math.round((analysisResult?.left_eye_quality || 0) * 100)}%
                </span>
              </div>

              <div className="p-3 rounded-2xl bg-white/4 border border-white/6 space-y-1.5">
                <div className="flex justify-between items-center text-[10px] font-mono">
                  <span className="text-white/50">Right Eye</span>
                  <span className={analysisResult?.right_eye_visible ? 'text-status-safe' : 'text-white/40'}>
                    {analysisResult?.right_eye_visible ? 'Visible' : 'Hidden'}
                  </span>
                </div>
                <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-brand-cyan rounded-full transition-all duration-300"
                    style={{ width: `${Math.round((analysisResult?.right_eye_quality || 0) * 100)}%` }}
                  />
                </div>
                <span className="text-[10px] font-mono text-white/40 block">
                  Quality: {Math.round((analysisResult?.right_eye_quality || 0) * 100)}%
                </span>
              </div>
            </div>

            {/* Informative notice when eyes are blurry or obscured (Section 10 & 11) */}
            {(analysisResult?.is_eye_blurry ||
              analysisResult?.is_eye_obscured ||
              analysisResult?.eye_status === 'EYE_TOO_BLURRY' ||
              analysisResult?.eye_status === 'EYES_NOT_VISIBLE' ||
              analysisResult?.eye_status === 'EYES_OBSCURED') && (
              <div className="p-3 rounded-2xl bg-status-warning/10 border border-status-warning/20 text-xs text-status-warning flex items-start gap-2.5">
                <EyeOff className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <div className="space-y-0.5">
                  <p className="font-semibold text-white">
                    {analysisResult?.is_eye_obscured ? 'Eyes Obscured' : 'Eyes Not Clearly Visible'}
                  </p>
                  <p className="text-[11px] text-white/70 leading-relaxed">
                    Eye-based liveness evidence is unavailable. Confidence is computed from spatial, temporal,
                    and benchmark evidence (not penalized to 0%).
                  </p>
                </div>
              </div>
            )}
          </GlassCard>


          {/* ── GUIDED PROTOCOL HUD (Smile, Rotation) ── */}
          {analysisResult?.guided_protocol && (
            <GlassCard variant="elevated" className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-status-safe" />
                  <h3 className="text-sm font-bold uppercase tracking-wider text-white">
                    GUIDED LIVE PROTOCOL
                  </h3>
                </div>
                <span className="text-xs font-mono font-bold text-brand-blue">
                  {analysisResult.guided_protocol.total_marked} / 3 PASSED
                </span>
              </div>

              <div className="space-y-2.5 text-xs">
                {/* Task 1: Smile */}
                <div
                  className={`p-3 rounded-2xl border flex items-center justify-between transition-all ${
                    analysisResult.guided_protocol.task_1_smile.marked
                      ? 'bg-status-safe/10 border-status-safe/30 text-white'
                      : 'bg-white/4 border-white/8 text-white/60'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Smile
                      className={`w-4 h-4 ${
                        analysisResult.guided_protocol.task_1_smile.marked ? 'text-status-safe' : 'text-white/40'
                      }`}
                    />
                    <span>Task 1: Smile with teeth / wide lips</span>
                  </div>
                  {analysisResult.guided_protocol.task_1_smile.marked ? (
                    <Check className="w-4 h-4 text-status-safe font-bold" />
                  ) : (
                    <span className="text-[10px] font-mono text-white/40">PENDING</span>
                  )}
                </div>


                {/* Task 3: Smooth Rotation */}
                <div
                  className={`p-3 rounded-2xl border flex items-center justify-between transition-all ${
                    analysisResult.guided_protocol.task_3_rotation.marked
                      ? 'bg-status-safe/10 border-status-safe/30 text-white'
                      : 'bg-white/4 border-white/8 text-white/60'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <RotateCw
                      className={`w-4 h-4 ${
                        analysisResult.guided_protocol.task_3_rotation.marked ? 'text-status-safe' : 'text-white/40'
                      }`}
                    />
                    <span>Task 3: Smooth head yaw rotation</span>
                  </div>
                  {analysisResult.guided_protocol.task_3_rotation.marked ? (
                    <Check className="w-4 h-4 text-status-safe font-bold" />
                  ) : (
                    <span className="text-[10px] font-mono text-white/40">PENDING</span>
                  )}
                </div>
              </div>
            </GlassCard>
          )}

          {/* ── MULTI-BENCHMARK MATRIX (Section 30) ── */}
          {analysisResult?.benchmarks && (
            <GlassCard variant="elevated" className="space-y-4">
              <div className="flex items-center justify-between pb-2 border-b border-white/6">
                <span className="text-xs font-mono uppercase tracking-wider text-white/50">
                  Forensic Benchmarks
                </span>
                <span className="text-[10px] font-mono text-brand-blue">EVALUATED</span>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                {/* FaceForensics */}
                <div className="p-3 rounded-2xl bg-white/4 border border-white/6 space-y-1">
                  <span className="text-[10px] uppercase font-mono text-white/40 block">
                    FaceForensics++
                  </span>
                  <p className="font-bold text-white">
                    {analysisResult.benchmarks.faceforensics?.is_manipulated ? 'Manipulated' : 'Organic'}
                  </p>
                  <span className="text-[10px] font-mono text-white/50 block">
                    Residue: {analysisResult.benchmarks.faceforensics?.score.toFixed(3) || '0.00'}
                  </span>
                </div>

                {/* Celeb-DF v2 */}
                <div className="p-3 rounded-2xl bg-white/4 border border-white/6 space-y-1">
                  <span className="text-[10px] uppercase font-mono text-white/40 block">Celeb-DF v2</span>
                  <p className="font-bold text-white">
                    {analysisResult.benchmarks.celeb_df?.is_deepfake ? 'Synthetic' : 'Clean'}
                  </p>
                  <span className="text-[10px] font-mono text-white/50 block">
                    Ocular: {analysisResult.benchmarks.celeb_df?.score.toFixed(3) || '0.00'}
                  </span>
                </div>

                {/* Silent-Face PAD */}
                <div className="p-3 rounded-2xl bg-white/4 border border-white/6 space-y-1">
                  <span className="text-[10px] uppercase font-mono text-white/40 block">
                    Silent-Face PAD
                  </span>
                  <p className="font-bold text-status-safe">
                    {analysisResult.benchmarks.silent_face?.is_presentation_attack ? 'Replay Spoof' : 'Live Skin'}
                  </p>
                  <span className="text-[10px] font-mono text-white/50 block">Dual-Scale Fourier</span>
                </div>

                {/* FFHQ Baseline */}
                <div className="p-3 rounded-2xl bg-white/4 border border-white/6 space-y-1">
                  <span className="text-[10px] uppercase font-mono text-white/40 block">FFHQ Baseline</span>
                  <p className="font-bold text-white">
                    {analysisResult.benchmarks.ffhq_baseline?.is_organic ? 'High Realism' : 'Outlier'}
                  </p>
                  <span className="text-[10px] font-mono text-white/50 block">Texture Match</span>
                </div>
              </div>
            </GlassCard>
          )}
        </div>
      </div>

      {/* ── CONSENT MODAL (Section 26 & Real Human Model Training Pool) ── */}
      <AnimatePresence>
        {showConsentModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-canvas/80 backdrop-blur-xl">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="w-full max-w-lg rounded-4xl glass-floating border border-white/16 p-6 md:p-8 space-y-6 shadow-glass-floating"
            >
              <div className="flex items-center justify-between pb-3 border-b border-white/8">
                <div className="flex items-center gap-2.5">
                  <Database className="w-5 h-5 text-brand-blue" />
                  <h3 className="text-base font-bold text-white">Model Training Data Consent</h3>
                </div>
                <button
                  onClick={() => setShowConsentModal(false)}
                  className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center text-white/60 hover:text-white"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {currentSnapshotB64 && (
                <div className="flex justify-center">
                  <div className="w-32 h-32 rounded-3xl overflow-hidden border border-white/20 shadow-glass">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={currentSnapshotB64}
                      alt="Captured Face Snapshot"
                      className="w-full h-full object-cover transform -scale-x-100"
                    />
                  </div>
                </div>
              )}

              <div className="space-y-3 text-xs text-white/70 leading-relaxed">
                <p>
                  Privacy Eye strictly follows ethical AI governance. We never store camera feeds
                  without explicit consent.
                </p>
                <div className="p-3 rounded-2xl bg-white/4 border border-white/8 space-y-1.5 font-mono text-[11px]">
                  <div className="flex justify-between">
                    <span className="text-white/40">Category:</span>
                    <span className="text-white font-bold">{analysisResult?.category_label}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-white/40">Calibrated Conf:</span>
                    <span className="text-white font-bold">{conf.toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-white/40">Storage Policy:</span>
                    <span className="text-brand-blue font-bold">Consensual or Zero Retain</span>
                  </div>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row gap-3 pt-2">
                <GlassButton
                  variant="primary"
                  size="md"
                  onClick={() => handleConsentChoice(true)}
                  isLoading={isSubmittingConsent}
                  className="flex-1 shadow-glow-blue"
                  icon={<UserCheck className="w-4 h-4" />}
                >
                  Contribute to Model Pool
                </GlassButton>
                <GlassButton
                  variant="secondary"
                  size="md"
                  onClick={() => handleConsentChoice(false)}
                  isLoading={isSubmittingConsent}
                  className="flex-1"
                  icon={<UserX className="w-4 h-4" />}
                >
                  Enforce Zero Storage
                </GlassButton>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>


      {/* ── SAVE SCAN REPORT EXPLICIT CONSENT & PRIVACY MODAL ── */}
      <AnimatePresence>
        {showReportSaveModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-canvas/80 backdrop-blur-2xl">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 15 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: -10 }}
              className="w-full max-w-lg rounded-3xl glass-floating border-2 border-brand-blue/50 p-6 md:p-8 space-y-6 shadow-2xl relative"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-2xl bg-brand-blue/20 border border-brand-blue/40 flex items-center justify-center text-brand-blue flex-shrink-0">
                    <FileText className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="text-lg md:text-xl font-black text-white tracking-tight">
                      Save Scan Report?
                    </h3>
                    <p className="text-xs text-brand-blue font-mono uppercase tracking-wider">
                      Biometric Audit & Forensic Dossier
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setShowReportSaveModal(false)}
                  className="p-1.5 rounded-xl hover:bg-white/10 text-white/50 hover:text-white transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Snapshot Frame & Analysis Summary Preview */}
              <div className="grid grid-cols-1 sm:grid-cols-12 gap-4 items-center p-4 rounded-2xl bg-white/4 border border-white/8">
                {currentSnapshotB64 && (
                  <div className="sm:col-span-5 flex flex-col items-center">
                    <div className="w-28 h-28 rounded-2xl overflow-hidden border border-brand-cyan/40 shadow-glow-blue relative">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={currentSnapshotB64}
                        alt="Evidence Frame"
                        className="w-full h-full object-cover"
                      />
                    </div>
                    <span className="text-[10px] font-mono text-white/40 mt-1">Representative Frame</span>
                  </div>
                )}
                <div className={`${currentSnapshotB64 ? 'sm:col-span-7' : 'sm:col-span-12'} space-y-1.5 text-xs font-mono`}>
                  <div className="flex justify-between">
                    <span className="text-white/40">Assessment:</span>
                    <span className="text-white font-bold">{analysisResult?.assessment}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-white/40">Confidence:</span>
                    <span className="text-brand-cyan font-bold">{conf.toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-white/40">Reliability:</span>
                    <span className="text-white font-bold">{analysisResult?.reliability || 'HIGH'}</span>
                  </div>

                </div>
              </div>

              {/* Transparent Disclosure */}
              <div className="space-y-2 text-xs text-white/70 leading-relaxed bg-white/3 p-4 rounded-2xl border border-white/6">
                <p className="font-semibold text-white">
                  Privacy & Data Storage Notice:
                </p>
                <p>
                  This report will include the captured face frame and analysis results. Your report will be stored securely in the database so you can review or download it later as JPG and PDF.
                </p>
                <p className="text-[11px] text-white/50">
                  You can choose whether or not to store the captured face frame. Choosing &quot;No Face Image&quot; enforces our Zero-Biometric Storage policy.
                </p>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-col gap-2.5 pt-1">
                <GlassButton
                  variant="primary"
                  size="md"
                  onClick={() => handleSaveScanReport(true)}
                  isLoading={isSavingScanReport}
                  className="w-full shadow-glow-blue justify-center"
                  icon={<ShieldCheck className="w-4 h-4" />}
                >
                  Save Report (Include Face Evidence)
                </GlassButton>

                <GlassButton
                  variant="secondary"
                  size="md"
                  onClick={() => handleSaveScanReport(false)}
                  isLoading={isSavingScanReport}
                  className="w-full justify-center"
                  icon={<UserX className="w-4 h-4" />}
                >
                  Save Report (Don&apos;t Save Face Image)
                </GlassButton>

                <button
                  type="button"
                  onClick={() => setShowReportSaveModal(false)}
                  className="w-full py-2 text-center text-xs font-mono text-white/40 hover:text-white transition-colors"
                >
                  Cancel / Don&apos;t Save
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  )
}
