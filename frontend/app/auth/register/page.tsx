'use client'
import React, { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { motion } from 'framer-motion'
import { Eye, EyeOff, Lock, Mail, User, ArrowRight, Check, ShieldCheck } from 'lucide-react'
import toast from 'react-hot-toast'

import { authApi, getErrorMessage } from '@/lib/api'
import { BrandLogo } from '@/components/layout/BrandLogo'
import { GlassCard } from '@/components/ui/GlassCard'
import { GlassButton } from '@/components/ui/GlassButton'

interface RegisterForm {
  full_name: string
  email: string
  password: string
}

export default function RegisterPage() {
  const router = useRouter()
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<RegisterForm>()

  const password = watch('password', '')

  const strengthRules = [
    { label: '8+ chars', met: password.length >= 8 },
    { label: 'Uppercase', met: /[A-Z]/.test(password) },
    { label: 'Number', met: /[0-9]/.test(password) },
  ]

  const onSubmit = async (data: RegisterForm) => {
    setLoading(true)
    try {
      await authApi.register(data.email, data.password, data.full_name)
      await authApi.login(data.email, data.password)
      toast.success('Account created! Welcome to Privacy Eye.')
      router.push('/dashboard')
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-canvas relative">
      {/* Background ambient lighting */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-brand-blue/10 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-brand-violet/10 rounded-full blur-[100px] pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md"
      >
        <div className="flex justify-center mb-8">
          <BrandLogo size="lg" />
        </div>

        <GlassCard variant="floating" className="p-8 md:p-10 space-y-6 border border-white/14">
          <div className="text-center space-y-1">
            <span className="text-xs uppercase font-mono tracking-widest text-brand-blue">
              Autonomous Verification
            </span>
            <h1 className="text-2xl font-bold tracking-tight text-white">Create Account</h1>
            <p className="text-xs text-white/50">Gain full access to real-time biometric defense</p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-1.5">
              <label className="block text-xs font-semibold text-white/70">Full Name</label>
              <div className="relative">
                <User className="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-white/40" />
                <input
                  type="text"
                  placeholder="Security Specialist"
                  className="glass-input pl-11"
                  {...register('full_name', { required: 'Name is required' })}
                />
              </div>
              {errors.full_name && (
                <p className="text-xs text-status-danger">{errors.full_name.message}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <label className="block text-xs font-semibold text-white/70">Work Email</label>
              <div className="relative">
                <Mail className="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-white/40" />
                <input
                  type="email"
                  placeholder="specialist@agency.gov"
                  className="glass-input pl-11"
                  {...register('email', { required: 'Email address is required' })}
                />
              </div>
              {errors.email && (
                <p className="text-xs text-status-danger">{errors.email.message}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <label className="block text-xs font-semibold text-white/70">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-white/40" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••••••"
                  className="glass-input pl-11 pr-11"
                  {...register('password', {
                    required: 'Password is required',
                    minLength: { value: 8, message: 'Minimum 8 characters' },
                  })}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-white/40 hover:text-white transition-colors"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>

              {/* Password strength tags */}
              <div className="flex gap-2 pt-1">
                {strengthRules.map((rule, idx) => (
                  <span
                    key={idx}
                    className={`text-[10px] font-mono px-2 py-0.5 rounded-md flex items-center gap-1 ${
                      rule.met ? 'bg-status-safe/15 text-status-safe' : 'bg-white/5 text-white/30'
                    }`}
                  >
                    <Check className={`w-3 h-3 ${rule.met ? 'opacity-100' : 'opacity-0'}`} />
                    {rule.label}
                  </span>
                ))}
              </div>
            </div>

            <GlassButton
              type="submit"
              variant="primary"
              size="lg"
              isLoading={loading}
              className="w-full shadow-glow-blue mt-2"
              icon={<ArrowRight className="w-4 h-4" />}
            >
              Register & Initialize
            </GlassButton>
          </form>

          <div className="pt-4 border-t border-white/6 text-center text-xs text-white/50">
            Already have an active key?{' '}
            <Link href="/auth/login" className="text-brand-blue font-semibold hover:underline">
              Sign In
            </Link>
          </div>
        </GlassCard>
      </motion.div>
    </div>
  )
}
