'use client';

import React, { useEffect, useState } from 'react';
import { Navbar } from '../../components/Navbar';
import { AIChatDrawer } from '../../components/AIChatDrawer';
import { ProtectedRoute } from '../../components/ProtectedRoute';
import { api } from '../../lib/api';
import { CalendarEvent } from '../../lib/types';
import { Calendar, CheckCircle2, Link2, ShieldCheck, Clock, MapPin, Plus, X, Trash2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function CalendarPage() {
  const [isAgentOpen, setIsAgentOpen] = useState(false);
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [loading, setLoading] = useState(true);

  // Create Event Modal State
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [summary, setSummary] = useState('');
  const [eventDate, setEventDate] = useState(new Date().toISOString().split('T')[0]);
  const [startTime, setStartTime] = useState('17:00');
  const [endTime, setEndTime] = useState('18:00');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const fetchCalendarData = async () => {
    try {
      const [evts, statusRes] = await Promise.all([
        api.getEvents(),
        api.getCalendarStatus(),
      ]);
      setEvents(evts);
      setIsConnected(statusRes.connected);
    } catch (err) {
      console.error("Failed to load calendar data", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCalendarData();
  }, []);

  const handleConnectGoogle = async () => {
    try {
      const authUrl = await api.getGoogleAuthUrl();
      window.location.href = authUrl;
    } catch {
      await api.connectMockCalendar();
      setIsConnected(true);
      fetchCalendarData();
    }
  };

  const handleCreateEvent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!summary.trim() || isSubmitting) return;

    setIsSubmitting(true);
    try {
      const startDateTime = `${eventDate}T${startTime}:00`;
      const endDateTime = `${eventDate}T${endTime}:00`;

      await api.createEvent({
        summary: summary.trim(),
        description: description.trim() || undefined,
        start: startDateTime,
        end: endDateTime,
      });

      setSummary('');
      setDescription('');
      setIsCreateModalOpen(false);
      await fetchCalendarData();
    } catch (err) {
      console.error("Failed to create calendar event", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteEvent = async (eventId: string, eventTitle: string) => {
    if (!window.confirm(`Delete "${eventTitle}" from your Google Calendar?\n\nThis action cannot be undone.`)) return;
    setDeletingId(eventId);
    try {
      await api.deleteEvent(eventId);
      await fetchCalendarData();
    } catch (err) {
      console.error('Failed to delete event', err);
    } finally {
      setDeletingId(null);
    }
  };

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

  return (
    <ProtectedRoute>
      <div className="min-h-screen flex flex-col bg-background">
        <Navbar onOpenAgent={() => setIsAgentOpen(true)} />

        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
          
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">Google Calendar Integration</h1>
              <p className="text-xs text-gray-400 mt-1">
                Synchronize your schedule, identify free focus time windows, and prevent agent scheduling conflicts.
              </p>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setIsCreateModalOpen(true)}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm shadow-md transition hover:scale-105"
              >
                <Plus className="w-4 h-4" />
                <span>Create Event</span>
              </button>

              {isConnected ? (
                <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-sm font-semibold">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span>Google Account Connected</span>
                </div>
              ) : (
                <button
                  onClick={handleConnectGoogle}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white font-semibold text-sm shadow-md transition hover:scale-105"
                >
                  <Link2 className="w-4 h-4" />
                  <span>Connect Google Calendar</span>
                </button>
              )}
            </div>
          </div>

          {/* OAuth Security Card */}
          <div className="glass-panel p-6 rounded-2xl border border-gray-800 bg-surface-card/40 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 flex items-center justify-center shrink-0">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">OAuth 2.0 Security & Token Storage</h3>
                <p className="text-xs text-gray-400 mt-1 max-w-2xl">
                  The agent requests access to calendar events (`calendar.readonly` & `calendar.events`) to compute free focus time windows. Tokens are stored encrypted in the database.
                </p>
              </div>
            </div>
            <div className="text-right shrink-0">
              <span className="text-xs font-mono text-gray-400 block">Scope: Google Calendar API</span>
              <span className={`text-xs font-mono font-bold block mt-0.5 ${isConnected ? 'text-emerald-400' : 'text-amber-400'}`}>
                Status: {isConnected ? 'Authorized & Synced' : 'Connected'}
              </span>
            </div>
          </div>

          {/* Calendar Events Grid */}
          <div className="glass-panel rounded-2xl p-6 border border-gray-800 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Calendar className="w-5 h-5 text-cyan-400" />
                <span>Upcoming Synced Events</span>
              </h2>
              <span className="text-xs text-gray-400">{events.length} events loaded</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {events.map((evt) => (
                <div key={evt.id} className="p-4 rounded-xl bg-surface-card/60 border border-gray-800/80 space-y-2 hover:border-gray-700 transition group">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono font-bold text-cyan-400 flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5" />
                      {formatTimeString(evt.start)} – {formatTimeString(evt.end)}
                    </span>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-violet-500/20 text-violet-300 border border-violet-500/30">
                        Google Calendar
                      </span>
                      <button
                        onClick={() => handleDeleteEvent(evt.id, evt.summary)}
                        disabled={deletingId === evt.id}
                        title="Delete event"
                        className="opacity-0 group-hover:opacity-100 p-1 rounded-lg text-gray-500 hover:text-red-400 hover:bg-red-500/10 transition disabled:opacity-40"
                      >
                        {deletingId === evt.id
                          ? <span className="text-[10px] text-gray-400">Deleting…</span>
                          : <Trash2 className="w-3.5 h-3.5" />}
                      </button>
                    </div>
                  </div>
                  <h3 className="text-base font-bold text-white">{evt.summary}</h3>
                  {evt.description && <p className="text-xs text-gray-400">{evt.description}</p>}
                  {evt.location && (
                    <span className="text-xs text-gray-400 flex items-center gap-1 mt-1">
                      <MapPin className="w-3.5 h-3.5 text-gray-500" />
                      {evt.location}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>

        </main>

        {/* Create Event Modal */}
        <AnimatePresence>
          {isCreateModalOpen && (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={() => setIsCreateModalOpen(false)}
                className="fixed inset-0 bg-black/60 backdrop-blur-xs"
              />
              <motion.div
                initial={{ scale: 0.95, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.95, opacity: 0 }}
                className="relative w-full max-w-lg glass-panel rounded-2xl p-6 border border-gray-800 bg-surface shadow-2xl z-10 space-y-5"
              >
                <div className="flex items-center justify-between border-b border-gray-800 pb-4">
                  <div className="flex items-center gap-2">
                    <Calendar className="w-5 h-5 text-indigo-400" />
                    <h3 className="text-lg font-bold text-white">Create Google Calendar Event</h3>
                  </div>
                  <button
                    onClick={() => setIsCreateModalOpen(false)}
                    className="p-1 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 transition"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                <form onSubmit={handleCreateEvent} className="space-y-4">
                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-gray-400 mb-1">
                      Event Title *
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Project Review Meeting"
                      value={summary}
                      onChange={(e) => setSummary(e.target.value)}
                      className="w-full px-3.5 py-2.5 bg-surface-card border border-gray-800 rounded-xl text-sm text-white focus:outline-none focus:border-indigo-500"
                    />
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div>
                      <label className="block text-xs font-semibold uppercase tracking-wider text-gray-400 mb-1">
                        Date *
                      </label>
                      <input
                        type="date"
                        required
                        value={eventDate}
                        onChange={(e) => setEventDate(e.target.value)}
                        className="w-full px-3 py-2 bg-surface-card border border-gray-800 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold uppercase tracking-wider text-gray-400 mb-1">
                        Start Time *
                      </label>
                      <input
                        type="time"
                        required
                        value={startTime}
                        onChange={(e) => setStartTime(e.target.value)}
                        className="w-full px-3 py-2 bg-surface-card border border-gray-800 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold uppercase tracking-wider text-gray-400 mb-1">
                        End Time *
                      </label>
                      <input
                        type="time"
                        required
                        value={endTime}
                        onChange={(e) => setEndTime(e.target.value)}
                        className="w-full px-3 py-2 bg-surface-card border border-gray-800 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-gray-400 mb-1">
                      Description (Optional)
                    </label>
                    <textarea
                      rows={3}
                      placeholder="Sprint review meeting with key stakeholders..."
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      className="w-full px-3.5 py-2.5 bg-surface-card border border-gray-800 rounded-xl text-sm text-white focus:outline-none focus:border-indigo-500"
                    />
                  </div>

                  <div className="flex items-center justify-end gap-3 pt-2">
                    <button
                      type="button"
                      onClick={() => setIsCreateModalOpen(false)}
                      className="px-4 py-2 rounded-xl text-sm font-semibold text-gray-400 hover:text-white transition"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={isSubmitting || !summary.trim()}
                      className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold text-sm shadow-md transition"
                    >
                      {isSubmitting ? 'Creating...' : 'Sync to Calendar'}
                    </button>
                  </div>
                </form>
              </motion.div>
            </div>
          )}
        </AnimatePresence>

        <AIChatDrawer
          isOpen={isAgentOpen}
          onClose={() => setIsAgentOpen(false)}
          onPlanUpdated={fetchCalendarData}
        />
      </div>
    </ProtectedRoute>
  );
}
