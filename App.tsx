/**
 * Multi-Framework Super-Agent Platform
 * React Web Frontend with Role-Based Access Control
 */

import React, { useState, useEffect, useCallback } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import axios, { AxiosInstance } from 'axios';

// ============================================================================
// Type Definitions
// ============================================================================

export enum UserRole {
  ADMIN = 'admin',
  ANALYST = 'analyst',
  USER = 'user',
  SERVICE_ACCOUNT = 'service_account',
}

export enum TaskPriority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  URGENT = 'urgent',
}

export enum ExecutionEngine {
  DIRECT_LLM = 'direct_llm',
  CREWAI = 'crewai',
  AUTOGEN = 'autogen',
}

export interface User {
  id: string;
  username: string;
  email: string;
  role: UserRole;
  isActive: boolean;
  createdAt: Date;
  lastLogin?: Date;
}

export interface ExecutionRequest {
  taskDescription: string;
  priority: TaskPriority;
  context?: Record<string, any>;
  maxTokens?: number;
  temperature?: number;
}

export interface ExecutionResponse {
  executionId: string;
  status: string;
  result?: string;
  executionTime: number;
  engine: ExecutionEngine;
  tokensUsed: number;
  costUsd: number;
  timestamp: Date;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

// ============================================================================
// API Client Setup
// ============================================================================

class ApiClient {
  private client: AxiosInstance;
  private token: string | null = null;

  constructor(baseURL: string = 'http://localhost:8000') {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add token to requests
    this.client.interceptors.request.use((config) => {
      if (this.token) {
        config.headers.Authorization = `Bearer ${this.token}`;
      }
      return config;
    });

    // Handle responses
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Token expired or invalid
          this.token = null;
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  setToken(token: string) {
    this.token = token;
    localStorage.setItem('token', token);
  }

  getToken(): string | null {
    return this.token || localStorage.getItem('token');
  }

  async login(username: string, password: string): Promise<{ accessToken: string; user: User }> {
    const response = await this.client.post('/auth/login', { username, password });
    this.setToken(response.data.access_token);
    return { accessToken: response.data.access_token, user: response.data.user };
  }

  async logout(): Promise<void> {
    this.token = null;
    localStorage.removeItem('token');
  }

  async refreshToken(): Promise<string> {
    const response = await this.client.post('/auth/refresh');
    this.setToken(response.data.access_token);
    return response.data.access_token;
  }

  async executeAgent(request: ExecutionRequest): Promise<ExecutionResponse> {
    const response = await this.client.post('/api/v1/execute', request);
    return response.data;
  }

  async getExecutionHistory(limit: number = 50, offset: number = 0): Promise<ExecutionResponse[]> {
    const response = await this.client.get('/api/v1/executions', {
      params: { limit, offset },
    });
    return response.data;
  }

  async getMetrics(): Promise<any> {
    const response = await this.client.get('/metrics');
    return response.data;
  }

  async getSystemStatus(): Promise<any> {
    const response = await this.client.get('/health/detailed');
    return response.data;
  }
}

const apiClient = new ApiClient();

// ============================================================================
// Redux Store Setup
// ============================================================================

interface RootState {
  auth: AuthState;
  executions: {
    items: ExecutionResponse[];
    currentExecution: ExecutionResponse | null;
    isLoading: boolean;
    error: string | null;
  };
  ui: {
    theme: 'light' | 'dark';
    sidebarOpen: boolean;
    notifications: Array<{ id: string; message: string; type: 'info' | 'error' | 'success' }>;
  };
}

const initialState: RootState = {
  auth: {
    user: null,
    token: localStorage.getItem('token') || null,
    isAuthenticated: !!localStorage.getItem('token'),
    isLoading: false,
    error: null,
  },
  executions: {
    items: [],
    currentExecution: null,
    isLoading: false,
    error: null,
  },
  ui: {
    theme: (localStorage.getItem('theme') as 'light' | 'dark') || 'light',
    sidebarOpen: true,
    notifications: [],
  },
};

// Actions
const authSlice = {
  login: (user: User, token: string) => ({
    type: 'auth/login',
    payload: { user, token },
  }),
  logout: () => ({
    type: 'auth/logout',
  }),
  setError: (error: string) => ({
    type: 'auth/setError',
    payload: error,
  }),
};

const executionsSlice = {
  setExecutions: (items: ExecutionResponse[]) => ({
    type: 'executions/setExecutions',
    payload: items,
  }),
  addExecution: (execution: ExecutionResponse) => ({
    type: 'executions/addExecution',
    payload: execution,
  }),
  setCurrentExecution: (execution: ExecutionResponse | null) => ({
    type: 'executions/setCurrentExecution',
    payload: execution,
  }),
  setLoading: (isLoading: boolean) => ({
    type: 'executions/setLoading',
    payload: isLoading,
  }),
};

// ============================================================================
// Authentication Components
// ============================================================================

const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const dispatch = useDispatch();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const { accessToken, user } = await apiClient.login(username, password);
      dispatch(authSlice.login(user, accessToken));
      window.location.href = '/dashboard';
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 to-blue-900 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Super-Agent Platform</h1>
        <p className="text-gray-600 mb-6">Multi-Framework AI Agent Orchestration</p>

