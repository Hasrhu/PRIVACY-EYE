'use client'
import React, { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { motion } from 'framer-motion'
import { Eye, EyeOff, Lock, Mail, ArrowRight, ShieldCheck } from 'lucide-react'
import toast from 'react-hot-toast'

import { authApi, getErrorMessage } from '@/lib/api'
import { BrandLogo } from '@/components/layout/BrandLogo'
import { GlassCard } from '@/components/ui/GlassCard'
import { GlassButton } from '@/components/ui/GlassButton'

interface LoginForm {
  email: string
  password: string
}

export default function LoginPage() {
  const router = useRouter()
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>()

  const onSubmit = async (data: LoginForm) => {
    setLoading(true)
    try {
      await authApi.login(data.email, data.password)
      toast.success('Authentication confirmed.')
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
              Secure Perimeter Access
            </span>
            <h1 className="text-2xl font-bold tracking-tight text-white">Sign In to Privacy Eye</h1>
            <p className="text-xs text-white/50">Enter credentials to unlock active protection</p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-1.5">
              <label className="block text-xs font-semibold text-white/70">Email Address</label>
              <div className="relative">
                <Mail className="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-white/40" />
                <input
                  type="email"
                  placeholder="analyst@enterprise.com"
                  className="glass-input pl-11"
                  {...register('email', { required: 'Email address is required' })}
                />
              </div>
              {errors.email && (
                <p className="text-xs text-status-danger">{errors.email.message}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="block text-xs font-semibold text-white/70">Password</label>
                <span className="text-[11px] text-brand-blue cursor-pointer hover:underline">
                  Forgot?
                </span>
              </div>
              <div className="relative">
                <Lock className="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-white/40" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••••••"
                  className="glass-input pl-11 pr-11"
                  {...register('password', { required: 'Password is required' })}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-white/40 hover:text-white transition-colors"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {errors.password && (
                <p className="text-xs text-status-danger">{errors.password.message}</p>
              )}
            </div>

            <GlassButton
              type="submit"
              variant="primary"
              size="lg"
              isLoading={loading}
              className="w-full shadow-glow-blue mt-2"
              icon={<ArrowRight className="w-4 h-4" />}
            >
              Sign In
            </GlassButton>
          </form>

          <div className="pt-4 border-t border-white/6 text-center text-xs text-white/50">
            Don't have an account?{' '}
            <Link href="/auth/register" className="text-brand-blue font-semibold hover:underline">
              Create an account
            </Link>
          </div>
        </GlassCard>
      </motion.div>
    </div>
  )
}
