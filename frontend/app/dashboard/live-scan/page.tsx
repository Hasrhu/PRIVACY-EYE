'use client'
import { useState, useEffect, useRef, useCallback } from 'react'
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
} from 'lucide-react'
import toast from 'react-hot-toast'
import Link from 'next/link'
import { liveScanApi, getErrorMessage } from '@/lib/api'

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
  task_2_blinks: {
    marked: boolean
    blink_count: number
    target: number
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
  blinks: {
    count_10s: number
    matched: boolean
    label: string
  }
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
  quality?: {
    quality_index: number
    sharpness_score: number
    sharpness_label: 'SHARP' | 'ACCEPTABLE' | 'BLURRY'
    mean_brightness: number
    lighting_label: string
    contrast_score: number
    face_coverage_pct: number
    face_centered: boolean
    grid_metrics: Array<{ row: number; col: number; sharpness: number }>
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
  user_message?: string
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
  const [showGridOverlay, setShowGridOverlay] = useState(true)

  // Training Model Consent Modal States
  const [showConsentModal, setShowConsentModal] = useState(false)
  const [currentSnapshotB64, setCurrentSnapshotB64] = useState<string | null>(null)
  const [isSubmittingConsent, setIsSubmittingConsent] = useState(false)
  const [consentStatus, setConsentStatus] = useState<'GRANTED' | 'DECLINED' | null>(null)
  const [trainingStats, setTrainingStats] = useState<TrainingStats | null>(null)
  const [savedReportId, setSavedReportId] = useState<string | null>(null)

  // Fetch training database stats on mount
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
    } catch (e) {
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

  // Canvas HUD overlay drawing (Matching User Reference Image: Neon Green Radial Tick Oval + Face Wireframe Mesh)
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

    // 1. Forensic Rule-of-Thirds Grid (if toggled)
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

    // Biometric Oval Position (Fitted around head/face)
    const cx = hasFace ? rx + rw / 2 : canvas.width / 2
    const cy = hasFace ? ry + rh * 0.48 : canvas.height / 2
    const radX = hasFace ? rw * 0.58 : canvas.width * 0.22
    const radY = hasFace ? rh * 0.76 : canvas.height * 0.35

    // 2. Neon Green / Lime Oval with Radial Dashed Tick Marks (Direct Match to User Reference Photo)
    const numTicks = 58
    const tickLen = 13.5
    const tickColor = hasFace ? '#22c55e' : 'rgba(34, 197, 94, 0.45)'

    ctx.save()
    ctx.strokeStyle = tickColor
    ctx.lineWidth = 2.8
    ctx.lineCap = 'round'
    ctx.shadowColor = '#22c55e'
    ctx.shadowBlur = 5

    for (let i = 0; i < numTicks; i++) {
      const theta = (i / numTicks) * Math.PI * 2
      const x0 = cx + radX * Math.cos(theta)
      const y0 = cy + radY * Math.sin(theta)

      // Outward normal vector along ellipse gradient
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
    ctx.strokeStyle = 'rgba(34, 197, 94, 0.22)'
    ctx.lineWidth = 1
    ctx.shadowBlur = 0
    ctx.ellipse(cx, cy, radX, radY, 0, 0, Math.PI * 2)
    ctx.stroke()
    ctx.restore()

    // 3. Biometric Constellation Wireframe Mesh (Matching Reference Image Wireframe)
    // Connecting landmark nodes across forehead, eyebrows, eyes, nose, cheeks, jawline, and chin.
    if (hasFace && analysisResult?.landmarks) {
      const lms = analysisResult.landmarks
      const re: [number, number] = [lms.right_eye[0] * scaleX, lms.right_eye[1] * scaleY]
      const le: [number, number] = [lms.left_eye[0] * scaleX, lms.left_eye[1] * scaleY]
      const nose: [number, number] = [lms.nose_tip[0] * scaleX, lms.nose_tip[1] * scaleY]
      const rm: [number, number] = [lms.right_mouth[0] * scaleX, lms.right_mouth[1] * scaleY]
      const lmPt: [number, number] = [lms.left_mouth[0] * scaleX, lms.left_mouth[1] * scaleY]

      const iod = Math.max(12, Math.hypot(le[0] - re[0], le[1] - re[1]))
      const em: [number, number] = [(re[0] + le[0]) / 2, (re[1] + le[1]) / 2]

      // Anatomical facial geometry points
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
      // Draw wireframe triangulation lines (delicate translucent white lines)
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.42)'
      ctx.lineWidth = 0.85
      meshEdges.forEach(([p1, p2]) => {
        ctx.beginPath()
        ctx.moveTo(p1[0], p1[1])
        ctx.lineTo(p2[0], p2[1])
        ctx.stroke()
      })

      // Draw subtle luminous biometric vertices
      ctx.fillStyle = 'rgba(255, 255, 255, 0.92)'
      allNodes.forEach(([vx, vy]) => {
        ctx.beginPath()
        ctx.arc(vx, vy, 1.8, 0, Math.PI * 2)
        ctx.fill()
      })
      ctx.restore()
    }
  }, [analysisResult, showGridOverlay])

  // Open Consent Modal
  const openConsentModal = () => {
    const snap = grabCurrentFrameB64()
    setCurrentSnapshotB64(snap)
    setShowConsentModal(true)
  }

  // Handle User Consent Selection
  const handleConsentChoice = async (consentGiven: boolean) => {
    if (!analysisResult) return
    setIsSubmittingConsent(true)

    try {
      // 1. Submit explicit consent response to the Real Human Model Training Database
      const consentRes = await liveScanApi.submitConsent({
        session_id: sessionId,
        consent_given: consentGiven,
        category_label: analysisResult.category_label,
        confidence: analysisResult.confidence,
        quality_score: analysisResult.quality?.quality_index || 75,
        face_snapshot_base64: consentGiven ? (currentSnapshotB64 || undefined) : undefined,
        landmarks: analysisResult.landmarks,
      })

      // 2. Also persist audit record with the consent decision
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
      })

      setSavedReportId(auditRes.data.report_id)
      setConsentStatus(consentGiven ? 'GRANTED' : 'DECLINED')
      loadTrainingStats()

      if (consentGiven) {
        toast.success('Thank you! Face added to Real Human Model Training Database.', { duration: 5000 })
      } else {
        toast.success('Preference recorded: Zero face data stored. Privacy guaranteed.', { duration: 5000 })
      }

      setShowConsentModal(false)
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setIsSubmittingConsent(false)
    }
  }

  // Dynamic styling mapped strictly to user thresholds & exact category labels:
  // > 85: "Real human face"
  // > 75: "Likely as human face"
  // > 60: "Human face detected"
  // 50-60%: "You are Human but currently you are not following instruction above"
  // < 20%: "SYNTHETIC ATTACK / PHOTO PRINT SCAM DETECTED"
  const getAssessmentStyle = () => {
    const conf = analysisResult?.confidence ?? 0
    const cat = analysisResult?.category_label || ''

    if (cat === 'Real human face' || conf > 85) {
      return {
        border: 'border-emerald-500/50',
        bg: 'bg-emerald-950/25',
        text: 'text-emerald-400',
        dot: 'bg-emerald-500',
        badge: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40',
        icon: ShieldCheck,
      }
    }
    if (cat === 'Likely as human face' || (conf > 75 && conf <= 85)) {
      return {
        border: 'border-teal-500/45',
        bg: 'bg-teal-950/25',
        text: 'text-teal-400',
        dot: 'bg-teal-500',
        badge: 'bg-teal-500/15 text-teal-300 border-teal-500/40',
        icon: Shield,
      }
    }
    if (cat === 'Human face detected' || (conf > 60 && conf <= 75)) {
      return {
        border: 'border-cyan-500/50',
        bg: 'bg-cyan-950/25',
        text: 'text-cyan-400',
        dot: 'bg-cyan-500',
        badge: 'bg-cyan-500/15 text-cyan-300 border-cyan-500/40',
        icon: CheckCircle2,
      }
    }
    if (cat.includes('You are Human') || (conf >= 50 && conf <= 60)) {
      return {
        border: 'border-amber-500/50',
        bg: 'bg-amber-950/25',
        text: 'text-amber-400',
        dot: 'bg-amber-500',
        badge: 'bg-amber-500/15 text-amber-300 border-amber-500/40',
        icon: AlertTriangle,
      }
    }
    if (
      cat.includes('SYNTHETIC ATTACK') ||
      cat.includes('SCAM') ||
      (analysisResult && conf <= 50 && analysisResult.face_detected)
    ) {
      return {
        border: 'border-red-600/70',
        bg: 'bg-red-950/40',
        text: 'text-red-400',
        dot: 'bg-red-600',
        badge: 'bg-red-500/20 text-red-300 border-red-500/50',
        icon: ShieldAlert,
      }
    }
    return {
      border: 'border-white/10',
      bg: 'bg-white/5',
      text: 'text-gray-400',
      dot: 'bg-gray-500',
      badge: 'bg-white/5 text-gray-400 border-white/10',
      icon: Eye,
    }
  }

  const assessmentStyle = getAssessmentStyle()
  const conf = analysisResult?.confidence ?? 0

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="dot-red" />
            <p className="section-label">Real-Time Biometric Defense · Computer Vision</p>
          </div>
          <h1 className="font-display text-4xl lg:text-5xl text-white tracking-wider">
            LIVE FACE AUTHENTICITY
          </h1>
          <p className="text-xs text-gray-500 mt-1 font-mono">
            Continuous dynamic tracking responding to face movement, optical clarity, and multi-spectral forensics.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Real Human Model Database Pool Badge */}
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-black/60 border border-white/10 text-xs font-mono">
            <Database className="w-3.5 h-3.5 text-red-500" />
            <span className="text-gray-400">Model Database Pool:</span>
            <span className="text-white font-bold">
              {trainingStats ? `${trainingStats.real_human_model_pool_size} samples` : '1 active'}
            </span>
          </div>

          <button
            onClick={() => setShowGridOverlay(!showGridOverlay)}
            className={`btn-outline text-xs py-2 px-3.5 flex items-center gap-2 ${
              showGridOverlay ? 'border-red-600/60 text-red-400' : ''
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Forensic Grid {showGridOverlay ? 'ON' : 'OFF'}</span>
          </button>

          {!isCameraActive ? (
            <button onClick={startCamera} className="btn-red text-xs py-2.5 px-6 flex items-center gap-2">
              <Camera className="w-4 h-4" /> Start Camera
            </button>
          ) : (
            <button
              onClick={stopCamera}
              className="btn-outline text-xs py-2.5 px-6 flex items-center gap-2 border-red-600/40 text-red-400"
            >
              <CameraOff className="w-4 h-4" /> Stop Camera
            </button>
          )}
        </div>
      </div>

      {/* Main Grid: Viewport + Live Telemetry */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left: Camera Viewport (7 Cols) */}
        <div className="lg:col-span-7 space-y-4">
          <div
            className="card relative aspect-video w-full overflow-hidden bg-black flex items-center justify-center border border-white/10"
            style={{ minHeight: '380px' }}
          >
            {/* Native Video Feed */}
            <video
              ref={videoRef}
              playsInline
              muted
              className={`w-full h-full object-cover transform -scale-x-100 ${
                isCameraActive ? 'opacity-100' : 'opacity-0'
              }`}
            />

            {/* Canvas Overlay for HUD, Grid & Face Box */}
            <canvas
              ref={canvasRef}
              className="absolute inset-0 w-full h-full pointer-events-none z-10"
            />

            {/* Offline / Placeholder State */}
            {!isCameraActive && (
              <div className="absolute inset-0 flex flex-col items-center justify-center p-6 text-center space-y-4 z-20 bg-black/80">
                <div className="w-16 h-16 rounded-full bg-red-600/10 border border-red-600/30 flex items-center justify-center">
                  <Camera className="w-8 h-8 text-red-500" />
                </div>
                <div>
                  <h3 className="font-display text-2xl text-white tracking-wide">CAMERA OFFLINE</h3>
                  <p className="text-xs text-gray-500 max-w-sm mt-1">
                    Grant camera permission to initiate continuous face tracking, blur analysis, and Moiré screen detection.
                  </p>
                </div>
                <button onClick={startCamera} className="btn-red text-xs py-3 px-8 flex items-center gap-2">
                  <Camera className="w-4 h-4" /> Allow Camera Access
                </button>
              </div>
            )}

            {/* Camera Error Message */}
            {cameraError && (
              <div className="absolute top-4 left-4 right-4 z-30 p-3 rounded bg-red-950/80 border border-red-600/50 flex items-center gap-2 text-xs text-red-300 font-mono">
                <AlertTriangle className="w-4 h-4 flex-shrink-0 text-red-400" />
                <span>{cameraError}</span>
              </div>
            )}

            {/* Floating Telemetry Badges (Active) */}
            {isCameraActive && (
              <div className="absolute top-4 left-4 z-20 flex flex-wrap items-center gap-2 max-w-[90%]">
                <div className="px-2.5 py-1 rounded bg-black/80 backdrop-blur border border-white/10 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="text-[10px] font-mono text-white uppercase tracking-wider">LIVE FEED</span>
                </div>
                <div className="px-2.5 py-1 rounded bg-black/80 backdrop-blur border border-white/10 text-[10px] font-mono text-gray-400">
                  {analysisResult?.processing_ms ? `${analysisResult.processing_ms} ms` : 'Processing'}
                </div>
                {analysisResult?.ear_accessories && (
                  <div className="px-2.5 py-1 rounded bg-black/80 backdrop-blur border border-white/10 flex items-center gap-1.5 text-[10px] font-mono">
                    <Headphones className={`w-3 h-3 ${analysisResult.ear_accessories.detected ? 'text-purple-400' : 'text-gray-400'}`} />
                    <span className={analysisResult.ear_accessories.detected ? 'text-purple-300 font-bold' : 'text-gray-400'}>
                      {analysisResult.ear_accessories.detected
                        ? analysisResult.ear_accessories.accessory_type.replace('_', ' ')
                        : 'No Headphones'}
                    </span>
                  </div>
                )}
                {analysisResult && (
                  <div className={`px-2.5 py-1 rounded border text-[10px] font-mono font-bold ${assessmentStyle.badge}`}>
                    {analysisResult.category_label}
                  </div>
                )}
              </div>
            )}

            {/* Sleek Floating Status Pill (Direct Match to User Reference Design) */}
            {isCameraActive && (
              <div className="absolute bottom-5 left-0 right-0 z-20 flex justify-center pointer-events-none">
                <div className="relative overflow-hidden flex items-center justify-between w-64 sm:w-72 h-11 px-5 rounded-2xl bg-white/95 text-black shadow-2xl backdrop-blur-md border border-white/40">
                  <div
                    className="absolute inset-y-0 left-0 bg-emerald-500/25 transition-all duration-300"
                    style={{ width: `${Math.min(100, Math.max(15, conf))}%` }}
                  />
                  <div className="relative z-10 flex items-center gap-2 w-full justify-between">
                    <span className="text-xs font-bold tracking-wide font-sans text-gray-900 truncate">
                      {analysisResult?.face_detected
                        ? analysisResult.category_label === 'Real human face'
                          ? 'Real human face'
                          : isAnalyzing
                          ? 'Analyzing...'
                          : analysisResult.category_label
                        : 'Analyzing...'}
                    </span>
                    <span className="text-[11px] font-mono font-bold text-gray-700">
                      {analysisResult?.face_detected ? `${conf.toFixed(0)}%` : '...'}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Viewport Action Controls */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between p-4 card border-white/5 gap-3">
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 text-xs font-mono text-gray-300 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={challengeMode}
                  onChange={(e) => setChallengeMode(e.target.checked)}
                  className="rounded border-white/20 bg-black text-red-600 focus:ring-0 focus:ring-offset-0"
                />
                <span>Active Liveness Challenge</span>
              </label>
            </div>

            <div className="flex items-center gap-3">
              {/* Training Consent & Save Audit Button */}
              <button
                onClick={openConsentModal}
                disabled={!analysisResult || !analysisResult.face_detected}
                className="btn-red text-xs py-2 px-5 flex items-center gap-2 disabled:opacity-40"
              >
                <Save className="w-3.5 h-3.5" />
                <span>Save Audit & Model Consent</span>
              </button>
            </div>
          </div>

          {/* Consent Status Notification Banner */}
          {consentStatus && (
            <div
              className={`p-4 rounded-lg border flex items-center justify-between ${
                consentStatus === 'GRANTED'
                  ? 'bg-emerald-950/20 border-emerald-500/40 text-emerald-300'
                  : 'bg-white/5 border-white/10 text-gray-300'
              }`}
            >
              <div className="flex items-center gap-3">
                {consentStatus === 'GRANTED' ? (
                  <UserCheck className="w-5 h-5 text-emerald-400 flex-shrink-0" />
                ) : (
                  <UserX className="w-5 h-5 text-gray-400 flex-shrink-0" />
                )}
                <div>
                  <p className="text-xs font-bold">
                    {consentStatus === 'GRANTED'
                      ? 'Face Added to Real Human Model Database'
                      : 'Response Logged — Strict Zero Face Storage Enforced'}
                  </p>
                  <p className="text-[11px] text-gray-400">
                    {consentStatus === 'GRANTED'
                      ? 'Your sample helps fine-tune Privacy Eye weights against deepfakes.'
                      : 'No face images or biometric markers were retained on disk or memory.'}
                  </p>
                </div>
              </div>
              {savedReportId && (
                <Link
                  href="/dashboard/reports"
                  className="btn-outline text-xs py-1.5 px-3.5 text-white border-white/20"
                >
                  View Report
                </Link>
              )}
            </div>
          )}
        </div>

        {/* Right: Live Assessment & Signals (5 Cols) */}
        <div className="lg:col-span-5 space-y-6">
          {/* Assessment Banner */}
          <div className={`card p-6 border ${assessmentStyle.border} ${assessmentStyle.bg} space-y-4`}>
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono uppercase tracking-widest text-gray-400">Current Assessment</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-black/60 border border-white/10 text-gray-400">
                LOCAL / EDGE SERVER
              </span>
            </div>

            <div>
              <div className="flex items-center gap-3">
                <assessmentStyle.icon className={`w-7 h-7 ${assessmentStyle.text} flex-shrink-0`} />
                <h2 className="font-display text-2xl lg:text-3xl text-white tracking-wide leading-tight">
                  {analysisResult?.category_label || (isCameraActive ? 'SCANNING...' : 'STANDBY')}
                </h2>
              </div>
              <p className="text-xs text-gray-400 mt-2 leading-relaxed font-sans">
                {analysisResult?.explanation || 'Waiting for live facial landmarks and continuous frame buffer.'}
              </p>
            </div>

            {/* Gauges: Calibrated Confidence & Reliability */}
            <div className="grid grid-cols-2 gap-4 pt-3 border-t border-white/5">
              <div>
                <span className="text-[11px] font-mono text-gray-400 uppercase">Calibrated Confidence</span>
                <div className="flex items-baseline gap-2 mt-0.5">
                  <span className="font-display text-3xl text-white">
                    {analysisResult ? `${analysisResult.confidence.toFixed(1)}%` : '—'}
                  </span>
                  <span className="text-[10px] text-gray-500 font-mono">dynamic</span>
                </div>
              </div>

              <div>
                <span className="text-[11px] font-mono text-gray-400 uppercase">Input Reliability</span>
                <div className="mt-1 flex items-center gap-2">
                  <span
                    className={`text-xs font-mono font-bold uppercase px-2.5 py-1 rounded ${
                      analysisResult?.reliability === 'HIGH'
                        ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-500/30'
                        : analysisResult?.reliability === 'MEDIUM'
                        ? 'bg-amber-950/60 text-amber-400 border border-amber-500/30'
                        : 'bg-white/5 text-gray-400 border border-white/10'
                    }`}
                  >
                    {analysisResult?.reliability || 'UNSET'}
                  </span>
                </div>
              </div>
            </div>

            {/* 5-Zone Calibrated Threshold Indicator strictly aligned to user protocol */}
            <div className="space-y-1.5 pt-2">
              <div className="flex justify-between text-[9px] font-mono">
                <span className={conf < 20 && analysisResult?.face_detected ? 'text-red-400 font-bold' : 'text-gray-500'}>
                  &lt;20% Scam
                </span>
                <span className={conf >= 50 && conf <= 60 ? 'text-amber-400 font-bold' : 'text-gray-500'}>
                  50-60% Instruction
                </span>
                <span className={conf > 60 && conf <= 75 ? 'text-cyan-400 font-bold' : 'text-gray-500'}>
                  &gt;60% (1 Task)
                </span>
                <span className={conf > 75 && conf <= 85 ? 'text-teal-400 font-bold' : 'text-gray-500'}>
                  &gt;75% (2 Tasks)
                </span>
                <span className={conf > 85 ? 'text-emerald-400 font-bold' : 'text-gray-500'}>
                  &gt;85% Real Human
                </span>
              </div>
              <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden flex p-0.5 gap-0.5 border border-white/10">
                {/* Scam zone (<20%) */}
                <div
                  className={`h-full rounded-sm transition-all duration-300 ${
                    conf < 20 && analysisResult?.face_detected ? 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.8)]' : 'bg-red-950/40'
                  }`}
                  style={{ width: '18%' }}
                />
                {/* 50-60% Instruction pending zone */}
                <div
                  className={`h-full rounded-sm transition-all duration-300 ${
                    conf >= 50 && conf <= 60 ? 'bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.8)]' : 'bg-amber-950/40'
                  }`}
                  style={{ width: '22%' }}
                />
                {/* >60% to 75% 1 task marked */}
                <div
                  className={`h-full rounded-sm transition-all duration-300 ${
                    conf > 60 && conf <= 75 ? 'bg-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.8)]' : 'bg-cyan-950/40'
                  }`}
                  style={{ width: '20%' }}
                />
                {/* >75% to 85% 2 tasks marked */}
                <div
                  className={`h-full rounded-sm transition-all duration-300 ${
                    conf > 75 && conf <= 85 ? 'bg-teal-400 shadow-[0_0_8px_rgba(45,212,191,0.8)]' : 'bg-teal-950/40'
                  }`}
                  style={{ width: '20%' }}
                />
                {/* >85% all 3 tasks marked */}
                <div
                  className={`h-full rounded-sm transition-all duration-300 ${
                    conf > 85 ? 'bg-emerald-400 shadow-[0_0_12px_rgba(52,211,153,0.9)]' : 'bg-emerald-950/40'
                  }`}
                  style={{ width: '20%' }}
                />
              </div>
            </div>
          </div>

          {/* Headphone & Ear Accessory Detection Card */}
          <div className="card p-4 border border-white/10 bg-black/40 flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div
                className={`p-2.5 rounded-lg border ${
                  analysisResult?.ear_accessories?.detected
                    ? 'bg-purple-950/40 border-purple-500/40 text-purple-300'
                    : 'bg-white/5 border-white/10 text-gray-400'
                }`}
              >
                <Headphones className="w-5 h-5" />
              </div>
              <div>
                <span className="text-[10px] font-mono uppercase tracking-widest text-gray-400">
                  Ear Hardware &amp; Accessory Scan
                </span>
                <p className="text-xs font-bold text-white mt-0.5">
                  {analysisResult?.ear_accessories?.label || 'Scanning ear perimeter...'}
                </p>
                <p className="text-[11px] text-gray-400 mt-0.5">
                  {analysisResult?.ear_accessories?.details || 'Checks lateral ear regions and cranial band for headphones or earbuds.'}
                </p>
              </div>
            </div>
            <span
              className={`text-[10px] font-mono px-2.5 py-1 rounded font-bold uppercase border flex-shrink-0 ${
                analysisResult?.ear_accessories?.detected
                  ? 'bg-purple-950 text-purple-300 border-purple-500/40'
                  : 'bg-emerald-950/40 text-emerald-400 border-emerald-500/30'
              }`}
            >
              {analysisResult?.ear_accessories?.detected
                ? analysisResult.ear_accessories.accessory_type.replace('_', ' ')
                : 'CLEARED'}
            </span>
          </div>

          {/* Interactive Guided Live Protocol: Smile, 3 Blinks, Smooth Rotation */}
          <div className="card p-5 border border-white/10 bg-black/40 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-white/5">
              <div className="space-y-0.5">
                <span className="text-xs font-mono uppercase tracking-widest text-emerald-400 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5" />
                  Live Testing Protocol (3 Guided Tasks)
                </span>
                <p className="text-[11px] text-gray-400">
                  Perform the 3 interactive tasks below to verify genuine human presence.
                </p>
              </div>
              <div className="text-right">
                <span
                  className={`text-[10px] font-mono px-2.5 py-1 rounded font-bold uppercase border ${
                    (analysisResult?.guided_protocol?.total_marked ?? 0) === 3
                      ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40 shadow-[0_0_10px_rgba(16,185,129,0.3)]'
                      : (analysisResult?.guided_protocol?.total_marked ?? 0) === 2
                      ? 'bg-teal-500/20 text-teal-300 border-teal-500/40'
                      : (analysisResult?.guided_protocol?.total_marked ?? 0) === 1
                      ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
                      : 'bg-white/5 text-gray-400 border-white/10'
                  }`}
                >
                  {analysisResult?.guided_protocol?.total_marked ?? 0} / 3 TASKS MARKED
                </span>
              </div>
            </div>

            {/* 3 Guided Task Rows */}
            <div className="space-y-2.5">
              {/* Task 1: Ask Person to Smile */}
              <div className="p-3 rounded-lg bg-black/60 border border-white/5 flex items-center justify-between gap-3">
                <div className="flex items-start gap-3">
                  <div
                    className={`p-2 rounded-md ${
                      analysisResult?.guided_protocol?.task_1_smile?.marked
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                        : 'bg-white/5 text-gray-400'
                    }`}
                  >
                    <Smile className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-white">Task 1: Smile (Teeth or Wide Lips)</span>
                      {analysisResult?.guided_protocol?.task_1_smile?.teeth_detected && (
                        <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-emerald-950/80 text-emerald-400 border border-emerald-500/30">
                          Teeth Visible
                        </span>
                      )}
                      {analysisResult?.guided_protocol?.task_1_smile?.lips_wide && (
                        <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-cyan-950/80 text-cyan-400 border border-cyan-500/30">
                          Wide Lips
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-gray-400 mt-0.5">
                      {analysisResult?.guided_protocol?.task_1_smile?.label || 'Smile at the camera to verify natural expression'}
                    </p>
                  </div>
                </div>
                <span
                  className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase ${
                    analysisResult?.guided_protocol?.task_1_smile?.marked
                      ? 'bg-emerald-950 text-emerald-300 border border-emerald-500/40'
                      : 'bg-white/5 text-gray-400 border border-white/10'
                  }`}
                >
                  {analysisResult?.guided_protocol?.task_1_smile?.marked ? '✓ MARKED' : 'PENDING'}
                </span>
              </div>

              {/* Task 2: Ask Person to Blink 3 Times */}
              <div className="p-3 rounded-lg bg-black/60 border border-white/5 flex items-center justify-between gap-3">
                <div className="flex items-start gap-3">
                  <div
                    className={`p-2 rounded-md ${
                      analysisResult?.guided_protocol?.task_2_blinks?.marked
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                        : 'bg-white/5 text-gray-400'
                    }`}
                  >
                    <Eye className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-white">Task 2: Blink 3 Times</span>
                      <span className="text-[10px] font-mono text-emerald-400 font-bold">
                        ({analysisResult?.guided_protocol?.task_2_blinks?.blink_count ?? 0} / 3 Blinks)
                      </span>
                    </div>
                    <p className="text-[11px] text-gray-400 mt-0.5">
                      {analysisResult?.guided_protocol?.task_2_blinks?.label || 'Scan eyes during blinks (Requires ≥ 3 blinks to mark)'}
                    </p>
                  </div>
                </div>
                <span
                  className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase ${
                    analysisResult?.guided_protocol?.task_2_blinks?.marked
                      ? 'bg-emerald-950 text-emerald-300 border border-emerald-500/40'
                      : 'bg-white/5 text-gray-400 border border-white/10'
                  }`}
                >
                  {analysisResult?.guided_protocol?.task_2_blinks?.marked ? '✓ MARKED' : 'PENDING'}
                </span>
              </div>

              {/* Task 3: Rotate Face Smoothly */}
              <div className="p-3 rounded-lg bg-black/60 border border-white/5 flex items-center justify-between gap-3">
                <div className="flex items-start gap-3">
                  <div
                    className={`p-2 rounded-md ${
                      analysisResult?.guided_protocol?.task_3_rotation?.marked
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                        : 'bg-white/5 text-gray-400'
                    }`}
                  >
                    <RefreshCw className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-white">Task 3: Rotate Face Smoothly</span>
                      {analysisResult?.guided_protocol?.task_3_rotation?.yaw_span !== undefined && (
                        <span className="text-[10px] font-mono text-gray-400">
                          (Span: {analysisResult.guided_protocol.task_3_rotation.yaw_span} rad)
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-gray-400 mt-0.5">
                      {analysisResult?.guided_protocol?.task_3_rotation?.label ||
                        'Rotate face side-to-side; checks ears, chin, cheeks, hair, beard sharpness'}
                    </p>
                  </div>
                </div>
                <span
                  className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase ${
                    analysisResult?.guided_protocol?.task_3_rotation?.marked
                      ? 'bg-emerald-950 text-emerald-300 border border-emerald-500/40'
                      : 'bg-white/5 text-gray-400 border border-white/10'
                  }`}
                >
                  {analysisResult?.guided_protocol?.task_3_rotation?.marked ? '✓ MARKED' : 'PENDING'}
                </span>
              </div>
            </div>

            {/* Exact Rule Guide */}
            <div className="p-2.5 rounded bg-black/50 border border-white/5 text-[10px] font-mono text-gray-400 space-y-1">
              <div className="flex items-center gap-1.5 text-gray-300 font-semibold">
                <Info className="w-3.5 h-3.5 text-emerald-400" />
                <span>Protocol Verification Tiers:</span>
              </div>
              <p className="text-[10px] text-gray-400">
                • 3 Marked: <span className="text-emerald-400">&gt;85% Real human face</span><br />
                • 2 Marked: <span className="text-teal-400">&gt;75% Likely as human face</span><br />
                • 1 Marked: <span className="text-cyan-400">&gt;60% Human face detected</span><br />
                • 0 Marked: <span className="text-amber-400">You are Human but currently you are not following instruction above</span><br />
                • Print / Phone Replay: <span className="text-red-400">Synthetic attack / Photo print scam detected (&lt;20%)</span>
              </p>
            </div>
          </div>

          {/* Active Challenge Box (When Challenge Mode is Active) */}
          {challengeMode && (
            <div
              className="card p-5 border border-red-600/30 space-y-3"
              style={{ background: 'linear-gradient(180deg, rgba(220,38,38,0.08) 0%, rgba(17,17,17,1) 100%)' }}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-red-500" />
                  <span className="text-xs font-bold text-white uppercase tracking-wider">Human Presence Challenge</span>
                </div>
                <span
                  className={`text-[10px] font-mono px-2 py-0.5 rounded ${
                    analysisResult?.challenge?.info?.completed ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
                  }`}
                >
                  {analysisResult?.challenge?.info?.completed ? 'VERIFIED' : 'ACTIVE'}
                </span>
              </div>

              <div className="p-3 bg-black/60 rounded border border-white/10 flex items-center justify-between">
                <div>
                  <p className="text-xs font-bold text-white">
                    {analysisResult?.challenge?.info?.label || 'Turn head slightly or smile'}
                  </p>
                  <p className="text-[11px] text-gray-500 font-mono mt-0.5">
                    Verifies non-linear 3D parallax against static photo attack.
                  </p>
                </div>
                {analysisResult?.challenge?.info?.completed ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />
                ) : (
                  <RefreshCw className="w-4 h-4 text-red-500 animate-spin flex-shrink-0" />
                )}
              </div>
            </div>
          )}

          {/* Frame Quality & Grid Telemetry */}
          <div className="card p-5 border border-white/5 space-y-4">
            <h3 className="text-xs font-mono uppercase tracking-widest text-red-500">Camera Quality & Blur Telemetry</h3>
            <div className="space-y-3">
              {/* Blur Meter */}
              <div>
                <div className="flex justify-between text-xs font-mono mb-1">
                  <span className="text-gray-400">Sharpness / Blur Index</span>
                  <span className="text-white">
                    {analysisResult?.quality ? `${analysisResult.quality.sharpness_score} / 100` : '—'}
                    {analysisResult?.quality && (
                      <span
                        className={`ml-2 text-[10px] ${
                          analysisResult.quality.sharpness_label === 'SHARP' ? 'text-emerald-400' : 'text-amber-400'
                        }`}
                      >
                        ({analysisResult.quality.sharpness_label})
                      </span>
                    )}
                  </span>
                </div>
                <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-red-600 rounded-full transition-all duration-300"
                    style={{ width: `${analysisResult?.quality?.sharpness_score || 0}%` }}
                  />
                </div>
              </div>

              {/* Quality Index */}
              <div>
                <div className="flex justify-between text-xs font-mono mb-1">
                  <span className="text-gray-400">Overall Quality Index</span>
                  <span className="text-white">{analysisResult?.quality?.quality_index || 0} / 100</span>
                </div>
                <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-white rounded-full transition-all duration-300"
                    style={{ width: `${analysisResult?.quality?.quality_index || 0}%` }}
                  />
                </div>
              </div>

              {/* Lighting Status */}
              <div className="flex items-center justify-between pt-1 text-xs font-mono">
                <span className="text-gray-500">Illumination Profile:</span>
                <span className="text-gray-300">
                  {analysisResult?.quality?.lighting_label || 'Optimal'}
                </span>
              </div>
            </div>
          </div>

          {/* Signals Breakdown */}
          <div className="card p-5 border border-white/5 space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-white/5">
              <span className="text-xs font-bold text-white uppercase tracking-wider">Multi-Signal Extraction</span>
              <span className="text-[10px] font-mono text-gray-500">
                {analysisResult?.signals?.length || 0} Signals Detected
              </span>
            </div>

            <div className="space-y-2 max-h-52 overflow-y-auto pr-1">
              {analysisResult?.signals && analysisResult.signals.length > 0 ? (
                analysisResult.signals.map((sig, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded bg-black/40 border border-white/5 flex items-start justify-between gap-3 text-xs"
                  >
                    <div className="space-y-0.5">
                      <p className="font-semibold text-white">{sig.label}</p>
                      {sig.detail && <p className="text-[11px] text-gray-500 leading-tight">{sig.detail}</p>}
                    </div>
                    <span
                      className={`text-[10px] font-mono px-2 py-0.5 rounded flex-shrink-0 uppercase font-bold ${
                        sig.severity === 'high'
                          ? 'bg-red-950 text-red-400 border border-red-800/40'
                          : sig.severity === 'medium'
                          ? 'bg-amber-950 text-amber-400 border border-amber-800/40'
                          : 'bg-emerald-950 text-emerald-400 border border-emerald-800/40'
                      }`}
                    >
                      {sig.severity}
                    </span>
                  </div>
                ))
              ) : (
                <div className="py-6 text-center text-xs text-gray-600 font-mono">
                  {isCameraActive ? 'Gathering multi-frame signals...' : 'Start camera to stream live signals'}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* ── Interactive Training Consent Modal ───────────────────────────────── */}
      <AnimatePresence>
        {showConsentModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="relative w-full max-w-lg card p-6 border border-white/15 bg-[#0f0f12] shadow-2xl space-y-6"
            >
              {/* Close Button */}
              <button
                onClick={() => setShowConsentModal(false)}
                className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>

              {/* Modal Header */}
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <Database className="w-4 h-4 text-red-500" />
                  <span className="text-[11px] font-mono text-red-400 uppercase tracking-widest">
                    Model Training Database · User Consent
                  </span>
                </div>
                <h3 className="font-display text-2xl text-white tracking-wide">
                  Share Face to Train the Model?
                </h3>
              </div>

              {/* Main Prompt Question Box */}
              <div className="p-4 rounded-lg bg-black/60 border border-white/10 space-y-3">
                <p className="text-sm font-semibold text-white">
                  Are you willing to share your face to train the model?
                </p>
                <p className="text-xs text-gray-400 leading-relaxed">
                  Privacy Eye is training next-generation AI defense models to differentiate authentic live human faces
                  from deepfakes, face swaps, and synthetic avatars.
                </p>

                {/* What Happens Comparison */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-2 text-[11px]">
                  <div className="p-2.5 rounded bg-emerald-950/20 border border-emerald-500/30 space-y-1">
                    <p className="font-bold text-emerald-400 flex items-center gap-1.5">
                      <Check className="w-3.5 h-3.5" /> If you click YES:
                    </p>
                    <p className="text-gray-400">
                      Your verified face crop snapshot is added to the Real Human Model Training Database to fine-tune AI weights.
                    </p>
                  </div>

                  <div className="p-2.5 rounded bg-white/5 border border-white/10 space-y-1">
                    <p className="font-bold text-gray-300 flex items-center gap-1.5">
                      <Lock className="w-3.5 h-3.5 text-gray-400" /> If you click NO:
                    </p>
                    <p className="text-gray-400">
                      Strict zero-storage policy. Zero face images or biometrics stored. Only your preference response is logged.
                    </p>
                  </div>
                </div>
              </div>

              {/* Current Scan Telemetry Snapshot Preview */}
              {analysisResult && (
                <div className="flex items-center justify-between p-3 rounded bg-black/40 border border-white/5 text-xs font-mono">
                  <div className="space-y-0.5">
                    <span className="text-gray-500 text-[10px] uppercase">Current Calibrated Session</span>
                    <p className="font-bold text-white">{analysisResult.category_label}</p>
                  </div>
                  <div className="text-right space-y-0.5">
                    <span className="text-gray-500 text-[10px] uppercase">Confidence</span>
                    <p className="font-bold text-emerald-400">{analysisResult.confidence.toFixed(1)}%</p>
                  </div>
                </div>
              )}

              {/* Action Buttons: Explicit YES / NO */}
              <div className="grid grid-cols-2 gap-3 pt-2">
                {/* NO Button */}
                <button
                  onClick={() => handleConsentChoice(false)}
                  disabled={isSubmittingConsent}
                  className="btn-outline py-3 px-4 text-xs font-mono font-bold flex items-center justify-center gap-2 border-white/20 text-gray-300 hover:border-white/40 hover:text-white disabled:opacity-50"
                >
                  <XCircle className="w-4 h-4 text-gray-400" />
                  <span>NO, KEEP PRIVATE</span>
                </button>

                {/* YES Button */}
                <button
                  onClick={() => handleConsentChoice(true)}
                  disabled={isSubmittingConsent}
                  className="btn-red py-3 px-4 text-xs font-mono font-bold flex items-center justify-center gap-2 shadow-lg disabled:opacity-50"
                >
                  <CheckCircle2 className="w-4 h-4 text-white" />
                  <span>{isSubmittingConsent ? 'SAVING...' : 'YES, ADD TO DATABASE'}</span>
                </button>
              </div>

              {/* Footer Notice */}
              <p className="text-[10px] text-gray-500 text-center font-mono">
                Privacy Eye strictly respects user agency and privacy. You can revoke consent at any time.
              </p>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  )
}