        <form onSubmit={handleLogin} className="space-y-4">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Enter your username"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Enter your password"
              required
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-2 rounded-lg transition duration-200"
          >
            {isLoading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <div className="mt-6 flex items-center">
          <div className="flex-1 border-t border-gray-300"></div>
          <span className="px-3 text-sm text-gray-500">or continue with</span>
          <div className="flex-1 border-t border-gray-300"></div>
        </div>

        <button className="w-full mt-4 bg-gray-100 hover:bg-gray-200 text-gray-800 font-semibold py-2 rounded-lg transition duration-200">
          Sign in with OAuth 2.0
        </button>
      </div>
    </div>
  );
};

// ============================================================================
// Protected Route Component
// ============================================================================

interface ProtectedRouteProps {
  requiredRole?: UserRole;
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ requiredRole, children }) => {
  const { user, isAuthenticated } = useSelector((state: RootState) => state.auth);

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />;
  }

  if (requiredRole) {
    const roleHierarchy = {
      [UserRole.ADMIN]: 4,
      [UserRole.ANALYST]: 3,
      [UserRole.USER]: 2,
      [UserRole.SERVICE_ACCOUNT]: 1,
    };

    if (roleHierarchy[user.role] < roleHierarchy[requiredRole]) {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <h1 className="text-3xl font-bold text-gray-900 mb-4">Access Denied</h1>
            <p className="text-gray-600">You don't have permission to access this resource.</p>
          </div>
        </div>
      );
    }
  }

  return <>{children}</>;
};

// ============================================================================
// Dashboard Components
// ============================================================================

