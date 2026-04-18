import axios, { type AxiosInstance, type AxiosError } from 'axios';
import type {
  LoginRequest,
  RegisterRequest,
  AuthResponse,
  User,
} from '../types/auth';
import type { Message, Diary, DiaryListResponse } from '../types/diary';

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add JWT token
    this.client.interceptors.request.use(
      (config) => {
        const token = this.getToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor to handle 401 errors
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          this.clearToken();
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Token management
  private getToken(): string | null {
    return localStorage.getItem('access_token');
  }

  private setToken(token: string): void {
    localStorage.setItem('access_token', token);
  }

  private clearToken(): void {
    localStorage.removeItem('access_token');
  }

  // Authentication endpoints
  async login(data: LoginRequest): Promise<AuthResponse> {
    const formData = new URLSearchParams();
    formData.append('username', data.email); // OAuth2 uses 'username' field but we pass email
    formData.append('password', data.password);

    const response = await this.client.post<AuthResponse>(
      '/api/auth/token',
      formData,
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    );

    this.setToken(response.data.access_token);
    return response.data;
  }

  async register(data: RegisterRequest): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>(
      '/api/auth/register',
      data
    );
    this.setToken(response.data.access_token);
    return response.data;
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.client.get<User>('/api/auth/me');
    return response.data;
  }

  logout(): void {
    this.clearToken();
    window.location.href = '/login';
  }

  // Conversation endpoints
  // TODO: 完全な実装が必要
  // 1. 会話がない場合は POST /api/conversations で作成
  // 2. POST /api/conversations/{id}/messages でメッセージ送信
  // 3. AI返信はWebSocketまたはポーリングで取得
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  async chat(_messages: Message[]): Promise<{ response: string }> {
    // 暫定実装: エラーをスローして未実装を明示
    throw new Error(
      'Chat API is not fully implemented. Need to integrate with /api/conversations endpoints.'
    );
  }

  private conversationId: number | null = null;

  async getOrCreateConversation(characterId: number): Promise<{ id: number }> {
    // 会話が存在しない場合は作成
    if (!this.conversationId) {
      const response = await this.client.post<{ id: number }>(
        '/api/conversations',
        { character_id: characterId }
      );
      this.conversationId = response.data.id;
    }
    return { id: this.conversationId };
  }

  async sendMessage(
    conversationId: number,
    content: string
  ): Promise<{ id: number; content: string }> {
    const response = await this.client.post<{ id: number; content: string }>(
      `/api/conversations/${conversationId}/messages`,
      { content }
    );
    return response.data;
  }

  async getMessages(conversationId: number): Promise<Message[]> {
    const response = await this.client.get<{ messages: Message[] }>(
      `/api/conversations/${conversationId}/messages`
    );
    return response.data.messages;
  }

  // Diary endpoints
  async getDiaries(limit = 10, offset = 0): Promise<DiaryListResponse> {
    const response = await this.client.get<DiaryListResponse>('/api/diaries', {
      params: { limit, offset },
    });
    return response.data;
  }

  async getDiary(id: number): Promise<Diary> {
    const response = await this.client.get<Diary>(`/api/diaries/${id}`);
    return response.data;
  }

  async createDiary(date: string, content: string): Promise<Diary> {
    const response = await this.client.post<Diary>('/api/diaries', {
      date,
      content,
    });
    return response.data;
  }

  async updateDiary(id: number, content: string): Promise<Diary> {
    const response = await this.client.put<Diary>(`/api/diaries/${id}`, {
      content,
    });
    return response.data;
  }

  async deleteDiary(id: number): Promise<void> {
    await this.client.delete(`/api/diaries/${id}`);
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }
}

export const apiClient = new ApiClient();
