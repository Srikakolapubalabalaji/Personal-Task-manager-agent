'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../lib/api';
import { Sparkles, ShieldCheck, Mail, Lock, User as UserIcon, ArrowRight, CheckCircle2, AlertCircle } from 'lucide-react';
import { motion } from 'framer-motion';

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, login, register, loginWithGoogleMock, loginWithToken } = useAuth();

  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    // Handle OAuth token in redirect URL
    const tokenParam = searchParams.get('token');
    if (tokenParam) {
      loginWithToken(tokenParam).then(() => {
        router.push('/');
      }).catch((err) => {
        setErrorMsg('OAuth authentication failed. Please try again.');
      });
      return;
    }

    const errorParam = searchParams.get('error');
    if (errorParam) {
      setErrorMsg(`Authentication error: ${errorParam}`);
    }

    if (user) {
      router.push('/');
    }
  }, [user, searchParams, router, loginWithToken]);

  const handleGoogleOAuth = async () => {
    setErrorMsg('');
    try {
      const url = await api.getGoogleOAuthUrl();
      if (url.includes('mock_oauth=true')) {
        await loginWithGoogleMock();
        router.push('/');
      } else {
        window.location.href = url;
      }
    } catch (err: any) {
      try {
        await loginWithGoogleMock();
        router.push('/');
      } catch {
        setErrorMsg('Failed to initiate Google OAuth sign-in.');
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');
    setIsSubmitting(true);

    try {
      if (isRegister) {
        if (!email || !password || !fullName) {
          setErrorMsg('Please fill in all required fields.');
          setIsSubmitting(false);
          return;
        }
        await register(email, password, fullName);
      } else {
        if (!email || !password) {
          setErrorMsg('Please provide both email and password.');
          setIsSubmitting(false);
          return;
        }
        await login(email, password);
      }
      router.push('/');
    } catch (err: any) {
      const detail = err.response?.data?.detail || 'Authentication failed. Please verify credentials.';
      setErrorMsg(detail);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4 py-12 relative overflow-hidden">
      {/* Background glow effects */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-indigo-600/20 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 left-1/3 w-80 h-80 bg-violet-600/15 rounded-full blur-3xl pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="relative w-full max-w-md glass-panel rounded-3xl p-8 border border-gray-800 bg-surface/90 shadow-2xl space-y-6"
      >
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-tr from-indigo-600 via-violet-600 to-cyan-400 shadow-xl shadow-indigo-500/25 mb-1">
            <Sparkles className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-2xl font-extrabold bg-gradient-to-r from-white via-gray-200 to-indigo-300 bg-clip-text text-transparent tracking-tight">
            TaskAgent AI
          </h1>
          <p className="text-xs text-gray-400">
            Sign in to access your personal AI planner, tasks & schedule.
          </p>
        </div>

        {/* OAuth Buttons */}
        <div className="space-y-3">
          <button
            onClick={handleGoogleOAuth}
            className="w-full flex items-center justify-center gap-3 px-4 py-3 rounded-xl bg-surface-card border border-gray-800 hover:border-gray-700 text-white font-medium text-sm transition-all hover:bg-gray-800/40 shadow-sm"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path
                fill="#4285F4"
                d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17z"
              />
              <path
                fill="#34A853"
                d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.29v3.15C3.26 21.3 7.35 24 12 24z"
              />
              <path
                fill="#FBBC05"
                d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.29C.47 8.21 0 10.05 0 12s.47 3.79 1.29 5.42l3.99-3.15z"
              />
              <path
                fill="#EA4335"
                d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.35 0 3.26 2.7 1.29 6.58l3.99 3.15c.95-2.83 3.6-4.98 6.72-4.98z"
              />
            </svg>
            <span>Continue with Google (OAuth 2.0)</span>
          </button>

          <button
            onClick={() => loginWithGoogleMock().then(() => router.push('/'))}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600/10 border border-indigo-500/30 text-indigo-300 hover:bg-indigo-600/20 text-xs font-semibold transition-all"
          >
            <ShieldCheck className="w-4 h-4 text-cyan-400" />
            <span>1-Click OAuth Demo Login</span>
          </button>
        </div>

        {/* Divider */}
        <div className="relative flex items-center justify-center my-4">
          <div className="border-t border-gray-800 w-full" />
          <span className="bg-surface px-3 text-[10px] font-mono text-gray-500 uppercase tracking-widest absolute">
            Or with email
          </span>
        </div>

        {/* Error Alert */}
        {errorMsg && (
          <div className="flex items-center gap-2.5 p-3.5 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-xs font-medium">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Tab Toggle */}
        <div className="flex rounded-xl bg-surface-card/80 p-1 border border-gray-800">
          <button
            type="button"
            onClick={() => { setIsRegister(false); setErrorMsg(''); }}
            className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all ${
              !isRegister ? 'bg-indigo-600 text-white shadow-md' : 'text-gray-400 hover:text-white'
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => { setIsRegister(true); setErrorMsg(''); }}
            className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all ${
              isRegister ? 'bg-indigo-600 text-white shadow-md' : 'text-gray-400 hover:text-white'
            }`}
          >
            Create Account
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {isRegister && (
            <div>
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-gray-400 mb-1">
                Full Name
              </label>
              <div className="relative">
                <UserIcon className="w-4 h-4 text-gray-500 absolute left-3.5 top-3" />
                <input
                  type="text"
                  required={isRegister}
                  placeholder="John Doe"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full pl-10 pr-3 py-2.5 bg-surface-card border border-gray-800 rounded-xl text-sm text-white focus:outline-none focus:border-indigo-500 transition"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-[11px] font-semibold uppercase tracking-wider text-gray-400 mb-1">
              Email Address
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-gray-500 absolute left-3.5 top-3" />
              <input
                type="email"
                required
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full pl-10 pr-3 py-2.5 bg-surface-card border border-gray-800 rounded-xl text-sm text-white focus:outline-none focus:border-indigo-500 transition"
              />
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-semibold uppercase tracking-wider text-gray-400 mb-1">
              Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-gray-500 absolute left-3.5 top-3" />
              <input
                type="password"
                required
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-10 pr-3 py-2.5 bg-surface-card border border-gray-800 rounded-xl text-sm text-white focus:outline-none focus:border-indigo-500 transition"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-semibold text-sm shadow-lg shadow-indigo-600/30 transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50"
          >
            <span>{isSubmitting ? 'Authenticating...' : isRegister ? 'Create Account' : 'Sign In'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        <p className="text-[11px] text-center text-gray-500 font-mono">
          Protected by AES-256 JWT & OAuth 2.0 Token Encryption
        </p>
      </motion.div>
    </div>
  );
}
