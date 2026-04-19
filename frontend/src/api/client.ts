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
    const response = await this.client.post<AuthResponse>('/api/auth/token', {
      email: data.email,
      password: data.password,
    });

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

  async getOrCreateConversation(characterId: number): Promise<{ id: number }> {
    // localStorageから会話IDを取得
    const storedConversationId = localStorage.getItem(
      `conversation_${characterId}`
    );

    if (storedConversationId) {
      // 既存の会話IDがある場合は、それが有効か確認
      try {
        await this.client.get(
          `/api/conversations/${storedConversationId}/messages`
        );
        return { id: parseInt(storedConversationId, 10) };
      } catch (error) {
        // 会話が見つからない場合は、localStorageから削除
        localStorage.removeItem(`conversation_${characterId}`);
      }
    }

    // 会話が存在しない場合は新規作成
    const response = await this.client.post<{ id: number }>(
      '/api/conversations',
      { character_id: characterId }
    );

    // localStorageに保存
    localStorage.setItem(
      `conversation_${characterId}`,
      response.data.id.toString()
    );

    return { id: response.data.id };
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
    interface BackendMessage {
      id: number;
      conversation_id: number;
      content: string;
      sender_type: 'user' | 'character';
      sender_id: number;
      sent_at: string;
    }

    const response = await this.client.get<{ messages: BackendMessage[] }>(
      `/api/conversations/${conversationId}/messages`
    );

    // Convert backend format to frontend format
    return response.data.messages.map((msg) => ({
      role:
        msg.sender_type === 'user' ? ('user' as const) : ('assistant' as const),
      content: msg.content,
      timestamp: msg.sent_at,
    }));
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
