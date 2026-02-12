export interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  history?: Message[];
}

export interface ChatResponse {
  message: string;
  conversation_id: string;
  agent_type: string;
  intent?: string;
  sources?: string[];
  metadata?: {
    timestamp: string;
    tool_calls?: number;
    docs_retrieved?: number;
    [key: string]: unknown;
  };
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
}

export interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string;
  is_active: boolean;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
  full_name?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  email: string;
  username: string;
}
