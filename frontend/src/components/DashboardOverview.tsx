'use client';

import React from 'react';
import { DailyPlanResponse, Task, CalendarEvent } from '../lib/types';
import { 
  CheckCircle2, Clock, AlertTriangle, Calendar, Sparkles, ArrowRight, Zap, Play 
} from 'lucide-react';
import { motion } from 'framer-motion';

interface DashboardOverviewProps {
  plan: DailyPlanResponse | null;
  tasks: Task[];
  events: CalendarEvent[];
  onOpenAgent: () => void;
  onCompleteTask: (id: string) => void;
}

export const DashboardOverview: React.FC<DashboardOverviewProps> = ({
  plan,
  tasks,
  events,
  onOpenAgent,
  onCompleteTask,
}) => {
  const completedCount = tasks.filter((t) => t.status === 'COMPLETED').length;
  const pendingCount = tasks.filter((t) => t.status === 'PENDING').length;
  const totalCount = tasks.length;
  const progressPercent = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;
  const overdueCount = plan?.overdue_count || 0;

  const nextTask = tasks.find((t) => t.status === 'PENDING');

  const formatTimeString = (dateStr: string): string => {
    if (!dateStr) return '';
    if (dateStr.includes('T')) {
      const timePart = dateStr.split('T')[1];
      const match = timePart.match(/^(\d{2}):(\d{2})/);
      if (match) return `${match[1]}:${match[2]}`;
    }
    const match = dateStr.match(/(\d{2}):(\d{2})/);
    if (match) return `${match[1]}:${match[2]}`;
    return dateStr;
  };

  const todayStr = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });

  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <div className="glass-panel rounded-2xl p-6 sm:p-8 relative overflow-hidden border border-indigo-500/20 bg-gradient-to-r from-indigo-950/40 via-surface to-surface">
        <div className="absolute top-0 right-0 w-96 h-96 bg-glow-violet opacity-50 pointer-events-none" />
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
          <div>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 mb-3">
              <Calendar className="w-3.5 h-3.5" />
              {todayStr}
            </span>
            <h1 className="text-3xl font-extrabold text-white tracking-tight">
              Good day! Ready for a focused schedule?
            </h1>
            <p className="text-gray-400 mt-2 text-sm max-w-xl">
              Your AI Agent has synchronized your Google Calendar and prioritized your tasks based on deadline urgency and effort estimates.
            </p>
          </div>
          <button
            onClick={onOpenAgent}
            className="flex items-center gap-3 px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-600 via-violet-600 to-cyan-500 text-white font-semibold shadow-lg shadow-indigo-500/30 hover:shadow-indigo-500/50 hover:scale-[1.02] transition-all duration-200"
          >
            <Sparkles className="w-5 h-5 text-cyan-200" />
            <span>Generate Optimized Plan</span>
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        {/* Progress % */}
        <div className="glass-panel p-5 rounded-xl border border-gray-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase text-gray-400">Today's Progress</span>
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="text-3xl font-extrabold text-white">{progressPercent}%</span>
            <span className="text-xs text-gray-400">{completedCount} of {totalCount} completed</span>
          </div>
          <div className="mt-3 w-full bg-gray-800 rounded-full h-2 overflow-hidden">
            <motion.div
              className="bg-gradient-to-r from-emerald-500 to-cyan-400 h-2 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${progressPercent}%` }}
              transition={{ duration: 0.8, ease: 'easeOut' }}
            />
          </div>
        </div>

        {/* Pending Tasks */}
        <div className="glass-panel p-5 rounded-xl border border-gray-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase text-gray-400">Pending Tasks</span>
            <Clock className="w-5 h-5 text-cyan-400" />
          </div>
          <div className="mt-3">
            <span className="text-3xl font-extrabold text-white">{pendingCount}</span>
            <span className="block text-xs text-gray-400 mt-1">Requires ~{plan?.required_task_hours || 0} hrs effort</span>
          </div>
        </div>

        {/* Overdue Warning */}
        <div className={`glass-panel p-5 rounded-xl border ${overdueCount > 0 ? 'border-amber-500/30 bg-amber-950/10' : 'border-gray-800'}`}>
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase text-gray-400">Overdue Items</span>
            <AlertTriangle className={`w-5 h-5 ${overdueCount > 0 ? 'text-amber-400 animate-bounce' : 'text-gray-500'}`} />
          </div>
          <div className="mt-3">
            <span className={`text-3xl font-extrabold ${overdueCount > 0 ? 'text-amber-400' : 'text-white'}`}>{overdueCount}</span>
            <span className="block text-xs text-gray-400 mt-1">
              {overdueCount > 0 ? 'High priority boost applied' : 'No overdue tasks'}
            </span>
          </div>
        </div>

        {/* Available Focus Hours */}
        <div className="glass-panel p-5 rounded-xl border border-gray-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase text-gray-400">Available Focus</span>
            <Zap className="w-5 h-5 text-violet-400" />
          </div>
          <div className="mt-3">
            <span className="text-3xl font-extrabold text-white">{plan ? plan.available_hours : 0} hrs</span>
            <span className="block text-xs text-gray-400 mt-1">Workday window (9 AM–6 PM)</span>
          </div>
        </div>

      </div>

      {/* Recommended Next Task Box */}
      {nextTask && (
        <div className="glass-panel rounded-xl p-5 border border-indigo-500/30 bg-gradient-to-r from-indigo-900/20 to-surface flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/20 text-indigo-400 flex items-center justify-center shrink-0">
              <Play className="w-5 h-5 fill-current" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider text-indigo-400">Recommended Next Task</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                  Priority Score: {nextTask.priority_score.toFixed(0)}
                </span>
              </div>
              <h3 className="text-lg font-bold text-white mt-1">{nextTask.title}</h3>
              <p className="text-xs text-gray-400 mt-0.5">{nextTask.description || 'Closest deadline with high effort fit.'}</p>
            </div>
          </div>
          <button
            onClick={() => onCompleteTask(nextTask.id)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-sm transition shadow-md shadow-emerald-600/20 shrink-0"
          >
            <CheckCircle2 className="w-4 h-4" />
            Mark Complete
          </button>
        </div>
      )}

      {/* Daily Plan Schedule & Recommendation */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Daily Schedule Timeline (2 Cols) */}
        <div className="lg:col-span-2 glass-panel rounded-2xl p-6 border border-gray-800">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <span>Today's Daily Plan</span>
                {plan?.is_overloaded && (
                  <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                    Overloaded
                  </span>
                )}
              </h2>
              <p className="text-xs text-gray-400 mt-1">
                Interval packed task windows avoiding Google Calendar meeting conflicts.
              </p>
            </div>
            <button onClick={onOpenAgent} className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1">
              Ask Agent to adjust <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Schedule List */}
          <div className="space-y-3">
            {plan?.schedule.map((slot, idx) => (
              <div
                key={idx}
                className={`p-4 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-3 transition-all ${
                  slot.item_type === 'EVENT'
                    ? 'bg-violet-950/20 border-violet-500/30 text-violet-200'
                    : 'bg-surface-card/60 border-gray-800 text-gray-200 hover:border-gray-700'
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className="text-xs font-bold font-mono px-2.5 py-1 rounded bg-gray-900 border border-gray-800 text-gray-300 shrink-0">
                    {slot.time || `${formatTimeString(slot.start_time)} – ${formatTimeString(slot.end_time)}`}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-sm text-white">{slot.title}</span>
                      {slot.item_type === 'EVENT' ? (
                        <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-violet-500/20 text-violet-300 border border-violet-500/30">
                          Calendar Meeting
                        </span>
                      ) : (
                        <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded ${
                          slot.priority === 'HIGH' ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' : 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                        }`}>
                          {slot.priority || 'Task'}
                        </span>
                      )}
                    </div>
                    {slot.reasoning && (
                      <p className="text-xs text-gray-400 mt-1 italic">{slot.reasoning}</p>
                    )}
                  </div>
                </div>
                <span className="text-xs text-gray-400 shrink-0 self-end sm:self-center font-mono">
                  {slot.duration_minutes} min
                </span>
              </div>
            ))}
          </div>

          {/* AI Recommendation Alert */}
          {plan?.recommendation && (
            <div className="mt-6 p-4 rounded-xl bg-indigo-950/30 border border-indigo-500/30 text-indigo-200 text-xs flex items-start gap-3">
              <Sparkles className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold block text-indigo-300 mb-0.5">Agent Strategy Recommendation</span>
                {plan.recommendation}
              </div>
            </div>
          )}
        </div>

        {/* Google Calendar Events Sidebar (1 Col) */}
        <div className="glass-panel rounded-2xl p-6 border border-gray-800">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <Calendar className="w-5 h-5 text-cyan-400" />
              <span>Calendar Events</span>
            </h2>
            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
              Synced
            </span>
          </div>

          <div className="space-y-4">
            {events.map((evt) => (
              <div key={evt.id} className="p-3.5 rounded-xl bg-surface-card/40 border border-gray-800/80 hover:border-gray-700 transition">
                <span className="text-xs font-bold text-cyan-400 block font-mono">
                  {formatTimeString(evt.start)} – {formatTimeString(evt.end)}
                </span>
                <h4 className="text-sm font-semibold text-white mt-1">{evt.summary}</h4>
                {evt.location && (
                  <span className="text-xs text-gray-400 block mt-1">📍 {evt.location}</span>
                )}
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
};
