export type TaskPriority = 'HIGH' | 'MEDIUM' | 'LOW';
export type TaskStatus = 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';

export interface Subtask {
  id: string;
  task_id: string;
  title: string;
  status: 'PENDING' | 'COMPLETED';
  created_at: string;
  completed_at?: string;
}

export interface Task {
  id: string;
  user_id: string;
  title: string;
  description?: string;
  status: TaskStatus;
  priority: TaskPriority;
  priority_score: number;
  due_date?: string;
  estimated_minutes: number;
  category: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  subtasks: Subtask[];
}

export interface CalendarEvent {
  id: string;
  summary: string;
  description?: string;
  start: string;
  end: string;
  location?: string;
  is_all_day: boolean;
}

export interface CalendarEventCreate {
  summary: string;
  description?: string;
  start: string;
  end: string;
  location?: string;
}

export interface ScheduledSlot {
  item_type: 'TASK' | 'EVENT' | 'BREAK';
  id: string;
  title: string;
  start_time: string;
  end_time: string;
  duration_minutes: number;
  priority?: TaskPriority;
  reasoning?: string;
  time?: string;
}

export interface DailyPlanResponse {
  date: string;
  available_hours: number;
  required_task_hours: number;
  is_overloaded: boolean;
  tasks_count: number;
  overdue_count: number;
  schedule: ScheduledSlot[];
  recommendation: string;
  unscheduled_tasks: Task[];
}

export interface ToolCallTrace {
  tool_name: string;
  arguments: Record<string, any>;
  output: any;
}

export interface AgentChatResponse {
  response: string;
  tool_calls: ToolCallTrace[];
  conversation_id: string;
}
