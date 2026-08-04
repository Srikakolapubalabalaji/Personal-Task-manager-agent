'use client';

import React, { useEffect, useState } from 'react';
import { Navbar } from '../components/Navbar';
import { DashboardOverview } from '../components/DashboardOverview';
import { AIChatDrawer } from '../components/AIChatDrawer';
import { ProtectedRoute } from '../components/ProtectedRoute';
import { api } from '../lib/api';
import { Task, DailyPlanResponse, CalendarEvent } from '../lib/types';

export default function DashboardPage() {
  const [isAgentOpen, setIsAgentOpen] = useState(false);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [plan, setPlan] = useState<DailyPlanResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [tList, eList, pRes] = await Promise.all([
        api.getTasks(),
        api.getEvents(),
        api.getDailyPlan(),
      ]);
      setTasks(tList);
      setEvents(eList);
      setPlan(pRes);
    } catch (err) {
      console.error("Failed to load dashboard data", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCompleteTask = async (taskId: string) => {
    await api.completeTask(taskId);
    fetchData();
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen flex flex-col bg-background">
        <Navbar onOpenAgent={() => setIsAgentOpen(true)} />

        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : (
            <DashboardOverview
              plan={plan}
              tasks={tasks}
              events={events}
              onOpenAgent={() => setIsAgentOpen(true)}
              onCompleteTask={handleCompleteTask}
            />
          )}
        </main>

        <AIChatDrawer
          isOpen={isAgentOpen}
          onClose={() => setIsAgentOpen(false)}
          onPlanUpdated={fetchData}
        />
      </div>
    </ProtectedRoute>
  );
}
