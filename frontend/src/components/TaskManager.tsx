'use client';

import React, { useState } from 'react';
import { Task, TaskPriority, TaskStatus } from '../lib/types';
import { 
  Plus, CheckCircle2, Trash2, Sparkles, Calendar, Clock, Tag, ChevronDown, ChevronRight, Search, ListTree 
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface TaskManagerProps {
  tasks: Task[];
  onCreateTask: (data: any) => void;
  onCompleteTask: (id: string) => void;
  onBreakdownTask: (id: string) => void;
  onDeleteTask: (id: string) => void;
}

export const TaskManager: React.FC<TaskManagerProps> = ({
  tasks,
  onCreateTask,
  onCompleteTask,
  onBreakdownTask,
  onDeleteTask,
}) => {
  const [filter, setFilter] = useState<'ALL' | 'PENDING' | 'HIGH' | 'COMPLETED'>('ALL');
  const [search, setSearch] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [expandedTaskId, setExpandedTaskId] = useState<string | null>(null);

  // Modal Form state
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState<TaskPriority>('MEDIUM');
  const [dueDate, setDueDate] = useState('');
  const [estimatedMinutes, setEstimatedMinutes] = useState(60);
  const [category, setCategory] = useState('General');

  const filteredTasks = tasks.filter((t) => {
    const matchesSearch = t.title.toLowerCase().includes(search.toLowerCase()) || 
                          (t.description && t.description.toLowerCase().includes(search.toLowerCase()));
    if (!matchesSearch) return false;

    if (filter === 'PENDING') return t.status === 'PENDING';
    if (filter === 'HIGH') return t.priority === 'HIGH';
    if (filter === 'COMPLETED') return t.status === 'COMPLETED';
    return true;
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    onCreateTask({
      title,
      description,
      priority,
      due_date: dueDate ? new Date(dueDate).toISOString() : undefined,
      estimated_minutes: Number(estimatedMinutes),
      category,
    });
    setTitle('');
    setDescription('');
    setIsModalOpen(false);
  };

  return (
    <div className="space-y-6">
      
      {/* Header & Action Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Task Management Hub</h1>
          <p className="text-xs text-gray-400 mt-1">Organize, estimate effort, and let AI decompose complex workflows.</p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm shadow-lg shadow-indigo-600/30 transition hover:scale-105 active:scale-95"
        >
          <Plus className="w-4 h-4" />
          <span>New Task</span>
        </button>
      </div>

      {/* Filter & Search Bar */}
      <div className="glass-panel p-4 rounded-xl border border-gray-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        
        {/* Search Input */}
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-gray-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search tasks by title or keyword..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-surface-card/60 border border-gray-800 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
          />
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto">
          {(['ALL', 'PENDING', 'HIGH', 'COMPLETED'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wider transition ${
                filter === f
                  ? 'bg-indigo-600 text-white'
                  : 'bg-surface-card/40 text-gray-400 hover:text-white hover:bg-gray-800'
              }`}
            >
              {f}
            </button>
          ))}
        </div>

      </div>

      {/* Task List */}
      <div className="space-y-3">
        {filteredTasks.length === 0 ? (
          <div className="glass-panel p-12 text-center rounded-2xl border border-gray-800">
            <ListTree className="w-12 h-12 text-gray-600 mx-auto mb-3" />
            <h3 className="text-lg font-bold text-white">No tasks found</h3>
            <p className="text-xs text-gray-400 mt-1">Create a new task or adjust your search filters.</p>
          </div>
        ) : (
          filteredTasks.map((task) => {
            const isExpanded = expandedTaskId === task.id;
            return (
              <div
                key={task.id}
                className="glass-panel rounded-xl p-4 border border-gray-800/80 hover:border-gray-700 transition"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-3">
                    <button
                      onClick={() => onCompleteTask(task.id)}
                      className={`mt-1 w-5 h-5 rounded-md border flex items-center justify-center transition ${
                        task.status === 'COMPLETED'
                          ? 'bg-emerald-500 border-emerald-500 text-white'
                          : 'border-gray-600 hover:border-indigo-400'
                      }`}
                    >
                      {task.status === 'COMPLETED' && <CheckCircle2 className="w-4 h-4" />}
                    </button>
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className={`text-base font-bold ${task.status === 'COMPLETED' ? 'line-through text-gray-500' : 'text-white'}`}>
                          {task.title}
                        </span>
                        {/* Priority Badge */}
                        <span className={`text-[10px] uppercase font-extrabold px-2 py-0.5 rounded ${
                          task.priority === 'HIGH'
                            ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                            : task.priority === 'MEDIUM'
                            ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                            : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                        }`}>
                          {task.priority}
                        </span>
                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                          Score: {task.priority_score.toFixed(0)}
                        </span>
                      </div>

                      {task.description && (
                        <p className="text-xs text-gray-400 mt-1">{task.description}</p>
                      )}

                      {/* Task Metadata */}
                      <div className="flex items-center gap-4 mt-2 text-xs text-gray-400 flex-wrap">
                        {task.due_date && (
                          <span className="flex items-center gap-1">
                            <Calendar className="w-3.5 h-3.5 text-cyan-400" />
                            {new Date(task.due_date).toLocaleDateString()}
                          </span>
                        )}
                        <span className="flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5 text-indigo-400" />
                          {task.estimated_minutes} min
                        </span>
                        <span className="flex items-center gap-1">
                          <Tag className="w-3.5 h-3.5 text-violet-400" />
                          {task.category}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Right Actions */}
                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      onClick={() => onBreakdownTask(task.id)}
                      title="Decompose task into AI subtasks"
                      className="px-2.5 py-1.5 rounded-lg bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-xs font-semibold flex items-center gap-1 transition"
                    >
                      <Sparkles className="w-3.5 h-3.5 text-cyan-300" />
                      <span>AI Breakdown</span>
                    </button>
                    {task.subtasks.length > 0 && (
                      <button
                        onClick={() => setExpandedTaskId(isExpanded ? null : task.id)}
                        className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 transition"
                      >
                        {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                      </button>
                    )}
                    <button
                      onClick={() => onDeleteTask(task.id)}
                      className="p-1.5 rounded-lg text-gray-500 hover:text-rose-400 hover:bg-rose-950/20 transition"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Subtask Drawer */}
                <AnimatePresence>
                  {isExpanded && task.subtasks.length > 0 && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="mt-4 pt-3 border-t border-gray-800 pl-8 space-y-2"
                    >
                      <span className="text-[10px] font-bold uppercase text-gray-500 tracking-wider">Subtasks Breakdown</span>
                      {task.subtasks.map((st) => (
                        <div key={st.id} className="flex items-center gap-2 text-xs text-gray-300">
                          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                          <span className={st.status === 'COMPLETED' ? 'line-through text-gray-500' : ''}>{st.title}</span>
                        </div>
                      ))}
                    </motion.div>
                  )}
                </AnimatePresence>

              </div>
            );
          })
        )}
      </div>

      {/* New Task Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="glass-panel w-full max-w-lg rounded-2xl p-6 border border-gray-800 bg-surface space-y-4"
          >
            <h2 className="text-xl font-bold text-white">Create New Task</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase text-gray-400 mb-1">Title *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Prepare PostgreSQL interview questions"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-3 py-2 bg-surface-card border border-gray-800 rounded-lg text-sm text-white focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase text-gray-400 mb-1">Description</label>
                <textarea
                  rows={2}
                  placeholder="Additional context or links..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full px-3 py-2 bg-surface-card border border-gray-800 rounded-lg text-sm text-white focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold uppercase text-gray-400 mb-1">Priority</label>
                  <select
                    value={priority}
                    onChange={(e) => setPriority(e.target.value as TaskPriority)}
                    className="w-full px-3 py-2 bg-surface-card border border-gray-800 rounded-lg text-sm text-white focus:border-indigo-500 focus:outline-none"
                  >
                    <option value="HIGH">High Priority</option>
                    <option value="MEDIUM">Medium Priority</option>
                    <option value="LOW">Low Priority</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase text-gray-400 mb-1">Estimated Duration (Mins)</label>
                  <input
                    type="number"
                    min={15}
                    step={15}
                    value={estimatedMinutes}
                    onChange={(e) => setEstimatedMinutes(Number(e.target.value))}
                    className="w-full px-3 py-2 bg-surface-card border border-gray-800 rounded-lg text-sm text-white focus:border-indigo-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold uppercase text-gray-400 mb-1">Due Date</label>
                  <input
                    type="datetime-local"
                    value={dueDate}
                    onChange={(e) => setDueDate(e.target.value)}
                    className="w-full px-3 py-2 bg-surface-card border border-gray-800 rounded-lg text-sm text-white focus:border-indigo-500 focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase text-gray-400 mb-1">Category</label>
                  <input
                    type="text"
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full px-3 py-2 bg-surface-card border border-gray-800 rounded-lg text-sm text-white focus:border-indigo-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-800">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-lg text-sm font-medium text-gray-400 hover:text-white transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm shadow-md shadow-indigo-600/30 transition"
                >
                  Save Task
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}

    </div>
  );
};
