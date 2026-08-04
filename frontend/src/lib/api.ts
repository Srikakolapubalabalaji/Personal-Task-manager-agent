import axios from 'axios';
import { Task, DailyPlanResponse, CalendarEvent, CalendarEventCreate, AgentChatResponse } from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

const client = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Auto-attach JWT token if present in localStorage
client.interceptors.request.use(async (config) => {
  if (typeof window !== 'undefined') {
    let token = localStorage.getItem('token');
    if (!token && !config.url?.includes('/auth/')) {
      // Auto register/login demo user to guarantee seamless backend database connectivity
      try {
        const authRes = await axios.post(`${API_BASE}/auth/register`, {
          email: 'demo@taskagent.ai',
          password: 'Password123!',
          full_name: 'Demo User'
        });
        token = authRes.data.access_token;
        localStorage.setItem('token', token);
      } catch {
        try {
          const authRes = await axios.post(`${API_BASE}/auth/login`, {
            email: 'demo@taskagent.ai',
            password: 'Password123!'
          });
          token = authRes.data.access_token;
          localStorage.setItem('token', token);
        } catch (e) {
          console.error("Auto-auth failed", e);
        }
      }
    }
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

export const api = {
  // Auth
  async login(email: string, password: string) {
    const res = await client.post('/auth/login', { email, password });
    if (res.data.access_token && typeof window !== 'undefined') {
      localStorage.setItem('token', res.data.access_token);
    }
    return res.data;
  },

  async register(email: string, password: string, full_name: string) {
    const res = await client.post('/auth/register', { email, password, full_name });
    if (res.data.access_token && typeof window !== 'undefined') {
      localStorage.setItem('token', res.data.access_token);
    }
    return res.data;
  },

  // Tasks
  async getTasks(): Promise<Task[]> {
    const res = await client.get('/tasks');
    return res.data;
  },

  async createTask(data: { title: string; description?: string; priority: string; due_date?: string; estimated_minutes: number; category: string }): Promise<Task> {
    const res = await client.post('/tasks', data);
    return res.data;
  },

  async completeTask(taskId: string): Promise<Task> {
    const res = await client.post(`/tasks/${taskId}/complete`);
    return res.data;
  },

  async breakdownTask(taskId: string): Promise<Task> {
    const res = await client.post(`/tasks/${taskId}/breakdown`);
    return res.data;
  },

  async deleteTask(taskId: string): Promise<void> {
    await client.delete(`/tasks/${taskId}`);
  },

  // Calendar
  async getEvents(): Promise<CalendarEvent[]> {
    const res = await client.get('/calendar/events');
    return res.data;
  },

  async createEvent(data: CalendarEventCreate): Promise<CalendarEvent> {
    const res = await client.post('/calendar/events', data);
    return res.data;
  },

  async deleteEvent(eventId: string): Promise<void> {
    await client.delete(`/calendar/events/${eventId}`);
  },

  async getCalendarStatus() {
    const res = await client.get('/calendar/status');
    return res.data;
  },

  async getGoogleAuthUrl(): Promise<string> {
    const res = await client.get('/calendar/auth-url');
    return res.data.auth_url;
  },

  async connectMockCalendar() {
    const res = await client.post('/calendar/connect-mock');
    return res.data;
  },

  // Planner
  async getDailyPlan(): Promise<DailyPlanResponse> {
    const res = await client.get('/planner/today');
    return res.data;
  },

  // Agent Chat
  async sendAgentChat(message: string): Promise<AgentChatResponse> {
    const res = await client.post('/agent/chat', { message });
    return res.data;
  }
};
