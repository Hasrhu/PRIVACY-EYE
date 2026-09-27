'use client'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { ArrowRight, Plus, Eye, Shield, Zap, Activity, ChevronRight, Check, Camera } from 'lucide-react'

const SIGNALS = [
  'Error Level Analysis', 'FFT Frequency Domain', 'EXIF Forensics',
  'Temporal Consistency', 'Face Boundary Detection', 'Mel-Spectrogram Variance',
  'Spectral Flatness', 'Zero-Crossing Rate', 'Compression Artifacts',
  'Noise Inconsistency', 'Provenance Metadata', 'SHA-256 Hashing',
  'Moiré Screen Pattern Detection', 'Active Liveness Pose Challenge', 'Laplacian Blur Analysis',
]

const PROCESS = [
  { num: '01', title: 'CAPTURE', desc: 'Stream live webcam video or drop any image, video, or audio file into Privacy Eye.' },
  { num: '02', title: 'QUALITY & GRID', desc: 'Laplacian variance checks sharpness, motion blur, and spatial grid illumination.' },
  { num: '03', title: 'FACE & BIOMETRICS', desc: 'YuNet detects 5-point facial landmarks, head pose yaw/pitch, and liveness micro-motion.' },
  { num: '04', title: 'EVIDENCE FUSION', desc: 'Moiré screen detection, face-swap seam gradients, and temporal continuity are fused into a calibrated assessment.' },
  { num: '05', title: 'EXPLAIN & REPORT', desc: 'Gemini AI agent breaks down technical metrics into plain-language actionable evidence.' },
]

const CAPABILITIES = [
  { icon: Camera, label: 'Live Camera Liveness', sub: 'YuNet · Replay · Face-Swap · 3D Pose' },
  { icon: Eye, label: 'Image Forensics', sub: 'ELA · FFT · Noise · EXIF' },
  { icon: Activity, label: 'Video Analysis', sub: 'Temporal · Frame · Consistency' },
  { icon: Shield, label: 'Voice / Audio', sub: 'Mel · Spectral · Prosody' },
  { icon: Zap, label: 'AI Report Agent', sub: 'Gemini · Evidence · PDF' },
]

const STATS = [
  { num: '15+', label: 'Detection Signals' },
  { num: '3',   label: 'Media Types' },
  { num: '<5s', label: 'Avg Analysis Time' },
  { num: '0',   label: 'Files Stored' },
]

const fadeUp = {
  hidden: { opacity: 0, y: 40 },
  show:   { opacity: 1, y: 0 },
}

