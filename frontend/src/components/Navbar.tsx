'use client';

import React from 'react';
import { Calendar, CheckCircle2, Sparkles, LayoutDashboard, ListTodo, LogOut, User as UserIcon } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '../context/AuthContext';

interface NavbarProps {
  onOpenAgent: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onOpenAgent }) => {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const navItems = [
    { label: 'Dashboard', href: '/', icon: LayoutDashboard },
    { label: 'Tasks', href: '/tasks', icon: ListTodo },
    { label: 'Calendar', href: '/calendar', icon: Calendar },
  ];

  const getInitials = (name?: string, email?: string) => {
    if (name && name.trim()) {
      return name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
    }
    if (email) {
      return email.substring(0, 2).toUpperCase();
    }
    return 'U';
  };

  return (
    <nav className="sticky top-0 z-40 w-full glass-panel border-b border-gray-800/60 bg-surface/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-violet-600 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <span className="text-lg font-bold bg-gradient-to-r from-white via-gray-200 to-indigo-300 bg-clip-text text-transparent">
              TaskAgent AI
            </span>
            <span className="block text-[10px] uppercase tracking-wider font-semibold text-cyan-400">
              Personal Planning Engine
            </span>
          </div>
        </div>

        {/* Navigation Links */}
        <div className="hidden md:flex items-center gap-1 bg-surface-card/60 p-1.5 rounded-xl border border-gray-800">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
                }`}
              >
                <Icon className="w-4 h-4" />
                {item.label}
              </Link>
            );
          })}
        </div>

        {/* Right Actions & User Profile */}
        <div className="flex items-center gap-3">
          <button
            onClick={onOpenAgent}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 text-white font-medium text-sm hover:from-indigo-500 hover:to-violet-500 shadow-lg shadow-indigo-600/30 transition-all duration-200 hover:scale-105 active:scale-95"
          >
            <Sparkles className="w-4 h-4 text-cyan-300 animate-pulse" />
            <span className="hidden sm:inline">Ask AI Planner</span>
          </button>

          {user && (
            <div className="flex items-center gap-2 pl-2 border-l border-gray-800">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-surface-card/80 border border-gray-800/80">
                <div className="w-7 h-7 rounded-lg bg-indigo-600/30 border border-indigo-500/40 text-indigo-300 text-xs font-extrabold flex items-center justify-center">
                  {getInitials(user.full_name, user.email)}
                </div>
                <div className="hidden lg:block text-left">
                  <span className="block text-xs font-semibold text-white leading-tight">
                    {user.full_name || 'User'}
                  </span>
                  <span className="block text-[10px] text-gray-400 leading-tight truncate max-w-[120px]">
                    {user.email}
                  </span>
                </div>
              </div>

              <button
                onClick={logout}
                title="Log out"
                className="p-2 rounded-xl text-gray-400 hover:text-red-400 hover:bg-red-500/10 border border-transparent hover:border-red-500/20 transition"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>

      </div>
    </nav>
  );
};