const ExecutionForm: React.FC = () => {
  const [taskDescription, setTaskDescription] = useState('');
  const [priority, setPriority] = useState<TaskPriority>(TaskPriority.MEDIUM);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<ExecutionResponse | null>(null);
  const dispatch = useDispatch();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const response = await apiClient.executeAgent({
        taskDescription,
        priority,
      });

      setResult(response);
      dispatch(executionsSlice.addExecution(response));
      setTaskDescription('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Execution failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-4">Execute Agent</h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Task Description</label>
          <textarea
            value={taskDescription}
            onChange={(e) => setTaskDescription(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Describe your task (minimum 10 characters)"
            minLength={10}
            maxLength={5000}
            rows={6}
            required
          />
          <p className="mt-1 text-sm text-gray-500">
            {taskDescription.length}/5000 characters
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Priority</label>
          <select
            value={priority}
            onChange={(e) => setPriority(e.target.value as TaskPriority)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {Object.values(TaskPriority).map((p) => (
              <option key={p} value={p}>
                {p.charAt(0).toUpperCase() + p.slice(1)}
              </option>
            ))}
          </select>
        </div>

        <button
          type="submit"
          disabled={isLoading || taskDescription.length < 10}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-2 rounded-lg transition duration-200"
        >
          {isLoading ? 'Executing...' : 'Execute'}
        </button>
      </form>

      {result && (
        <div className="mt-6 bg-gray-50 border border-gray-200 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Result</h3>
          <div className="space-y-2 text-sm">
            <p>
              <strong>Execution ID:</strong> {result.executionId}
            </p>
            <p>
              <strong>Engine:</strong> {result.engine}
            </p>
            <p>
              <strong>Duration:</strong> {result.executionTime.toFixed(2)}s
            </p>
            <p>
              <strong>Tokens:</strong> {result.tokensUsed}
            </p>
            <p>
              <strong>Cost:</strong> ${result.costUsd.toFixed(4)}
            </p>
            <p className="mt-2">
              <strong>Result:</strong>
            </p>
            <p className="bg-white p-3 rounded border border-gray-300 mt-1">{result.result}</p>
          </div>
        </div>
      )}
    </div>
  );
};

const Dashboard: React.FC = () => {
  const { user } = useSelector((state: RootState) => state.auth);
  const { items: executions } = useSelector((state: RootState) => state.executions);
  const [systemStatus, setSystemStatus] = useState<any>(null);

  useEffect(() => {
    // Load system status
    apiClient.getSystemStatus().then(setSystemStatus).catch(console.error);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-md">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">Super-Agent Platform</h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">
              {user?.username} ({user?.role})
            </span>
            <button
              onClick={() => apiClient.logout()}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition duration-200"
            >
              Logout
            </button>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          {systemStatus && (
            <>
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-sm font-medium text-gray-600">System Status</h3>
                <p className={`text-2xl font-bold mt-2 ${
                  systemStatus.status === 'healthy' ? 'text-green-600' : 'text-yellow-600'
                }`}>
                  {systemStatus.status}
                </p>
              </div>
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-sm font-medium text-gray-600">Database</h3>
                <p className={`text-lg font-bold mt-2 ${
                  systemStatus.dependencies.database === 'healthy'
                    ? 'text-green-600'
                    : 'text-red-600'
                }`}>
                  {systemStatus.dependencies.database}
                </p>
              </div>
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-sm font-medium text-gray-600">Cache</h3>
                <p className={`text-lg font-bold mt-2 ${
                  systemStatus.dependencies.cache === 'healthy' ? 'text-green-600' : 'text-red-600'
                }`}>
                  {systemStatus.dependencies.cache}
                </p>
              </div>
            </>
          )}
        </div>

        <ExecutionForm />

        {user?.role === UserRole.ADMIN && (
          <div className="mt-8 bg-white rounded-lg shadow-md p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Execution History (Admin)</h2>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-100">
                  <tr>
                    <th className="px-6 py-3 text-left text-sm font-medium text-gray-900">
                      Execution ID
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-medium text-gray-900">Engine</th>
                    <th className="px-6 py-3 text-left text-sm font-medium text-gray-900">
                      Duration (s)
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-medium text-gray-900">Cost</th>
                  </tr>
                </thead>
                <tbody>
                  {executions.slice(0, 10).map((exec) => (
                    <tr key={exec.executionId} className="border-t border-gray-200">
                      <td className="px-6 py-4 text-sm text-gray-900">{exec.executionId}</td>
                      <td className="px-6 py-4 text-sm text-gray-900">{exec.engine}</td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        {exec.executionTime.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">${exec.costUsd.toFixed(4)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// ============================================================================
// Main App Component
// ============================================================================

const App: React.FC = () => {
  const isAuthenticated = useSelector((state: RootState) => state.auth.isAuthenticated);

  return (
    <Router>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Router>
  );
};

export default App;