export default function LandingPage() {
  return (
    <main style={{ background: '#0a0a0a', minHeight: '100vh' }} className="grid-overlay">

      {/* ── Nav ────────────────────────────────────────────────── */}
      <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-8 py-5" style={{ background: 'rgba(10,10,10,0.9)', backdropFilter: 'blur(12px)', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded flex items-center justify-center" style={{ background: '#dc2626' }}>
            <Eye className="w-4 h-4 text-white" />
          </div>
          <span className="font-display text-xl tracking-wider text-white">PRIVACY EYE</span>
        </div>
        <div className="hidden md:flex items-center gap-8 text-xs font-semibold tracking-wide3 uppercase text-gray-400">
          <a href="#detect" className="hover:text-white transition-colors">Detect</a>
          <a href="#process" className="hover:text-white transition-colors">Process</a>
          <a href="#signals" className="hover:text-white transition-colors">Signals</a>
          <a href="#pricing" className="hover:text-white transition-colors">Pricing</a>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/auth/login" className="btn-outline text-xs py-2.5 px-5">Sign In</Link>
          <Link href="/auth/register" className="btn-red text-xs py-2.5 px-5">
            Get Started <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </nav>

      {/* ── HERO ───────────────────────────────────────────────── */}
      <section className="relative min-h-screen flex flex-col justify-end pb-24 px-8 pt-32 max-w-screen-xl mx-auto w-full">
        {/* Top-right label */}
        <div className="absolute top-28 right-8 text-right hidden lg:block">
          <p className="text-xs font-semibold tracking-wide4 uppercase" style={{ color: '#dc2626' }}>Available Worldwide</p>
          <div className="flex items-center justify-end gap-2 mt-1">
            <span className="dot-red" />
            <span className="text-xs text-gray-400 font-mono">Detection Active</span>
          </div>
        </div>

        {/* Hero title — editorial large */}
        <motion.div initial="hidden" animate="show" variants={fadeUp} transition={{ duration: 0.8 }}>
          <p className="section-label mb-4">AI Authenticity Platform · Cybersecurity</p>
          <h1 className="font-display text-white leading-none" style={{ fontSize: 'clamp(5rem, 14vw, 13rem)' }}>
            PRIVACY<br />
            <span style={{ color: '#dc2626', WebkitTextStroke: '0px', display: 'block', lineHeight: 0.9 }}>EYE</span>
          </h1>
        </motion.div>

        <motion.div initial="hidden" animate="show" variants={fadeUp} transition={{ duration: 0.8, delay: 0.2 }} className="mt-10 flex flex-col lg:flex-row gap-10 lg:items-end justify-between">
          <div className="max-w-lg">
            <h2 className="text-xl font-bold text-white mb-3">
              AI Deepfake & Synthetic<br />Media Detection Platform
            </h2>
            <p className="text-sm leading-relaxed" style={{ color: '#6b7280' }}>
              Privacy Eye analyzes images, videos, and audio with real forensic signals and machine learning classifiers — then explains exactly what it found, why it flagged it, and what you should do next.
            </p>
            <p className="text-sm font-semibold mt-3" style={{ color: '#9ca3af' }}>
              · No media stored · Encrypted in transit · Privacy first
            </p>
            <div className="flex flex-wrap items-center gap-4 mt-8">
              <Link href="/dashboard/live-scan" className="btn-red flex items-center gap-2">
                <Camera className="w-4 h-4" /> Live Camera Scan
              </Link>
              <Link href="/auth/register" className="btn-outline">
                Start Free <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 gap-4 lg:w-64">
            {STATS.map((s) => (
              <div key={s.label} className="card p-4">
                <div className="stat-num">{s.num}</div>
                <p className="text-xs font-semibold uppercase tracking-wide2 mt-1" style={{ color: '#6b7280' }}>{s.label}</p>
              </div>
            ))}
          </div>
        </motion.div>
      </section>

      <hr className="hr-red mx-8" />

      {/* ── SELECTED CAPABILITIES ──────────────────────────────── */}
      <section id="detect" className="py-20 px-8 max-w-screen-xl mx-auto w-full">
        <div className="flex items-center justify-between mb-12">
          <div>
            <p className="section-label mb-2">What We Detect</p>
            <h2 className="text-3xl font-black text-white">Detection Capabilities</h2>
          </div>
          <Link href="/auth/register" className="btn-ghost-red text-sm">
            View All Features <ChevronRight className="w-4 h-4" />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {CAPABILITIES.map((c, i) => (
            <motion.div
              key={c.label}
              className="card-hover p-8 group cursor-pointer"
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              viewport={{ once: true }}
            >
              <div className="w-12 h-12 rounded-lg flex items-center justify-center mb-5 transition-colors" style={{ background: 'rgba(220,38,38,0.1)' }}>
                <c.icon className="w-6 h-6 group-hover:text-white transition-colors" style={{ color: '#dc2626' }} />
              </div>
              <div className="text-xs font-bold uppercase tracking-wide2 mb-1" style={{ color: '#dc2626' }}>
                {String(i + 1).padStart(2, '0')}
              </div>
              <h3 className="font-bold text-white text-lg mb-2">{c.label}</h3>
              <p className="text-xs font-mono" style={{ color: '#6b7280' }}>{c.sub}</p>
              <ArrowRight className="w-4 h-4 mt-4 opacity-0 group-hover:opacity-100 transition-all" style={{ color: '#dc2626' }} />
            </motion.div>
          ))}
        </div>
      </section>

      <hr className="hr-red mx-8" />

      {/* ── WORK PROCESS ─────────────────────────────────────────── */}
      <section id="process" className="py-20 px-8 max-w-screen-xl mx-auto w-full">
        <div className="grid lg:grid-cols-2 gap-16">
          <div>
            <p className="section-label mb-2">How It Works</p>
            <h2 className="text-3xl font-black text-white mb-6">Detection Process</h2>
            <p className="text-sm leading-relaxed mb-8" style={{ color: '#6b7280' }}>
              Privacy Eye uses a multi-stage pipeline combining real forensic signal extraction with machine learning classifiers and an AI report agent — so you always understand the evidence, not just the verdict.
            </p>
            {/* Quote */}
            <div className="card-red p-6 relative">
              <div className="absolute -top-3 left-6 text-5xl font-display" style={{ color: '#dc2626', lineHeight: 1 }}>"</div>
              <p className="text-sm font-semibold text-white leading-relaxed pt-3">
                Good detection is not just how accurate it is, but how well it explains why.
              </p>
              <p className="text-xs mt-3" style={{ color: '#dc2626' }}>— Privacy Eye Design Principle</p>
            </div>
          </div>

          <div className="space-y-4">
            {PROCESS.map((p, i) => (
              <motion.div
                key={p.num}
                className="flex gap-5 p-5 card group hover:border-red-500/40 transition-all"
                initial={{ opacity: 0, x: 30 }}
                whileInView={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.08 }}
                viewport={{ once: true }}
              >
                <div className="flex-shrink-0">
                  <span className="font-display text-2xl" style={{ color: '#dc2626' }}>{p.num}</span>
                </div>
                <div>
                  <h3 className="font-bold text-white text-sm tracking-wide2 mb-1">{p.title}</h3>
                  <p className="text-xs leading-relaxed" style={{ color: '#6b7280' }}>{p.desc}</p>
                </div>
                <ArrowRight className="w-4 h-4 ml-auto flex-shrink-0 self-center opacity-0 group-hover:opacity-100 transition-opacity" style={{ color: '#dc2626' }} />
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <hr className="hr-red mx-8" />

      {/* ── DETECTION SIGNALS ─────────────────────────────────────── */}
      <section id="signals" className="py-20 px-8 max-w-screen-xl mx-auto w-full">
        <p className="section-label mb-2">Technical Depth</p>
        <h2 className="text-3xl font-black text-white mb-10">Detection Signals</h2>
        <div className="flex flex-wrap gap-3">
          {SIGNALS.map((s, i) => (
            <motion.div
              key={s}
              className="flex items-center gap-2 px-4 py-2.5 rounded-full text-sm font-semibold"
              style={{ background: '#1a1a1a', border: '1px solid rgba(255,255,255,0.06)', color: '#9ca3af' }}
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.04 }}
              viewport={{ once: true }}
              whileHover={{ borderColor: 'rgba(220,38,38,0.4)', color: '#fff' }}
            >
              <Plus className="w-3 h-3" style={{ color: '#dc2626' }} />
              {s}
            </motion.div>
          ))}
        </div>
      </section>

      <hr className="hr-red mx-8" />

      {/* ── PRIVACY PROMISE ──────────────────────────────────────── */}
      <section className="py-20 px-8 max-w-screen-xl mx-auto w-full">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          <div>
            <p className="section-label mb-2">Our Promise</p>
            <h2 className="font-display text-white leading-none" style={{ fontSize: 'clamp(3rem, 6vw, 5rem)' }}>
              NO STORAGE.<br />
              <span style={{ color: '#dc2626' }}>NO SPYING.</span><br />
              ONLY DETECTION.
            </h2>
          </div>
          <div className="space-y-4">
            {[
              ['Zero media retention',           'Your file is analyzed in memory and immediately deleted after processing.'],
              ['Encrypted in transit',            'All uploads use HTTPS/TLS encryption. We never transmit unencrypted media.'],
              ['No third-party sharing',          'Your media and results are never shared with advertisers or data brokers.'],
              ['Local processing where possible', 'Lightweight detection signals run client-side. Cloud only when required.'],
            ].map(([title, desc]) => (
              <div key={title} className="flex gap-4 p-4 card">
                <div className="w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5" style={{ background: 'rgba(220,38,38,0.15)' }}>
                  <Check className="w-3 h-3" style={{ color: '#dc2626' }} />
                </div>
                <div>
                  <p className="text-sm font-bold text-white mb-0.5">{title}</p>
                  <p className="text-xs leading-relaxed" style={{ color: '#6b7280' }}>{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <hr className="hr-red mx-8" />

      {/* ── PRICING ─────────────────────────────────────────────── */}
      <section id="pricing" className="py-20 px-8 max-w-screen-xl mx-auto w-full">
        <p className="section-label mb-2 text-center">Transparent Pricing</p>
        <h2 className="text-3xl font-black text-white mb-12 text-center">Plans</h2>
        <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
          {[
            { name: 'Free', price: '$0', scans: '20 scans/mo', features: ['Image & Audio detection', 'Basic risk scoring', 'JSON export', 'Forensics only'], cta: 'Start Free', highlight: false },
            { name: 'Pro', price: '$12', scans: '500 scans/mo', features: ['All Free features', 'Video analysis', 'AI Report Agent (Gemini)', 'PDF export', 'Priority processing'], cta: 'Get Pro', highlight: true },
            { name: 'Enterprise', price: 'Custom', scans: 'Unlimited', features: ['All Pro features', 'REST API access', 'SSO / SAML', 'SLA guarantee', 'Audit logs', 'Custom models'], cta: 'Contact Us', highlight: false },
          ].map((plan) => (
            <div key={plan.name} className="p-8 rounded-xl" style={{ background: plan.highlight ? '#dc2626' : '#111111', border: plan.highlight ? 'none' : '1px solid rgba(255,255,255,0.06)' }}>
              <p className="text-xs font-bold uppercase tracking-wide3 mb-2" style={{ color: plan.highlight ? 'rgba(255,255,255,0.7)' : '#dc2626' }}>{plan.name}</p>
              <div className="font-display text-5xl text-white mb-1">{plan.price}</div>
              <p className="text-xs mb-6" style={{ color: plan.highlight ? 'rgba(255,255,255,0.7)' : '#6b7280' }}>{plan.scans}</p>
              <div className="space-y-2.5 mb-8">
                {plan.features.map(f => (
                  <div key={f} className="flex items-center gap-2 text-sm">
                    <Check className="w-3.5 h-3.5 flex-shrink-0" style={{ color: plan.highlight ? '#fff' : '#dc2626' }} />
                    <span style={{ color: plan.highlight ? '#fff' : '#9ca3af' }}>{f}</span>
                  </div>
                ))}
              </div>
              <Link href="/auth/register" className={plan.highlight ? 'btn-outline w-full justify-center py-3 block text-center' : 'btn-red w-full justify-center py-3 block text-center'} style={!plan.highlight ? {} : { borderColor: 'rgba(255,255,255,0.5)', color: '#fff' }}>
                {plan.cta}
              </Link>
            </div>
          ))}
        </div>
      </section>

      {/* ── CTA ─────────────────────────────────────────────────── */}
      <section className="py-24 px-8">
        <div className="max-w-screen-xl mx-auto">
          <div className="rounded-2xl p-16 text-center" style={{ background: '#111111', border: '1px solid rgba(220,38,38,0.2)' }}>
            <p className="section-label mb-4">Ready?</p>
            <h2 className="font-display text-white mb-6" style={{ fontSize: 'clamp(3rem, 7vw, 6rem)', lineHeight: 0.9 }}>
              LET&apos;S CHECK<br />
              <span style={{ color: '#dc2626' }}>WHAT&apos;S REAL.</span>
            </h2>
            <p className="text-sm max-w-md mx-auto mb-10" style={{ color: '#6b7280' }}>
              Free tier · No credit card · 20 scans per month · Start in 30 seconds.
            </p>
            <Link href="/auth/register" className="btn-red text-base px-10 py-4">
              Create Free Account <ArrowRight className="w-5 h-5" />
            </Link>
          </div>
        </div>
      </section>

      {/* ── Footer ──────────────────────────────────────────────── */}
      <footer style={{ borderTop: '1px solid rgba(255,255,255,0.04)' }} className="px-8 py-10">
        <div className="max-w-screen-xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 rounded flex items-center justify-center" style={{ background: '#dc2626' }}>
              <Eye className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="font-display tracking-wider text-white">PRIVACY EYE</span>
          </div>
          <p className="text-xs" style={{ color: '#6b7280' }}>
            AI Can Fake It. Privacy Eye Can Check It. — Results are probabilistic indicators only.
          </p>
          <div className="flex gap-6 text-xs font-semibold uppercase tracking-wide2" style={{ color: '#6b7280' }}>
            <Link href="/auth/login" className="hover:text-white transition-colors">Sign In</Link>
            <Link href="/auth/register" className="hover:text-white transition-colors">Register</Link>
          </div>
        </div>
      </footer>
    </main>
  )
}
