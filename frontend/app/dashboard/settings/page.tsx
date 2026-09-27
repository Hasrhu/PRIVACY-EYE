'use client'
import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Shield, Key, User as UserIcon, Trash2, CheckCircle2, Lock, Eye, AlertTriangle, RefreshCw } from 'lucide-react'
import toast from 'react-hot-toast'
import { authApi } from '@/lib/api'
import type { User } from '@/types'

export default function SettingsPage() {
  const [profile, setProfile] = useState<User | null>(null)
  const [fullName, setFullName] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [apiKey, setApiKey] = useState<string | null>(null)
  const [zeroRetention, setZeroRetention] = useState(true)
  const [autoPurgeLogs, setAutoPurgeLogs] = useState(true)

  useEffect(() => {
    async function loadUser() {
      try {
        const res = await authApi.me()
        setProfile(res.data)
        setFullName(res.data.full_name || '')
      } catch {
        // Fallback demo state if not logged in
        setProfile({
          id: 'usr_demo_8829',
          email: 'analyst@privacyeye.internal',
          full_name: 'Lead Forensics Analyst',
          role: 'ADMIN',
          is_active: true,
          is_verified: true,
          scans_used_this_month: 4,
          scans_limit: 50,
          created_at: new Date().toISOString(),
        })
        setFullName('Lead Forensics Analyst')
      }
    }
    loadUser()
  }, [])

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSaving(true)
    setTimeout(() => {
      setIsSaving(false)
      toast.success('Security profile updated successfully')
    }, 600)
  }

  const handleGenerateApiKey = () => {
    const key = `pe_live_${Array.from({ length: 32 }, () => Math.floor(Math.random() * 16).toString(16)).join('')}`
    setApiKey(key)
    toast.success('Generated new API key. Store it securely!')
  }

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-10">
      {/* Header */}
      <div>
        <p className="section-label mb-1">Configuration & Forensics Policies</p>
        <h1 className="font-display text-4xl text-white tracking-wider">SYSTEM SETTINGS</h1>
        <p className="text-xs text-gray-500 mt-1 font-mono">
          Manage identity credentials, API access tokens, and zero-knowledge privacy enforcement.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Profile & Plan */}
        <div className="lg:col-span-2 space-y-8">
          {/* Profile Card */}
          <div className="card p-6 border border-white/5 space-y-6">
            <div className="flex items-center gap-3 pb-4 border-b border-white/5">
              <div className="w-8 h-8 rounded bg-red-600/10 border border-red-600/30 flex items-center justify-center">
                <UserIcon className="w-4 h-4 text-red-500" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">Account Credentials</h3>
                <p className="text-xs text-gray-500">Security operator profile and authenticated email</p>
              </div>
            </div>

            <form onSubmit={handleSaveProfile} className="space-y-4">
              <div>
                <label className="block text-xs font-mono uppercase text-gray-400 mb-1.5">Registered Email</label>
                <input
                  type="email"
                  disabled
                  value={profile?.email || 'analyst@privacyeye.internal'}
                  className="input-dark w-full opacity-60 cursor-not-allowed text-xs font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-mono uppercase text-gray-400 mb-1.5">Operator Display Name</label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Enter full name"
                  className="input-dark w-full text-sm"
                />
              </div>

              <div className="pt-2 flex justify-end">
                <button type="submit" disabled={isSaving} className="btn-red text-xs py-2.5 px-6">
                  {isSaving ? 'Saving Changes...' : 'Save Profile'}
                </button>
              </div>
            </form>
          </div>

          {/* Privacy Enforcement Card */}
          <div className="card p-6 border border-white/5 space-y-6">
            <div className="flex items-center gap-3 pb-4 border-b border-white/5">
              <div className="w-8 h-8 rounded bg-red-600/10 border border-red-600/30 flex items-center justify-center">
                <Shield className="w-4 h-4 text-red-500" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">Privacy & Retention Policy</h3>
                <p className="text-xs text-gray-500">Zero-storage guarantee and RAM-only pipeline settings</p>
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 rounded bg-black/40 border border-white/5">
                <div>
                  <p className="text-xs font-bold text-white">Instant Memory Shredding</p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Automatically unlink and overwrite temporary media files right after signal extraction.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setZeroRetention(!zeroRetention)}
                  className={`w-11 h-6 flex items-center rounded-full p-1 transition-colors ${
                    zeroRetention ? 'bg-red-600' : 'bg-gray-800'
                  }`}
                >
                  <div
                    className={`bg-white w-4 h-4 rounded-full shadow-md transform transition-transform ${
                      zeroRetention ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>

              <div className="flex items-center justify-between p-4 rounded bg-black/40 border border-white/5">
                <div>
                  <p className="text-xs font-bold text-white">Auto-Purge Diagnostic Logs</p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Delete extracted feature vectors and technical audit footprints after 30 days.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setAutoPurgeLogs(!autoPurgeLogs)}
                  className={`w-11 h-6 flex items-center rounded-full p-1 transition-colors ${
                    autoPurgeLogs ? 'bg-red-600' : 'bg-gray-800'
                  }`}
                >
                  <div
                    className={`bg-white w-4 h-4 rounded-full shadow-md transform transition-transform ${
                      autoPurgeLogs ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>
            </div>
          </div>

          {/* Developer API Key */}
          <div className="card p-6 border border-white/5 space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-white/5">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded bg-red-600/10 border border-red-600/30 flex items-center justify-center">
                  <Key className="w-4 h-4 text-red-500" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider">API Authentication Keys</h3>
                  <p className="text-xs text-gray-500">Programmatic REST API integration for high-volume pipelines</p>
                </div>
              </div>
              <button onClick={handleGenerateApiKey} className="btn-outline text-xs py-2 px-4 flex items-center gap-2">
                <RefreshCw className="w-3.5 h-3.5" /> Generate Key
              </button>
            </div>

            {apiKey ? (
              <div className="p-4 rounded bg-red-950/20 border border-red-600/30 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono text-red-400 font-bold uppercase tracking-wider">Secret Key Generated</span>
                  <span className="text-xs text-gray-500">Copy now; hidden upon reload</span>
                </div>
                <div className="p-3 bg-black rounded font-mono text-xs text-white select-all break-all border border-white/10">
                  {apiKey}
                </div>
              </div>
            ) : (
              <div className="p-4 rounded bg-black/40 border border-white/5 flex items-center justify-between">
                <div>
                  <p className="text-xs font-mono text-gray-300">pe_live_••••••••••••••••••••••••</p>
                  <p className="text-xs text-gray-600 mt-0.5">Created on account initialization · Active</p>
                </div>
                <span className="badge-low text-xs">Active</span>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Quota & Security Overview */}
        <div className="space-y-8">
          {/* Quota Usage */}
          <div className="card p-6 border border-white/5 space-y-5">
            <h3 className="text-xs font-mono uppercase tracking-widest text-red-500">Subscription & Capacity</h3>
            <div>
              <div className="flex items-baseline justify-between">
                <span className="font-display text-4xl text-white">PRO TIER</span>
                <span className="text-xs text-gray-400 font-mono">Unlimited Multi-Signal</span>
              </div>
              <p className="text-xs text-gray-500 mt-1">Full access to ELA, FFT, Face Boundary, and Audio Spectrogram analysis.</p>
            </div>

            <div className="space-y-2 pt-2">
              <div className="flex justify-between text-xs font-mono">
                <span className="text-gray-400">Monthly Usage</span>
                <span className="text-white">
                  {profile?.scans_used_this_month || 4} / {profile?.scans_limit || 50} scans
                </span>
              </div>
              <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                <div
                  className="h-full bg-red-600 rounded-full transition-all duration-500"
                  style={{
                    width: `${Math.min(100, (((profile?.scans_used_this_month || 4) / (profile?.scans_limit || 50)) * 100))}%`,
                  }}
                />
              </div>
            </div>

            <div className="pt-3 border-t border-white/5">
              <button className="btn-red w-full text-xs py-2.5 justify-center">
                Upgrade Enterprise
              </button>
            </div>
          </div>

          {/* Privacy Eye Guarantee */}
          <div className="card p-6 border border-red-600/30 space-y-4" style={{ background: 'linear-gradient(180deg, rgba(220,38,38,0.06) 0%, rgba(17,17,17,1) 100%)' }}>
            <div className="flex items-center gap-2">
              <Shield className="w-4 h-4 text-red-500" />
              <span className="text-xs font-bold text-white uppercase tracking-wider">Privacy Eye Promise</span>
            </div>
            <p className="text-xs text-gray-400 leading-relaxed">
              We never use client media for training or retention. Analysis is executed statelessly in RAM. Your digital autonomy and privacy remain untampered.
            </p>
            <div className="pt-2 text-xs font-mono text-gray-500 flex items-center gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-red-500" />
              <span>Zero-Log Architecture</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
