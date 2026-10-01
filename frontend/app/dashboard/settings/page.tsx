'use client'
import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Shield,
  Key,
  User as UserIcon,
  Trash2,
  CheckCircle2,
  Lock,
  Eye,
  AlertTriangle,
  RefreshCw,
  Laptop,
  LogOut,
  ShieldCheck,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { authApi, api, getErrorMessage } from '@/lib/api'
import { useAuth } from '@/contexts/AuthContext'
import type { User } from '@/types'
import { GlassCard } from '@/components/ui/GlassCard'
import { GlassButton } from '@/components/ui/GlassButton'

export default function SettingsPage() {
  const { user, refreshUser, logout } = useAuth()
  const [fullName, setFullName] = useState('')
  const [isSavingName, setIsSavingName] = useState(false)

  // Password Change State
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [isChangingPassword, setIsChangingPassword] = useState(false)

  // Sessions State
  const [sessions, setSessions] = useState<any[]>([])
  const [loadingSessions, setLoadingSessions] = useState(false)

  // Account Deletion State
  const [deleteConfirmation, setDeleteConfirmation] = useState('')
  const [isDeleting, setIsDeleting] = useState(false)

  useEffect(() => {
    if (user?.full_name) {
      setFullName(user.full_name)
    }
    fetchSessions()
  }, [user])

  const fetchSessions = async () => {
    setLoadingSessions(true)
    try {
      const res = await authApi.getSessions()
      setSessions(res.data || [])
    } catch {
      // ignore
    } finally {
      setLoadingSessions(false)
    }
  }

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!fullName.trim()) return
    setIsSavingName(true)
    try {
      await api.patch('/users/me', null, { params: { full_name: fullName.trim() } })
      await refreshUser()
      toast.success('Display name updated successfully.')
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setIsSavingName(false)
    }
  }

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!currentPassword || !newPassword) {
      toast.error('Please fill all password fields.')
      return
    }
    if (newPassword !== confirmPassword) {
      toast.error('New passwords do not match.')
      return
    }

    setIsChangingPassword(true)
    try {
      await authApi.changePassword(currentPassword, newPassword, confirmPassword)
      toast.success('Password updated! Other sessions have been signed out.')
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
      fetchSessions()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setIsChangingPassword(false)
    }
  }

  const handleLogoutAll = async () => {
    if (!confirm('Are you sure you want to sign out all other devices and sessions?')) return
    try {
      const res: any = await authApi.logoutAll()
      toast.success(res?.data?.message || 'All other sessions have been terminated.')
      fetchSessions()
    } catch (err) {
      toast.error(getErrorMessage(err))
    }
  }

  const handleDeleteSession = async (sessionId: string) => {
    try {
      await authApi.deleteSession(sessionId)
      toast.success('Session terminated.')
      fetchSessions()
    } catch (err) {
      toast.error(getErrorMessage(err))
    }
  }

  const handleDeleteAccount = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!deleteConfirmation) {
      toast.error('Enter your password to confirm account deletion.')
      return
    }
    if (!confirm('CRITICAL ACTION: This will permanently delete your account, analysis history, and reports. Proceed?')) {
      return
    }

    setIsDeleting(true)
    try {
      await authApi.deleteAccount(deleteConfirmation)
      toast.success('Account permanently deleted.')
      await logout()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <div className="max-w-5xl mx-auto space-y-10">
      {/* Header */}
      <div>
        <span className="text-xs uppercase font-mono tracking-widest text-brand-blue">
          Account Governance & Credentials
        </span>
        <h1 className="text-3xl font-bold tracking-tight text-white mt-1">Security & Settings</h1>
        <p className="text-sm text-white/50 mt-1">
          Manage identity, authentication factors, active device sessions, and account autonomy
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Profile & Credentials */}
        <div className="lg:col-span-2 space-y-8">
          {/* Identity Card */}
          <GlassCard className="p-6 md:p-8 space-y-6">
            <div className="flex items-center gap-3 pb-4 border-b border-white/8">
              <div className="w-10 h-10 rounded-2xl bg-brand-blue/10 border border-brand-blue/20 flex items-center justify-center">
                <UserIcon className="w-5 h-5 text-brand-blue" />
              </div>
              <div>
                <h2 className="text-base font-semibold text-white">Operator Profile</h2>
                <p className="text-xs text-white/50">Stored securely in PostgreSQL</p>
              </div>
            </div>

            <form onSubmit={handleSaveProfile} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-white/70">Display Name</label>
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="glass-input"
                    placeholder="Operator Name"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-white/70">Email Address (Immutable)</label>
                  <input
                    type="email"
                    disabled
                    value={user?.email || ''}
                    className="glass-input opacity-60 cursor-not-allowed bg-black/40"
                  />
                </div>
              </div>

              <div className="flex justify-end pt-2">
                <GlassButton type="submit" variant="primary" size="sm" isLoading={isSavingName}>
                  Save Profile Changes
                </GlassButton>
              </div>
            </form>
          </GlassCard>

          {/* Change Password Card */}
          <GlassCard className="p-6 md:p-8 space-y-6">
            <div className="flex items-center gap-3 pb-4 border-b border-white/8">
              <div className="w-10 h-10 rounded-2xl bg-brand-violet/10 border border-brand-violet/20 flex items-center justify-center">
                <Lock className="w-5 h-5 text-brand-violet" />
              </div>
              <div>
                <h2 className="text-base font-semibold text-white">Argon2id Password Security</h2>
                <p className="text-xs text-white/50">Update login credentials and invalidate compromised sessions</p>
              </div>
            </div>

            <form onSubmit={handleChangePassword} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-white/70">Current Password</label>
                <input
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  className="glass-input"
                  placeholder="••••••••••••"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-white/70">New Password (8+ chars)</label>
                  <input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="glass-input"
                    placeholder="••••••••••••"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-white/70">Confirm New Password</label>
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="glass-input"
                    placeholder="••••••••••••"
                  />
                </div>
              </div>

              <div className="flex justify-end pt-2">
                <GlassButton type="submit" variant="primary" size="sm" isLoading={isChangingPassword}>
                  Update Password
                </GlassButton>
              </div>
            </form>
          </GlassCard>

          {/* Active Device Sessions Card */}
          <GlassCard className="p-6 md:p-8 space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-white/8">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-2xl bg-brand-cyan/10 border border-brand-cyan/20 flex items-center justify-center">
                  <Laptop className="w-5 h-5 text-brand-cyan" />
                </div>
                <div>
                  <h2 className="text-base font-semibold text-white">Active Device Sessions</h2>
                  <p className="text-xs text-white/50">Track and terminate active sessions across platforms</p>
                </div>
              </div>
              <GlassButton variant="danger" size="sm" onClick={handleLogoutAll} icon={<LogOut className="w-3.5 h-3.5" />}>
                Logout Everywhere
              </GlassButton>
            </div>

            <div className="space-y-3">
              {sessions.map((sess) => (
                <div
                  key={sess.id}
                  className="p-4 rounded-2xl bg-white/[0.03] border border-white/8 flex items-center justify-between"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-medium text-white">
                        {sess.user_agent?.includes('Mozilla') ? 'Web Browser' : 'API Client'}
                      </span>
                      {sess.is_current && (
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-status-safe/15 text-status-safe border border-status-safe/30">
                          Current Device
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] font-mono text-white/40">
                      IP: {sess.ip_address || 'Localhost'} • Last active: {new Date(sess.last_used_at).toLocaleTimeString()}
                    </p>
                  </div>

                  {!sess.is_current && (
                    <button
                      onClick={() => handleDeleteSession(sess.id)}
                      className="text-xs text-status-danger hover:underline font-mono"
                    >
                      Revoke
                    </button>
                  )}
                </div>
              ))}
            </div>
          </GlassCard>

          {/* Danger Zone: Account Deletion */}
          <GlassCard className="p-6 md:p-8 space-y-6 border-status-danger/30 bg-status-danger/5">
            <div className="flex items-center gap-3 pb-4 border-b border-status-danger/20">
              <div className="w-10 h-10 rounded-2xl bg-status-danger/10 border border-status-danger/30 flex items-center justify-center">
                <Trash2 className="w-5 h-5 text-status-danger" />
              </div>
              <div>
                <h2 className="text-base font-semibold text-white">Delete Account</h2>
                <p className="text-xs text-status-danger/80">Permanent, irreversible cascading wipe</p>
              </div>
            </div>

            <form onSubmit={handleDeleteAccount} className="space-y-4">
              <p className="text-xs text-white/60 leading-relaxed">
                Deleting your account immediately purges all biometric records, video analyses, forensic signals, and persistent sessions from PostgreSQL.
              </p>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-white/70">Confirm Password to Delete</label>
                <input
                  type="password"
                  value={deleteConfirmation}
                  onChange={(e) => setDeleteConfirmation(e.target.value)}
                  className="glass-input"
                  placeholder="Enter current password"
                />
              </div>

              <div className="flex justify-end pt-2">
                <GlassButton type="submit" variant="danger" size="sm" isLoading={isDeleting}>
                  Permanently Delete My Account
                </GlassButton>
              </div>
            </form>
          </GlassCard>
        </div>

        {/* Right Column: Account Status & Quota */}
        <div className="space-y-6">
          <GlassCard className="p-6 space-y-4 border border-brand-blue/20">
            <div className="flex items-center gap-2 text-brand-blue">
              <ShieldCheck className="w-4 h-4" />
              <span className="text-xs font-mono uppercase tracking-wider font-bold">
                Account Status
              </span>
            </div>

            <div>
              <div className="text-2xl font-bold text-white uppercase font-mono">
                {user?.role || 'USER'}
              </div>
              <p className="text-xs text-white/50 mt-1">
                Database ID: <span className="font-mono">{user?.id?.slice(0, 8)}...</span>
              </p>
            </div>

            <div className="pt-2 border-t border-white/8 space-y-2 text-xs">
              <div className="flex justify-between text-white/70">
                <span>Monthly Scans:</span>
                <span className="font-mono text-white">
                  {user?.scans_used_this_month || 0} / {user?.scans_limit || 20}
                </span>
              </div>
              <div className="h-1.5 w-full bg-white/10 rounded-full overflow-hidden">
                <div
                  className="h-full bg-brand-blue rounded-full transition-all"
                  style={{
                    width: `${Math.min(100, (((user?.scans_used_this_month || 0) / (user?.scans_limit || 20)) * 100))}%`,
                  }}
                />
              </div>
            </div>
          </GlassCard>
        </div>
      </div>
    </div>
  )
}
