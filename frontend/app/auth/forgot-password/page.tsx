'use client'
import React, { useState } from 'react'
import Link from 'next/link'
import { useForm } from 'react-hook-form'
import { motion } from 'framer-motion'
import { Mail, ArrowRight, ShieldCheck, CheckCircle2 } from 'lucide-react'
import toast from 'react-hot-toast'

import { authApi, getErrorMessage } from '@/lib/api'
import { BrandLogo } from '@/components/layout/BrandLogo'
import { GlassCard } from '@/components/ui/GlassCard'
import { GlassButton } from '@/components/ui/GlassButton'

interface ForgotForm {
  email: string
}

export default function ForgotPasswordPage() {
  const [loading, setLoading] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotForm>()

  const onSubmit = async (data: ForgotForm) => {
    setLoading(true)
    try {
      await authApi.forgotPassword(data.email)
      setSubmitted(true)
      toast.success('Request received.')
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-canvas relative">
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
              Credential Recovery
            </span>
            <h1 className="text-2xl font-bold tracking-tight text-white">Reset Password</h1>
            <p className="text-xs text-white/50">
              Enter your registered work email to receive password reset instructions
            </p>
          </div>

          {submitted ? (
            <div className="space-y-4 py-4 text-center">
              <div className="w-12 h-12 mx-auto rounded-2xl bg-status-safe/10 border border-status-safe/30 flex items-center justify-center">
                <CheckCircle2 className="w-6 h-6 text-status-safe" />
              </div>
              <p className="text-xs text-white/80 leading-relaxed">
                If an account exists for that email, recovery instructions have been dispatched. Check your inbox and spam folders.
              </p>
              <Link href="/auth/login" className="block pt-2">
                <GlassButton variant="primary" size="md" className="w-full">
                  Return to Sign In
                </GlassButton>
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-white/70">Email Address</label>
                <div className="relative">
                  <Mail className="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-white/40" />
                  <input
                    type="email"
                    placeholder="analyst@agency.gov"
                    className="glass-input pl-11"
                    {...register('email', { required: 'Email is required' })}
                  />
                </div>
                {errors.email && (
                  <p className="text-xs text-status-danger">{errors.email.message}</p>
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
                Send Recovery Link
              </GlassButton>
            </form>
          )}

          <div className="pt-4 border-t border-white/6 text-center text-xs text-white/50">
            Remember your credentials?{' '}
            <Link href="/auth/login" className="text-brand-blue font-semibold hover:underline">
              Sign In
            </Link>
          </div>
        </GlassCard>
      </motion.div>
    </div>
  )
}
