'use client'
import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { motion } from 'framer-motion'
import { Eye, EyeOff, ArrowRight, Shield, Check } from 'lucide-react'
import toast from 'react-hot-toast'
import { authApi, getErrorMessage } from '@/lib/api'

interface RegisterForm { full_name: string; email: string; password: string; confirm: string }

export default function RegisterPage() {
  const router = useRouter()
  const [showPw, setShowPw] = useState(false)
  const [loading, setLoading] = useState(false)
  const { register, handleSubmit, watch, formState: { errors } } = useForm<RegisterForm>()
  const password = watch('password', '')

  const strength = [
    { label: '8+ characters',    ok: password.length >= 8 },
    { label: 'Uppercase letter', ok: /[A-Z]/.test(password) },
    { label: 'Number',           ok: /[0-9]/.test(password) },
  ]

  const onSubmit = async (data: RegisterForm) => {
    setLoading(true)
    try {
      await authApi.register(data.email, data.password, data.full_name)
      await authApi.login(data.email, data.password)
      toast.success('Account created. Welcome to Privacy Eye.')
      router.push('/dashboard')
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen grid lg:grid-cols-2" style={{ background: '#0a0a0a' }}>
      {/* Left panel */}
      <div className="hidden lg:flex flex-col justify-between p-12 relative overflow-hidden" style={{ background: '#111111', borderRight: '1px solid rgba(255,255,255,0.04)' }}>
        <div className="absolute inset-0 grid-overlay opacity-50" />
        <Link href="/" className="flex items-center gap-3 relative z-10">
          <div className="w-8 h-8 rounded flex items-center justify-center" style={{ background: '#dc2626' }}>
            <Shield className="w-5 h-5 text-white" />
          </div>
          <span className="font-display text-xl tracking-wider text-white">PRIVACY EYE</span>
        </Link>

        <div className="relative z-10">
          <h1 className="font-display text-white leading-none mb-6" style={{ fontSize: '5rem' }}>
            JOIN THE<br />
            <span style={{ color: '#dc2626' }}>DIGITAL<br />DEFENSE.</span>
          </h1>
          <div className="space-y-3 mt-8">
            {['Free tier — 20 scans/month', 'No credit card required', 'Instant access to all scanners', 'AI-powered evidence reports'].map(f => (
              <div key={f} className="flex items-center gap-3 text-sm" style={{ color: '#9ca3af' }}>
                <Check className="w-4 h-4 flex-shrink-0" style={{ color: '#dc2626' }} />
                {f}
              </div>
            ))}
          </div>
        </div>

        <p className="text-xs relative z-10" style={{ color: '#374151' }}>
          Results are probabilistic indicators only. Not legal advice.
        </p>
      </div>

      {/* Right panel */}
      <div className="flex items-center justify-center px-6 py-12">
        <motion.div
          className="w-full max-w-md"
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <Link href="/" className="flex items-center gap-3 mb-10 lg:hidden">
            <div className="w-7 h-7 rounded flex items-center justify-center" style={{ background: '#dc2626' }}>
              <Shield className="w-4 h-4 text-white" />
            </div>
            <span className="font-display text-lg tracking-wider text-white">PRIVACY EYE</span>
          </Link>

          <p className="section-label mb-3">Create Account</p>
          <h2 className="text-3xl font-black text-white mb-8">Register</h2>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wide2 mb-2" style={{ color: '#9ca3af' }}>Full Name</label>
              <input type="text" className="input-dark" placeholder="Jane Smith"
                {...register('full_name', { required: 'Name is required' })} />
              {errors.full_name && <p className="text-xs mt-1.5 font-medium" style={{ color: '#dc2626' }}>{errors.full_name.message}</p>}
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wide2 mb-2" style={{ color: '#9ca3af' }}>Email</label>
              <input type="email" className="input-dark" placeholder="you@example.com"
                {...register('email', { required: 'Email is required' })} />
              {errors.email && <p className="text-xs mt-1.5 font-medium" style={{ color: '#dc2626' }}>{errors.email.message}</p>}
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wide2 mb-2" style={{ color: '#9ca3af' }}>Password</label>
              <div className="relative">
                <input type={showPw ? 'text' : 'password'} className="input-dark pr-11" placeholder="Min 8 chars"
                  {...register('password', { required: 'Password is required', minLength: { value: 8, message: 'Min 8 characters' } })} />
                <button type="button" onClick={() => setShowPw(!showPw)} className="absolute right-3.5 top-1/2 -translate-y-1/2" style={{ color: '#6b7280' }}>
                  {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {password && (
                <div className="mt-2 flex gap-3 flex-wrap">
                  {strength.map(s => (
                    <div key={s.label} className="flex items-center gap-1.5 text-xs font-medium" style={{ color: s.ok ? '#10b981' : '#4b5563' }}>
                      <Check className="w-3 h-3" /> {s.label}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wide2 mb-2" style={{ color: '#9ca3af' }}>Confirm Password</label>
              <input type="password" className="input-dark" placeholder="••••••••"
                {...register('confirm', { required: true, validate: v => v === password || 'Passwords do not match' })} />
              {errors.confirm && <p className="text-xs mt-1.5 font-medium" style={{ color: '#dc2626' }}>{errors.confirm.message}</p>}
            </div>

            <button type="submit" disabled={loading} className="btn-red w-full justify-center mt-2" style={{ width: '100%' }}>
              {loading ? <><span className="spinner w-4 h-4" style={{ borderTopColor: '#fff' }} /> Creating account…</> : <>Create Account <ArrowRight className="w-4 h-4" /></>}
            </button>
          </form>

          <p className="text-center text-sm mt-8" style={{ color: '#6b7280' }}>
            Already have an account?{' '}
            <Link href="/auth/login" className="font-bold transition-colors hover:text-white" style={{ color: '#dc2626' }}>Sign in</Link>
          </p>
        </motion.div>
      </div>
    </div>
  )
}
