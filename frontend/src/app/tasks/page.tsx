'use client';

import React, { useEffect, useState } from 'react';
import { Navbar } from '../../components/Navbar';
import { TaskManager } from '../../components/TaskManager';
import { AIChatDrawer } from '../../components/AIChatDrawer';
import { api } from '../../lib/api';
import { Task } from '../../lib/types';

export default function TasksPage() {
  const [isAgentOpen, setIsAgentOpen] = useState(false);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchTasks = async () => {
    try {
      const data = await api.getTasks();
      setTasks(data);
    } catch (err) {
      console.error("Failed to load tasks", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  const handleCreateTask = async (taskData: any) => {
    await api.createTask(taskData);
    fetchTasks();
  };

  const handleCompleteTask = async (taskId: string) => {
    await api.completeTask(taskId);
    fetchTasks();
  };

  const handleBreakdownTask = async (taskId: string) => {
    await api.breakdownTask(taskId);
    fetchTasks();
  };

  const handleDeleteTask = async (taskId: string) => {
    await api.deleteTask(taskId);
    fetchTasks();
  };

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Navbar onOpenAgent={() => setIsAgentOpen(true)} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          <TaskManager
            tasks={tasks}
            onCreateTask={handleCreateTask}
            onCompleteTask={handleCompleteTask}
            onBreakdownTask={handleBreakdownTask}
            onDeleteTask={handleDeleteTask}
          />
        )}
      </main>

      <AIChatDrawer
        isOpen={isAgentOpen}
        onClose={() => setIsAgentOpen(false)}
        onPlanUpdated={fetchTasks}
      />
    </div>
  );
}
