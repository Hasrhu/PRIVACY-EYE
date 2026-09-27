'use client'
import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { motion } from 'framer-motion'
import { Eye, EyeOff, ArrowRight, Shield } from 'lucide-react'
import toast from 'react-hot-toast'
import { authApi, getErrorMessage } from '@/lib/api'

interface LoginForm { email: string; password: string }

export default function LoginPage() {
  const router = useRouter()
  const [showPw, setShowPw] = useState(false)
  const [loading, setLoading] = useState(false)
  const { register, handleSubmit, formState: { errors } } = useForm<LoginForm>()

  const onSubmit = async (data: LoginForm) => {
    setLoading(true)
    try {
      await authApi.login(data.email, data.password)
      toast.success('Welcome back.')
      router.push('/dashboard')
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen grid lg:grid-cols-2" style={{ background: '#0a0a0a' }}>
      {/* Left panel — branding */}
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
            VERIFY<br />
            <span style={{ color: '#dc2626' }}>WHAT<br />YOU SEE.</span>
          </h1>
          <p className="text-sm max-w-sm" style={{ color: '#6b7280', lineHeight: '1.7' }}>
            AI Can Fake It. Privacy Eye Can Check It. Deepfake detection, voice clone analysis, and synthetic media forensics — all in one platform.
          </p>
        </div>

        <div className="flex gap-8 relative z-10">
          {[['15+', 'Signals'], ['<5s', 'Analysis'], ['0', 'Files Stored']].map(([n, l]) => (
            <div key={l}>
              <div className="font-display text-3xl" style={{ color: '#dc2626' }}>{n}</div>
              <div className="text-xs font-semibold uppercase tracking-wide2 mt-0.5" style={{ color: '#6b7280' }}>{l}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Right panel — form */}
      <div className="flex items-center justify-center px-6 py-12">
        <motion.div
          className="w-full max-w-md"
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          {/* Mobile logo */}
          <Link href="/" className="flex items-center gap-3 mb-10 lg:hidden">
            <div className="w-7 h-7 rounded flex items-center justify-center" style={{ background: '#dc2626' }}>
              <Shield className="w-4 h-4 text-white" />
            </div>
            <span className="font-display text-lg tracking-wider text-white">PRIVACY EYE</span>
          </Link>

          <p className="section-label mb-3">Welcome Back</p>
          <h2 className="text-3xl font-black text-white mb-8">Sign In</h2>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wide2 mb-2" style={{ color: '#9ca3af' }}>Email</label>
              <input type="email" className="input-dark" placeholder="you@example.com"
                {...register('email', { required: 'Email is required' })} />
              {errors.email && <p className="text-xs mt-1.5 font-medium" style={{ color: '#dc2626' }}>{errors.email.message}</p>}
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wide2 mb-2" style={{ color: '#9ca3af' }}>Password</label>
              <div className="relative">
                <input type={showPw ? 'text' : 'password'} className="input-dark pr-11" placeholder="••••••••"
                  {...register('password', { required: 'Password is required' })} />
                <button type="button" onClick={() => setShowPw(!showPw)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 transition-colors"
                  style={{ color: '#6b7280' }}>
                  {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {errors.password && <p className="text-xs mt-1.5 font-medium" style={{ color: '#dc2626' }}>{errors.password.message}</p>}
            </div>

            <button type="submit" disabled={loading} className="btn-red w-full justify-center mt-2" style={{ width: '100%' }}>
              {loading ? <><span className="spinner w-4 h-4" style={{ borderTopColor: '#fff' }} /> Signing in…</> : <>Sign In <ArrowRight className="w-4 h-4" /></>}
            </button>
          </form>

          <p className="text-center text-sm mt-8" style={{ color: '#6b7280' }}>
            No account?{' '}
            <Link href="/auth/register" className="font-bold transition-colors hover:text-white" style={{ color: '#dc2626' }}>
              Create one free
            </Link>
          </p>

          <p className="text-center text-xs mt-6" style={{ color: '#374151' }}>
            Results are probabilistic indicators only. Not legal advice.
          </p>
        </motion.div>
      </div>
    </div>
  )
}
